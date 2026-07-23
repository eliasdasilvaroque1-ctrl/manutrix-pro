"""Work Order routes: OS CRUD, Kanban, Statistics, History"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid

from deps import (
    db, get_current_user, check_admin_only, check_write_permission, check_not_gerente,
    audit_log, criar_notificacao, generate_os_numero, get_scoped_asset_ids, verify_org_access, audit_field_changes,
    build_visibility_query, build_dashboard_visibility, ROLE_GROUPS, logger
)
from models import (
    OSCreate, OSUpdate, OSStatus,
    NotificacaoTipo, KanbanMoveBody, ConcluirOSBody
)
from data_architecture import rebuild_daily_metrics, rebuild_monthly_metrics

router = APIRouter()

# ============== STATE MACHINE ==============
# Valid transitions: { current_status: { next_status: [allowed_roles] } }
OS_TRANSITIONS = {
    "solicitada": {
        "em_analise": ["master", "admin", "pcm"],
        "rejeitada": ["master", "admin", "pcm"],
        "cancelada": ["master", "admin"],
    },
    "em_analise": {
        "aprovada": ["master", "admin", "pcm"],
        "rejeitada": ["master", "admin", "pcm"],
        "cancelada": ["master", "admin"],
    },
    "aprovada": {
        "planejada": ["master", "admin", "pcm"],
        "cancelada": ["master", "admin"],
    },
    "aberta": {
        "planejada": ["master", "admin", "pcm"],
        "programada": ["master", "admin", "pcm"],
        "em_execucao": ["master", "admin", "pcm", "supervisor"] + ROLE_GROUPS['execucao'],
        "cancelada": ["master", "admin"],
    },
    "planejada": {
        "programada": ["master", "admin", "pcm"],
        "cancelada": ["master", "admin"],
    },
    "programada": {
        "disponivel": ["master", "admin", "pcm"],
        "em_execucao": ["master", "admin", "supervisor"] + ROLE_GROUPS['execucao'],
        "cancelada": ["master", "admin"],
    },
    "disponivel": {
        "em_execucao": ["master", "admin", "supervisor"] + ROLE_GROUPS['execucao'],
        "cancelada": ["master", "admin"],
    },
    "em_execucao": {
        "pausada": ["master", "admin", "supervisor"] + ROLE_GROUPS['execucao'],
        "concluida": ["master", "admin", "supervisor"] + ROLE_GROUPS['execucao'],
        "cancelada": ["master", "admin"],
    },
    "pausada": {
        "em_execucao": ["master", "admin", "supervisor"] + ROLE_GROUPS['execucao'],
        "cancelada": ["master", "admin"],
    },
    "concluida": {
        "encerrada": ["master", "admin", "gerente"],
    },
    # Terminal states: "encerrada", "cancelada", "rejeitada" — no transitions allowed
}

def validate_os_transition(current_status, new_status, user_role):
    """Validate state machine transition. Returns (valid, error_message)."""
    allowed = OS_TRANSITIONS.get(current_status, {})
    if new_status not in allowed:
        valid_targets = list(allowed.keys()) or ["(estado terminal)"]
        return False, f"Transicao {current_status} → {new_status} nao permitida. Transicoes validas: {', '.join(valid_targets)}"
    allowed_roles = allowed[new_status]
    if user_role not in allowed_roles:
        return False, f"Perfil '{user_role}' nao pode executar transicao {current_status} → {new_status}"
    return True, None


@router.get("/ordens-servico")
async def list_os(
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    disciplina: Optional[str] = None,
    prioridade: Optional[str] = None,
    responsavel_id: Optional[str] = None,
    ativo_id: Optional[str] = None,
    sector_id: Optional[str] = None,
    origem: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    user: Dict = Depends(get_current_user)
):
    # Sanitize pagination
    limit = min(max(limit, 1), 200)
    skip = max(skip, 0)

    # Start with role-based visibility filter
    query = await build_visibility_query(user, entity_type="os")

    # Apply optional frontend filters (visual only)
    if status:
        query['status'] = status
    if tipo:
        query['tipo'] = tipo
    if disciplina:
        query['disciplina'] = disciplina
    if prioridade:
        query['prioridade'] = prioridade
    if responsavel_id:
        query['responsavel_id'] = responsavel_id
    if ativo_id:
        query['ativo_id'] = ativo_id
    if origem:
        query['origem'] = origem

    if sector_id:
        asset_ids = await get_scoped_asset_ids(user.get('organization_id', ''), sector_id=sector_id)
        if asset_ids is not None:
            query['ativo_id'] = {"$in": asset_ids}

    # Projeção reduzida para lista (excluir campos pesados)
    list_projection = {
        "_id": 0,
        "fotos": 0,
        "servicos_realizados": 0,
        "campos_personalizados": 0,
        "campos_personalizados_ids": 0,
        "historico_status": 0,
    }

    os_list = await db.ordens_servico.find(query, list_projection).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    ativo_ids = list(set(o.get('ativo_id') for o in os_list if o.get('ativo_id')))
    resp_ids = list(set(o.get('responsavel_id') for o in os_list if o.get('responsavel_id')))
    equipe_all_ids = list(set(uid for o in os_list for uid in (o.get('equipe') or [])))

    # Batch lookups em paralelo
    import asyncio as _aio
    async def _noop_list(): return []
    ativos_task = db.ativos.find({"id": {"$in": ativo_ids}}, {"_id": 0, "id": 1, "tag": 1, "nome": 1, "sector_id": 1}).to_list(len(ativo_ids)) if ativo_ids else _noop_list()
    resp_task = db.users.find({"id": {"$in": resp_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(len(resp_ids)) if resp_ids else _noop_list()
    equipe_task = db.users.find({"id": {"$in": equipe_all_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(len(equipe_all_ids)) if equipe_all_ids else _noop_list()

    ativos_batch, resp_batch, equipe_batch = await _aio.gather(ativos_task, resp_task, equipe_task)

    sector_ids = list(set(a.get('sector_id') for a in ativos_batch if a.get('sector_id')))
    sectors_batch = await db.sectors.find({"id": {"$in": sector_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(len(sector_ids)) if sector_ids else []
    sector_map = {s['id']: s for s in sectors_batch}

    equipe_map = {u['id']: u.get('nome', '') for u in equipe_batch}

    ativo_map = {a['id']: a for a in ativos_batch}
    resp_map = {r['id']: r for r in resp_batch}

    for a in ativos_batch:
        if a.get('sector_id'):
            a['sector'] = sector_map.get(a['sector_id'])

    for os in os_list:
        os['ativo'] = ativo_map.get(os.get('ativo_id'))
        os['responsavel'] = resp_map.get(os.get('responsavel_id'))
        equipe_ids = os.get('equipe', [])
        if equipe_ids:
            os['equipe_nomes'] = [equipe_map.get(uid, '') for uid in equipe_ids if uid in equipe_map]
        try:
            if os.get('data_planejada') and os.get('status') not in ['concluida', 'cancelada']:
                planned = datetime.fromisoformat(str(os['data_planejada']).replace('Z', '+00:00'))
                os['atrasada'] = datetime.now(timezone.utc) > planned
            else:
                os['atrasada'] = False
        except Exception:
            os['atrasada'] = False

    return os_list


@router.get("/ordens-servico/estatisticas")
async def os_estatisticas(user: Dict = Depends(get_current_user)):
    query = await build_dashboard_visibility(user)

    now = datetime.now(timezone.utc).isoformat()
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0).isoformat()

    # SINGLE aggregation: status + tipo + disciplina + origem counts in one pipeline
    facet_pipeline = [
        {"$match": query},
        {"$facet": {
            "por_status": [{"$group": {"_id": "$status", "count": {"$sum": 1}}}],
            "por_tipo": [{"$group": {"_id": "$tipo", "count": {"$sum": 1}}}],
            "por_disciplina": [{"$group": {"_id": "$disciplina", "count": {"$sum": 1}}}],
            "por_origem": [{"$group": {"_id": "$origem", "count": {"$sum": 1}}}],
        }}
    ]
    facet_result = await db.ordens_servico.aggregate(facet_pipeline).to_list(1)
    facet = facet_result[0] if facet_result else {}

    status_counts = {r['_id']: r['count'] for r in facet.get('por_status', []) if r['_id']}
    tipo_counts = {r['_id']: r['count'] for r in facet.get('por_tipo', []) if r['_id']}
    disciplina_counts = {r['_id']: r['count'] for r in facet.get('por_disciplina', []) if r['_id']}
    origem_counts = {r['_id']: r['count'] for r in facet.get('por_origem', []) if r['_id']}

    # 2 additional counts (atrasadas + concluidas_mes)
    atrasadas = await db.ordens_servico.count_documents({**query, "status": {"$nin": ["concluida", "encerrada", "cancelada"]}, "data_planejada": {"$lt": now, "$ne": None}})
    concluidas_mes = await db.ordens_servico.count_documents({**query, "status": {"$in": ["concluida", "encerrada"]}, "data_conclusao": {"$gte": month_start}})

    active_statuses = ["solicitada", "em_analise", "aguardando_aprovacao", "aguardando_material",
                       "programada", "disponivel", "em_execucao", "pausada", "aberta", "planejada"]

    return {
        "por_status": status_counts, "por_tipo": tipo_counts,
        "por_disciplina": disciplina_counts, "por_origem": origem_counts,
        "atrasadas": atrasadas, "concluidas_mes": concluidas_mes,
        "aguardando_aprovacao": status_counts.get("aguardando_aprovacao", 0),
        "aguardando_material": status_counts.get("aguardando_material", 0),
        "total_abertas": sum(status_counts.get(s, 0) for s in active_statuses)
    }


@router.get("/ordens-servico/backlog")
async def get_backlog(user: Dict = Depends(get_current_user)):
    query = await build_visibility_query(user, entity_type="os")
    query['status'] = {"$in": ["solicitada", "em_analise", "aguardando_aprovacao", "aguardando_material",
                                "programada", "disponivel", "em_execucao", "pausada", "aberta", "planejada"]}
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", 1).to_list(500)
    enriched = []
    for os in os_list:
        ativo = await db.ativos.find_one({"id": os.get('ativo_id')}, {"_id": 0})
        created = datetime.fromisoformat(os['created_at'].replace('Z', '+00:00')) if isinstance(os['created_at'], str) else os['created_at']
        days_open = (datetime.now(timezone.utc) - created).days
        prio = os.get('prioridade', 'media')
        cor = 'vermelho' if days_open > 7 or prio == 'critica' else ('amarelo' if days_open > 3 or prio == 'alta' else 'verde')
        enriched.append({**os, "ativo": ativo, "dias_aberto": days_open, "cor_prioridade": cor})
    return enriched


@router.get("/ordens-servico/{os_id}")
async def get_os(os_id: str, user: Dict = Depends(get_current_user)):
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os, "OS")
    os['ativo'] = await db.ativos.find_one({"id": os.get('ativo_id')}, {"_id": 0})
    if os.get('ativo') and os['ativo'].get('sector_id'):
        os['ativo']['sector'] = await db.sectors.find_one({"id": os['ativo']['sector_id']}, {"_id": 0, "nome": 1})
    if os.get('responsavel_id'):
        os['responsavel'] = await db.users.find_one({"id": os['responsavel_id']}, {"_id": 0, "nome": 1, "email": 1, "telefone": 1})
    # Enrich actor names
    for field in ['criado_por', 'planejado_por', 'iniciado_por', 'concluido_por', 'alterado_por']:
        uid = os.get(field)
        if uid:
            u = await db.users.find_one({"id": uid}, {"_id": 0, "nome": 1})
            os[f'{field}_nome'] = u.get('nome') if u else uid
    # Enrich equipe/executantes names
    equipe_ids = os.get('equipe', [])
    if equipe_ids:
        equipe_users = await db.users.find({"id": {"$in": equipe_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(len(equipe_ids))
        os['equipe_nomes'] = {u['id']: u.get('nome') for u in equipe_users}
    # Materiais sugeridos do ativo
    os['materiais_sugeridos'] = await db.ativo_materiais.find({"ativo_id": os.get('ativo_id'), "deleted_at": None}, {"_id": 0}).to_list(50)
    return os


@router.post("/ordens-servico")
async def create_os(data: OSCreate, user: Dict = Depends(get_current_user)):
    # Operador pode criar solicitação, gerente não
    allowed_roles = ['admin', 'master', 'pcm', 'supervisor', 'operador'] + ROLE_GROUPS['execucao']
    check_write_permission(user, allowed_roles)
    check_not_gerente(user)

    # Técnicos só podem criar OS corretiva (execução direta)
    role = user.get('role', '')
    if role in ROLE_GROUPS['execucao'] and data.tipo != 'corretiva':
        raise HTTPException(status_code=403, detail="Técnicos podem criar apenas OS corretiva (execução direta)")

    ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")

    org_id = ativo.get('organization_id', user.get('organization_id', ''))

    # Validate procedimento_id if provided
    if data.procedimento_id:
        proc = await db.procedimentos.find_one({"id": data.procedimento_id, "deleted_at": None}, {"_id": 0, "organization_id": 1})
        if not proc:
            raise HTTPException(status_code=404, detail="Procedimento não encontrado")
        if proc.get('organization_id') != org_id:
            raise HTTPException(status_code=404, detail="Procedimento não encontrado")

    numero = await generate_os_numero(org_id)

    role = user.get('role', '')
    is_operacional = role in ROLE_GROUPS['operacional']

    # Determine initial status based on role and origin
    execucao_direta = getattr(data, 'execucao_direta', False) or (hasattr(data, 'origem') and data.origem == 'execucao_direta')
    if execucao_direta and role in (ROLE_GROUPS['execucao'] + ['supervisor', 'admin', 'master', 'pcm']):
        # Direct execution: OS goes straight to em_execucao (no PCM backlog)
        status_inicial = "em_execucao"
        origem = "execucao_direta"
    elif role == 'operador':
        status_inicial = "solicitada"
        origem = data.origem or "operador"
    elif role in ('supervisor',):
        status_inicial = data.status if hasattr(data, 'status') and data.status else "em_analise"
        origem = data.origem or "supervisor"
    else:
        status_inicial = "programada"
        origem = data.origem or "pcm"

    # Check if approval is needed (from org_config workflow rules)
    aprovacao = {"necessaria": False, "status": "nao_requer", "aprovador": None, "data": None, "observacao": ""}
    config = await db.org_config.find_one({"organization_id": org_id}, {"_id": 0, "workflow": 1})
    workflow = config.get("workflow", {}) if config else {}
    tipos_aprovacao = workflow.get("tipos_que_precisam_aprovacao", [])
    limite_custo = workflow.get("aprovacao_gerente_acima", 10000)
    custo_total = (data.custo_pecas or 0) + (data.custo_mao_obra or 0)
    if data.tipo in tipos_aprovacao or custo_total >= limite_custo:
        aprovacao["necessaria"] = True
        aprovacao["status"] = "pendente"

    os_id = str(uuid.uuid4())
    os_doc = {
        "id": os_id, "numero": numero, "ativo_id": data.ativo_id,
        "organization_id": org_id, "tipo": data.tipo,
        "disciplina": data.disciplina or ativo.get('disciplina', 'mecanica'),
        "sector_id": ativo.get('sector_id', ''),
        "origem": origem,
        "prioridade": data.prioridade, "titulo": data.titulo,
        "descricao": data.descricao, "justificativa": data.justificativa,
        "status": status_inicial,
        "aprovacao": aprovacao,
        "responsavel_id": data.responsavel_id, "equipe": data.equipe or [],
        "data_abertura": datetime.now(timezone.utc).isoformat(),
        "data_planejada": data.data_planejada,
        "data_inicio": datetime.now(timezone.utc).isoformat() if execucao_direta else None,
        "data_conclusao": None,
        "custo_pecas": data.custo_pecas, "custo_mao_obra": data.custo_mao_obra,
        "custo_total": custo_total,
        "causa_falha": data.causa_falha,
        "equipamento_parado": data.equipamento_parado,
        "horas_parada": data.horas_parada,
        "procedimento_id": data.procedimento_id or None,
        "procedimento": data.procedimento,
        "seguranca": data.seguranca,
        "campos_personalizados_valores": data.campos_personalizados_valores or {},
        "layout_snapshot": None,
        "assinaturas_dados": data.assinaturas_dados or [],
        "tempo_execucao_minutos": None, "observacoes": None, "servicos_realizados": None,
        "criado_por": user.get('id'),
        "planejado_por": None, "data_planejamento": None,
        "iniciado_por": user.get('id') if execucao_direta else None,
        "concluido_por": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None
    }

    # Auto-snapshot: freeze active layout + custom fields for this org/type
    try:
        # Prioritize layouts matching the OS type specifically
        layout = await db.layouts_documento.find_one(
            {"organization_id": org_id, "deleted_at": None, "status": "ativo",
             "tipo_documento": {"$in": [data.tipo, f"os_{data.tipo}"]}},
            {"_id": 0}
        )
        if not layout:
            layout = await db.layouts_documento.find_one(
                {"organization_id": org_id, "deleted_at": None, "status": "ativo",
                 "$or": [{"tipo_documento": None}, {"tipo_documento": ""}]},
                {"_id": 0}
            )
        if layout:
            os_doc["layout_snapshot"] = {k: v for k, v in layout.items() if k not in ("_id", "organization_id", "deleted_at", "deleted_by")}
        # Freeze custom fields — filter by layout's list if available, else all applicable
        campo_ids = (layout or {}).get("campos_personalizados_ids", []) if layout else []
        if campo_ids:
            campos = await db.campos_personalizados.find(
                {"organization_id": org_id, "id": {"$in": campo_ids}, "status": "ativo", "deleted_at": None},
                {"_id": 0}
            ).sort("ordem", 1).to_list(100)
        else:
            campos = await db.campos_personalizados.find(
                {"organization_id": org_id, "status": "ativo", "deleted_at": None, "aplicacao_modulos": "os"},
                {"_id": 0}
            ).sort("ordem", 1).to_list(100)
        if campos:
            applicable = [c for c in campos if not c.get("aplicacao_tipos") or data.tipo in c["aplicacao_tipos"]]
            if applicable:
                os_doc["campos_personalizados_definicoes"] = [{k: v for k, v in c.items() if k not in ("_id", "organization_id", "deleted_at", "deleted_by")} for c in applicable]
    except Exception as e:
        logger.warning(f"Auto-snapshot OS layout/campos: {e}")

    await db.ordens_servico.insert_one(os_doc)
    await audit_log("create", "ordens_servico", os_id, user, f"OS #{numero} criada — {data.tipo}/{data.disciplina}")
    if data.responsavel_id:
        await criar_notificacao(data.responsavel_id, org_id, NotificacaoTipo.OS_ATRIBUIDA,
            f"Nova OS atribuída: #{numero}", f"Ativo: {ativo.get('tag', '')} - {data.titulo}", f"/os/{os_id}")
    os_doc.pop('_id', None)
    return os_doc


@router.put("/ordens-servico/{os_id}")
async def update_os(os_id: str, data: OSUpdate, user: Dict = Depends(get_current_user)):
    role = user.get('role', '')
    # PCM/admin can edit anything; supervisor can edit most; gerente only status changes
    if role == 'gerente':
        if data.status not in (None, 'aguardando_aprovacao', 'programada', 'cancelada'):
            pass  # allow approval-related changes only
    else:
        check_write_permission(user, ['admin', 'master', 'pcm', 'supervisor'])
    existing = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, existing, "OS")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    # Allow procedimento_id removal (explicit null or empty string)
    raw_dump = data.model_dump()
    if 'procedimento_id' in raw_dump and raw_dump['procedimento_id'] in (None, ''):
        update_data['procedimento_id'] = None

    # Validate procedimento_id if being changed to a non-null value
    if update_data.get('procedimento_id'):
        pid = update_data['procedimento_id']
        org_id = existing.get('organization_id', user.get('organization_id', ''))
        proc = await db.procedimentos.find_one({"id": pid, "deleted_at": None}, {"_id": 0, "organization_id": 1})
        if not proc or proc.get('organization_id') != org_id:
            raise HTTPException(status_code=404, detail="Procedimento não encontrado")

    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['alterado_por'] = user.get('id')

    if 'custo_pecas' in update_data or 'custo_mao_obra' in update_data:
        pecas = update_data.get('custo_pecas', existing.get('custo_pecas', 0))
        mao_obra = update_data.get('custo_mao_obra', existing.get('custo_mao_obra', 0))
        update_data['custo_total'] = pecas + mao_obra

    await db.ordens_servico.update_one({"id": os_id}, {"$set": update_data})
    await audit_field_changes("ordens_servico", os_id, f"OS #{existing.get('numero','')}", existing, update_data, user)
    return await db.ordens_servico.find_one({"id": os_id}, {"_id": 0})


@router.delete("/ordens-servico/{os_id}")
async def delete_os(os_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    existing = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, existing, "OS")
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "ordens_servico", os_id, user, f"OS #{existing.get('numero')} excluída")
    return {"success": True, "message": "OS excluída com sucesso"}


@router.post("/ordens-servico/{os_id}/iniciar")
async def iniciar_os(os_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor'] + ROLE_GROUPS['execucao'])
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os, "OS")
    allowed_start = ['aberta', 'programada', 'disponivel', 'planejada', 'pausada', 'solicitada', 'em_analise']
    if os.get('status') not in allowed_start:
        raise HTTPException(status_code=400, detail=f"OS com status '{os.get('status')}' não pode ser iniciada")
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"status": "em_execucao", "data_inicio": datetime.now(timezone.utc).isoformat(), "iniciado_por": user.get('id'), "alterado_por": user.get('id'), "updated_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("status_change", "ordens_servico", os_id, user, f"OS #{os.get('numero')} → em_execucao")
    return {"success": True, "message": "OS iniciada"}


@router.post("/ordens-servico/{os_id}/pausar")
async def pausar_os(os_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor'] + ROLE_GROUPS['execucao'])
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")
    if os_doc.get('status') != 'em_execucao':
        raise HTTPException(status_code=400, detail=f"OS com status '{os_doc.get('status')}' não pode ser pausada")
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"status": "pausada", "alterado_por": user.get('id'), "updated_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("status_change", "ordens_servico", os_id, user, f"OS #{os_doc.get('numero')} → pausada")
    return {"success": True, "message": "OS pausada"}


@router.patch("/ordens-servico/{os_id}/status")
async def update_os_status(os_id: str, body: KanbanMoveBody, user: Dict = Depends(get_current_user)):
    """Kanban drag-and-drop status update — validated by state machine."""
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")

    current_status = os_doc.get('status', '')
    new_status = body.new_status
    user_role = user.get('role', '')

    # Validate transition via state machine
    valid, error = validate_os_transition(current_status, new_status, user_role)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    update = {"status": new_status, "alterado_por": user.get('id'), "updated_at": datetime.now(timezone.utc).isoformat()}
    if new_status in ('planejada', 'programada') and not os_doc.get('planejado_por'):
        update['planejado_por'] = user.get('id')
        update['data_planejamento'] = datetime.now(timezone.utc).isoformat()
    if new_status == 'em_execucao' and not os_doc.get('data_inicio'):
        update['data_inicio'] = datetime.now(timezone.utc).isoformat()
        update['iniciado_por'] = user.get('id')
    await db.ordens_servico.update_one({"id": os_id}, {"$set": update})
    await audit_log("status_change", "ordens_servico", os_id, user, f"OS #{os_doc.get('numero')} {current_status} → {new_status}")
    return {"success": True, "new_status": new_status, "from_status": current_status}


@router.get("/ordens-servico/{os_id}/transitions")
async def get_os_transitions(os_id: str, user: Dict = Depends(get_current_user)):
    """Return valid state transitions for the current OS status and user role."""
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0, "status": 1})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    status = os_doc.get('status', '')
    role = user.get('role', '')
    allowed = OS_TRANSITIONS.get(status, {})
    transitions = [s for s, roles in allowed.items() if role in roles]
    return {"current_status": status, "valid_transitions": transitions}

@router.post("/ordens-servico/{os_id}/concluir")
async def concluir_os(os_id: str, body: ConcluirOSBody = ConcluirOSBody(), user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor'] + ROLE_GROUPS['execucao'])
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")
    if os_doc.get('status') in ('concluida', 'cancelada'):
        raise HTTPException(status_code=400, detail=f"OS com status '{os_doc.get('status')}' não pode ser concluída novamente")
    if not os_doc.get('data_inicio') and not body.data_inicio:
        raise HTTPException(status_code=400, detail="Informe a data e hora de início da execução.")
    descricao = body.servicos_realizados or body.observacoes or os_doc.get('descricao')
    if not descricao:
        raise HTTPException(status_code=400, detail="Descrição do serviço é obrigatória para fechar a OS")
    # Photo check: skip for rapid finish
    if not body.skip_foto_check and os_doc.get('tipo') in ['corretiva']:
        org_id = os_doc.get('organization_id', '')
        config = await db.org_config.find_one({"organization_id": org_id}, {"_id": 0, "workflow": 1})
        foto_obr = config.get('workflow', {}).get('foto_obrigatoria_corretiva', True) if config else True
        if foto_obr:
            attachments = await db.attachments.count_documents({"entity_type": "work_order", "entity_id": os_id})
            if attachments == 0:
                raise HTTPException(status_code=400, detail="OS corretiva exige pelo menos uma foto/evidência anexada. Adicione fotos antes de concluir.")
    tempo = body.tempo_execucao_minutos
    data_inicio_final = body.data_inicio or os_doc.get('data_inicio')
    data_conclusao_final = body.data_conclusao or datetime.now(timezone.utc).isoformat()
    if tempo is None and data_inicio_final:
        start = datetime.fromisoformat(data_inicio_final.replace('Z', '+00:00'))
        end = datetime.fromisoformat(data_conclusao_final.replace('Z', '+00:00'))
        tempo = max(1, int((end - start).total_seconds() / 60))
    if not tempo:
        raise HTTPException(status_code=400, detail="Tempo gasto é obrigatório para fechar a OS")
    # Atomic update: only update if status is still not concluida (prevents race condition)
    update_fields = {
        "status": "concluida", "data_conclusao": data_conclusao_final,
        "tempo_execucao_minutos": tempo, "descricao_servico": descricao,
        "concluido_por": user.get('id'), "alterado_por": user.get('id'),
        "observacoes": body.observacoes, "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if body.data_inicio and not os_doc.get('data_inicio'):
        update_fields['data_inicio'] = body.data_inicio
        update_fields['iniciado_por'] = user.get('id')
    result = await db.ordens_servico.update_one(
        {"id": os_id, "status": {"$nin": ["concluida", "cancelada"]}},
        {"$set": update_fields}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=409, detail="OS já foi concluída ou cancelada por outro usuário")
    await audit_log("status_change", "ordens_servico", os_id, user, f"OS #{os_doc.get('numero')} → concluida (tempo: {tempo}min)")
    try:
        metric_dt = datetime.fromisoformat(data_conclusao_final.replace('Z', '+00:00'))
        metric_date = metric_dt.strftime("%Y-%m-%d")
        participant_ids = set((os_doc.get("equipe") or []) + [os_doc.get("responsavel_id"), user.get("id")])
        for uid in [uid for uid in participant_ids if uid]:
            await rebuild_daily_metrics(db, os_doc.get("organization_id", user.get("organization_id", "")), uid, metric_date)
            await rebuild_monthly_metrics(db, os_doc.get("organization_id", user.get("organization_id", "")), uid, metric_dt.year, metric_dt.month)
    except Exception as e:
        logger.warning(f"Metrics rebuild failed after OS conclusion: {e}")
    return {"success": True, "tempo_execucao_minutos": tempo}


@router.get("/ordens-servico/{os_id}/historico")
async def get_os_historico(os_id: str, user: Dict = Depends(get_current_user)):
    """Get transition history for a specific OS"""
    logs = await db.audit_logs.find(
        {"entity_type": "ordens_servico", "entity_id": os_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return logs



# ============== MATERIAIS UTILIZADOS NA OS ==============

@router.get("/ordens-servico/{os_id}/materiais")
async def list_os_materiais(os_id: str, user: Dict = Depends(get_current_user)):
    """List materials consumed in a work order"""
    materiais = await db.os_materiais.find(
        {"os_id": os_id, "deleted_at": None}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return materiais


@router.post("/ordens-servico/{os_id}/materiais")
async def add_os_material(os_id: str, body: dict, user: Dict = Depends(get_current_user)):
    """Add consumed material to OS — deducts from stock automatically"""
    check_write_permission(user, ['admin', 'pcm', 'supervisor'] + ROLE_GROUPS['execucao'])
    
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")
    
    item_estoque_id = body.get('item_estoque_id')
    quantidade = body.get('quantidade', 0)
    
    if not item_estoque_id:
        raise HTTPException(status_code=400, detail="Item de estoque é obrigatório")
    if quantidade <= 0:
        raise HTTPException(status_code=400, detail="Quantidade deve ser maior que zero")
    
    # Get stock item
    item = await db.itens_estoque.find_one({"id": item_estoque_id, "deleted_at": None}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item de estoque não encontrado")
    verify_org_access(user, item, "Item de estoque")
    
    # Block negative stock
    current_qty = item.get('quantidade', 0)
    if quantidade > current_qty:
        raise HTTPException(status_code=400, detail=f"Estoque insuficiente. Disponível: {current_qty} {item.get('unidade','UN')}")
    
    # Get ativo info
    ativo = await db.ativos.find_one({"id": os_doc.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
    
    # Deduct from stock
    new_qty = current_qty - quantidade
    cost = item.get('custo_unitario', 0)
    await db.itens_estoque.update_one(
        {"id": item_estoque_id},
        {"$set": {"quantidade": new_qty, "valor_total": new_qty * cost, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Record material in OS
    mat_id = str(uuid.uuid4())
    mat_doc = {
        "id": mat_id,
        "os_id": os_id,
        "os_numero": os_doc.get('numero'),
        "item_estoque_id": item_estoque_id,
        "codigo": item.get('sku', ''),
        "descricao": item.get('nome', ''),
        "quantidade": quantidade,
        "unidade": item.get('unidade', 'UN'),
        "local_estoque": ' '.join(filter(None, [item.get('almoxarifado'), item.get('prateleira'), item.get('posicao')])),
        "custo_unitario": cost,
        "custo_total": quantidade * cost,
        "image_url": (item.get('images') or [None])[0],
        "ativo_id": os_doc.get('ativo_id'),
        "ativo_tag": ativo.get('tag', '') if ativo else '',
        "usuario_id": user.get('id'),
        "usuario_nome": user.get('nome', user.get('email', '')),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.os_materiais.insert_one(mat_doc)
    
    # Record stock movement
    mov_doc = {
        "id": str(uuid.uuid4()),
        "item_id": item_estoque_id,
        "item_codigo": item.get('sku', ''),
        "item_descricao": item.get('nome', ''),
        "tipo": "saida",
        "quantidade": -quantidade,
        "custo_unitario": cost,
        "motivo": f"Consumo em OS #{os_doc.get('numero','')}",
        "os_id": os_id,
        "os_numero": os_doc.get('numero'),
        "ativo_id": os_doc.get('ativo_id'),
        "ativo_tag": ativo.get('tag', '') if ativo else '',
        "usuario_id": user.get('id'),
        "usuario_nome": user.get('nome', user.get('email', '')),
        "organization_id": item.get('organization_id', ''),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.movimentacoes_estoque.insert_one(mov_doc)
    
    await audit_log("material_consumo", "ordens_servico", os_id, user,
        f"Material: {item.get('sku','')} {item.get('nome','')} x{quantidade} na OS #{os_doc.get('numero','')}")
    
    mat_doc.pop('_id', None)
    return mat_doc


@router.delete("/ordens-servico/{os_id}/materiais/{material_id}")
async def remove_os_material(os_id: str, material_id: str, user: Dict = Depends(get_current_user)):
    """Remove/return material from OS — restores stock"""
    check_write_permission(user, ['admin', 'pcm', 'supervisor'])
    
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")
    
    mat = await db.os_materiais.find_one({"id": material_id, "os_id": os_id, "deleted_at": None}, {"_id": 0})
    if not mat:
        raise HTTPException(status_code=404, detail="Material não encontrado nesta OS")
    
    # Restore stock
    item = await db.itens_estoque.find_one({"id": mat['item_estoque_id']}, {"_id": 0})
    if item:
        new_qty = item.get('quantidade', 0) + mat['quantidade']
        cost = item.get('custo_unitario', 0)
        await db.itens_estoque.update_one(
            {"id": mat['item_estoque_id']},
            {"$set": {"quantidade": new_qty, "valor_total": new_qty * cost, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        # Record return movement
        mov_doc = {
            "id": str(uuid.uuid4()),
            "item_id": mat['item_estoque_id'],
            "item_codigo": mat.get('codigo', ''),
            "item_descricao": mat.get('descricao', ''),
            "tipo": "devolucao",
            "quantidade": mat['quantidade'],
            "custo_unitario": cost,
            "motivo": f"Devolução da OS #{mat.get('os_numero','')}",
            "os_id": os_id,
            "os_numero": mat.get('os_numero'),
            "ativo_id": mat.get('ativo_id'),
            "ativo_tag": mat.get('ativo_tag', ''),
            "usuario_id": user.get('id'),
            "usuario_nome": user.get('nome', user.get('email', '')),
            "organization_id": item.get('organization_id', ''),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.movimentacoes_estoque.insert_one(mov_doc)
    
    # Soft delete
    await db.os_materiais.update_one({"id": material_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    
    await audit_log("material_devolucao", "ordens_servico", os_id, user,
        f"Devolvido: {mat.get('codigo','')} {mat.get('descricao','')} x{mat['quantidade']} da OS #{mat.get('os_numero','')}")
    
    return {"success": True}


# ============== APROVAÇÃO (GERENTE) ==============

@router.post("/ordens-servico/{os_id}/aprovar")
async def aprovar_os(os_id: str, data: dict, user: Dict = Depends(get_current_user)):
    """Gerente/Admin aprova ou rejeita OS."""
    check_write_permission(user, ['admin', 'master', 'gerente'])
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")
    if os_doc.get('status') != 'aguardando_aprovacao':
        raise HTTPException(status_code=400, detail="OS não está aguardando aprovação")

    decisao = data.get("decisao", "")
    observacao = data.get("observacao", "")

    if decisao == "aprovada":
        new_status = "programada"
        aprov_status = "aprovada"
    elif decisao == "rejeitada":
        new_status = "cancelada"
        aprov_status = "rejeitada"
    elif decisao == "revisao":
        new_status = "em_analise"
        aprov_status = "revisao"
    else:
        raise HTTPException(status_code=400, detail="Decisão inválida: aprovada, rejeitada, revisao")

    aprovacao = {
        "necessaria": True,
        "status": aprov_status,
        "aprovador": user.get("id"),
        "aprovador_nome": user.get("nome", ""),
        "data": datetime.now(timezone.utc).isoformat(),
        "observacao": observacao,
    }

    await db.ordens_servico.update_one({"id": os_id}, {"$set": {
        "aprovacao": aprovacao,
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }})
    await audit_log("aprovacao", "ordens_servico", os_id, user,
        f"OS #{os_doc.get('numero','')} {aprov_status}: {observacao}")
    return await db.ordens_servico.find_one({"id": os_id}, {"_id": 0})


@router.post("/ordens-servico/{os_id}/enviar-aprovacao")
async def enviar_para_aprovacao(os_id: str, user: Dict = Depends(get_current_user)):
    """PCM/Supervisor envia OS para aprovação do gerente."""
    check_write_permission(user, ['admin', 'master', 'pcm', 'supervisor'])
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")

    await db.ordens_servico.update_one({"id": os_id}, {"$set": {
        "status": "aguardando_aprovacao",
        "aprovacao.status": "pendente",
        "aprovacao.necessaria": True,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }})
    await audit_log("enviar_aprovacao", "ordens_servico", os_id, user,
        f"OS #{os_doc.get('numero','')} enviada para aprovação")
    return await db.ordens_servico.find_one({"id": os_id}, {"_id": 0})


# ============== DOSSIÊ PERMANENTE ==============

@router.get("/dossie/os/{os_id}")
async def dossie_os(os_id: str, user: Dict = Depends(get_current_user)):
    """Dossiê completo de uma OS — somente leitura. Retorna todos os dados enriquecidos."""
    if user.get('role') not in ['master', 'admin', 'pcm', 'supervisor', 'gerente']:
        raise HTTPException(status_code=403, detail="Sem permissão para visualizar dossiê")
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")

    # Enrich ativo
    ativo = await db.ativos.find_one({"id": os_doc.get('ativo_id')}, {"_id": 0})
    sector = await db.sectors.find_one({"id": ativo.get('sector_id') if ativo else ''}, {"_id": 0, "nome": 1}) if ativo else None
    unidade = await db.unidades.find_one({"organization_id": os_doc.get('organization_id'), "deleted_at": None}, {"_id": 0, "nome": 1})
    os_doc['ativo'] = ativo
    os_doc['ativo_sector'] = sector.get('nome') if sector else ''
    os_doc['ativo_unidade'] = unidade.get('nome') if unidade else ''

    # Resolve user names
    async def name(uid):
        if not uid: return None
        u = await db.users.find_one({"id": uid}, {"_id": 0, "nome": 1, "role": 1})
        return u if u else None

    os_doc['solicitante'] = await name(os_doc.get('criado_por'))
    os_doc['responsavel'] = await name(os_doc.get('responsavel_id'))
    os_doc['iniciado_por_info'] = await name(os_doc.get('iniciado_por'))
    os_doc['concluido_por_info'] = await name(os_doc.get('concluido_por'))

    # Equipe/Executantes with HH
    executantes = []
    equipe_ids = os_doc.get('equipe') or []
    for uid in equipe_ids:
        u = await name(uid)
        hh_events = await db.hh_events.find({"os_id": os_id, "user_id": uid, "tipo": "pausa"}, {"_id": 0, "duracao_minutos": 1}).to_list(100)
        hh_total = sum(e.get('duracao_minutos', 0) for e in hh_events)
        executantes.append({"id": uid, "nome": u.get('nome') if u else uid, "role": u.get('role') if u else '', "hh_minutos": hh_total})
    os_doc['executantes'] = executantes

    # HH summary
    hh_all = await db.hh_events.find({"os_id": os_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    os_doc['hh_eventos'] = hh_all

    # Materiais consumidos
    materiais = await db.os_materiais.find({"os_id": os_id, "deleted_at": None}, {"_id": 0}).to_list(100)
    for m in materiais:
        item = await db.itens_estoque.find_one({"id": m.get('item_estoque_id')}, {"_id": 0, "nome": 1, "codigo": 1})
        m['item_nome'] = item.get('nome') if item else ''
        m['item_codigo'] = item.get('codigo') if item else ''
    os_doc['materiais'] = materiais

    # Fotos/Anexos
    attachments = await db.attachments.find({"entity_type": "ordens_servico", "entity_id": os_id}, {"_id": 0}).to_list(50)
    os_doc['fotos'] = attachments

    # Histórico/Auditoria
    hist = await db.audit_logs.find({"entity_id": os_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    os_doc['auditoria'] = hist

    # Aprovação
    os_doc['aprovacao'] = os_doc.get('aprovacao', {})
    if os_doc['aprovacao'].get('aprovador_id'):
        aprov = await name(os_doc['aprovacao']['aprovador_id'])
        os_doc['aprovacao']['aprovador_nome'] = aprov.get('nome') if aprov else ''

    return os_doc


@router.get("/dossie/inspecao/{insp_id}")
async def dossie_inspecao(insp_id: str, user: Dict = Depends(get_current_user)):
    """Dossiê completo de uma Inspeção — somente leitura."""
    if user.get('role') not in ['master', 'admin', 'pcm', 'supervisor', 'gerente']:
        raise HTTPException(status_code=403, detail="Sem permissão para visualizar dossiê")
    insp = await db.inspecoes.find_one({"id": insp_id, "deleted_at": None}, {"_id": 0})
    if not insp:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    verify_org_access(user, insp, "Inspeção")

    # Ativo
    ativo = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0})
    sector = await db.sectors.find_one({"id": ativo.get('sector_id') if ativo else ''}, {"_id": 0, "nome": 1}) if ativo else None
    unidade = await db.unidades.find_one({"organization_id": insp.get('organization_id'), "deleted_at": None}, {"_id": 0, "nome": 1})
    insp['ativo'] = ativo
    insp['ativo_sector'] = sector.get('nome') if sector else ''
    insp['ativo_unidade'] = unidade.get('nome') if unidade else ''

    # Plano utilizado
    if insp.get('plano_id'):
        plano = await db.planos_inspecao.find_one({"id": insp['plano_id']}, {"_id": 0, "nome": 1, "tipo": 1, "frequencia": 1})
        insp['plano'] = plano

    # User names
    async def name(uid):
        if not uid: return None
        u = await db.users.find_one({"id": uid}, {"_id": 0, "nome": 1, "role": 1})
        return u if u else None

    insp['executado_por_info'] = await name(insp.get('concluido_por') or insp.get('criado_por'))
    insp['criado_por_info'] = await name(insp.get('criado_por'))

    # Fotos/Anexos
    attachments = await db.attachments.find({"entity_type": "inspecoes", "entity_id": insp_id}, {"_id": 0}).to_list(50)
    insp['fotos'] = attachments

    # Não-conformidades
    checklist = insp.get('checklist', [])
    nao_conformes = [c for c in checklist if c.get('resposta') in ('nao_conforme', 'reprovado', 'nao')]
    insp['nao_conformidades'] = nao_conformes

    return insp


@router.get("/dossie/pesquisa")
async def dossie_pesquisa(
    q: Optional[str] = None,
    tipo: Optional[str] = None,
    tag: Optional[str] = None,
    area: Optional[str] = None,
    executante: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    """Pesquisa global em OS e Inspeções concluídas para o dossiê."""
    org_id = user.get('organization_id', '')
    results = []

    # Build asset filter by tag/area
    asset_ids = None
    if tag or area:
        ativo_q = {"organization_id": org_id, "deleted_at": None}
        if tag:
            ativo_q["tag"] = {"$regex": tag, "$options": "i"}
        if area:
            sectors = await db.sectors.find({"nome": {"$regex": area, "$options": "i"}}, {"_id": 0, "id": 1}).to_list(100)
            sector_ids = [s['id'] for s in sectors]
            if sector_ids:
                ativo_q["sector_id"] = {"$in": sector_ids}
        ativos = await db.ativos.find(ativo_q, {"_id": 0, "id": 1, "tag": 1, "nome": 1}).to_list(500)
        asset_ids = [a['id'] for a in ativos]
        if not asset_ids:
            return []

    # OS search
    if not tipo or tipo in ('os', 'corretiva', 'preventiva', 'melhoria'):
        os_q = {"organization_id": org_id, "deleted_at": None}
        if asset_ids is not None:
            os_q["ativo_id"] = {"$in": asset_ids}
        if q:
            os_q["$or"] = [
                {"numero": {"$regex": q, "$options": "i"}},
                {"titulo": {"$regex": q, "$options": "i"}},
            ]
        if tipo in ('corretiva', 'preventiva', 'melhoria'):
            os_q["tipo"] = tipo
        if data_inicio:
            os_q["created_at"] = {"$gte": data_inicio}
        if data_fim:
            os_q.setdefault("created_at", {})["$lte"] = data_fim
        if executante:
            users_match = await db.users.find({"nome": {"$regex": executante, "$options": "i"}, "organization_id": org_id}, {"_id": 0, "id": 1}).to_list(50)
            uids = [u['id'] for u in users_match]
            if uids:
                os_q["$or"] = os_q.get("$or", []) + [{"equipe": {"$in": uids}}, {"concluido_por": {"$in": uids}}]

        oss = await db.ordens_servico.find(os_q, {"_id": 0, "id": 1, "numero": 1, "titulo": 1, "tipo": 1, "status": 1, "ativo_id": 1, "data_conclusao": 1, "created_at": 1, "tempo_execucao_minutos": 1}).sort("created_at", -1).to_list(100)
        for o in oss:
            ativo = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1, "sector_id": 1})
            sec = await db.sectors.find_one({"id": ativo.get('sector_id') if ativo else ''}, {"_id": 0, "nome": 1}) if ativo else None
            results.append({
                "tipo_registro": "os", "id": o['id'], "numero": o.get('numero'), "titulo": o.get('titulo'),
                "tipo": o.get('tipo'), "status": o.get('status'), "data": o.get('data_conclusao') or o.get('created_at'),
                "tag": ativo.get('tag') if ativo else '', "equipamento": ativo.get('nome') if ativo else '',
                "area": sec.get('nome') if sec else '', "tempo_minutos": o.get('tempo_execucao_minutos')
            })

    # Inspeção search
    if not tipo or tipo == 'inspecao':
        insp_q = {"organization_id": org_id, "deleted_at": None}
        if asset_ids is not None:
            insp_q["ativo_id"] = {"$in": asset_ids}
        if q:
            insp_q["tipo"] = {"$regex": q, "$options": "i"}
        if data_inicio:
            insp_q["created_at"] = {"$gte": data_inicio}
        if data_fim:
            insp_q.setdefault("created_at", {})["$lte"] = data_fim

        insps = await db.inspecoes.find(insp_q, {"_id": 0, "id": 1, "tipo": 1, "status": 1, "resultado": 1, "ativo_id": 1, "data_conclusao": 1, "created_at": 1, "duracao_minutos": 1}).sort("created_at", -1).to_list(100)
        for i in insps:
            ativo = await db.ativos.find_one({"id": i.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1, "sector_id": 1})
            sec = await db.sectors.find_one({"id": ativo.get('sector_id') if ativo else ''}, {"_id": 0, "nome": 1}) if ativo else None
            results.append({
                "tipo_registro": "inspecao", "id": i['id'], "tipo": i.get('tipo'), "status": i.get('status'),
                "resultado": i.get('resultado'), "data": i.get('data_conclusao') or i.get('created_at'),
                "tag": ativo.get('tag') if ativo else '', "equipamento": ativo.get('nome') if ativo else '',
                "area": sec.get('nome') if sec else '', "tempo_minutos": i.get('duracao_minutos')
            })

    results.sort(key=lambda r: r.get('data', ''), reverse=True)
    return results
