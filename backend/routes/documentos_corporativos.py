"""MAINTRIX — RC5.0: Biblioteca Corporativa de Documentos
Missão 1: CRUD, versionamento, auditoria, RBAC, multiempresa.
Missão 2: Upload, vínculo automático com OS, snapshot, confirmação de leitura.
Collection: documentos_corporativos
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
import uuid
import re
import logging
import hashlib

from deps import db, get_current_user
from routes.doc_config import archive_version

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== CONSTANTS ==============

DOCUMENT_TYPES = [
    "procedimento_operacional", "procedimento_manutencao", "instrucao_trabalho",
    "seguranca", "apr", "norma_interna", "manual", "checklist",
    "formulario", "documento_tecnico", "outro",
]

DOCUMENT_STATUSES = [
    "rascunho", "em_revisao", "aprovado", "publicado", "obsoleto", "arquivado",
]

ALLOWED_FILE_TYPES = [
    "application/pdf", "image/png", "image/jpeg", "image/webp",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain", "text/csv",
]

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


# ============== PYDANTIC MODELS ==============

class DocumentoCorporativo(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    document_type: str
    category: Optional[str] = None
    department: Optional[str] = None
    discipline: Optional[str] = None
    applicable_asset_types: List[str] = []
    applicable_asset_ids: List[str] = []
    applicable_work_order_types: List[str] = []
    applicable_areas: List[str] = []
    tags: List[str] = []
    revision: Optional[str] = None
    status: str = "rascunho"
    content: Optional[str] = Field(None, max_length=50000)
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    safety_document: bool = False
    requires_acknowledgement: bool = False
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    motivo_alteracao: Optional[str] = None

    @field_validator('document_type')
    @classmethod
    def validate_type(cls, v):
        if v not in DOCUMENT_TYPES:
            raise ValueError(f"Tipo inválido: {v}. Válidos: {', '.join(DOCUMENT_TYPES)}")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in DOCUMENT_STATUSES:
            raise ValueError(f"Status inválido: {v}. Válidos: {', '.join(DOCUMENT_STATUSES)}")
        return v

    @field_validator('code')
    @classmethod
    def sanitize_code(cls, v):
        if v:
            v = re.sub(r'[<>"\';]', '', v).strip()
        return v

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v):
        if v:
            v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
        return v


class StatusChange(BaseModel):
    status: str
    motivo: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in DOCUMENT_STATUSES:
            raise ValueError(f"Status inválido: {v}")
        return v


# ============== HELPERS ==============

def _require_editor(user):
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissão para esta operação")
    return user.get('organization_id', ''), user.get('id', '')


async def _audit_log(org_id: str, user_id: str, action: str, document_id: str, details: dict = None):
    """Record audit entry for document operations."""
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "user_id": user_id,
        "action": action,
        "entity_type": "documento_corporativo",
        "entity_id": document_id,
        "details": details or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


async def _check_unique_code(org_id: str, code: str, exclude_id: str = None):
    """Ensure code is unique within the organization."""
    if not code:
        return
    query = {"organization_id": org_id, "code": code, "deleted_at": None}
    if exclude_id:
        query["id"] = {"$ne": exclude_id}
    existing = await db.documentos_corporativos.find_one(query)
    if existing:
        raise HTTPException(status_code=409, detail=f"Código '{code}' já existe nesta empresa")


# ============== ENDPOINTS ==============

@router.get("/documentos-corporativos")
async def list_documentos(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    document_type: Optional[str] = None,
    category: Optional[str] = None,
    discipline: Optional[str] = None,
    status: Optional[str] = None,
    safety_document: Optional[bool] = None,
    effective_after: Optional[str] = None,
    expiration_before: Optional[str] = None,
    sort_by: str = Query("updated_at", regex="^(title|code|document_type|status|created_at|updated_at|version)$"),
    sort_order: int = Query(-1, ge=-1, le=1),
    user=Depends(get_current_user),
):
    """List documents with search, filters and pagination. Multi-tenant isolated."""
    org_id = user.get('organization_id', '')
    role = user.get('role', '')

    query = {"organization_id": org_id, "deleted_at": None}

    # Técnico only sees published
    if role == 'tecnico':
        query["status"] = "publicado"
        query["is_active"] = True

    if search:
        search_re = {"$regex": re.escape(search), "$options": "i"}
        query["$or"] = [{"title": search_re}, {"code": search_re}, {"description": search_re}, {"tags": search_re}]

    if document_type:
        query["document_type"] = document_type
    if category:
        query["category"] = category
    if discipline:
        query["discipline"] = discipline
    if status and role != 'tecnico':
        query["status"] = status
    if safety_document is not None:
        query["safety_document"] = safety_document
    if effective_after:
        query["effective_date"] = {"$gte": effective_after}
    if expiration_before:
        query.setdefault("expiration_date", {})
        if isinstance(query["expiration_date"], dict):
            query["expiration_date"]["$lte"] = expiration_before
        else:
            query["expiration_date"] = {"$lte": expiration_before}

    total = await db.documentos_corporativos.count_documents(query)
    skip = (page - 1) * per_page
    sort_dir = sort_order if sort_order != 0 else -1

    items = await db.documentos_corporativos.find(query, {"_id": 0}).sort(sort_by, sort_dir).skip(skip).limit(per_page).to_list(per_page)

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": ceil(total / per_page) if total > 0 else 0,
    }


@router.get("/documentos-corporativos/{doc_id}")
async def get_documento(doc_id: str, user=Depends(get_current_user)):
    """Get a single document by ID. Multi-tenant isolated."""
    org_id = user.get('organization_id', '')
    role = user.get('role', '')

    doc = await db.documentos_corporativos.find_one({"id": doc_id, "organization_id": org_id, "deleted_at": None}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    # Técnico only sees published
    if role == 'tecnico' and doc.get('status') != 'publicado':
        raise HTTPException(status_code=403, detail="Documento não disponível")

    return doc


@router.post("/documentos-corporativos")
async def create_documento(body: DocumentoCorporativo, user=Depends(get_current_user)):
    """Create a new corporate document."""
    org_id, user_id = _require_editor(user)
    await _check_unique_code(org_id, body.code)

    # Validate file_type if present
    if body.file_type and body.file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo de arquivo não permitido: {body.file_type}")
    if body.file_size and body.file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"Arquivo excede o limite de {MAX_FILE_SIZE // (1024*1024)}MB")

    doc = body.model_dump(exclude={"motivo_alteracao"})
    doc.update({
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "version": 1,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user_id,
        "deleted_at": None,
        "deleted_by": None,
    })
    await db.documentos_corporativos.insert_one(doc)
    await archive_version("documento_corporativo", doc, user_id, "Criação inicial")
    await _audit_log(org_id, user_id, "create", doc["id"], {"title": doc["title"], "status": doc["status"]})

    return {"id": doc["id"], "version": 1, "status": "created"}


@router.put("/documentos-corporativos/{doc_id}")
async def update_documento(doc_id: str, body: DocumentoCorporativo, user=Depends(get_current_user)):
    """Update a document. If published, increments version."""
    org_id, user_id = _require_editor(user)

    existing = await db.documentos_corporativos.find_one({"id": doc_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    await _check_unique_code(org_id, body.code, exclude_id=doc_id)

    update = body.model_dump(exclude={"motivo_alteracao"})
    new_version = existing.get("version", 1)

    # If document was published/approved, editing creates new version
    if existing.get("status") in ("publicado", "aprovado"):
        new_version += 1

    update["version"] = new_version
    # Preserve status if body sends default "rascunho" and existing was different
    if update.get("status") == "rascunho" and existing.get("status") not in (None, "rascunho"):
        update["status"] = existing.get("status")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = user_id

    await db.documentos_corporativos.update_one({"id": doc_id, "organization_id": org_id}, {"$set": update})

    updated_doc = await db.documentos_corporativos.find_one({"id": doc_id}, {"_id": 0})
    await archive_version("documento_corporativo", updated_doc, user_id, body.motivo_alteracao or f"Atualização v{new_version}")
    await _audit_log(org_id, user_id, "update", doc_id, {
        "title": update.get("title"), "version": new_version,
        "motivo": body.motivo_alteracao, "status_anterior": existing.get("status"), "status_novo": update.get("status"),
    })

    return {"status": "updated", "version": new_version}


@router.patch("/documentos-corporativos/{doc_id}/status")
async def change_status(doc_id: str, body: StatusChange, user=Depends(get_current_user)):
    """Change document status (publish, archive, etc.)."""
    org_id, user_id = _require_editor(user)

    existing = await db.documentos_corporativos.find_one({"id": doc_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    old_status = existing.get("status", "rascunho")

    # PCM can only publish if explicitly allowed (admin/master can always)
    role = user.get('role', '')
    if body.status == 'publicado' and role == 'pcm':
        pass  # PCM allowed to publish per CTO spec

    await db.documentos_corporativos.update_one(
        {"id": doc_id, "organization_id": org_id},
        {"$set": {"status": body.status, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user_id}}
    )

    updated_doc = await db.documentos_corporativos.find_one({"id": doc_id}, {"_id": 0})
    await archive_version("documento_corporativo", updated_doc, user_id, body.motivo or f"Status: {old_status} → {body.status}")
    await _audit_log(org_id, user_id, "status_change", doc_id, {
        "status_anterior": old_status, "status_novo": body.status, "motivo": body.motivo,
    })

    return {"status": body.status, "previous": old_status}


@router.delete("/documentos-corporativos/{doc_id}")
async def delete_documento(doc_id: str, user=Depends(get_current_user)):
    """Soft-delete a document."""
    org_id, user_id = _require_editor(user)

    existing = await db.documentos_corporativos.find_one({"id": doc_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    await archive_version("documento_corporativo", existing, user_id, "Exclusão")
    await db.documentos_corporativos.update_one(
        {"id": doc_id, "organization_id": org_id},
        {"$set": {
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": user_id,
            "is_active": False,
        }}
    )
    await _audit_log(org_id, user_id, "delete", doc_id, {"title": existing.get("title")})

    return {"status": "deleted"}


@router.post("/documentos-corporativos/{doc_id}/restaurar")
async def restaurar_documento(doc_id: str, user=Depends(get_current_user)):
    """Restore a soft-deleted document."""
    org_id, user_id = _require_editor(user)

    existing = await db.documentos_corporativos.find_one({"id": doc_id, "organization_id": org_id, "deleted_at": {"$ne": None}})
    if not existing:
        raise HTTPException(status_code=404, detail="Documento excluído não encontrado")

    await db.documentos_corporativos.update_one(
        {"id": doc_id, "organization_id": org_id},
        {"$set": {"deleted_at": None, "deleted_by": None, "is_active": True, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user_id}}
    )
    await _audit_log(org_id, user_id, "restore", doc_id, {"title": existing.get("title")})

    return {"status": "restored"}


@router.get("/documentos-corporativos/{doc_id}/versoes")
async def list_versoes(doc_id: str, user=Depends(get_current_user)):
    """List all versions of a document."""
    org_id = user.get('organization_id', '')
    versions = await db.biblioteca_versoes.find(
        {"item_type": "documento_corporativo", "item_id": doc_id, "organization_id": org_id},
        {"_id": 0}
    ).sort("versao", -1).to_list(100)
    return versions


@router.post("/documentos-corporativos/{doc_id}/restaurar-versao/{versao}")
async def restaurar_versao(doc_id: str, versao: int, motivo: str = Query("Restauração de versão"), user=Depends(get_current_user)):
    """Restore a document to a previous version."""
    org_id, user_id = _require_editor(user)

    target = await db.biblioteca_versoes.find_one(
        {"item_type": "documento_corporativo", "item_id": doc_id, "organization_id": org_id, "versao": versao},
        {"_id": 0}
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Versão {versao} não encontrada")

    current = await db.documentos_corporativos.find_one({"id": doc_id, "organization_id": org_id, "deleted_at": None})
    if not current:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    snapshot = target["snapshot"]
    new_version = (current.get("version") or 0) + 1
    restore_data = {k: v for k, v in snapshot.items() if k not in ("id", "organization_id", "version", "created_at", "created_by", "updated_at", "updated_by", "deleted_at", "deleted_by")}
    restore_data["version"] = new_version
    restore_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    restore_data["updated_by"] = user_id
    restore_data["deleted_at"] = None

    await db.documentos_corporativos.update_one({"id": doc_id, "organization_id": org_id}, {"$set": restore_data})
    restored_doc = await db.documentos_corporativos.find_one({"id": doc_id}, {"_id": 0})
    await archive_version("documento_corporativo", restored_doc, user_id, f"Restaurado de v{versao}: {motivo}")
    await _audit_log(org_id, user_id, "restore_version", doc_id, {"versao_restaurada": versao, "nova_versao": new_version, "motivo": motivo})

    return {"status": "restored", "versao_restaurada": versao, "nova_versao": new_version}


@router.get("/documentos-corporativos/{doc_id}/audit")
async def get_audit_log(doc_id: str, user=Depends(get_current_user)):
    """Get audit log for a document. Admin/PCM only."""
    org_id = user.get('organization_id', '')
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissão")
    logs = await db.audit_logs.find(
        {"entity_type": "documento_corporativo", "entity_id": doc_id, "organization_id": org_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return logs


@router.get("/documentos-corporativos-stats")
async def get_stats(user=Depends(get_current_user)):
    """Get document counts by status for KPI indicators."""
    org_id = user.get('organization_id', '')
    base = {"organization_id": org_id, "deleted_at": None}
    total = await db.documentos_corporativos.count_documents(base)
    publicados = await db.documentos_corporativos.count_documents({**base, "status": "publicado"})
    em_revisao = await db.documentos_corporativos.count_documents({**base, "status": "em_revisao"})
    obsoletos = await db.documentos_corporativos.count_documents({**base, "status": "obsoleto"})
    arquivados = await db.documentos_corporativos.count_documents({**base, "status": "arquivado"})
    rascunhos = await db.documentos_corporativos.count_documents({**base, "status": "rascunho"})
    seguranca = await db.documentos_corporativos.count_documents({**base, "safety_document": True})
    return {"total": total, "publicados": publicados, "em_revisao": em_revisao, "obsoletos": obsoletos, "arquivados": arquivados, "rascunhos": rascunhos, "seguranca": seguranca}


@router.post("/documentos-corporativos/{doc_id}/duplicar")
async def duplicar_documento(doc_id: str, user=Depends(get_current_user)):
    """Duplicate a document as a new draft with auto-generated code."""
    org_id, user_id = _require_editor(user)
    source = await db.documentos_corporativos.find_one({"id": doc_id, "organization_id": org_id, "deleted_at": None}, {"_id": 0})
    if not source:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    new_id = str(uuid.uuid4())
    new_code = f"{source.get('code', 'DOC')}-COPY-{new_id[:4].upper()}" if source.get('code') else None
    new_doc = {k: v for k, v in source.items() if k not in ("_id", "id", "version", "created_at", "created_by", "updated_at", "updated_by")}
    new_doc.update({
        "id": new_id,
        "title": f"{source['title']} (Cópia)",
        "code": new_code,
        "version": 1,
        "status": "rascunho",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user_id,
        "deleted_at": None,
        "deleted_by": None,
    })
    await db.documentos_corporativos.insert_one(new_doc)
    await archive_version("documento_corporativo", new_doc, user_id, f"Duplicado de {source.get('title')}")
    await _audit_log(org_id, user_id, "duplicate", new_id, {"source_id": doc_id, "source_title": source.get("title")})

    return {"id": new_id, "title": new_doc["title"], "code": new_code, "status": "created"}


# ============== MISSÃO 2: UPLOAD ==============

UPLOAD_ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.png', '.jpg', '.jpeg'}
UPLOAD_ALLOWED_MIMES = {
    'application/pdf', 'image/png', 'image/jpeg',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}
UPLOAD_MAX_SIZE = 25 * 1024 * 1024  # 25MB


def _safe_filename(name: str) -> str:
    """Sanitize filename: remove path traversal, special chars."""
    name = Path(name).name  # strip path
    name = re.sub(r'[^\w.\-]', '_', name)
    return name[:100]


@router.post("/documentos-corporativos/{doc_id}/upload")
async def upload_document_file(doc_id: str, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload or replace file for a corporate document. Keeps version history."""
    org_id, user_id = _require_editor(user)

    doc = await db.documentos_corporativos.find_one({"id": doc_id, "organization_id": org_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in UPLOAD_ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extensão não permitida: {ext}. Permitidas: {', '.join(UPLOAD_ALLOWED_EXTENSIONS)}")

    # Read and validate size
    content = await file.read()
    if len(content) > UPLOAD_MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"Arquivo excede {UPLOAD_MAX_SIZE // (1024*1024)}MB")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    # Validate MIME
    mime = file.content_type or ''
    if mime and mime not in UPLOAD_ALLOWED_MIMES and ext not in ('.jpg', '.jpeg', '.png'):
        raise HTTPException(status_code=400, detail=f"Tipo MIME não permitido: {mime}")

    safe_name = _safe_filename(file.filename)
    file_hash = hashlib.sha256(content).hexdigest()[:16]

    # Try object storage first, fallback to local
    try:
        from server import objstore, UPLOAD_DIR
        if objstore.is_available():
            storage_path = objstore.upload_file("docs", org_id, f"{doc_id}_{safe_name}", content, mime or "application/octet-stream")
            file_url = f"/api/storage/{storage_path}"
        else:
            filename = f"doc_{doc_id}_{uuid.uuid4().hex[:8]}{ext}"
            filepath = UPLOAD_DIR / filename
            with open(filepath, 'wb') as f:
                f.write(content)
            file_url = f"/api/uploads/{filename}"
    except Exception as e:
        logger.warning(f"Upload storage error: {e}")
        filename = f"doc_{doc_id}_{uuid.uuid4().hex[:8]}{ext}"
        import aiofiles
        upload_dir = Path("/app/backend/uploads")
        upload_dir.mkdir(exist_ok=True)
        async with aiofiles.open(upload_dir / filename, 'wb') as f:
            await f.write(content)
        file_url = f"/api/uploads/{filename}"

    # Archive old file info before updating
    old_file = {k: doc.get(k) for k in ('file_url', 'file_name', 'file_type', 'file_size') if doc.get(k)}
    if old_file:
        await db.documentos_file_history.insert_one({
            "id": str(uuid.uuid4()), "document_id": doc_id, "organization_id": org_id,
            **old_file, "replaced_at": datetime.now(timezone.utc).isoformat(), "replaced_by": user_id,
        })

    # Update document with new file
    await db.documentos_corporativos.update_one(
        {"id": doc_id, "organization_id": org_id},
        {"$set": {
            "file_url": file_url, "file_name": safe_name, "file_type": mime or ext,
            "file_size": len(content), "file_hash": file_hash,
            "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user_id,
        }}
    )
    await _audit_log(org_id, user_id, "upload", doc_id, {"file_name": safe_name, "file_size": len(content), "file_hash": file_hash})

    return {"file_url": file_url, "file_name": safe_name, "file_size": len(content), "status": "uploaded"}


# ============== MISSÃO 2: VÍNCULO AUTOMÁTICO ==============

@router.get("/documentos-corporativos/vinculo-automatico/{os_id}")
async def get_documentos_vinculados(os_id: str, user=Depends(get_current_user)):
    """Get all published documents applicable to a specific OS, matched by area/ativo/tipo/disciplina."""
    org_id = user.get('organization_id', '')

    os_doc = await db.ordens_servico.find_one({"id": os_id, "organization_id": org_id}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")

    tipo_os = os_doc.get("tipo", "")
    disciplina = os_doc.get("disciplina", "")
    ativo_id = os_doc.get("ativo_id", "")

    # Get asset info for matching
    ativo = await db.ativos.find_one({"id": ativo_id}, {"_id": 0, "tipo": 1, "area": 1, "setor": 1, "tag": 1}) if ativo_id else {}
    ativo_tipo = (ativo or {}).get("tipo", "")
    ativo_area = (ativo or {}).get("area", "") or (ativo or {}).get("setor", "")

    # Query: published docs in this org that match any applicable criteria
    query = {
        "organization_id": org_id,
        "status": "publicado",
        "deleted_at": None,
        "is_active": True,
    }

    all_docs = await db.documentos_corporativos.find(query, {"_id": 0}).sort("title", 1).to_list(200)

    # Filter by applicability
    matched = []
    for doc in all_docs:
        score = 0
        app_types = doc.get("applicable_work_order_types", [])
        app_assets = doc.get("applicable_asset_types", [])
        app_asset_ids = doc.get("applicable_asset_ids", [])
        app_areas = doc.get("applicable_areas", [])
        app_discipline = doc.get("discipline", "")

        # Universal docs (no restrictions) always match
        if not app_types and not app_assets and not app_asset_ids and not app_areas:
            score = 1
        else:
            if app_types and tipo_os in app_types:
                score += 10
            if app_assets and ativo_tipo and ativo_tipo in app_assets:
                score += 10
            if app_asset_ids and ativo_id in app_asset_ids:
                score += 20
            if app_areas and ativo_area and ativo_area in app_areas:
                score += 5

        # Discipline match
        if app_discipline and disciplina and app_discipline == disciplina:
            score += 5

        if score > 0:
            doc["_match_score"] = score
            matched.append(doc)

    # Sort by score descending, then safety docs first
    matched.sort(key=lambda d: (-d.get("_match_score", 0), -int(d.get("safety_document", False)), d.get("title", "")))

    # Clean score from response
    for doc in matched:
        doc.pop("_match_score", None)

    await _audit_log(org_id, user.get('id', ''), "vinculo_automatico", os_id, {"matched_count": len(matched), "tipo_os": tipo_os, "ativo_id": ativo_id})

    return {"os_id": os_id, "documentos": matched, "total": len(matched)}


# ============== MISSÃO 2: CONFIRMAÇÃO DE LEITURA ==============

class ConfirmacaoLeitura(BaseModel):
    documento_id: str
    versao_lida: int = 1


@router.post("/documentos-corporativos/confirmar-leitura/{os_id}")
async def confirmar_leitura(os_id: str, body: ConfirmacaoLeitura, user=Depends(get_current_user)):
    """Register acknowledgement that user has read a document for an OS."""
    org_id = user.get('organization_id', '')
    user_id = user.get('id', '')

    # Validate OS exists
    os_doc = await db.ordens_servico.find_one({"id": os_id, "organization_id": org_id})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")

    # Validate document exists
    doc = await db.documentos_corporativos.find_one({"id": body.documento_id, "organization_id": org_id, "deleted_at": None}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    # Check if already confirmed
    existing = await db.confirmacoes_leitura.find_one({
        "os_id": os_id, "documento_id": body.documento_id, "user_id": user_id, "organization_id": org_id
    })
    if existing:
        return {"status": "already_confirmed", "confirmed_at": existing.get("confirmed_at")}

    confirmation = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "os_id": os_id,
        "documento_id": body.documento_id,
        "documento_code": doc.get("code"),
        "documento_title": doc.get("title"),
        "versao_lida": body.versao_lida or doc.get("version", 1),
        "user_id": user_id,
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.confirmacoes_leitura.insert_one(confirmation)
    await _audit_log(org_id, user_id, "confirmacao_leitura", body.documento_id, {
        "os_id": os_id, "versao": body.versao_lida or doc.get("version", 1),
    })

    return {"status": "confirmed", "confirmed_at": confirmation["confirmed_at"]}


@router.get("/documentos-corporativos/confirmacoes/{os_id}")
async def get_confirmacoes(os_id: str, user=Depends(get_current_user)):
    """Get all reading confirmations for an OS."""
    org_id = user.get('organization_id', '')
    confirmations = await db.confirmacoes_leitura.find(
        {"os_id": os_id, "organization_id": org_id}, {"_id": 0}
    ).to_list(200)
    return confirmations


@router.get("/documentos-corporativos/pendentes-confirmacao/{os_id}")
async def get_pendentes_confirmacao(os_id: str, user=Depends(get_current_user)):
    """Check if all required documents have been acknowledged before OS can start."""
    org_id = user.get('organization_id', '')
    user_id = user.get('id', '')

    # Get matched documents that require acknowledgement
    vinculo = await get_documentos_vinculados(os_id, user)
    required = [d for d in vinculo["documentos"] if d.get("requires_acknowledgement")]

    if not required:
        return {"all_confirmed": True, "pending": [], "total_required": 0}

    confirmed_ids = set()
    confirmations = await db.confirmacoes_leitura.find(
        {"os_id": os_id, "user_id": user_id, "organization_id": org_id}, {"_id": 0}
    ).to_list(100)
    for c in confirmations:
        confirmed_ids.add(c.get("documento_id"))

    pending = [{"id": d["id"], "title": d["title"], "code": d.get("code")} for d in required if d["id"] not in confirmed_ids]

    return {"all_confirmed": len(pending) == 0, "pending": pending, "total_required": len(required), "confirmed": len(required) - len(pending)}


# ============== MISSÃO 2: SNAPSHOT NA OS ==============

@router.post("/documentos-corporativos/snapshot/{os_id}")
async def create_snapshot(os_id: str, user=Depends(get_current_user)):
    """Freeze applicable documents into the OS at execution start."""
    org_id = user.get('organization_id', '')
    user_id = user.get('id', '')

    os_doc = await db.ordens_servico.find_one({"id": os_id, "organization_id": org_id})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")

    # Get matched documents
    vinculo = await get_documentos_vinculados(os_id, user)
    docs = vinculo.get("documentos", [])

    snapshots = []
    for doc in docs:
        snap = {
            "documento_id": doc["id"],
            "code": doc.get("code"),
            "title": doc.get("title"),
            "version": doc.get("version", 1),
            "document_type": doc.get("document_type"),
            "safety_document": doc.get("safety_document", False),
            "content_preview": (doc.get("content") or "")[:500],
            "file_url": doc.get("file_url"),
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }
        snapshots.append(snap)

    await db.ordens_servico.update_one(
        {"id": os_id, "organization_id": org_id},
        {"$set": {
            "documentos_snapshot": snapshots,
            "documentos_snapshot_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    await _audit_log(org_id, user_id, "snapshot_documentos", os_id, {"count": len(snapshots)})

    return {"status": "snapshot_created", "documents_frozen": len(snapshots)}
