"""MAINTRIX — Sprint 2: Biblioteca Corporativa — Conteúdo Reutilizável
Checklists, Modelos de Inspeção e Modelos de OS — todos versionados.
Collections: checklists_padrao, modelos_inspecao, modelos_os
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import logging

from deps import db, get_current_user
from routes.doc_config import archive_version, require_editor

router = APIRouter()
logger = logging.getLogger(__name__)

INDEXES = {
    "checklists_padrao": [
        {"keys": [("organization_id", 1), ("deleted_at", 1)], "name": "org_active"},
    ],
    "modelos_inspecao": [
        {"keys": [("organization_id", 1), ("deleted_at", 1)], "name": "org_active"},
    ],
    "modelos_os": [
        {"keys": [("organization_id", 1), ("deleted_at", 1)], "name": "org_active"},
    ],
}


# ============== PYDANTIC MODELS ==============

class ChecklistPadrao(BaseModel):
    nome: str
    descricao: Optional[str] = None
    disciplina: Optional[str] = None
    categoria: Optional[str] = None
    itens: List[dict] = []  # [{descricao, tipo, tolerancia_min, tolerancia_max, unidade, obrigatorio, opcoes, ordem}]
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None


class ModeloInspecao(BaseModel):
    nome: str
    tipo: Optional[str] = None
    disciplina: Optional[str] = None
    checklist_id: Optional[str] = None
    checklist_snapshot: Optional[dict] = None
    procedimento_id: Optional[str] = None
    procedimento_snapshot: Optional[dict] = None
    seguranca_id: Optional[str] = None
    seguranca_snapshot: Optional[dict] = None
    campos_obrigatorios: List[str] = []
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None


class ModeloOS(BaseModel):
    nome: str
    tipo_os: Optional[str] = None
    disciplina: Optional[str] = None
    prioridade_padrao: str = "media"
    procedimento_id: Optional[str] = None
    procedimento_snapshot: Optional[dict] = None
    seguranca_id: Optional[str] = None
    seguranca_snapshot: Optional[dict] = None
    checklist_id: Optional[str] = None
    checklist_snapshot: Optional[dict] = None
    campos_obrigatorios: List[str] = []
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None


# ============== GENERIC VERSIONED CRUD FACTORY ==============

async def _resolve_snapshots(body_dict: dict, org_id: str):
    """If a *_id is set but *_snapshot is empty, auto-populate the snapshot from the library."""
    mapping = [
        ("checklist_id", "checklist_snapshot", "checklists_padrao"),
        ("procedimento_id", "procedimento_snapshot", "procedimentos_padrao"),
        ("seguranca_id", "seguranca_snapshot", "seguranca_padrao"),
    ]
    for id_field, snap_field, collection in mapping:
        ref_id = body_dict.get(id_field)
        if ref_id and not body_dict.get(snap_field):
            src = await db[collection].find_one({"id": ref_id, "deleted_at": None}, {"_id": 0})
            if src:
                body_dict[snap_field] = {k: v for k, v in src.items() if k not in ("_id", "organization_id", "deleted_at", "deleted_by")}
    return body_dict


def register_library_crud(item_type: str, collection: str, model_class, prefix: str):
    """Register CRUD + versioning + history + restore endpoints for a library type."""

    @router.get(f"/{prefix}")
    async def list_items(user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id = user.get('organization_id', '')
        items = await db[_coll].find({"organization_id": org_id, "deleted_at": None}, {"_id": 0}).sort("nome", 1).to_list(500)
        return items

    @router.post(f"/{prefix}")
    async def create_item(body: model_class, user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id, user_id = require_editor(user)
        doc = body.model_dump(exclude={"motivo_alteracao"})
        doc = await _resolve_snapshots(doc, org_id)
        doc.update({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "versao": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id,
            "updated_at": None,
            "deleted_at": None,
        })
        await db[_coll].insert_one(doc)
        await archive_version(_type, doc, user_id, "Criação inicial")
        return {"id": doc["id"], "versao": 1, "status": "created"}

    @router.get(f"/{prefix}/{{item_id}}")
    async def get_item(item_id: str, user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id = user.get('organization_id', '')
        item = await db[_coll].find_one({"id": item_id, "organization_id": org_id, "deleted_at": None}, {"_id": 0})
        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        return item

    @router.put(f"/{prefix}/{{item_id}}")
    async def update_item(item_id: str, body: model_class, user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id, user_id = require_editor(user)
        existing = await db[_coll].find_one({"id": item_id, "organization_id": org_id, "deleted_at": None})
        if not existing:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        update = body.model_dump(exclude={"motivo_alteracao"})
        update = await _resolve_snapshots(update, org_id)
        new_version = (existing.get("versao") or 0) + 1
        update["versao"] = new_version
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        update["updated_by"] = user_id
        await db[_coll].update_one({"id": item_id, "organization_id": org_id}, {"$set": update})
        updated_doc = await db[_coll].find_one({"id": item_id}, {"_id": 0})
        await archive_version(_type, updated_doc, user_id, body.motivo_alteracao or f"Atualização para v{new_version}")
        return {"status": "updated", "versao": new_version}

    @router.delete(f"/{prefix}/{{item_id}}")
    async def delete_item(item_id: str, user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id, user_id = require_editor(user)
        existing = await db[_coll].find_one({"id": item_id, "organization_id": org_id, "deleted_at": None})
        if not existing:
            raise HTTPException(status_code=404, detail="Não encontrado")
        await archive_version(_type, existing, user_id, "Exclusão")
        await db[_coll].update_one({"id": item_id, "organization_id": org_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat(), "deleted_by": user_id}})
        return {"status": "deleted"}

    @router.get(f"/{prefix}/{{item_id}}/versoes")
    async def list_versions(item_id: str, user=Depends(get_current_user), _type=item_type):
        org_id = user.get('organization_id', '')
        versions = await db.biblioteca_versoes.find(
            {"item_type": _type, "item_id": item_id, "organization_id": org_id},
            {"_id": 0}
        ).sort("versao", -1).to_list(100)
        return versions

    @router.post(f"/{prefix}/{{item_id}}/restaurar/{{versao}}")
    async def restore_item(item_id: str, versao: int, motivo: str = Query("Restauração"), user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id, user_id = require_editor(user)
        target = await db.biblioteca_versoes.find_one(
            {"item_type": _type, "item_id": item_id, "organization_id": org_id, "versao": versao},
            {"_id": 0}
        )
        if not target:
            raise HTTPException(status_code=404, detail=f"Versão {versao} não encontrada")
        current = await db[_coll].find_one({"id": item_id, "organization_id": org_id, "deleted_at": None})
        if not current:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        snapshot = target["snapshot"]
        new_version = (current.get("versao") or 0) + 1
        restore_data = {k: v for k, v in snapshot.items() if k not in ("id", "organization_id", "versao", "created_at", "created_by", "updated_at", "updated_by", "deleted_at")}
        restore_data["versao"] = new_version
        restore_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        restore_data["updated_by"] = user_id
        restore_data["deleted_at"] = None
        await db[_coll].update_one({"id": item_id, "organization_id": org_id}, {"$set": restore_data})
        restored_doc = await db[_coll].find_one({"id": item_id}, {"_id": 0})
        await archive_version(_type, restored_doc, user_id, f"Restaurado de v{versao}: {motivo}")
        return {"status": "restored", "versao_restaurada": versao, "nova_versao": new_version}


# ============== REGISTER ALL LIBRARY MODULES ==============

register_library_crud("checklist", "checklists_padrao", ChecklistPadrao, "doc-config/checklists")
register_library_crud("modelo_inspecao", "modelos_inspecao", ModeloInspecao, "doc-config/modelos-inspecao")
register_library_crud("modelo_os", "modelos_os", ModeloOS, "doc-config/modelos-os")
