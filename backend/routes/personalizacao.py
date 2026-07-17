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


BLOCK_TYPES = [
    "header", "footer", "equipment", "info", "description", "team", "dates",
    "procedure", "safety", "checklist", "signature", "qr_code", "photos",
    "materials", "indicators", "history", "custom_fields", "free_text",
    "separator", "page_break", "observations",
]

SINGULAR_BLOCKS = {"header", "footer"}  # max 1 of each


class LayoutBlock(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    order: int = 0
    visible: bool = True
    settings: dict = {}
    library_ref_id: Optional[str] = None
    library_ref_type: Optional[str] = None

    @field_validator('type')
    @classmethod
    def validate_block_type(cls, v):
        if v not in BLOCK_TYPES:
            raise ValueError(f"Tipo de bloco inválido: {v}. Válidos: {', '.join(BLOCK_TYPES)}")
        return v


class LayoutDocumento(BaseModel):
    nome: str
    tipo_documento: Optional[str] = None
    orientacao: str = "retrato"
    tamanho_pagina: str = "A4"
    schema_version: int = 1
    blocks: List[LayoutBlock] = []
    # Legacy flat fields (backward compat)
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
    publication_status: str = "rascunho"  # rascunho, publicado, inativo
    status: str = "ativo"
    motivo_alteracao: Optional[str] = None

    @field_validator('orientacao')
    @classmethod
    def validate_orientacao(cls, v):
        if v not in ('retrato', 'paisagem'):
            raise ValueError("Orientação deve ser 'retrato' ou 'paisagem'")
        return v

    @field_validator('publication_status')
    @classmethod
    def validate_pub_status(cls, v):
        if v not in ('rascunho', 'publicado', 'inativo'):
            raise ValueError("Status de publicação deve ser 'rascunho', 'publicado' ou 'inativo'")
        return v

    @field_validator('blocks')
    @classmethod
    def validate_blocks(cls, v):
        if not v:
            return v
        ids = set()
        singular_counts = {}
        for block in v:
            if block.id in ids:
                raise ValueError(f"ID de bloco duplicado: {block.id}")
            ids.add(block.id)
            if block.type in SINGULAR_BLOCKS:
                singular_counts[block.type] = singular_counts.get(block.type, 0) + 1
                if singular_counts[block.type] > 1:
                    raise ValueError(f"Apenas 1 bloco '{block.type}' permitido por layout")
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



# ============== SIGNATURE CAPTURE ENDPOINT ==============

class SignatureCapture(BaseModel):
    entity_type: str  # "os" or "inspecao"
    entity_id: str
    bloco_assinatura_id: Optional[str] = None
    papel: str = "executor"
    nome: str
    cargo: Optional[str] = None
    matricula: Optional[str] = None
    imagem_base64: str  # base64 PNG from canvas
    status: str = "assinado"


@router.post("/assinaturas/capturar", tags=["assinatura_digital"])
async def capturar_assinatura(body: SignatureCapture, user=Depends(get_current_user)):
    """Capture a digital signature and attach to an OS or Inspection."""
    org_id = user.get('organization_id', '')
    user_id = user.get('id', '')

    # Validate entity exists
    collection = "ordens_servico" if body.entity_type == "os" else "inspecoes"
    entity = await db[collection].find_one({"id": body.entity_id, "organization_id": org_id}, {"_id": 0, "id": 1})
    if not entity:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    sig_doc = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "entity_type": body.entity_type,
        "entity_id": body.entity_id,
        "bloco_assinatura_id": body.bloco_assinatura_id,
        "papel": body.papel,
        "nome": body.nome,
        "cargo": body.cargo,
        "matricula": body.matricula,
        "imagem_base64": body.imagem_base64,
        "status": body.status,
        "usuario_id": user_id,
        "data_assinatura": datetime.now(timezone.utc).isoformat(),
        "hash_referencia": str(uuid.uuid4())[:12],
    }
    await db.assinaturas_digitais.insert_one(sig_doc)

    # Also update the entity's assinaturas_dados array
    ass_entry = {
        "bloco_id": body.bloco_assinatura_id,
        "papel": body.papel,
        "nome": body.nome,
        "cargo": body.cargo,
        "matricula": body.matricula,
        "data": sig_doc["data_assinatura"],
        "status": body.status,
        "imagem_url": f"sig:{sig_doc['id']}",
        "hash": sig_doc["hash_referencia"],
        "usuario_id": user_id,
    }
    await db[collection].update_one(
        {"id": body.entity_id, "organization_id": org_id},
        {"$push": {"assinaturas_dados": ass_entry}}
    )

    logger.info(f"Signature captured: {body.papel} on {body.entity_type}/{body.entity_id}")
    return {"id": sig_doc["id"], "hash": sig_doc["hash_referencia"], "status": "captured"}


# ============== LAYOUT BUILDER ENDPOINTS ==============

