"""Central de Trabalho routes: role-adaptive work center for all profiles"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta

from deps import (
    db, get_current_user, get_user_disciplinas,
    build_visibility_query, build_dashboard_visibility,
    _get_asset_ids_for_areas, audit_log
)

router = APIRouter()


async def _bulk_enrich_ativos(items: list) -> None:
    """Enrich OS/inspeção items with ativo data using a single bulk query instead of N+1."""
    ativo_ids = list({item.get('ativo_id') for item in items if item.get('ativo_id')})
    if not ativo_ids:
        for item in items:
            item['ativo'] = None
        return
    ativos_cursor = db.ativos.find({"id": {"$in": ativo_ids}}, {"_id": 0, "id": 1, "tag": 1, "nome": 1, "sector_id": 1})
    ativo_map = {a['id']: a async for a in ativos_cursor}
    for item in items:
        item['ativo'] = ativo_map.get(item.get('ativo_id'))


@router.get("/central")
async def get_central_trabalho(user: Dict = Depends(get_current_user)):
    """Central de Trabalho adaptativa por perfil.
    Returns role-specific work items grouped by urgency."""
    role = user.get('role', 'tecnico')
    user_id = user.get('id', '')
    org_id = user.get('organization_id', '')
    now = datetime.now(timezone.utc)
    hoje = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    amanha = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    fim_semana = (now + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    result = {"role": role, "user_nome": user.get('nome', ''), "turno": user.get('turno', '')}

    # ===== ATIVIDADES VENCIDAS (todas as roles) =====
    os_query_base = await build_visibility_query(user, entity_type="os")
    vencidas_os = await db.ordens_servico.find(
        {**os_query_base, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]},
         "data_planejada": {"$lt": hoje, "$ne": None}},
        {"_id": 0}
    ).sort("data_planejada", 1).to_list(50)

    insp_query_base = await build_visibility_query(user, entity_type="inspecao")
    vencidas_insp = await db.inspecoes.find(
        {**insp_query_base, "status": {"$in": ["pendente", "em_andamento"]},
         "data_programada": {"$lt": hoje, "$ne": None}},
        {"_id": 0, "checklist": 0}
    ).sort("data_programada", 1).to_list(50)

    result['vencidas'] = {
        "os": vencidas_os,
        "inspecoes": vencidas_insp,
        "total": len(vencidas_os) + len(vencidas_insp)
    }

    # ===== HOJE =====
    hoje_os = await db.ordens_servico.find(
        {**os_query_base, "status": {"$in": ["aberta", "planejada", "em_execucao"]},
         "data_planejada": {"$gte": hoje, "$lt": amanha}},
        {"_id": 0}
    ).sort("prioridade", -1).to_list(50)

    hoje_insp = await db.inspecoes.find(
        {**insp_query_base, "status": {"$in": ["pendente", "em_andamento"]},
         "data_programada": {"$gte": hoje, "$lt": amanha}},
        {"_id": 0, "checklist": 0}
    ).sort("data_programada", 1).to_list(50)

    result['hoje'] = {
        "os": hoje_os,
        "inspecoes": hoje_insp,
        "total": len(hoje_os) + len(hoje_insp)
    }

    # ===== SEMANA =====
    semana_os = await db.ordens_servico.find(
        {**os_query_base, "status": {"$in": ["aberta", "planejada"]},
         "data_planejada": {"$gte": amanha, "$lt": fim_semana}},
        {"_id": 0}
    ).sort("data_planejada", 1).to_list(50)

    semana_insp = await db.inspecoes.find(
        {**insp_query_base, "status": "pendente",
         "data_programada": {"$gte": amanha, "$lt": fim_semana}},
        {"_id": 0, "checklist": 0}
    ).sort("data_programada", 1).to_list(50)

    result['semana'] = {
        "os": semana_os,
        "inspecoes": semana_insp,
        "total": len(semana_os) + len(semana_insp)
    }

    # ===== SEM DATA (backlog) =====
    sem_data_q = {**os_query_base, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}}
    sem_data_q.setdefault("$and", []).append(
        {"$or": [{"data_planejada": None}, {"data_planejada": {"$exists": False}}, {"data_planejada": ""}]}
    )
    sem_data_os = await db.ordens_servico.find(sem_data_q, {"_id": 0}).sort("created_at", -1).to_list(30)

    result['sem_data'] = {"os": sem_data_os, "total": len(sem_data_os)}

    # ===== EM EXECUÇÃO (ativas agora) =====
    em_exec_os = await db.ordens_servico.find(
        {**os_query_base, "status": "em_execucao"},
        {"_id": 0}
    ).sort("data_inicio", -1).to_list(20)

    em_exec_insp = await db.inspecoes.find(
        {**insp_query_base, "status": "em_andamento"},
        {"_id": 0, "checklist": 0}
    ).to_list(20)

    result['em_execucao'] = {
        "os": em_exec_os,
        "inspecoes": em_exec_insp,
        "total": len(em_exec_os) + len(em_exec_insp)
    }

    # ===== ROLE-SPECIFIC SECTIONS =====
    criticas = []
    if role in ('supervisor', 'admin', 'master', 'pcm'):
        planos_q = {"organization_id": org_id, "deleted_at": None, "status": {"$in": ["rascunho", "ativo"]}}
        planos_pendentes = await db.planos_inspecao.find(planos_q, {"_id": 0, "checklist": 0}).to_list(20)
        result['planos_pendentes'] = planos_pendentes

        criticas = await db.ordens_servico.find(
            {**os_query_base, "status": {"$in": ["aberta", "em_execucao"]},
             "prioridade": {"$in": ["emergencia", "alta"]}},
            {"_id": 0}
        ).sort("created_at", -1).to_list(10)
        result['os_criticas'] = criticas

    if role in ('admin', 'master'):
        base_q = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
        result['resumo'] = {
            "total_os_abertas": await db.ordens_servico.count_documents({**base_q, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}}),
            "total_insp_pendentes": await db.inspecoes.count_documents({**base_q, "status": {"$in": ["pendente", "em_andamento"]}}),
            "total_ativos": await db.ativos.count_documents({**base_q}),
            "ativos_parados": await db.ativos.count_documents({**base_q, "status": {"$in": ["parado", "manutencao"]}}),
        }

    # ===== BULK ENRICH all OS and inspections with ativo data (1 query instead of N) =====
    all_items = vencidas_os + hoje_os + semana_os + sem_data_os + em_exec_os + criticas + vencidas_insp + hoje_insp + semana_insp + em_exec_insp
    await _bulk_enrich_ativos(all_items)

    # Summary counts
    total_atividades = result['vencidas']['total'] + result['hoje']['total'] + result['semana']['total'] + result['em_execucao']['total']
    result['total_atividades'] = total_atividades

    return result


@router.post("/migrate/planos-legados")
async def migrate_planos_legados(user: Dict = Depends(get_current_user)):
    """Migrate legacy plans: status 'ativo' → 'aprovado'. With audit trail."""
    if user.get('role') not in ('admin', 'master'):
        raise HTTPException(status_code=403, detail="Apenas administradores")
    org_id = user.get('organization_id', '')

    # Find legacy plans
    legacy = await db.planos_inspecao.find(
        {"organization_id": org_id, "deleted_at": None, "status": "ativo"},
        {"_id": 0, "id": 1, "nome": 1, "status": 1}
    ).to_list(1000)

    if not legacy:
        return {"message": "Nenhum plano legado encontrado", "migrated": 0}

    # Backup info for audit
    backup_ids = [p['id'] for p in legacy]

    # Migrate
    result = await db.planos_inspecao.update_many(
        {"organization_id": org_id, "deleted_at": None, "status": "ativo"},
        {"$set": {
            "status": "aprovado",
            "aprovado_por": user.get('id'),
            "aprovado_em": datetime.now(timezone.utc).isoformat(),
            "migrado_de": "ativo",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    await audit_log("migration", "plano_inspecao", "bulk", user,
        f"Migração legado: {result.modified_count} planos 'ativo' → 'aprovado'. IDs: {','.join(backup_ids[:20])}")

    return {
        "message": f"{result.modified_count} planos migrados de 'ativo' para 'aprovado'",
        "migrated": result.modified_count,
        "plan_ids": backup_ids
    }


# ============== MINHA ÁREA (Field Operations) ==============

@router.get("/minha-area")
async def get_minha_area(user: Dict = Depends(get_current_user)):
    """Asset-centric field view: equipment in user's areas with plans, pending inspections, and active OS."""
    org_id = user.get('organization_id', '')
    user_id = user.get('id', '')
    area_ids = user.get('area_ids', [])
    disciplinas = get_user_disciplinas(user)
    turno = user.get('turno', 'ADM')

    # Get equipment in user's areas (or all if no area restriction)
    ativo_query = {"organization_id": org_id, "deleted_at": None}
    if area_ids:
        ativo_query["sector_id"] = {"$in": area_ids}
    ativos = await db.ativos.find(ativo_query, {"_id": 0, "id": 1, "tag": 1, "nome": 1, "tipo_equipamento": 1, "sector_id": 1, "criticidade": 1, "status_operacional": 1}).sort("tag", 1).to_list(200)

    ativo_ids = [a['id'] for a in ativos]

    # Enrich sectors
    sector_ids = list({a.get('sector_id') for a in ativos if a.get('sector_id')})
    sectors_map = {}
    if sector_ids:
        async for s in db.sectors.find({"id": {"$in": sector_ids}}, {"_id": 0, "id": 1, "nome": 1}):
            sectors_map[s['id']] = s['nome']
    for a in ativos:
        a['sector_nome'] = sectors_map.get(a.get('sector_id'), '')

    # Approved plans per equipment
    planos = await db.planos_inspecao.find(
        {"organization_id": org_id, "deleted_at": None, "status": "aprovado"},
        {"_id": 0, "id": 1, "nome": 1, "tipo": 1, "disciplina": 1, "frequencia": 1, "ativo_id": 1, "tipo_equipamento": 1, "perguntas": 1}
    ).to_list(500)

    # Map plans to equipment (direct binding + generic by tipo_equipamento)
    planos_por_ativo = {}
    for p in planos:
        if p.get('ativo_id'):
            planos_por_ativo.setdefault(p['ativo_id'], []).append(p)
        elif p.get('tipo_equipamento'):
            for a in ativos:
                if (a.get('tipo_equipamento') or '').lower() == p['tipo_equipamento'].lower():
                    planos_por_ativo.setdefault(a['id'], []).append({**p, '_generico': True})

    # Pending inspections for user
    insp_query = {"organization_id": org_id, "deleted_at": None, "status": {"$in": ["pendente", "em_andamento"]}}
    if ativo_ids:
        insp_query["ativo_id"] = {"$in": ativo_ids}
    inspecoes = await db.inspecoes.find(insp_query, {"_id": 0}).sort("data_programada", 1).to_list(50)
    await _bulk_enrich_ativos(inspecoes)

    # Active OS for user (assigned to me or in my areas)
    os_query = {"organization_id": org_id, "deleted_at": None, "status": {"$in": ["aberta", "em_execucao", "pausada", "programada", "disponivel", "solicitada"]}}
    if area_ids:
        asset_ids_for_os = await _get_asset_ids_for_areas(org_id, area_ids)
        os_query["$or"] = [{"responsavel_id": user_id}, {"equipe": user_id}, {"ativo_id": {"$in": asset_ids_for_os}}]
    else:
        os_query["$or"] = [{"responsavel_id": user_id}, {"equipe": user_id}]
    os_ativas = await db.ordens_servico.find(os_query, {"_id": 0}).sort("prioridade", -1).to_list(50)
    await _bulk_enrich_ativos(os_ativas)

    # My OS specifically (responsavel or in equipe)
    minhas_os = [o for o in os_ativas if o.get('responsavel_id') == user_id or user_id in (o.get('equipe') or [])]

    return {
        "user_nome": user.get('nome', ''),
        "turno": turno,
        "disciplinas": disciplinas,
        "equipamentos": ativos,
        "planos_por_ativo": planos_por_ativo,
        "inspecoes_pendentes": inspecoes,
        "minhas_os": minhas_os,
        "os_area": os_ativas,
        "contadores": {
            "equipamentos": len(ativos),
            "planos_ativos": sum(len(v) for v in planos_por_ativo.values()),
            "inspecoes_pendentes": len(inspecoes),
            "minhas_os": len(minhas_os),
            "os_area": len(os_ativas),
        }
    }


