"""
MAINTRIX ENTERPRISE — Biblioteca de Modelos & Classificação Técnica
Collections: categorias_equipamento, fabricantes, modelos_mestre
Auto-numbering via org_config.gerar_numero
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional, List
from datetime import datetime, timezone
import uuid, copy

from deps import (
    db, get_current_user, check_write_permission, check_admin_only,
    check_pcm_or_admin, verify_org_access, audit_log, logger
)
from org_config import gerar_numero

router = APIRouter()


# ============== AUTO-CODE HELPER ==============

async def next_code(org_id, prefix, entidade):
    """Generate next sequential code: CAT-000001, FAB-000001, etc."""
    counter_key = f"{entidade}_seq"
    result = await db.contadores.find_one_and_update(
        {"organization_id": org_id, "chave": counter_key},
        {"$inc": {"sequencial": 1},
         "$setOnInsert": {"id": str(uuid.uuid4()), "organization_id": org_id,
                          "chave": counter_key, "entidade": entidade,
                          "created_at": datetime.now(timezone.utc).isoformat()},
         "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True, return_document=True
    )
    seq = result.get("sequencial", 1)
    return f"{prefix}-{str(seq).zfill(6)}"


# ============== CATEGORIAS DE EQUIPAMENTO ==============

@router.get("/biblioteca/categorias")
async def list_categorias(
    search: str = None, status: str = None,
    skip: int = 0, limit: int = 50,
    user: Dict = Depends(get_current_user)
):
    query = {"organization_id": user.get("organization_id", ""), "deleted_at": None}
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"nome": {"$regex": search, "$options": "i"}},
            {"codigo": {"$regex": search, "$options": "i"}},
        ]
    total = await db.categorias_equipamento.count_documents(query)
    items = await db.categorias_equipamento.find(query, {"_id": 0}).sort("nome", 1).skip(skip).limit(limit).to_list(limit)
    return {"items": items, "total": total}

@router.post("/biblioteca/categorias")
async def create_categoria(data: dict, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    org_id = user.get("organization_id", "")
    codigo = await next_code(org_id, "CAT", "categorias")
    doc = {
        "id": str(uuid.uuid4()), "organization_id": org_id,
        "codigo": codigo, "nome": data.get("nome", ""),
        "descricao": data.get("descricao", ""),
        "status": "ativo",
        "created_by": user.get("id", ""), "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None,
    }
    await db.categorias_equipamento.insert_one(doc)
    await audit_log("create", "categoria_equipamento", doc["id"], user, f"Categoria: {doc['nome']} ({codigo})")
    doc.pop("_id", None)
    return doc

@router.put("/biblioteca/categorias/{cat_id}")
async def update_categoria(cat_id: str, data: dict, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    existing = await db.categorias_equipamento.find_one({"id": cat_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    verify_org_access(user, existing, "Categoria")
    updates = {k: v for k, v in data.items() if k in ("nome", "descricao", "status") and v is not None}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.categorias_equipamento.update_one({"id": cat_id}, {"$set": updates})
    return await db.categorias_equipamento.find_one({"id": cat_id}, {"_id": 0})

@router.delete("/biblioteca/categorias/{cat_id}")
async def delete_categoria(cat_id: str, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    existing = await db.categorias_equipamento.find_one({"id": cat_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    verify_org_access(user, existing, "Categoria")
    await db.categorias_equipamento.update_one({"id": cat_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "categoria_equipamento", cat_id, user, f"Categoria excluída: {existing.get('nome')}")
    return {"success": True}


# ============== FABRICANTES ==============

@router.get("/biblioteca/fabricantes")
async def list_fabricantes(
    search: str = None, categoria_id: str = None,
    skip: int = 0, limit: int = 50,
    user: Dict = Depends(get_current_user)
):
    query = {"organization_id": user.get("organization_id", ""), "deleted_at": None}
    if categoria_id:
        query["categoria_id"] = categoria_id
    if search:
        query["$or"] = [
            {"nome": {"$regex": search, "$options": "i"}},
            {"codigo": {"$regex": search, "$options": "i"}},
        ]
    total = await db.fabricantes.count_documents(query)
    items = await db.fabricantes.find(query, {"_id": 0}).sort("nome", 1).skip(skip).limit(limit).to_list(limit)
    return {"items": items, "total": total}

@router.post("/biblioteca/fabricantes")
async def create_fabricante(data: dict, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    org_id = user.get("organization_id", "")
    codigo = await next_code(org_id, "FAB", "fabricantes")
    doc = {
        "id": str(uuid.uuid4()), "organization_id": org_id,
        "codigo": codigo, "nome": data.get("nome", ""),
        "descricao": data.get("descricao", ""),
        "categoria_id": data.get("categoria_id"),
        "pais": data.get("pais", ""),
        "website": data.get("website", ""),
        "status": "ativo",
        "created_by": user.get("id", ""), "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None,
    }
    await db.fabricantes.insert_one(doc)
    await audit_log("create", "fabricante", doc["id"], user, f"Fabricante: {doc['nome']} ({codigo})")
    doc.pop("_id", None)
    return doc

@router.put("/biblioteca/fabricantes/{fab_id}")
async def update_fabricante(fab_id: str, data: dict, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    existing = await db.fabricantes.find_one({"id": fab_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Fabricante não encontrado")
    verify_org_access(user, existing, "Fabricante")
    updates = {k: v for k, v in data.items() if k in ("nome", "descricao", "categoria_id", "pais", "website", "status") and v is not None}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.fabricantes.update_one({"id": fab_id}, {"$set": updates})
    return await db.fabricantes.find_one({"id": fab_id}, {"_id": 0})

@router.delete("/biblioteca/fabricantes/{fab_id}")
async def delete_fabricante(fab_id: str, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    existing = await db.fabricantes.find_one({"id": fab_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Fabricante não encontrado")
    verify_org_access(user, existing, "Fabricante")
    await db.fabricantes.update_one({"id": fab_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "fabricante", fab_id, user, f"Fabricante excluído: {existing.get('nome')}")
    return {"success": True}


# ============== MODELOS MESTRE ==============

@router.get("/biblioteca/modelos-mestre")
async def list_modelos_mestre(
    search: str = None, categoria_id: str = None, fabricante_id: str = None,
    skip: int = 0, limit: int = 50,
    user: Dict = Depends(get_current_user)
):
    query = {"organization_id": user.get("organization_id", ""), "deleted_at": None}
    if categoria_id:
        query["categoria_id"] = categoria_id
    if fabricante_id:
        query["fabricante_id"] = fabricante_id
    if search:
        query["$or"] = [
            {"nome": {"$regex": search, "$options": "i"}},
            {"codigo": {"$regex": search, "$options": "i"}},
            {"modelo": {"$regex": search, "$options": "i"}},
        ]
    total = await db.modelos_mestre.count_documents(query)
    items = await db.modelos_mestre.find(query, {"_id": 0}).sort("nome", 1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with categoria/fabricante names
    cat_ids = list(set(i.get("categoria_id") for i in items if i.get("categoria_id")))
    fab_ids = list(set(i.get("fabricante_id") for i in items if i.get("fabricante_id")))
    cats = {c["id"]: c["nome"] for c in await db.categorias_equipamento.find({"id": {"$in": cat_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(100)} if cat_ids else {}
    fabs = {f["id"]: f["nome"] for f in await db.fabricantes.find({"id": {"$in": fab_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(100)} if fab_ids else {}
    for item in items:
        item["categoria_nome"] = cats.get(item.get("categoria_id"), "")
        item["fabricante_nome"] = fabs.get(item.get("fabricante_id"), "")
    
    return {"items": items, "total": total}

@router.post("/biblioteca/modelos-mestre")
async def create_modelo_mestre(data: dict, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    org_id = user.get("organization_id", "")
    codigo = await next_code(org_id, "MM", "modelos_mestre")
    
    # Process planos (master plans)
    planos = []
    for p in data.get("planos", []):
        plano_codigo = await next_code(org_id, "PLA", "planos")
        perguntas = []
        for i, q in enumerate(p.get("perguntas", [])):
            perguntas.append({
                "id": str(uuid.uuid4()),
                "texto": q.get("texto", q.get("descricao", "")),
                "tipo_campo": q.get("tipo_campo", q.get("tipo", "boolean")),
                "obrigatoria": q.get("obrigatoria", True),
                "foto_obrigatoria": q.get("foto_obrigatoria", False),
                "comentario_obrigatorio": q.get("comentario_obrigatorio", False),
                "unidade": q.get("unidade"),
                "valor_min": q.get("valor_min"),
                "valor_max": q.get("valor_max"),
                "opcoes": q.get("opcoes", []),
                "ordem": q.get("ordem", i),
            })
        planos.append({
            "id": str(uuid.uuid4()),
            "codigo": plano_codigo,
            "nome": p.get("nome", ""),
            "tipo": p.get("tipo", "inspecao"),
            "frequencia": p.get("frequencia"),
            "disciplina": p.get("disciplina"),
            "perguntas": perguntas,
        })
    
    doc = {
        "id": str(uuid.uuid4()), "organization_id": org_id,
        "codigo": codigo,
        "nome": data.get("nome", ""),
        "modelo": data.get("modelo", ""),
        "categoria_id": data.get("categoria_id"),
        "fabricante_id": data.get("fabricante_id"),
        "descricao": data.get("descricao", ""),
        "especificacoes": data.get("especificacoes", {}),
        "planos": planos,
        "versao": 1,
        "status": "ativo",
        "is_master": True,
        "created_by": user.get("id", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None,
    }
    await db.modelos_mestre.insert_one(doc)
    await audit_log("create", "modelo_mestre", doc["id"], user, f"Modelo Mestre: {doc['nome']} ({codigo})")
    doc.pop("_id", None)
    return doc

@router.get("/biblioteca/modelos-mestre/{mm_id}")
async def get_modelo_mestre(mm_id: str, user: Dict = Depends(get_current_user)):
    doc = await db.modelos_mestre.find_one({"id": mm_id, "deleted_at": None}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Modelo Mestre não encontrado")
    verify_org_access(user, doc, "Modelo Mestre")
    return doc

@router.put("/biblioteca/modelos-mestre/{mm_id}")
async def update_modelo_mestre(mm_id: str, data: dict, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    existing = await db.modelos_mestre.find_one({"id": mm_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Modelo Mestre não encontrado")
    verify_org_access(user, existing, "Modelo Mestre")
    allowed = ["nome", "modelo", "categoria_id", "fabricante_id", "descricao", "especificacoes", "planos", "status"]
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        updates["versao"] = existing.get("versao", 1) + 1
        await db.modelos_mestre.update_one({"id": mm_id}, {"$set": updates})
    return await db.modelos_mestre.find_one({"id": mm_id}, {"_id": 0})

@router.delete("/biblioteca/modelos-mestre/{mm_id}")
async def delete_modelo_mestre(mm_id: str, user: Dict = Depends(get_current_user)):
    check_pcm_or_admin(user)
    existing = await db.modelos_mestre.find_one({"id": mm_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Modelo Mestre não encontrado")
    verify_org_access(user, existing, "Modelo Mestre")
    await db.modelos_mestre.update_one({"id": mm_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "modelo_mestre", mm_id, user, f"Modelo Mestre excluído: {existing.get('nome')}")
    return {"success": True}


# ============== DEEP COPY: APLICAR MODELO AO ATIVO ==============

@router.post("/biblioteca/modelos-mestre/{mm_id}/aplicar/{ativo_id}")
async def aplicar_modelo_ao_ativo(
    mm_id: str, ativo_id: str,
    motivo: str = "Aplicação de modelo mestre",
    user: Dict = Depends(get_current_user)
):
    """Deep Copy: Creates independent plans on the asset from the master model."""
    check_pcm_or_admin(user)
    org_id = user.get("organization_id", "")
    
    modelo = await db.modelos_mestre.find_one({"id": mm_id, "deleted_at": None}, {"_id": 0})
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo Mestre não encontrado")
    verify_org_access(user, modelo, "Modelo Mestre")
    
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")
    
    created_plans = []
    now = datetime.now(timezone.utc).isoformat()
    
    for plano_mestre in modelo.get("planos", []):
        # Deep copy each plan
        plano_codigo = await next_code(org_id, "PLA", "planos")
        perguntas_copy = []
        for p in plano_mestre.get("perguntas", []):
            pergunta = {**p, "id": str(uuid.uuid4())}
            perguntas_copy.append(pergunta)
        
        plano_doc = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "nome": f"{plano_mestre.get('nome', '')} — {ativo.get('tag', ativo.get('nome', ''))}",
            "tipo": plano_mestre.get("tipo", "inspecao"),
            "categoria": plano_mestre.get("tipo", "inspecao"),
            "ativo_id": ativo_id,
            "frequencia": plano_mestre.get("frequencia"),
            "disciplina": plano_mestre.get("disciplina"),
            "status": "ativo",
            "versao": 1,
            "perguntas": perguntas_copy,
            # Rastreabilidade
            "modelo_origem_id": mm_id,
            "modelo_versao": modelo.get("versao", 1),
            "plano_origem_id": plano_mestre.get("id"),
            "motivo_criacao": motivo,
            "created_by": user.get("id", ""),
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        await db.planos_inspecao.insert_one(plano_doc)
        plano_doc.pop("_id", None)
        created_plans.append(plano_doc)
    
    # Update ativo with model reference
    await db.ativos.update_one({"id": ativo_id}, {"$set": {
        "modelo_mestre_id": mm_id,
        "categoria_id": modelo.get("categoria_id"),
        "fabricante_id": modelo.get("fabricante_id"),
        "modelo_id": mm_id,
        "updated_at": now,
    }})
    
    await audit_log("apply_model", "modelo_mestre", mm_id, user,
        f"Modelo '{modelo.get('nome')}' aplicado ao ativo '{ativo.get('tag')}' — {len(created_plans)} planos criados")
    
    return {
        "success": True,
        "modelo": modelo.get("nome"),
        "ativo": ativo.get("tag"),
        "planos_criados": len(created_plans),
        "planos": [{"id": p["id"], "nome": p["nome"], "tipo": p["tipo"]} for p in created_plans],
    }


# ============== INDEXES ==============

BIBLIOTECA_INDEXES = {
    "categorias_equipamento": [
        {"keys": [("organization_id", 1), ("nome", 1)], "name": "org_nome"},
        {"keys": [("organization_id", 1), ("codigo", 1)], "name": "org_codigo"},
    ],
    "fabricantes": [
        {"keys": [("organization_id", 1), ("nome", 1)], "name": "org_nome"},
        {"keys": [("organization_id", 1), ("categoria_id", 1)], "name": "org_cat"},
    ],
    "modelos_mestre": [
        {"keys": [("organization_id", 1), ("codigo", 1)], "name": "org_codigo"},
        {"keys": [("organization_id", 1), ("categoria_id", 1), ("fabricante_id", 1)], "name": "org_cat_fab"},
        {"keys": [("organization_id", 1), ("nome", 1)], "name": "org_nome"},
    ],
}