@router.post("/doc-config/layouts/{layout_id}/duplicar", tags=["layout_builder"])
async def duplicar_layout(layout_id: str, user=Depends(get_current_user)):
    """Duplicate a layout as a new draft."""
    org_id, user_id = require_editor(user)
    source = await db.layouts_documento.find_one({"id": layout_id, "organization_id": org_id, "deleted_at": None}, {"_id": 0})
    if not source:
        raise HTTPException(status_code=404, detail="Layout não encontrado")
    new_id = str(uuid.uuid4())
    new_doc = {k: v for k, v in source.items() if k not in ("_id", "id", "versao", "created_at", "created_by", "updated_at")}
    new_doc.update({
        "id": new_id, "nome": f"{source['nome']} (Cópia)",
        "versao": 1, "publication_status": "rascunho",
        "created_at": datetime.now(timezone.utc).isoformat(), "created_by": user_id,
        "updated_at": None,
    })
    # Regenerate block IDs to avoid conflicts
    for block in new_doc.get("blocks", []):
        block["id"] = str(uuid.uuid4())
    await db.layouts_documento.insert_one(new_doc)
    await archive_version("layout_documento", new_doc, user_id, f"Duplicado de {source['nome']}")
    return {"id": new_id, "nome": new_doc["nome"], "status": "created"}


@router.post("/doc-config/layouts/{layout_id}/publicar", tags=["layout_builder"])
async def publicar_layout(layout_id: str, user=Depends(get_current_user)):
    """Publish a draft layout. Only one published layout per tipo_documento per org."""
    org_id, user_id = require_editor(user)
    layout = await db.layouts_documento.find_one({"id": layout_id, "organization_id": org_id, "deleted_at": None})
    if not layout:
        raise HTTPException(status_code=404, detail="Layout não encontrado")
    if layout.get("publication_status") == "publicado":
        raise HTTPException(status_code=400, detail="Layout já está publicado")
    # Validate blocks
    blocks = layout.get("blocks", [])
    if blocks:
        for block in blocks:
            if block.get("library_ref_id"):
                ref_type_map = {"procedure": "procedimentos_padrao", "safety": "seguranca_padrao", "checklist": "checklists_padrao", "signature": "blocos_assinatura", "header": "cabecalhos_rodapes", "footer": "cabecalhos_rodapes", "custom_fields": "campos_personalizados"}
                coll = ref_type_map.get(block["type"])
                if coll:
                    ref = await db[coll].find_one({"id": block["library_ref_id"], "organization_id": org_id, "deleted_at": None})
                    if not ref:
                        raise HTTPException(status_code=400, detail=f"Referência inválida no bloco '{block['type']}': {block['library_ref_id']} não pertence à empresa ou não existe")
    # Deactivate other published layouts of same tipo_documento
    tipo = layout.get("tipo_documento")
    if tipo:
        await db.layouts_documento.update_many(
            {"organization_id": org_id, "tipo_documento": tipo, "publication_status": "publicado", "id": {"$ne": layout_id}, "deleted_at": None},
            {"$set": {"publication_status": "inativo", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    await db.layouts_documento.update_one(
        {"id": layout_id, "organization_id": org_id},
        {"$set": {"publication_status": "publicado", "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user_id}}
    )
    updated = await db.layouts_documento.find_one({"id": layout_id}, {"_id": 0})
    await archive_version("layout_documento", updated, user_id, "Publicação")
    return {"status": "published", "versao": updated.get("versao", 1)}


@router.get("/doc-config/layouts/publicado/{tipo_documento}", tags=["layout_builder"])
async def get_published_layout(tipo_documento: str, user=Depends(get_current_user)):
    """Get the active published layout for a document type."""
    org_id = user.get('organization_id', '')
    layout = await db.layouts_documento.find_one(
        {"organization_id": org_id, "tipo_documento": tipo_documento, "publication_status": "publicado", "deleted_at": None},
        {"_id": 0}
    )
    if not layout:
        return None
    return layout


@router.get("/doc-config/layouts/{layout_id}/preview-data", tags=["layout_builder"])
async def get_layout_preview_data(layout_id: str, user=Depends(get_current_user)):
    """Get resolved block data for preview — resolves library references."""
    org_id = user.get('organization_id', '')
    layout = await db.layouts_documento.find_one({"id": layout_id, "organization_id": org_id, "deleted_at": None}, {"_id": 0})
    if not layout:
        raise HTTPException(status_code=404, detail="Layout não encontrado")
    blocks = layout.get("blocks", [])
    resolved = []
    for block in sorted(blocks, key=lambda b: b.get("order", 0)):
        b = {**block}
        if block.get("library_ref_id"):
            ref_map = {"procedure": "procedimentos_padrao", "safety": "seguranca_padrao", "checklist": "checklists_padrao", "signature": "blocos_assinatura", "header": "cabecalhos_rodapes", "footer": "cabecalhos_rodapes", "custom_fields": "campos_personalizados"}
            coll = ref_map.get(block["type"])
            if coll:
                ref_doc = await db[coll].find_one({"id": block["library_ref_id"], "organization_id": org_id, "deleted_at": None}, {"_id": 0})
                if ref_doc:
                    b["library_data"] = {k: v for k, v in ref_doc.items() if k not in ("_id", "organization_id")}
        resolved.append(b)
    return {"layout": layout, "resolved_blocks": resolved}



# ============== REGISTER ALL MODULES ==============

_register_crud("campo_personalizado", "campos_personalizados", CampoPersonalizado, "doc-config/campos")
_register_crud("cabecalho_rodape", "cabecalhos_rodapes", CabecalhoRodape, "doc-config/cabecalhos-rodapes")
_register_crud("bloco_assinatura", "blocos_assinatura", BlocoAssinatura, "doc-config/assinaturas")
_register_crud("layout_documento", "layouts_documento", LayoutDocumento, "doc-config/layouts")
