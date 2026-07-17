"""MAINTRIX — Document Configuration Routes (per tenant)
Configurable document templates, procedures, safety, and print settings per organization.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid

from deps import db, get_current_user, is_admin

router = APIRouter()

# ============== MODELS ==============

class DocConfigUpdate(BaseModel):
    identidade_doc: Optional[dict] = None    # logo, nome, unidade, titulo, subtitulo, cores, codigo, versao, rodape, mostrar_maintrix, qr_position, qr_size
    os_config: Optional[dict] = None         # blocos visiveis, ordem, modo manual habilitado
    inspecao_config: Optional[dict] = None   # blocos visiveis, ordem
    foto_config: Optional[dict] = None       # classificacoes[], legenda_obrigatoria, grid_colunas, max_por_pagina
    assinatura_config: Optional[dict] = None # campos[], obrigatoriedade, posicao

class ProcedimentoPadrao(BaseModel):
    nome: str
    codigo: Optional[str] = None
    tipo_atividade: Optional[str] = None
    disciplina: Optional[str] = None
    equipamentos: List[str] = []
    objetivo: Optional[str] = None
    pre_requisitos: Optional[str] = None
    etapas: List[dict] = []     # [{numero, descricao, responsavel, tempo_estimado, observacao}]
    ferramentas: List[str] = []
    materiais: List[str] = []
    observacoes: Optional[str] = None
    status: str = "ativo"

class SegurancaPadrao(BaseModel):
    nome: str
    codigo: Optional[str] = None
    tipo_atividade: Optional[str] = None
    disciplina: Optional[str] = None
    equipamentos: List[str] = []
    riscos: List[dict] = []           # [{descricao, severidade, probabilidade}]
    medidas_controle: List[str] = []
    epis: List[str] = []
    epcs: List[str] = []
    loto: Optional[dict] = None       # {necessario: bool, pontos_bloqueio: [], procedimento}
    apr: Optional[dict] = None        # {necessaria: bool, numero, observacoes}
    pt: Optional[dict] = None         # {necessaria: bool, tipo, observacoes}
    bloqueios: List[dict] = []        # [{tipo, local, descricao}]
    observacoes: Optional[str] = None
    status: str = "ativo"


# ============== DOC CONFIG CRUD ==============

@router.get("/doc-config")
async def get_doc_config(user=Depends(get_current_user)):
    """Get document configuration for user's organization."""
    org_id = user.get('organization_id', '')
    config = await db.doc_config.find_one({"organization_id": org_id}, {"_id": 0})
    if not config:
        config = {"organization_id": org_id, "identidade_doc": {}, "os_config": {}, "inspecao_config": {}, "foto_config": {"classificacoes": ["antes", "durante", "depois", "falha", "componente", "seguranca", "outra"], "legenda_obrigatoria": False, "grid_colunas": 2, "max_por_pagina": 4}, "assinatura_config": {}}
    return config


@router.put("/doc-config")
async def update_doc_config(body: DocConfigUpdate, user=Depends(get_current_user)):
    """Update document configuration for user's organization. Admin/PCM only."""
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


# ============== PROCEDIMENTOS PADRÃO ==============

@router.get("/doc-config/procedimentos")
async def list_procedimentos(user=Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    items = await db.procedimentos_padrao.find({"organization_id": org_id, "deleted_at": None}, {"_id": 0}).sort("nome", 1).to_list(500)
    return items


@router.post("/doc-config/procedimentos")
async def create_procedimento(body: ProcedimentoPadrao, user=Depends(get_current_user)):
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissao")
    org_id = user.get('organization_id', '')
    doc = body.dict()
    doc.update({"id": str(uuid.uuid4()), "organization_id": org_id, "versao": 1, "created_at": datetime.now(timezone.utc).isoformat(), "created_by": user.get('id'), "updated_at": None, "deleted_at": None})
    await db.procedimentos_padrao.insert_one(doc)
    return {"id": doc["id"], "status": "created"}


@router.put("/doc-config/procedimentos/{proc_id}")
async def update_procedimento(proc_id: str, body: ProcedimentoPadrao, user=Depends(get_current_user)):
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissao")
    org_id = user.get('organization_id', '')
    existing = await db.procedimentos_padrao.find_one({"id": proc_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Procedimento nao encontrado")
    update = body.dict()
    update["versao"] = (existing.get("versao") or 0) + 1
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = user.get('id')
    await db.procedimentos_padrao.update_one({"id": proc_id, "organization_id": org_id}, {"$set": update})
    return {"status": "updated", "versao": update["versao"]}


@router.delete("/doc-config/procedimentos/{proc_id}")
async def delete_procedimento(proc_id: str, user=Depends(get_current_user)):
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissao")
    org_id = user.get('organization_id', '')
    result = await db.procedimentos_padrao.update_one({"id": proc_id, "organization_id": org_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    return {"status": "deleted"}


# ============== SEGURANÇA PADRÃO ==============

@router.get("/doc-config/seguranca")
async def list_seguranca(user=Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    items = await db.seguranca_padrao.find({"organization_id": org_id, "deleted_at": None}, {"_id": 0}).sort("nome", 1).to_list(500)
    return items


@router.post("/doc-config/seguranca")
async def create_seguranca(body: SegurancaPadrao, user=Depends(get_current_user)):
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissao")
    org_id = user.get('organization_id', '')
    doc = body.dict()
    doc.update({"id": str(uuid.uuid4()), "organization_id": org_id, "versao": 1, "created_at": datetime.now(timezone.utc).isoformat(), "created_by": user.get('id'), "updated_at": None, "deleted_at": None})
    await db.seguranca_padrao.insert_one(doc)
    return {"id": doc["id"], "status": "created"}


@router.put("/doc-config/seguranca/{seg_id}")
async def update_seguranca(seg_id: str, body: SegurancaPadrao, user=Depends(get_current_user)):
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissao")
    org_id = user.get('organization_id', '')
    existing = await db.seguranca_padrao.find_one({"id": seg_id, "organization_id": org_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    update = body.dict()
    update["versao"] = (existing.get("versao") or 0) + 1
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = user.get('id')
    await db.seguranca_padrao.update_one({"id": seg_id, "organization_id": org_id}, {"$set": update})
    return {"status": "updated", "versao": update["versao"]}


@router.delete("/doc-config/seguranca/{seg_id}")
async def delete_seguranca(seg_id: str, user=Depends(get_current_user)):
    role = user.get('role', '')
    if role not in ('master', 'admin', 'pcm'):
        raise HTTPException(status_code=403, detail="Sem permissao")
    org_id = user.get('organization_id', '')
    result = await db.seguranca_padrao.update_one({"id": seg_id, "organization_id": org_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Nao encontrado")
    return {"status": "deleted"}
