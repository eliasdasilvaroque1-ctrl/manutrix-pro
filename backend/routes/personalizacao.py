"""MAINTRIX — Sprint 3: Personalização Corporativa
Campos Personalizados, Cabeçalhos/Rodapés, Assinaturas, Layouts Reutilizáveis.
Todos versionados, multi-tenant, com RBAC e snapshot isolation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import logging
import re

from deps import db, get_current_user
from routes.doc_config import archive_version, require_editor

router = APIRouter()
logger = logging.getLogger(__name__)

INDEXES = {
    "campos_personalizados": [
        {"keys": [("organization_id", 1), ("status", 1), ("deleted_at", 1)], "name": "org_status_active"},
        {"keys": [("organization_id", 1), ("identificador_tecnico", 1)], "name": "org_ident", "unique": True},
    ],
    "cabecalhos_rodapes": [
        {"keys": [("organization_id", 1), ("tipo", 1), ("deleted_at", 1)], "name": "org_tipo_active"},
    ],
    "blocos_assinatura": [
        {"keys": [("organization_id", 1), ("deleted_at", 1)], "name": "org_active"},
    ],
    "layouts_documento": [
        {"keys": [("organization_id", 1), ("deleted_at", 1)], "name": "org_active"},
    ],
}

# ============== ENUMS & CONSTANTS ==============

TIPOS_CAMPO = [
    "texto_curto", "texto_longo", "numero", "decimal", "data", "hora", "data_hora",
    "selecao_unica", "multipla_selecao", "checkbox", "sim_nao",
    "foto", "assinatura", "qr_code", "url", "email", "telefone",
]

MODULOS_APLICACAO = ["os", "inspecao", "ativo"]

# ============== PYDANTIC MODELS (structured, no raw List[dict]) ==============

class OpcaoSelecao(BaseModel):
    valor: str
    label: str
    ordem: int = 0

class CampoPersonalizado(BaseModel):
    nome: str
    identificador_tecnico: str = Field(..., min_length=2, max_length=80)
    descricao: Optional[str] = None
    tipo: str
    obrigatorio: bool = False
    valor_padrao: Optional[str] = None
    placeholder: Optional[str] = None
    texto_ajuda: Optional[str] = None
    ordem: int = 0
    status: str = "ativo"
    validacao_min: Optional[float] = None
    validacao_max: Optional[float] = None
    limite_caracteres: Optional[int] = None
    mascara: Optional[str] = None
    unidade_medida: Optional[str] = None
    casas_decimais: Optional[int] = None
    opcoes: List[OpcaoSelecao] = []
    permissao_edicao: List[str] = []
    permissao_visualizacao: List[str] = []
    aplicacao_modulos: List[str] = []
    aplicacao_tipos: List[str] = []
    aplicacao_categorias: List[str] = []
    aplicacao_areas: List[str] = []
    motivo_alteracao: Optional[str] = None

    @field_validator('tipo')
    @classmethod
    def validate_tipo(cls, v):
        if v not in TIPOS_CAMPO:
            raise ValueError(f"Tipo inválido: {v}. Válidos: {', '.join(TIPOS_CAMPO)}")
        return v

    @field_validator('identificador_tecnico')
    @classmethod
    def validate_ident(cls, v):
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError("Identificador deve ser snake_case: letras minúsculas, números e underscores")
        return v

    @field_validator('aplicacao_modulos')
    @classmethod
    def validate_modulos(cls, v):
        for m in v:
            if m not in MODULOS_APLICACAO:
                raise ValueError(f"Módulo inválido: {m}. Válidos: {', '.join(MODULOS_APLICACAO)}")
        return v


class CabecalhoRodape(BaseModel):
    nome: str
    tipo: str  # "cabecalho" or "rodape"
    logo_url: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    texto_personalizado: Optional[str] = None
    mostrar_paginacao: bool = True
    mostrar_data_emissao: bool = True
    mostrar_identificacao_doc: bool = True
    mostrar_versao: bool = False
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None

    @field_validator('tipo')
    @classmethod
    def validate_tipo(cls, v):
        if v not in ('cabecalho', 'rodape'):
            raise ValueError("Tipo deve ser 'cabecalho' ou 'rodape'")
        return v


class CampoAssinatura(BaseModel):
    campo: str  # nome, cargo, matricula, data, papel, assinatura_imagem
    obrigatorio: bool = True
    ordem: int = 0


class BlocoAssinatura(BaseModel):
    nome: str
    papel: str  # executor, supervisor, inspetor, aprovador, etc.
    campos: List[CampoAssinatura] = []
    matricula_obrigatoria: bool = False
    captura_digital: bool = False
    status_opcoes: List[str] = Field(default_factory=lambda: ["pendente", "assinado", "recusado", "nao_aplicavel"])
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None


class LayoutDocumento(BaseModel):
    nome: str
    tipo_documento: Optional[str] = None
    orientacao: str = "retrato"
    tamanho_pagina: str = "A4"
    cabecalho_id: Optional[str] = None
    cabecalho_snapshot: Optional[dict] = None
    rodape_id: Optional[str] = None
    rodape_snapshot: Optional[dict] = None
    blocos_visiveis: List[str] = Field(default_factory=lambda: [
        "equipamento", "informacoes", "descricao", "equipe", "datas",
        "procedimento", "seguranca", "materiais", "observacoes", "fotos", "assinaturas"
    ])
    blocos_ordem: List[str] = []
    blocos_ocultos: List[str] = []
    campos_personalizados_ids: List[str] = []
    assinatura_ids: List[str] = []
    mostrar_fotos: bool = True
    mostrar_materiais: bool = True
    mostrar_historico: bool = False
    mostrar_checklist: bool = True
    mostrar_qr_code: bool = True
    quebras_pagina: List[str] = []
    colunas: int = 1
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None

    @field_validator('orientacao')
    @classmethod
    def validate_orientacao(cls, v):
        if v not in ('retrato', 'paisagem'):
            raise ValueError("Orientação deve ser 'retrato' ou 'paisagem'")
        return v


# ============== GENERIC VERSIONED CRUD (reused from Sprint 2 pattern) ==============

def _register_crud(item_type: str, collection: str, model_class, prefix: str):
    """Register versioned CRUD endpoints for a library type."""

    @router.get(f"/{prefix}", tags=[item_type])
    async def list_items(
        modulo: Optional[str] = None,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
        user=Depends(get_current_user), _type=item_type, _coll=collection
    ):
        org_id = user.get('organization_id', '')
        query = {"organization_id": org_id, "deleted_at": None}
        if status:
            query["status"] = status
        if modulo and _coll == "campos_personalizados":
            query["aplicacao_modulos"] = modulo
        if tipo and _coll in ("campos_personalizados", "layouts_documento"):
            query.setdefault("$or", [])
            query["$or"] = [{"aplicacao_tipos": tipo}, {"aplicacao_tipos": []}]
        items = await db[_coll].find(query, {"_id": 0}).sort("ordem" if _coll == "campos_personalizados" else "nome", 1).to_list(500)
        return items

    @router.post(f"/{prefix}", tags=[item_type])
    async def create_item(body: model_class, user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id, user_id = require_editor(user)
        doc = body.model_dump(exclude={"motivo_alteracao"}, mode="json")
        # Check unique identifier for campos_personalizados
        if _coll == "campos_personalizados":
            existing = await db[_coll].find_one({"organization_id": org_id, "identificador_tecnico": doc.get("identificador_tecnico"), "deleted_at": None})
            if existing:
                raise HTTPException(status_code=409, detail=f"Identificador '{doc['identificador_tecnico']}' já existe")
        # Auto-resolve snapshots for layouts
        if _coll == "layouts_documento":
            doc = await _resolve_layout_snapshots(doc, org_id)
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

    @router.get(f"/{prefix}/{{item_id}}", tags=[item_type])
    async def get_item(item_id: str, user=Depends(get_current_user), _coll=collection):
        org_id = user.get('organization_id', '')
        item = await db[_coll].find_one({"id": item_id, "organization_id": org_id, "deleted_at": None}, {"_id": 0})
        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        return item

    @router.put(f"/{prefix}/{{item_id}}", tags=[item_type])
    async def update_item(item_id: str, body: model_class, user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id, user_id = require_editor(user)
        existing = await db[_coll].find_one({"id": item_id, "organization_id": org_id, "deleted_at": None})
        if not existing:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        update = body.model_dump(exclude={"motivo_alteracao"}, mode="json")
        # Preserve immutable identifier
        if _coll == "campos_personalizados":
            update["identificador_tecnico"] = existing.get("identificador_tecnico")
        if _coll == "layouts_documento":
            update = await _resolve_layout_snapshots(update, org_id)
        new_version = (existing.get("versao") or 0) + 1
        update["versao"] = new_version
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        update["updated_by"] = user_id
        await db[_coll].update_one({"id": item_id, "organization_id": org_id}, {"$set": update})
        updated_doc = await db[_coll].find_one({"id": item_id}, {"_id": 0})
        await archive_version(_type, updated_doc, user_id, body.motivo_alteracao or f"Atualização para v{new_version}")
        return {"status": "updated", "versao": new_version}

    @router.delete(f"/{prefix}/{{item_id}}", tags=[item_type])
    async def delete_item(item_id: str, user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id, user_id = require_editor(user)
        existing = await db[_coll].find_one({"id": item_id, "organization_id": org_id, "deleted_at": None})
        if not existing:
            raise HTTPException(status_code=404, detail="Não encontrado")
        await archive_version(_type, existing, user_id, "Exclusão")
        await db[_coll].update_one({"id": item_id, "organization_id": org_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat(), "deleted_by": user_id}})
        return {"status": "deleted"}

    @router.get(f"/{prefix}/{{item_id}}/versoes", tags=[item_type])
    async def list_versions(item_id: str, user=Depends(get_current_user), _type=item_type):
        org_id = user.get('organization_id', '')
        versions = await db.biblioteca_versoes.find(
            {"item_type": _type, "item_id": item_id, "organization_id": org_id},
            {"_id": 0}
        ).sort("versao", -1).to_list(100)
        return versions

    @router.post(f"/{prefix}/{{item_id}}/restaurar/{{versao}}", tags=[item_type])
    async def restore_item(item_id: str, versao: int, motivo: str = Query("Restauração"), user=Depends(get_current_user), _type=item_type, _coll=collection):
        org_id, user_id = require_editor(user)
        target = await db.biblioteca_versoes.find_one(
            {"item_type": _type, "item_id": item_id, "organization_id": org_id, "versao": versao}, {"_id": 0}
        )
        if not target:
            raise HTTPException(status_code=404, detail=f"Versão {versao} não encontrada")
        current = await db[_coll].find_one({"id": item_id, "organization_id": org_id, "deleted_at": None})
        if not current:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        snapshot = target["snapshot"]
        new_version = (current.get("versao") or 0) + 1
        exclude_keys = {"id", "organization_id", "versao", "created_at", "created_by", "updated_at", "updated_by", "deleted_at", "identificador_tecnico"}
        restore_data = {k: v for k, v in snapshot.items() if k not in exclude_keys}
        restore_data["versao"] = new_version
        restore_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        restore_data["updated_by"] = user_id
        restore_data["deleted_at"] = None
        await db[_coll].update_one({"id": item_id, "organization_id": org_id}, {"$set": restore_data})
        restored_doc = await db[_coll].find_one({"id": item_id}, {"_id": 0})
        await archive_version(_type, restored_doc, user_id, f"Restaurado de v{versao}: {motivo}")
        return {"status": "restored", "versao_restaurada": versao, "nova_versao": new_version}


# ============== LAYOUT SNAPSHOT HELPER ==============

async def _resolve_layout_snapshots(doc: dict, org_id: str):
    """Auto-populate cabecalho/rodape snapshots from referenced IDs."""
    for id_field, snap_field, collection in [
        ("cabecalho_id", "cabecalho_snapshot", "cabecalhos_rodapes"),
        ("rodape_id", "rodape_snapshot", "cabecalhos_rodapes"),
    ]:
        ref_id = doc.get(id_field)
        if ref_id and not doc.get(snap_field):
            src = await db[collection].find_one({"id": ref_id, "organization_id": org_id, "deleted_at": None}, {"_id": 0})
            if src:
                doc[snap_field] = {k: v for k, v in src.items() if k not in ("_id", "organization_id", "deleted_at", "deleted_by")}
    return doc


# ============== BULK ENDPOINT: Get fields for a specific module context ==============

@router.get("/doc-config/campos/por-modulo/{modulo}", tags=["campos_personalizados"])
async def get_campos_por_modulo(
    modulo: str,
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    area: Optional[str] = None,
    user=Depends(get_current_user),
):
    """Get all active custom fields applicable to a specific module and context."""
    org_id = user.get('organization_id', '')
    query = {
        "organization_id": org_id,
        "status": "ativo",
        "deleted_at": None,
        "aplicacao_modulos": modulo,
    }
    fields = await db.campos_personalizados.find(query, {"_id": 0}).sort("ordem", 1).to_list(200)
    # Filter by context if provided
    if tipo:
        fields = [f for f in fields if not f.get("aplicacao_tipos") or tipo in f["aplicacao_tipos"]]
    if categoria:
        fields = [f for f in fields if not f.get("aplicacao_categorias") or categoria in f["aplicacao_categorias"]]
    if area:
        fields = [f for f in fields if not f.get("aplicacao_areas") or area in f["aplicacao_areas"]]
    return fields


# ============== REGISTER ALL MODULES ==============

_register_crud("campo_personalizado", "campos_personalizados", CampoPersonalizado, "doc-config/campos")
_register_crud("cabecalho_rodape", "cabecalhos_rodapes", CabecalhoRodape, "doc-config/cabecalhos-rodapes")
_register_crud("bloco_assinatura", "blocos_assinatura", BlocoAssinatura, "doc-config/assinaturas")
_register_crud("layout_documento", "layouts_documento", LayoutDocumento, "doc-config/layouts")
