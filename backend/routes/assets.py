"""Asset routes: Áreas (sectors), Ativos CRUD, Materiais por Equipamento"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid

from deps import (
    db, get_current_user, check_admin_only, check_write_permission,
    audit_log, criar_notificacao, generate_tag
)
from models import (
    SectorCreate, SectorUpdate, AtivoCreate, AtivoUpdate, AtivoMaterialCreate,
    NotificacaoTipo
)

router = APIRouter()


# ============== ÁREAS (sectors collection) ==============

@router.get("/sectors")
async def list_sectors(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    sectors = await db.sectors.find(query, {"_id": 0}).sort("nome", 1).to_list(500)
    for s in sectors:
        s['asset_count'] = await db.ativos.count_documents({"sector_id": s['id'], "deleted_at": None})
    return sectors

@router.get("/sectors/{sector_id}")
async def get_sector(sector_id: str, user: Dict = Depends(get_current_user)):
    s = await db.sectors.find_one({"id": sector_id, "deleted_at": None}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    return s

@router.post("/sectors")
async def create_sector(data: SectorCreate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    org_id = user.get('organization_id', '')
    existing = await db.sectors.find_one({"codigo": data.codigo.upper(), "organization_id": org_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail=f"Código '{data.codigo}' já existe")
    sector_id = str(uuid.uuid4())
    doc = {
        "id": sector_id, "organization_id": org_id,
        "codigo": data.codigo.upper(), "nome": data.nome,
        "descricao": data.descricao, "cor": data.cor, "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None
    }
    await db.sectors.insert_one(doc)
    doc.pop('_id', None)
    return doc

@router.put("/sectors/{sector_id}")
async def update_sector(sector_id: str, data: SectorUpdate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    if update:
        update['updated_at'] = datetime.now(timezone.utc).isoformat()
        await db.sectors.update_one({"id": sector_id}, {"$set": update})
    return await db.sectors.find_one({"id": sector_id}, {"_id": 0})

@router.delete("/sectors/{sector_id}")
async def delete_sector(sector_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    asset_count = await db.ativos.count_documents({"sector_id": sector_id, "deleted_at": None})
    if asset_count > 0:
        raise HTTPException(status_code=400, detail=f"Área possui {asset_count} ativos. Mova-os antes de excluir.")
    await db.sectors.update_one({"id": sector_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "sectors", sector_id, user, "Área excluída")
    return {"success": True}

@router.patch("/sectors/{sector_id}/toggle")
async def toggle_sector(sector_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    s = await db.sectors.find_one({"id": sector_id, "deleted_at": None}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    new_status = not s.get('is_active', True)
    await db.sectors.update_one({"id": sector_id}, {"$set": {"is_active": new_status}})
    return {"success": True, "is_active": new_status}

# Legacy compat
@router.get("/areas")
async def list_areas(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    return await db.sectors.find(query, {"_id": 0}).sort("nome", 1).to_list(500)


# ============== ATIVOS CRUD (simplified) ==============

@router.get("/ativos")
async def list_ativos(
    sector_id: Optional[str] = None,
    search: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if sector_id:
        query['sector_id'] = sector_id

    ativos = await db.ativos.find(query, {"_id": 0}).sort("tag", 1).to_list(1000)

    if search:
        sl = search.lower()
        ativos = [a for a in ativos if sl in a.get('tag', '').lower() or sl in a.get('nome', '').lower()]

    # Batch sectors
    sid_list = list(set(a.get('sector_id') for a in ativos if a.get('sector_id')))
    sectors = await db.sectors.find({"id": {"$in": sid_list}}, {"_id": 0}).to_list(len(sid_list)) if sid_list else []
    sector_map = {s['id']: s for s in sectors}

    for ativo in ativos:
        ativo['sector'] = sector_map.get(ativo.get('sector_id'))

    return ativos

@router.get("/ativos/qr/{qr_code}")
async def get_ativo_by_qr(qr_code: str, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"qr_code": qr_code, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return ativo

@router.get("/ativos/tag/{tag}")
async def get_ativo_by_tag(tag: str, user: Dict = Depends(get_current_user)):
    query = {"tag": tag.upper(), "deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    ativo = await db.ativos.find_one(query, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return ativo

@router.get("/ativos/{ativo_id}")
async def get_ativo(ativo_id: str, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")

    ativo['sector'] = await db.sectors.find_one({"id": ativo.get('sector_id')}, {"_id": 0})
    ativo['ordens_servico'] = await db.ordens_servico.find({"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    ativo['inspecoes'] = await db.inspecoes.find({"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    ativo['materiais'] = await db.ativo_materiais.find({"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}).to_list(100)

    # Auto-calculated KPIs from OS history
    os_corretivas = await db.ordens_servico.find(
        {"ativo_id": ativo_id, "tipo": "corretiva", "status": "concluida", "deleted_at": None},
        {"_id": 0, "tempo_execucao_minutos": 1, "data_abertura": 1, "data_conclusao": 1}
    ).to_list(500)

    total_os = await db.ordens_servico.count_documents({"ativo_id": ativo_id, "deleted_at": None})
    num_falhas = len(os_corretivas)
    tempos = [o['tempo_execucao_minutos'] for o in os_corretivas if o.get('tempo_execucao_minutos')]

    mttr_horas = round(sum(tempos) / len(tempos) / 60, 2) if tempos else 0
    # MTBF = total operational hours / number of failures (approx 720h/month operational)
    mtbf_horas = round(720 / num_falhas, 1) if num_falhas > 0 else 0
    disponibilidade = round(mtbf_horas / (mtbf_horas + mttr_horas) * 100, 1) if (mtbf_horas + mttr_horas) > 0 else 100

    ativo['kpis'] = {
        "mtbf_horas": mtbf_horas,
        "mttr_horas": mttr_horas,
        "disponibilidade_percent": disponibilidade,
        "total_os": total_os,
        "total_falhas": num_falhas
    }

    return ativo

@router.post("/ativos")
async def create_ativo(data: AtivoCreate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    org_id = user.get('organization_id', '')

    sector = await db.sectors.find_one({"id": data.sector_id, "deleted_at": None})
    if not sector:
        raise HTTPException(status_code=404, detail="Área não encontrada")

    tag = data.tag.upper() if data.tag else generate_tag()
    existing = await db.ativos.find_one({"tag": tag, "organization_id": org_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="TAG já existe")

    ativo_id = str(uuid.uuid4())
    ativo_doc = {
        "id": ativo_id, "tag": tag, "qr_code": str(uuid.uuid4()),
        "nome": data.nome, "tipo_equipamento": data.tipo_equipamento,
        "fabricante": data.fabricante, "modelo": data.modelo,
        "numero_serie": data.numero_serie,
        "sector_id": data.sector_id,
        "organization_id": org_id,
        "observacoes": data.observacoes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }

    await db.ativos.insert_one(ativo_doc)
    ativo_doc.pop('_id', None)
    return ativo_doc

@router.put("/ativos/{ativo_id}")
async def update_ativo(ativo_id: str, data: AtivoUpdate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    existing = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.ativos.update_one({"id": ativo_id}, {"$set": update_data})
    return await db.ativos.find_one({"id": ativo_id}, {"_id": 0})

@router.delete("/ativos/{ativo_id}")
async def delete_ativo(ativo_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin'])
    existing = await db.ativos.find_one({"id": ativo_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    await db.ativos.update_one({"id": ativo_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "ativos", ativo_id, user, f"Ativo {existing.get('tag','')} excluído")
    return {"success": True}


# ============== MATERIAIS POR EQUIPAMENTO ==============

@router.get("/ativos/{ativo_id}/materiais")
async def list_ativo_materiais(ativo_id: str, user: Dict = Depends(get_current_user)):
    """List materials linked to an asset"""
    return await db.ativo_materiais.find({"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}).to_list(100)

@router.post("/ativos/{ativo_id}/materiais")
async def add_ativo_material(ativo_id: str, data: AtivoMaterialCreate, user: Dict = Depends(get_current_user)):
    """Add material to an asset's bill of materials"""
    check_write_permission(user, ['admin', 'pcm', 'supervisor'])
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    mat_id = str(uuid.uuid4())
    doc = {
        "id": mat_id, "ativo_id": ativo_id,
        "nome": data.nome, "codigo": data.codigo,
        "quantidade": data.quantidade, "unidade": data.unidade,
        "observacoes": data.observacoes,
        "created_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None
    }
    await db.ativo_materiais.insert_one(doc)
    doc.pop('_id', None)
    return doc

@router.delete("/ativos/{ativo_id}/materiais/{material_id}")
async def remove_ativo_material(ativo_id: str, material_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm', 'supervisor'])
    await db.ativo_materiais.update_one({"id": material_id, "ativo_id": ativo_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    return {"success": True}