# ============== INDICADORES ==============

@router.get("/indicadores")
async def get_indicadores(
    periodo: str = "mes",
    user: Dict = Depends(get_current_user)
):
    """KPI indicators by collaborator, team, shift, equipment, discipline."""
    org_id = user.get('organization_id', '')
    now = datetime.now(timezone.utc)

    if periodo == "hoje":
        desde = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    elif periodo == "semana":
        desde = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    elif periodo == "ano":
        desde = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    else:
        desde = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    base_q = {"organization_id": org_id, "deleted_at": None}

    # OS stats in period
    os_periodo = await db.ordens_servico.find(
        {**base_q, "created_at": {"$gte": desde}},
        {"_id": 0, "id": 1, "status": 1, "tipo": 1, "disciplina": 1, "responsavel_id": 1, "tempo_execucao_minutos": 1, "data_conclusao": 1, "ativo_id": 1}
    ).to_list(5000)

    os_concluidas = [o for o in os_periodo if o.get('status') == 'concluida']
    os_abertas = [o for o in os_periodo if o.get('status') in ('aberta', 'em_execucao', 'pausada', 'programada', 'disponivel', 'solicitada')]

    # Inspections in period
    insp_periodo = await db.inspecoes.find(
        {**base_q, "created_at": {"$gte": desde}},
        {"_id": 0, "id": 1, "status": 1, "resultado": 1, "responsavel_id": 1, "duracao_minutos": 1, "ativo_id": 1, "tipo": 1, "disciplina": 1}
    ).to_list(5000)

    insp_concluidas = [i for i in insp_periodo if i.get('status') in ('concluida', 'com_pendencias')]

    # By collaborator
    por_colaborador = {}
    for o in os_concluidas:
        uid = o.get('responsavel_id', 'sem_responsavel')
        por_colaborador.setdefault(uid, {"os_concluidas": 0, "hh_total": 0, "inspecoes": 0})
        por_colaborador[uid]["os_concluidas"] += 1
        por_colaborador[uid]["hh_total"] += (o.get('tempo_execucao_minutos') or 0)
    for i in insp_concluidas:
        uid = i.get('responsavel_id', 'sem_responsavel')
        por_colaborador.setdefault(uid, {"os_concluidas": 0, "hh_total": 0, "inspecoes": 0})
        por_colaborador[uid]["inspecoes"] += 1

    # Enrich user names
    user_ids = list(por_colaborador.keys())
    users_map = {}
    if user_ids:
        async for u in db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "nome": 1, "turno": 1, "disciplina_principal": 1}):
            users_map[u['id']] = u
    for uid, stats in por_colaborador.items():
        u = users_map.get(uid, {})
        stats["nome"] = u.get("nome", "—")
        stats["turno"] = u.get("turno", "—")
        stats["disciplina"] = u.get("disciplina_principal", "—")

    # By discipline
    por_disciplina = {}
    for o in os_concluidas:
        d = o.get('disciplina', 'outros')
        por_disciplina.setdefault(d, {"os": 0, "hh": 0})
        por_disciplina[d]["os"] += 1
        por_disciplina[d]["hh"] += (o.get('tempo_execucao_minutos') or 0)

    # By turno
    por_turno = {}
    for uid, stats in por_colaborador.items():
        t = stats.get("turno", "ADM")
        por_turno.setdefault(t, {"os_concluidas": 0, "hh_total": 0, "pessoas": set()})
        por_turno[t]["os_concluidas"] += stats["os_concluidas"]
        por_turno[t]["hh_total"] += stats["hh_total"]
        por_turno[t]["pessoas"].add(uid)
    for t in por_turno:
        por_turno[t]["pessoas"] = len(por_turno[t]["pessoas"])

    # By equipment (top 10 most active)
    por_equipamento = {}
    for o in os_periodo:
        aid = o.get('ativo_id', '')
        if aid:
            por_equipamento.setdefault(aid, {"os_total": 0, "os_concluidas": 0, "hh": 0})
            por_equipamento[aid]["os_total"] += 1
            if o.get('status') == 'concluida':
                por_equipamento[aid]["os_concluidas"] += 1
                por_equipamento[aid]["hh"] += (o.get('tempo_execucao_minutos') or 0)

    # Enrich top 10 equipment
    top_equip = sorted(por_equipamento.items(), key=lambda x: x[1]['os_total'], reverse=True)[:10]
    if top_equip:
        equip_ids = [e[0] for e in top_equip]
        async for a in db.ativos.find({"id": {"$in": equip_ids}}, {"_id": 0, "id": 1, "tag": 1, "nome": 1}):
            if a['id'] in por_equipamento:
                por_equipamento[a['id']]["tag"] = a.get("tag", "")
                por_equipamento[a['id']]["nome"] = a.get("nome", "")

    tempos = [o.get('tempo_execucao_minutos', 0) for o in os_concluidas if o.get('tempo_execucao_minutos')]

    return {
        "periodo": periodo,
        "desde": desde,
        "resumo": {
            "os_criadas": len(os_periodo),
            "os_concluidas": len(os_concluidas),
            "os_backlog": len(os_abertas),
            "inspecoes_realizadas": len(insp_concluidas),
            "inspecoes_pendentes": len([i for i in insp_periodo if i.get('status') in ('pendente', 'em_andamento')]),
            "hh_total_minutos": sum(tempos),
            "tempo_medio_minutos": round(sum(tempos) / len(tempos), 1) if tempos else 0,
        },
        "por_colaborador": list(por_colaborador.values()),
        "por_disciplina": por_disciplina,
        "por_turno": {t: {"os_concluidas": v["os_concluidas"], "hh_total": v["hh_total"], "pessoas": v["pessoas"]} for t, v in por_turno.items()},
        "por_equipamento": [{"ativo_id": e[0], **e[1]} for e in top_equip],
    }
