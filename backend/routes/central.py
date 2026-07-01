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


async def _get_user_os(user: Dict, status_list: list, limit: int = 50) -> list:
    """Get OS visible to user with given statuses."""
    query = await build_visibility_query(user, entity_type="os")
    query['status'] = {"$in": status_list}
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("data_planejada", 1).to_list(limit)
    # Enrich with ativo info
    for o in os_list:
        ativo = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1, "sector_id": 1})
        o['ativo'] = ativo
    return os_list


async def _get_execucoes_pendentes(user: Dict, limit: int = 50) -> list:
    """Get pending inspection executions for user."""
    query = await build_visibility_query(user, entity_type="inspecao")
    query['status'] = {"$in": ["pendente", "em_andamento"]}
    inspecoes = await db.inspecoes.find(query, {"_id": 0}).sort("data_programada", 1).to_list(limit)
    for insp in inspecoes:
        ativo = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1, "sector_id": 1})
        insp['ativo'] = ativo
    return inspecoes


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
    for o in vencidas_os:
        a = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        o['ativo'] = a

    insp_query_base = await build_visibility_query(user, entity_type="inspecao")
    vencidas_insp = await db.inspecoes.find(
        {**insp_query_base, "status": {"$in": ["pendente", "em_andamento"]},
         "data_programada": {"$lt": hoje, "$ne": None}},
        {"_id": 0, "checklist": 0}
    ).sort("data_programada", 1).to_list(50)
    for insp in vencidas_insp:
        a = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        insp['ativo'] = a

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
    for o in hoje_os:
        a = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        o['ativo'] = a

    hoje_insp = await db.inspecoes.find(
        {**insp_query_base, "status": {"$in": ["pendente", "em_andamento"]},
         "data_programada": {"$gte": hoje, "$lt": amanha}},
        {"_id": 0, "checklist": 0}
    ).sort("data_programada", 1).to_list(50)
    for insp in hoje_insp:
        a = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        insp['ativo'] = a

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
    for o in semana_os:
        a = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        o['ativo'] = a

    semana_insp = await db.inspecoes.find(
        {**insp_query_base, "status": "pendente",
         "data_programada": {"$gte": amanha, "$lt": fim_semana}},
        {"_id": 0, "checklist": 0}
    ).sort("data_programada", 1).to_list(50)
    for insp in semana_insp:
        a = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        insp['ativo'] = a

    result['semana'] = {
        "os": semana_os,
        "inspecoes": semana_insp,
        "total": len(semana_os) + len(semana_insp)
    }

    # ===== SEM DATA (backlog) =====
    # Use $and to avoid overwriting visibility $or
    sem_data_q = {**os_query_base, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}}
    sem_data_q.setdefault("$and", []).append(
        {"$or": [{"data_planejada": None}, {"data_planejada": {"$exists": False}}, {"data_planejada": ""}]}
    )
    sem_data_os = await db.ordens_servico.find(sem_data_q, {"_id": 0}).sort("created_at", -1).to_list(30)
    for o in sem_data_os:
        a = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        o['ativo'] = a

    result['sem_data'] = {"os": sem_data_os, "total": len(sem_data_os)}

    # ===== EM EXECUÇÃO (ativas agora) =====
    em_exec_os = await db.ordens_servico.find(
        {**os_query_base, "status": "em_execucao"},
        {"_id": 0}
    ).sort("data_inicio", -1).to_list(20)
    for o in em_exec_os:
        a = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        o['ativo'] = a

    em_exec_insp = await db.inspecoes.find(
        {**insp_query_base, "status": "em_andamento"},
        {"_id": 0, "checklist": 0}
    ).to_list(20)
    for insp in em_exec_insp:
        a = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        insp['ativo'] = a

    result['em_execucao'] = {
        "os": em_exec_os,
        "inspecoes": em_exec_insp,
        "total": len(em_exec_os) + len(em_exec_insp)
    }

    # ===== ROLE-SPECIFIC SECTIONS =====

    if role in ('supervisor', 'admin', 'master', 'pcm'):
        # Planos pendentes de aprovação
        planos_q = {"organization_id": org_id, "deleted_at": None, "status": {"$in": ["rascunho", "ativo"]}}
        planos_pendentes = await db.planos_inspecao.find(planos_q, {"_id": 0, "checklist": 0}).to_list(20)
        result['planos_pendentes'] = planos_pendentes

        # OS críticas (emergência + alta prioridade)
        criticas = await db.ordens_servico.find(
            {**os_query_base, "status": {"$in": ["aberta", "em_execucao"]},
             "prioridade": {"$in": ["emergencia", "alta"]}},
            {"_id": 0}
        ).sort("created_at", -1).to_list(10)
        for o in criticas:
            a = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
            o['ativo'] = a
        result['os_criticas'] = criticas

    if role in ('admin', 'master'):
        # Resumo executivo
        base_q = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
        result['resumo'] = {
            "total_os_abertas": await db.ordens_servico.count_documents({**base_q, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}}),
            "total_insp_pendentes": await db.inspecoes.count_documents({**base_q, "status": {"$in": ["pendente", "em_andamento"]}}),
            "total_ativos": await db.ativos.count_documents({**base_q}),
            "ativos_parados": await db.ativos.count_documents({**base_q, "status": {"$in": ["parado", "manutencao"]}}),
        }

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
