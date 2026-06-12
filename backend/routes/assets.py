"""Asset routes: Plants, Sectors, Areas (legacy), Ativos CRUD"""
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
    PlantCreate, PlantUpdate, SectorCreate, SectorUpdate,
    AtivoCreate, AtivoUpdate, AssetStatus, Criticidade, NotificacaoTipo
)

router = APIRouter()


# ============== PLANTS ==============

@router.get("/plants")
async def list_plants(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    plants = await db.plants.find(query, {"_id": 0}).sort("codigo", 1).to_list(100)
    for p in plants:
        p['sector_count'] = await db.sectors.count_documents({"plant_id": p['id'], "deleted_at": None})
        p['asset_count'] = await db.ativos.count_documents({"plant_id": p['id'], "deleted_at": None})
    return plants

@router.get("/plants/{plant_id}")
async def get_plant(plant_id: str, user: Dict = Depends(get_current_user)):
    p = await db.plants.find_one({"id": plant_id, "deleted_at": None}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Planta não encontrada")
    p['sectors'] = await db.sectors.find({"plant_id": plant_id, "deleted_at": None}, {"_id": 0}).to_list(100)
    return p

@router.post("/plants")
async def create_plant(data: PlantCreate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    org_id = user.get('organization_id', '')
    existing = await db.plants.find_one({"codigo": data.codigo.upper(), "organization_id": org_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail=f"Código '{data.codigo}' já existe")
    
    plant_id = str(uuid.uuid4())
    doc = {
        "id": plant_id, "organization_id": org_id,
        "codigo": data.codigo.upper(), "nome": data.nome,
        "descricao": data.descricao, "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None
    }
    await db.plants.insert_one(doc)
    doc.pop('_id', None)
    return doc

@router.put("/plants/{plant_id}")
async def update_plant(plant_id: str, data: PlantUpdate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    await db.plants.update_one({"id": plant_id}, {"$set": update})
    return await db.plants.find_one({"id": plant_id}, {"_id": 0})

@router.delete("/plants/{plant_id}")
async def delete_plant(plant_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    asset_count = await db.ativos.count_documents({"plant_id": plant_id, "deleted_at": None})
    if asset_count > 0:
        raise HTTPException(status_code=400, detail=f"Planta possui {asset_count} ativos. Mova-os antes de excluir.")
    await db.plants.update_one({"id": plant_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "plants", plant_id, user, "Planta excluída")
    return {"success": True}


# ============== SECTORS ==============

@router.get("/sectors")
async def list_sectors(plant_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if plant_id:
        query['plant_id'] = plant_id
    sectors = await db.sectors.find(query, {"_id": 0}).sort("codigo", 1).to_list(500)
    plant_ids = list(set(s.get('plant_id') for s in sectors if s.get('plant_id')))
    plants = await db.plants.find({"id": {"$in": plant_ids}}, {"_id": 0, "id": 1, "nome": 1, "codigo": 1}).to_list(len(plant_ids)) if plant_ids else []
    plant_map = {p['id']: p for p in plants}
    for s in sectors:
        s['plant'] = plant_map.get(s.get('plant_id'))
        s['asset_count'] = await db.ativos.count_documents({"sector_id": s['id'], "deleted_at": None})
    return sectors

@router.get("/sectors/{sector_id}")
async def get_sector(sector_id: str, user: Dict = Depends(get_current_user)):
    s = await db.sectors.find_one({"id": sector_id, "deleted_at": None}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="Setor não encontrado")
    return s

@router.post("/sectors")
async def create_sector(data: SectorCreate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    org_id = user.get('organization_id', '')
    plant = await db.plants.find_one({"id": data.plant_id, "deleted_at": None})
    if not plant:
        raise HTTPException(status_code=404, detail="Planta não encontrada")
    existing = await db.sectors.find_one({"codigo": data.codigo.upper(), "plant_id": data.plant_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail=f"Código '{data.codigo}' já existe nesta planta")
    sector_id = str(uuid.uuid4())
    doc = {
        "id": sector_id, "organization_id": org_id, "plant_id": data.plant_id,
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
    await db.sectors.update_one({"id": sector_id}, {"$set": update})
    return await db.sectors.find_one({"id": sector_id}, {"_id": 0})

@router.delete("/sectors/{sector_id}")
async def delete_sector(sector_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    asset_count = await db.ativos.count_documents({"sector_id": sector_id, "deleted_at": None})
    if asset_count > 0:
        raise HTTPException(status_code=400, detail=f"Setor possui {asset_count} ativos. Mova-os antes de excluir.")
    await db.sectors.update_one({"id": sector_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "sectors", sector_id, user, "Setor excluído")
    return {"success": True}


# ============== AREAS (legacy compat) ==============

@router.get("/areas")
async def list_areas(planta_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if planta_id:
        query['planta_id'] = planta_id
    return await db.areas.find(query, {"_id": 0}).to_list(100)

@router.get("/areas/{area_id}")
async def get_area(area_id: str, user: Dict = Depends(get_current_user)):
    area = await db.areas.find_one({"id": area_id, "deleted_at": None}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    return area


# ============== ATIVOS CRUD ==============

@router.get("/ativos")
async def list_ativos(
    area_id: Optional[str] = None,
    status: Optional[AssetStatus] = None,
    criticidade: Optional[Criticidade] = None,
    search: Optional[str] = None,
    plant_id: Optional[str] = None,
    sector_id: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if area_id:
        query['$or'] = [{"area_id": area_id}, {"sector_id": area_id}]
    if plant_id:
        query['plant_id'] = plant_id
    if sector_id:
        query['sector_id'] = sector_id
    if status:
        query['status'] = status.value
    if criticidade:
        query['criticidade'] = criticidade.value
    
    ativos = await db.ativos.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    if search:
        search_lower = search.lower()
        ativos = [a for a in ativos if search_lower in a.get('tag', '').lower() or search_lower in a.get('nome', '').lower()]
    
    sid_list = list(set(a.get('sector_id') or a.get('area_id') for a in ativos if a.get('sector_id') or a.get('area_id')))
    pid_list = list(set(a.get('plant_id') for a in ativos if a.get('plant_id')))
    
    sectors = await db.sectors.find({"id": {"$in": sid_list}}, {"_id": 0}).to_list(len(sid_list)) if sid_list else []
    sector_map = {s['id']: s for s in sectors}
    if sid_list:
        legacy = await db.areas.find({"id": {"$in": sid_list}}, {"_id": 0}).to_list(len(sid_list))
        for la in legacy:
            if la['id'] not in sector_map:
                sector_map[la['id']] = la
    
    plants = await db.plants.find({"id": {"$in": pid_list}}, {"_id": 0, "id": 1, "nome": 1, "codigo": 1}).to_list(len(pid_list)) if pid_list else []
    plant_map = {p['id']: p for p in plants}
    
    for ativo in ativos:
        sid = ativo.get('sector_id') or ativo.get('area_id')
        ativo['area'] = sector_map.get(sid)
        ativo['sector'] = sector_map.get(sid)
        ativo['plant'] = plant_map.get(ativo.get('plant_id'))
        parts = [ativo.get('plant', {}).get('nome', ''), (ativo.get('sector') or {}).get('nome', ''), ativo.get('tag', '')]
        ativo['location_path'] = ' > '.join(p for p in parts if p)
    
    return ativos

@router.get("/ativos/{ativo_id}")
async def get_ativo(ativo_id: str, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    area = await db.areas.find_one({"id": ativo.get('area_id')}, {"_id": 0})
    ativo['area'] = area
    ativo['ordens_servico'] = await db.ordens_servico.find({"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    ativo['inspecoes'] = await db.inspecoes.find({"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    
    os_total = await db.ordens_servico.count_documents({"ativo_id": ativo_id, "deleted_at": None})
    os_corretivas = await db.ordens_servico.count_documents({"ativo_id": ativo_id, "tipo": "corretiva", "deleted_at": None})
    ativo['estatisticas'] = {"total_os": os_total, "os_corretivas": os_corretivas, "os_preventivas": os_total - os_corretivas}
    
    return ativo

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

@router.post("/ativos")
async def create_ativo(data: AtivoCreate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    org_id = user.get('organization_id', '')
    
    plant_id = data.plant_id
    sector_id = data.sector_id or data.area_id
    
    if sector_id:
        sector = await db.sectors.find_one({"id": sector_id, "deleted_at": None}, {"_id": 0})
        if sector:
            plant_id = plant_id or sector.get('plant_id')
        else:
            area = await db.areas.find_one({"id": sector_id}, {"_id": 0})
            if area:
                plant_id = plant_id or area.get('planta_id') or area.get('plant_id')
    
    if not plant_id:
        default_plant = await db.plants.find_one({"codigo": "PP", "deleted_at": None}, {"_id": 0})
        if default_plant:
            plant_id = default_plant['id']
    
    tag = data.tag.upper() if data.tag else generate_tag()
    existing = await db.ativos.find_one({"tag": tag, "organization_id": org_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="TAG já existe nesta organização")
    
    ativo_id = str(uuid.uuid4())
    ativo_doc = {
        "id": ativo_id, "tag": tag, "qr_code": str(uuid.uuid4()),
        "nome": data.nome, "tipo_equipamento": data.tipo_equipamento,
        "fabricante": data.fabricante, "modelo": data.modelo,
        "numero_serie": data.numero_serie,
        "plant_id": plant_id, "sector_id": sector_id, "area_id": sector_id,
        "organization_id": org_id, "centro_custo": data.centro_custo,
        "criticidade": data.criticidade.value, "status": data.status.value,
        "mtbf_horas": data.mtbf_horas, "mttr_horas": data.mttr_horas,
        "data_instalacao": data.data_instalacao, "garantia_ate": data.garantia_ate,
        "valor_aquisicao": data.valor_aquisicao, "depreciacao_anual": data.depreciacao_anual,
        "fornecedor": data.fornecedor, "foto_url": data.foto_url,
        "manual_url": data.manual_url, "observacoes": data.observacoes,
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
    
    update_data = {k: v.value if isinstance(v, Enum) else v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    if 'status' in update_data and update_data['status'] == 'parado' and existing.get('status') != 'parado':
        admins = await db.users.find(
            {"organization_id": existing.get('organization_id'), "role": {"$in": ["admin", "supervisor"]}, "deleted_at": None},
            {"_id": 0, "id": 1}
        ).to_list(10)
        for admin in admins:
            await criar_notificacao(
                admin['id'], existing.get('organization_id', ''), NotificacaoTipo.ATIVO_PARADO,
                f"Ativo Parado: {existing.get('tag', '')}",
                f"{existing.get('nome', '')} foi marcado como parado",
                f"/ativos/{ativo_id}"
            )
    
    await db.ativos.update_one({"id": ativo_id}, {"$set": update_data})
    return await db.ativos.find_one({"id": ativo_id}, {"_id": 0})

@router.delete("/ativos/{ativo_id}")
async def delete_ativo(ativo_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin'])
    existing = await db.ativos.find_one({"id": ativo_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    await db.ativos.update_one({"id": ativo_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "ativos", ativo_id, user, f"Ativo {existing.get('tag','')} - {existing.get('nome','')} excluído")
    return {"success": True, "message": "Ativo excluído com sucesso"}
