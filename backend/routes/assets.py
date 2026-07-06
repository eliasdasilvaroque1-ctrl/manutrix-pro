"""Asset routes: Áreas (sectors), Ativos CRUD, Materiais por Equipamento"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid

from deps import (
    db, get_current_user, check_admin_only, check_pcm_or_admin, check_write_permission,
    audit_log, criar_notificacao, generate_tag, verify_org_access, audit_field_changes,
    ROLE_GROUPS
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

    # Visibility: operador/técnicos see only assets in their areas
    role = user.get('role', '')
    if role in ROLE_GROUPS['operacional'] and not sector_id:
        area_ids = user.get('area_ids') or []
        if area_ids:
            query['sector_id'] = {"$in": area_ids}

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
    verify_org_access(user, ativo, "Ativo")

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
    check_pcm_or_admin(user)
    org_id = user.get('organization_id', '')

    sector = await db.sectors.find_one({"id": data.sector_id, "deleted_at": None})
    if not sector:
        raise HTTPException(status_code=404, detail="Área não encontrada")

    tag = data.tag.upper() if data.tag else generate_tag()
    existing = await db.ativos.find_one({"tag": tag, "sector_id": data.sector_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="TAG já existe nesta área")

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
    check_pcm_or_admin(user)
    existing = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, existing, "Ativo")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['alterado_por'] = user.get('id')
    await db.ativos.update_one({"id": ativo_id}, {"$set": update_data})
    await audit_field_changes("ativos", ativo_id, f"Ativo {existing.get('tag','')}", existing, update_data, user)
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

@router.post("/ativos/{ativo_id}/duplicar")
async def duplicate_ativo(ativo_id: str, body: dict, user: Dict = Depends(get_current_user)):
    """Duplicate an asset: copies tipo, fabricante, modelo, observacoes, BOM, manuais, fotos"""
    check_admin_only(user)
    org_id = user.get('organization_id', '')

    original = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not original:
        raise HTTPException(status_code=404, detail="Ativo original não encontrado")

    new_sector_id = body.get('sector_id', original.get('sector_id'))
    new_tag = (body.get('tag', '') or '').upper()
    new_numero_serie = body.get('numero_serie', '')

    if not new_tag:
        raise HTTPException(status_code=400, detail="TAG é obrigatória")

    sector = await db.sectors.find_one({"id": new_sector_id, "deleted_at": None})
    if not sector:
        raise HTTPException(status_code=404, detail="Área não encontrada")

    existing = await db.ativos.find_one({"tag": new_tag, "sector_id": new_sector_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="TAG já existe nesta área")

    new_id = str(uuid.uuid4())
    new_doc = {
        "id": new_id, "tag": new_tag, "qr_code": str(uuid.uuid4()),
        "nome": original.get('nome', ''),
        "tipo_equipamento": original.get('tipo_equipamento', ''),
        "fabricante": original.get('fabricante'),
        "modelo": original.get('modelo'),
        "numero_serie": new_numero_serie or None,
        "sector_id": new_sector_id,
        "organization_id": org_id,
        "observacoes": original.get('observacoes'),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.ativos.insert_one(new_doc)

    # Duplicate BOM (materiais)
    materiais = await db.ativo_materiais.find({"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}).to_list(200)
    for mat in materiais:
        mat_copy = {**mat, "id": str(uuid.uuid4()), "ativo_id": new_id, "created_at": datetime.now(timezone.utc).isoformat()}
        await db.ativo_materiais.insert_one(mat_copy)

    # Duplicate manuais (reference only — files stay shared)
    manuais = await db.manuais.find({"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}).to_list(50)
    for man in manuais:
        man_copy = {**man, "id": str(uuid.uuid4()), "ativo_id": new_id, "created_at": datetime.now(timezone.utc).isoformat()}
        await db.manuais.insert_one(man_copy)

    # Duplicate fotos/attachments
    attachments = await db.attachments.find({"entity_type": "asset", "entity_id": ativo_id}, {"_id": 0}).to_list(50)
    for att in attachments:
        att_copy = {**att, "id": str(uuid.uuid4()), "entity_id": new_id, "created_at": datetime.now(timezone.utc).isoformat()}
        await db.attachments.insert_one(att_copy)

    await audit_log("duplicate", "ativos", new_id, user, f"Ativo {new_tag} duplicado de {original.get('tag','')}")

    new_doc.pop('_id', None)
    new_doc['_duplicated_from'] = original.get('tag', '')
    new_doc['_materiais_copied'] = len(materiais)
    new_doc['_manuais_copied'] = len(manuais)
    new_doc['_fotos_copied'] = len(attachments)
    return new_doc


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

@router.put("/ativos/{ativo_id}/materiais/{material_id}")
async def update_ativo_material(ativo_id: str, material_id: str, data: AtivoMaterialCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm', 'supervisor'])
    mat = await db.ativo_materiais.find_one({"id": material_id, "ativo_id": ativo_id, "deleted_at": None})
    if not mat:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    update = {
        "nome": data.nome, "codigo": data.codigo,
        "quantidade": data.quantidade, "unidade": data.unidade,
        "observacoes": data.observacoes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.ativo_materiais.update_one({"id": material_id}, {"$set": update})
    return await db.ativo_materiais.find_one({"id": material_id}, {"_id": 0})



# ============== HISTÓRICO DO ATIVO (PRONTUÁRIO) ==============

@router.get("/ativos/{ativo_id}/historico")
async def get_ativo_historico(
    ativo_id: str,
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    usuario_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    """Full asset history: OS + Inspections + Anomalies + Material Consumption, with filters"""
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    eventos = []

    # Helper to resolve user name
    user_cache = {}
    async def get_user_name(uid):
        if not uid:
            return None
        if uid not in user_cache:
            u = await db.users.find_one({"id": uid}, {"_id": 0, "nome": 1})
            user_cache[uid] = u.get('nome') if u else uid
        return user_cache[uid]

    # OS
    if not tipo or tipo == 'os':
        os_query = {"ativo_id": ativo_id, "deleted_at": None}
        if status:
            os_query['status'] = status
        oss = await db.ordens_servico.find(
            os_query,
            {"_id": 0, "id": 1, "numero": 1, "tipo": 1, "status": 1, "titulo": 1,
             "descricao_servico": 1, "descricao": 1, "responsavel_id": 1, "criado_por": 1,
             "iniciado_por": 1, "concluido_por": 1, "data_abertura": 1,
             "data_conclusao": 1, "data_inicio": 1, "tempo_execucao_minutos": 1, "created_at": 1,
             "equipe": 1, "prioridade": 1}
        ).sort("created_at", -1).to_list(500)
        for o in oss:
            resp_nome = await get_user_name(o.get('responsavel_id'))
            criado_nome = await get_user_name(o.get('criado_por'))
            concluido_nome = await get_user_name(o.get('concluido_por'))
            ev_date = o.get('data_conclusao') or o.get('data_abertura') or o.get('created_at')
            if usuario_id and o.get('criado_por') != usuario_id and o.get('responsavel_id') != usuario_id and o.get('iniciado_por') != usuario_id and o.get('concluido_por') != usuario_id and usuario_id not in (o.get('equipe') or []):
                continue
            eventos.append({
                "tipo_evento": "os",
                "id": o['id'],
                "data": ev_date,
                "titulo": f"OS {o.get('tipo','').capitalize()} #{o.get('numero','')}",
                "descricao": o.get('descricao_servico') or o.get('titulo', ''),
                "status": o.get('status'),
                "prioridade": o.get('prioridade'),
                "usuario": resp_nome or criado_nome,
                "criado_por": criado_nome,
                "concluido_por": concluido_nome,
                "tempo_minutos": o.get('tempo_execucao_minutos'),
            })

    # Inspections
    if not tipo or tipo == 'inspecao':
        insp_query = {"ativo_id": ativo_id, "deleted_at": None}
        if status:
            insp_query['status'] = status
        insps = await db.inspecoes.find(
            insp_query,
            {"_id": 0, "id": 1, "tipo": 1, "status": 1, "resultado": 1,
             "responsavel_id": 1, "criado_por": 1, "concluido_por": 1,
             "data_conclusao": 1, "data_inicio": 1, "created_at": 1, "duracao_minutos": 1}
        ).sort("created_at", -1).to_list(500)
        for i in insps:
            resp_nome = await get_user_name(i.get('responsavel_id'))
            criado_nome = await get_user_name(i.get('criado_por'))
            concluido_nome = await get_user_name(i.get('concluido_por'))
            ev_date = i.get('data_conclusao') or i.get('created_at')
            if usuario_id and i.get('criado_por') != usuario_id and i.get('responsavel_id') != usuario_id and i.get('concluido_por') != usuario_id:
                continue
            eventos.append({
                "tipo_evento": "inspecao",
                "id": i['id'],
                "data": ev_date,
                "titulo": f"Inspeção {i.get('tipo','').capitalize()}",
                "descricao": f"Resultado: {i.get('resultado', 'pendente')}",
                "status": i.get('status'),
                "usuario": resp_nome or criado_nome,
                "concluido_por": concluido_nome,
                "tempo_minutos": i.get('duracao_minutos'),
            })

    # Anomalies
    if not tipo or tipo == 'anomalia':
        anom_query = {"ativo_id": ativo_id, "deleted_at": None}
        if status:
            anom_query['status'] = status
        anoms = await db.anomalias.find(
            anom_query,
            {"_id": 0, "id": 1, "descricao": 1, "severidade": 1, "status": 1,
             "criado_por": 1, "resolvido_por": 1, "encerrado_por": 1, "created_at": 1}
        ).sort("created_at", -1).to_list(500)
        for a in anoms:
            criado_nome = await get_user_name(a.get('criado_por'))
            encerrado_nome = await get_user_name(a.get('encerrado_por'))
            if usuario_id and a.get('criado_por') != usuario_id and a.get('resolvido_por') != usuario_id and a.get('encerrado_por') != usuario_id:
                continue
            eventos.append({
                "tipo_evento": "anomalia",
                "id": a['id'],
                "data": a.get('created_at'),
                "titulo": f"Anomalia ({a.get('severidade','media')})",
                "descricao": a.get('descricao', ''),
                "status": a.get('status', 'aberta'),
                "usuario": criado_nome,
                "encerrado_por": encerrado_nome,
            })

    # Material Consumption
    if not tipo or tipo == 'material':
        mat_query = {"ativo_id": ativo_id, "deleted_at": None}
        mats = await db.os_materiais.find(mat_query, {"_id": 0}).sort("created_at", -1).to_list(500)
        for m in mats:
            if usuario_id and m.get('usuario_id') != usuario_id:
                continue
            eventos.append({
                "tipo_evento": "material",
                "id": m['id'],
                "data": m.get('created_at'),
                "titulo": f"Material Consumido: {m.get('codigo','')}",
                "descricao": f"{m.get('descricao','')} — {m.get('quantidade',0)} {m.get('unidade','UN')} — OS #{m.get('os_numero','')}",
                "status": None,
                "usuario": m.get('usuario_nome'),
                "os_numero": m.get('os_numero'),
                "quantidade": m.get('quantidade'),
                "codigo": m.get('codigo'),
            })


    # Paradas Programadas (where area matches this asset's sector)
    if not tipo or tipo == 'parada':
        sector_id = ativo.get('sector_id')
        if sector_id:
            paradas = await db.paradas_programadas.find(
                {"area_id": sector_id, "deleted_at": None},
                {"_id": 0, "id": 1, "numero": 1, "tipo": 1, "status": 1, "descricao": 1,
                 "data_inicio": 1, "data_fim": 1, "duracao_horas": 1, "responsavel_id": 1, "created_at": 1}
            ).sort("created_at", -1).to_list(100)
            for pp in paradas:
                resp_nome = await get_user_name(pp.get('responsavel_id'))
                eventos.append({
                    "tipo_evento": "parada",
                    "id": pp['id'],
                    "data": pp.get('data_inicio') or pp.get('created_at'),
                    "titulo": f"Parada {pp.get('tipo','').replace('_',' ').capitalize()} {pp.get('numero','')}",
                    "descricao": pp.get('descricao', ''),
                    "status": pp.get('status'),
                    "usuario": resp_nome,
                    "duracao_horas": pp.get('duracao_horas'),
                })

    # Apply date filters
    if data_inicio:
        eventos = [e for e in eventos if (e.get('data') or '') >= data_inicio]
    if data_fim:
        eventos = [e for e in eventos if (e.get('data') or '') <= data_fim + 'T23:59:59']

    # Sort all by date descending
    eventos.sort(key=lambda x: x.get('data', '') or '', reverse=True)
    return eventos


@router.get("/ativos/{ativo_id}/saude")
async def get_ativo_saude(ativo_id: str, user: Dict = Depends(get_current_user)):
    """Equipment health summary for Prontuário do Ativo."""
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    verify_org_access(user, ativo, "Ativo")

    # Last and next for each type
    async def get_last(collection, query, date_field="data_conclusao"):
        doc = await collection.find_one(
            {**query, "deleted_at": None, date_field: {"$ne": None}},
            {"_id": 0}, sort=[(date_field, -1)]
        )
        return doc

    async def get_next_pending(collection, query):
        doc = await collection.find_one(
            {**query, "deleted_at": None, "status": {"$in": ["pendente", "planejada", "aberta"]}},
            {"_id": 0}, sort=[("data_programada", 1)]
        )
        return doc

    user_cache = {}
    async def resolve_user(uid):
        if not uid: return None
        if uid not in user_cache:
            u = await db.users.find_one({"id": uid}, {"_id": 0, "nome": 1})
            user_cache[uid] = u.get('nome') if u else None
        return user_cache[uid]

    # Inspections
    last_insp = await get_last(db.inspecoes, {"ativo_id": ativo_id, "tipo": {"$nin": ["lubrificacao"]}})
    next_insp = await get_next_pending(db.inspecoes, {"ativo_id": ativo_id, "tipo": {"$nin": ["lubrificacao"]}})

    # Preventivas (OS tipo=preventiva)
    last_prev = await get_last(db.ordens_servico, {"ativo_id": ativo_id, "tipo": "preventiva"}, "data_conclusao")
    next_prev_q = {"ativo_id": ativo_id, "tipo": "preventiva", "deleted_at": None, "status": {"$in": ["aberta", "planejada"]}}
    next_prev = await db.ordens_servico.find_one(next_prev_q, {"_id": 0}, sort=[("data_planejada", 1)])

    # Lubrificação
    last_lub = await get_last(db.inspecoes, {"ativo_id": ativo_id, "tipo": "lubrificacao"})

    # Last OS (any)
    last_os = await get_last(db.ordens_servico, {"ativo_id": ativo_id})

    # Last anomalia
    last_anom = await db.anomalias.find_one(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0}, sort=[("created_at", -1)]
    )

    async def format_event(doc, tipo):
        if not doc: return None
        executor = await resolve_user(doc.get('concluido_por') or doc.get('responsavel_id') or doc.get('criado_por'))
        return {
            "data": doc.get('data_conclusao') or doc.get('data_programada') or doc.get('data_planejada') or doc.get('created_at'),
            "executor": executor,
            "resultado": doc.get('resultado') or doc.get('status'),
            "id": doc.get('id'),
        }

    return {
        "ultima_inspecao": await format_event(last_insp, "inspecao"),
        "proxima_inspecao": await format_event(next_insp, "inspecao"),
        "ultima_preventiva": await format_event(last_prev, "preventiva"),
        "proxima_preventiva": await format_event(next_prev, "preventiva"),
        "ultima_lubrificacao": await format_event(last_lub, "lubrificacao"),
        "ultima_os": await format_event(last_os, "os"),
        "ultima_anomalia": await format_event(last_anom, "anomalia") if last_anom else None,
    }
