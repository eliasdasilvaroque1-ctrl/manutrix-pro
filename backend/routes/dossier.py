"""
Dossiê Digital routes — RC P1 v1.0
Endpoints para edição e gestão do Dossiê Digital do Ativo.
RBAC: Somente Master Admin, Administrador e PCM podem editar.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Dict
from datetime import datetime, timezone
import uuid
import os
import logging
from pathlib import Path

from deps import (
    db, get_current_user, audit_log, verify_org_access
)

router = APIRouter()
logger = logging.getLogger("maintrix.dossier")

# Níveis de visibilidade
VISIBILITY_LEVELS = ["public", "authenticated", "restricted", "hidden"]

# Defaults: hidden para dados sensíveis, public para blocos informativos do QR
DEFAULT_VISIBILITY = {
    "technical_data": "public",
    "history": "hidden",
    "inspections": "hidden",
    "maintenance": "hidden",
    "documents": "hidden",
    "curiosity": "public",
    "warning": "public",
    "safety": "public",
    "best_practices": "public",
}

DOSSIER_DOC_TYPES = ["manual", "catalogo", "lista_pecas", "diagrama", "procedimento", "outro"]
ALLOWED_IMAGE_EXTS = [".jpg", ".jpeg", ".png", ".webp"]
ALLOWED_DOC_EXTS = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_DOC_SIZE = 20 * 1024 * 1024


def _check_dossier_edit(user: dict):
    """Valida permissão de edição do Dossiê."""
    if user.get("role") not in ("master", "admin", "pcm"):
        raise HTTPException(status_code=403, detail="Somente Master Admin, Administrador e PCM podem editar o Dossiê Digital")


def get_visibility(dossier: dict, block: str) -> str:
    """Retorna nível de visibilidade de um bloco com default seguro."""
    vis = (dossier or {}).get("visibility", {})
    return vis.get(block, DEFAULT_VISIBILITY.get(block, "hidden"))


# ============== DOSSIER CRUD ==============

@router.get("/ativos/{ativo_id}/dossier")
async def get_dossier(ativo_id: str, user: Dict = Depends(get_current_user)):
    """Retorna Dossiê Digital do ativo para edição."""
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    dossier = ativo.get("public_dossier") or {}
    # Preenche defaults de visibilidade
    vis = dossier.get("visibility", {})
    for block, default in DEFAULT_VISIBILITY.items():
        vis.setdefault(block, default)
    dossier["visibility"] = vis

    # Incluir documentos do dossiê
    docs = await db.dossier_documents.find(
        {"ativo_id": ativo_id, "organization_id": ativo.get("organization_id"), "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)

    return {
        "public_dossier": dossier,
        "public_status": ativo.get("public_status", "nao_informado"),
        "documents": docs,
    }


@router.put("/ativos/{ativo_id}/dossier")
async def update_dossier(ativo_id: str, body: dict, user: Dict = Depends(get_current_user)):
    """Atualiza Dossiê Digital. RBAC: Master/Admin/PCM."""
    _check_dossier_edit(user)

    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0, "id": 1, "organization_id": 1})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    update = {}

    # Campos de texto (opcionais, max 5000 chars)
    for field in ["description", "curiosity", "warning", "safety", "best_practices"]:
        if field in body:
            update[f"public_dossier.{field}"] = str(body[field] or "")[:5000]

    # Status público
    if "public_status" in body:
        valid = ["operando", "parado", "em_manutencao", "indisponivel", "standby", "nao_informado"]
        ps = body["public_status"]
        if ps not in valid:
            raise HTTPException(status_code=400, detail=f"Status invalido: {ps}")
        update["public_status"] = ps

    # Localização extra
    if "location" in body:
        loc = body["location"]
        for field in ["linha", "ponto_instalacao"]:
            if field in loc:
                update[f"public_dossier.location.{field}"] = str(loc[field] or "")[:200]

    # Dados técnicos adicionais (não duplicar os que já existem no ativo)
    if "technical_data" in body:
        td = body["technical_data"]
        for field in ["corrente", "frequencia"]:
            if field in td:
                update[f"public_dossier.technical_data.{field}"] = str(td[field] or "")[:200]

    # Visibilidade por bloco
    if "visibility" in body:
        vis = body["visibility"]
        for block, level in vis.items():
            if block in DEFAULT_VISIBILITY and level in VISIBILITY_LEVELS:
                update[f"public_dossier.visibility.{block}"] = level

    if not update:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    update["public_dossier.updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.ativos.update_one({"id": ativo_id}, {"$set": update})

    changes = [k.replace("public_dossier.", "") for k in update.keys() if k != "public_dossier.updated_at"]
    await audit_log("update_dossier", "ativos", ativo_id, user, f"Dossie atualizado: {', '.join(changes)}")

    updated = await db.ativos.find_one({"id": ativo_id}, {"_id": 0, "public_dossier": 1, "public_status": 1})
    return {"success": True, "public_dossier": updated.get("public_dossier", {}), "public_status": updated.get("public_status", "nao_informado")}


# ============== FOTO PÚBLICA ==============

@router.post("/ativos/{ativo_id}/dossier/photo")
async def upload_dossier_photo(ativo_id: str, file: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    """Upload foto pública do equipamento. RBAC: Master/Admin/PCM."""
    _check_dossier_edit(user)

    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0, "id": 1, "organization_id": 1})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail=f"Formato nao permitido. Use: {', '.join(ALLOWED_IMAGE_EXTS)}")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"Imagem excede limite de {MAX_IMAGE_SIZE // (1024*1024)}MB")
    if len(content) < 100:
        raise HTTPException(status_code=400, detail="Arquivo vazio ou corrompido")

    import storage as objstore
    if not objstore.is_available():
        raise HTTPException(status_code=500, detail="Armazenamento indisponivel")

    storage_path = objstore.upload_file("dossier_photos", ativo_id, file.filename, content, file.content_type or "image/jpeg")
    file_url = f"/api/storage/{storage_path}"

    # Registrar no file_registry como público
    org_id = ativo.get("organization_id", "")
    await db.file_registry.update_one(
        {"url": file_url},
        {"$set": {
            "url": file_url, "organization_id": org_id, "uploaded_by": user["id"],
            "is_public": True, "category": "dossier_photo",
            "storage_provider": "supabase", "storage_path": storage_path,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    # Salvar referência no ativo
    await db.ativos.update_one({"id": ativo_id}, {"$set": {
        "public_dossier.image_url": file_url,
        "public_dossier.updated_at": datetime.now(timezone.utc).isoformat()
    }})

    await audit_log("dossier_photo_upload", "ativos", ativo_id, user, f"Foto publica adicionada: {file.filename}")
    return {"success": True, "image_url": file_url}


@router.delete("/ativos/{ativo_id}/dossier/photo")
async def delete_dossier_photo(ativo_id: str, user: Dict = Depends(get_current_user)):
    """Remove foto pública do equipamento. RBAC: Master/Admin/PCM."""
    _check_dossier_edit(user)

    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0, "id": 1, "organization_id": 1, "public_dossier": 1})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    image_url = (ativo.get("public_dossier") or {}).get("image_url", "")
    if image_url:
        await db.file_registry.delete_one({"url": image_url})

    await db.ativos.update_one({"id": ativo_id}, {"$set": {
        "public_dossier.image_url": "",
        "public_dossier.updated_at": datetime.now(timezone.utc).isoformat()
    }})

    await audit_log("dossier_photo_delete", "ativos", ativo_id, user, "Foto publica removida")
    return {"success": True}


# ============== DOCUMENTOS PÚBLICOS ==============

@router.post("/ativos/{ativo_id}/dossier/documents")
async def upload_dossier_document(
    ativo_id: str,
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form("outro"),
    user: Dict = Depends(get_current_user)
):
    """Upload documento para o Dossiê Digital. RBAC: Master/Admin/PCM."""
    _check_dossier_edit(user)

    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0, "id": 1, "organization_id": 1})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    if doc_type not in DOSSIER_DOC_TYPES:
        doc_type = "outro"

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_DOC_EXTS:
        raise HTTPException(status_code=400, detail=f"Formato nao permitido. Use: {', '.join(ALLOWED_DOC_EXTS)}")

    content = await file.read()
    if len(content) > MAX_DOC_SIZE:
        raise HTTPException(status_code=400, detail=f"Arquivo excede limite de {MAX_DOC_SIZE // (1024*1024)}MB")
    if len(content) < 100:
        raise HTTPException(status_code=400, detail="Arquivo vazio ou corrompido")

    import storage as objstore
    if not objstore.is_available():
        raise HTTPException(status_code=500, detail="Armazenamento indisponivel")

    storage_path = objstore.upload_file("dossier_docs", ativo_id, file.filename, content, file.content_type or "application/octet-stream")
    file_url = f"/api/storage/{storage_path}"
    org_id = ativo.get("organization_id", "")

    doc_id = str(uuid.uuid4())
    doc = {
        "id": doc_id,
        "ativo_id": ativo_id,
        "organization_id": org_id,
        "title": str(title)[:200],
        "doc_type": doc_type,
        "filename": file.filename,
        "file_url": file_url,
        "storage_path": storage_path,
        "size_bytes": len(content),
        "mime_type": file.content_type,
        "is_published": False,
        "uploaded_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None,
    }
    await db.dossier_documents.insert_one(doc)
    doc.pop("_id", None)

    # Registrar no file_registry (NÃO público até is_published=True)
    await db.file_registry.update_one(
        {"url": file_url},
        {"$set": {
            "url": file_url, "organization_id": org_id, "uploaded_by": user["id"],
            "is_public": False, "category": "dossier_document",
            "storage_provider": "supabase", "storage_path": storage_path,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    await audit_log("dossier_doc_upload", "ativos", ativo_id, user, f"Documento dossie: {title} ({doc_type})")
    return doc


@router.put("/ativos/{ativo_id}/dossier/documents/{doc_id}/publish")
async def toggle_publish_document(ativo_id: str, doc_id: str, body: dict, user: Dict = Depends(get_current_user)):
    """Altera flag de publicação de documento do Dossiê. RBAC: Master/Admin/PCM."""
    _check_dossier_edit(user)

    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0, "id": 1, "organization_id": 1})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    doc = await db.dossier_documents.find_one({
        "id": doc_id, "ativo_id": ativo_id,
        "organization_id": ativo.get("organization_id"), "deleted_at": None
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    is_pub = bool(body.get("is_published", False))
    await db.dossier_documents.update_one({"id": doc_id}, {"$set": {"is_published": is_pub}})

    # Atualizar file_registry
    if doc.get("file_url"):
        await db.file_registry.update_one({"url": doc["file_url"]}, {"$set": {"is_public": is_pub}})

    action = "publicado" if is_pub else "despublicado"
    await audit_log("dossier_doc_publish", "ativos", ativo_id, user, f"Documento {doc.get('title','')} {action}")
    return {"success": True, "is_published": is_pub}


@router.delete("/ativos/{ativo_id}/dossier/documents/{doc_id}")
async def delete_dossier_document(ativo_id: str, doc_id: str, user: Dict = Depends(get_current_user)):
    """Remove documento do Dossiê Digital. RBAC: Master/Admin/PCM."""
    _check_dossier_edit(user)

    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0, "id": 1, "organization_id": 1})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    doc = await db.dossier_documents.find_one({
        "id": doc_id, "ativo_id": ativo_id,
        "organization_id": ativo.get("organization_id"), "deleted_at": None
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    now = datetime.now(timezone.utc).isoformat()
    await db.dossier_documents.update_one({"id": doc_id}, {"$set": {"deleted_at": now}})

    if doc.get("file_url"):
        await db.file_registry.delete_one({"url": doc["file_url"]})

    await audit_log("dossier_doc_delete", "ativos", ativo_id, user, f"Documento dossie removido: {doc.get('title','')}")
    return {"success": True}
