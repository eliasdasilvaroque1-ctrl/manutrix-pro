"""MAINTRIX — Document Configuration & Corporate Library Routes
Configurable document templates, versioned procedures, safety, and print settings per organization.
Sprint 1: Full version governance — every edit creates an immutable version in biblioteca_versoes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
import logging

from deps import db, get_current_user, is_admin

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class DocConfigUpdate(BaseModel):
    identidade_doc: Optional[dict] = None
    os_config: Optional[dict] = None
    inspecao_config: Optional[dict] = None
    foto_config: Optional[dict] = None
    assinatura_config: Optional[dict] = None

class ProcedimentoPadrao(BaseModel):
    nome: str
    codigo: Optional[str] = None
    tipo_atividade: Optional[str] = None
    disciplina: Optional[str] = None
    equipamentos: List[str] = []
    objetivo: Optional[str] = None
    pre_requisitos: Optional[str] = None
    etapas: List[dict] = []
    ferramentas: List[str] = []
    materiais: List[str] = []
    observacoes: Optional[str] = None
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None

class SegurancaPadrao(BaseModel):
    nome: str
    codigo: Optional[str] = None
    tipo_atividade: Optional[str] = None
    disciplina: Optional[str] = None
    equipamentos: List[str] = []
    riscos: List[dict] = []
    medidas_controle: List[str] = []
    epis: List[str] = []
    epcs: List[str] = []
    loto: Optional[dict] = None
    apr: Optional[dict] = None
    pt: Optional[dict] = None
    bloqueios: List[dict] = []
    observacoes: Optional[str] = None
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None


# ============== VERSION GOVERNANCE HELPERS ==============

async def archive_version(item_type: str, item_doc: dict, user_id: str, motivo: str = None):
    """Archive current version of a library item before mutation. Creates immutable snapshot."""
    snapshot = {k: v for k, v in item_doc.items() if k != '_id'}
    version_doc = {
        "id": str(uuid.uuid4()),
        "item_type": item_type,
        "item_id": item_doc["id"],
        "organization_id": item_doc.get("organization_id", ""),
        "versao": item_doc.get("versao") or item_doc.get("version", 1),
        "snapshot": snapshot,
        "motivo": motivo,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
    }
    await db.biblioteca_versoes.insert_one(version_doc)
    return version_doc


def require_editor(user):
    """Validate user has editor role (master/admin/pcm)."""
    if user.get('role', '') not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissao")
    return user.get('organization_id', ''), user.get('id', '')


# ============== DOC CONFIG CRUD ==============

@router.get("/doc-config")
async def get_doc_config(user=Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    config = await db.doc_config.find_one({"organization_id": org_id}, {"_id": 0})
    if not config:
        config = {"organization_id": org_id, "identidade_doc": {}, "os_config": {}, "inspecao_config": {}, "foto_config": {"classificacoes": ["antes", "durante", "depois", "falha", "componente", "seguranca", "outra"], "legenda_obrigatoria": False, "grid_colunas": 2, "max_por_pagina": 4}, "assinatura_config": {}}
    return config


@router.put("/doc-config")
async def update_doc_config(body: DocConfigUpdate, user=Depends(get_current_user)):
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Somente Admin, Master ou PCM podem configurar documentos")
    org_id = user.get('organization_id', '')
    update = {"organization_id": org_id, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.get('id')}
    for field in ['identidade_doc', 'os_config', 'inspecao_config', 'foto_config', 'assinatura_config']:
        val = getattr(body, field, None)
        if val is not None:
            update[field] = val
    await db.doc_config.update_one({"organization_id": org_id}, {"$set": update}, upsert=True)
    return {"status": "ok"}


# ============== PROCEDIMENTOS PADRÃO (VERSIONADOS) ==============

@router.get("/doc-config/procedimentos")
async def list_procedimentos(user=Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    items = await db.procedimentos_padrao.find({"organization_id": org_id, "deleted_at": None}, {"_id": 0}).sort("nome", 1).to_list(500)
    return items


@router.post("/doc-config/procedimentos")
async def create_procedimento(body: ProcedimentoPadrao, user=Depends(get_current_user)):
    org_id, user_id = require_editor(user)
    doc = body.model_dump(exclude={"motivo_alteracao"})
    doc.update({
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "versao": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
        "updated_at": None,
        "deleted_at": None,
    })
    await db.procedimentos_padrao.insert_one(doc)
    # Archive v1 as the initial version
    await archive_version("procedimento", doc, user_id, "Criação inicial")
    return {"id": doc["id"], "versao": 1, "status": "created"}


@router.put("/doc-config/procedimentos/{proc_id}")
async def update_procedimento(proc_id: str, body: ProcedimentoPadrao, user=Depends(get_current_user)):
    org_id, user_id = require_editor(user)
    existing = await db.procedimentos_padrao.find_one({"id": proc_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Procedimento nao encontrado")
    # Apply update
    update = body.model_dump(exclude={"motivo_alteracao"})
    new_version = (existing.get("versao") or 0) + 1
    update["versao"] = new_version
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = user_id
    await db.procedimentos_padrao.update_one({"id": proc_id, "organization_id": org_id}, {"$set": update})
    # Archive new version (one entry per version, always AFTER mutation)
    updated_doc = await db.procedimentos_padrao.find_one({"id": proc_id}, {"_id": 0})
    await archive_version("procedimento", updated_doc, user_id, body.motivo_alteracao or f"Atualização para v{new_version}")
    return {"status": "updated", "versao": new_version}


@router.delete("/doc-config/procedimentos/{proc_id}")
async def delete_procedimento(proc_id: str, user=Depends(get_current_user)):
    org_id, user_id = require_editor(user)
    existing = await db.procedimentos_padrao.find_one({"id": proc_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    # Archive before soft delete
    await archive_version("procedimento", existing, user_id, "Exclusão")
    await db.procedimentos_padrao.update_one({"id": proc_id, "organization_id": org_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat(), "deleted_by": user_id}})
    return {"status": "deleted"}


@router.get("/doc-config/procedimentos/{proc_id}/versoes")
async def list_procedimento_versoes(proc_id: str, user=Depends(get_current_user)):
    """List all versions of a procedure, most recent first."""
    org_id = user.get('organization_id', '')
    versions = await db.biblioteca_versoes.find(
        {"item_type": "procedimento", "item_id": proc_id, "organization_id": org_id},
        {"_id": 0}
    ).sort("versao", -1).to_list(100)
    return versions


@router.post("/doc-config/procedimentos/{proc_id}/restaurar/{versao}")
async def restaurar_procedimento(proc_id: str, versao: int, motivo: str = Query("Restauração de versão anterior"), user=Depends(get_current_user)):
    """Restore a procedure to a previous version. Creates a new version with the old data."""
    org_id, user_id = require_editor(user)
    target = await db.biblioteca_versoes.find_one(
        {"item_type": "procedimento", "item_id": proc_id, "organization_id": org_id, "versao": versao},
        {"_id": 0}
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Versão {versao} não encontrada")
    current = await db.procedimentos_padrao.find_one({"id": proc_id, "organization_id": org_id, "deleted_at": None})
    if not current:
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    # Restore from snapshot — creates new incremented version
    snapshot = target["snapshot"]
    new_version = (current.get("versao") or 0) + 1
    restore_data = {k: v for k, v in snapshot.items() if k not in ("id", "organization_id", "versao", "created_at", "created_by", "updated_at", "updated_by", "deleted_at")}
    restore_data["versao"] = new_version
    restore_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    restore_data["updated_by"] = user_id
    restore_data["deleted_at"] = None
    await db.procedimentos_padrao.update_one({"id": proc_id, "organization_id": org_id}, {"$set": restore_data})
    # Archive the restored version (one entry per version)
    restored_doc = await db.procedimentos_padrao.find_one({"id": proc_id}, {"_id": 0})
    await archive_version("procedimento", restored_doc, user_id, f"Restaurado de v{versao}: {motivo}")
    return {"status": "restored", "versao_restaurada": versao, "nova_versao": new_version}


# ============== SEGURANÇA PADRÃO (VERSIONADA) ==============

@router.get("/doc-config/seguranca")
async def list_seguranca(user=Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    items = await db.seguranca_padrao.find({"organization_id": org_id, "deleted_at": None}, {"_id": 0}).sort("nome", 1).to_list(500)
    return items


@router.post("/doc-config/seguranca")
async def create_seguranca(body: SegurancaPadrao, user=Depends(get_current_user)):
    org_id, user_id = require_editor(user)
    doc = body.model_dump(exclude={"motivo_alteracao"})
    doc.update({
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "versao": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
        "updated_at": None,
        "deleted_at": None,
    })
    await db.seguranca_padrao.insert_one(doc)
    await archive_version("seguranca", doc, user_id, "Criação inicial")
    return {"id": doc["id"], "versao": 1, "status": "created"}


@router.put("/doc-config/seguranca/{seg_id}")
async def update_seguranca(seg_id: str, body: SegurancaPadrao, user=Depends(get_current_user)):
    org_id, user_id = require_editor(user)
    existing = await db.seguranca_padrao.find_one({"id": seg_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    update = body.model_dump(exclude={"motivo_alteracao"})
    new_version = (existing.get("versao") or 0) + 1
    update["versao"] = new_version
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = user_id
    await db.seguranca_padrao.update_one({"id": seg_id, "organization_id": org_id}, {"$set": update})
    # Archive new version (one entry per version)
    updated_doc = await db.seguranca_padrao.find_one({"id": seg_id}, {"_id": 0})
    await archive_version("seguranca", updated_doc, user_id, body.motivo_alteracao or f"Atualização para v{new_version}")
    return {"status": "updated", "versao": new_version}


@router.delete("/doc-config/seguranca/{seg_id}")
async def delete_seguranca(seg_id: str, user=Depends(get_current_user)):
    org_id, user_id = require_editor(user)
    existing = await db.seguranca_padrao.find_one({"id": seg_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    await archive_version("seguranca", existing, user_id, "Exclusão")
    await db.seguranca_padrao.update_one({"id": seg_id, "organization_id": org_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat(), "deleted_by": user_id}})
    return {"status": "deleted"}


@router.get("/doc-config/seguranca/{seg_id}/versoes")
async def list_seguranca_versoes(seg_id: str, user=Depends(get_current_user)):
    """List all versions of a safety template, most recent first."""
    org_id = user.get('organization_id', '')
    versions = await db.biblioteca_versoes.find(
        {"item_type": "seguranca", "item_id": seg_id, "organization_id": org_id},
        {"_id": 0}
    ).sort("versao", -1).to_list(100)
    return versions


@router.post("/doc-config/seguranca/{seg_id}/restaurar/{versao}")
async def restaurar_seguranca(seg_id: str, versao: int, motivo: str = Query("Restauração de versão anterior"), user=Depends(get_current_user)):
    """Restore a safety template to a previous version."""
    org_id, user_id = require_editor(user)
    target = await db.biblioteca_versoes.find_one(
        {"item_type": "seguranca", "item_id": seg_id, "organization_id": org_id, "versao": versao},
        {"_id": 0}
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Versão {versao} não encontrada")
    current = await db.seguranca_padrao.find_one({"id": seg_id, "organization_id": org_id, "deleted_at": None})
    if not current:
        raise HTTPException(status_code=404, detail="Modelo de segurança não encontrado")
    snapshot = target["snapshot"]
    new_version = (current.get("versao") or 0) + 1
    restore_data = {k: v for k, v in snapshot.items() if k not in ("id", "organization_id", "versao", "created_at", "created_by", "updated_at", "updated_by", "deleted_at")}
    restore_data["versao"] = new_version
    restore_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    restore_data["updated_by"] = user_id
    restore_data["deleted_at"] = None
    await db.seguranca_padrao.update_one({"id": seg_id, "organization_id": org_id}, {"$set": restore_data})
    restored_doc = await db.seguranca_padrao.find_one({"id": seg_id}, {"_id": 0})
    await archive_version("seguranca", restored_doc, user_id, f"Restaurado de v{versao}: {motivo}")
    return {"status": "restored", "versao_restaurada": versao, "nova_versao": new_version}
