"""
MAINTRIX PRO — Event & HH Routes
Endpoints for OS events, HH time tracking, team members, and metrics.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional, List
from datetime import datetime, timezone
import uuid
from deps import (
    db, get_current_user, check_write_permission, check_admin_only,
    verify_org_access, audit_log, is_admin, logger, ROLE_GROUPS
)
from data_architecture import (
    HHEvento, OSEventoTipo, FuncaoExecutante,
    HHRegistroCreate, OSExecutanteCreate,
    build_hh_registro, build_os_evento, build_os_executante, build_base_doc,
    rebuild_daily_metrics, rebuild_monthly_metrics,
)

router = APIRouter()


# ============== OS EVENTOS (Immutable Event Log) ==============

@router.get("/os/{os_id}/eventos")
async def list_os_eventos(os_id: str, user: Dict = Depends(get_current_user)):
    """List all events for an OS, ordered chronologically."""
    org_filter = {"organization_id": user.get("organization_id", "")} if user.get("organization_id") else {}
    eventos = await db.os_eventos.find(
        {"os_id": os_id, **org_filter},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(500)
    return eventos

@router.post("/os/{os_id}/eventos")
async def create_os_evento_manual(os_id: str, tipo: str, detalhes: dict = None, user: Dict = Depends(get_current_user)):
    """Record an OS event manually (admin/master only)."""
    check_admin_only(user)
    doc = build_os_evento(user, os_id, tipo, detalhes)
    doc["organization_id"] = user.get("organization_id", "")
    await db.os_eventos.insert_one(doc)
    doc.pop("_id", None)
    return doc


# ============== HH REGISTROS (Time Tracking) ==============

@router.get("/os/{os_id}/hh")
async def list_hh_registros(os_id: str, user: Dict = Depends(get_current_user)):
    """List all HH events for an OS."""
    org_filter = {"organization_id": user.get("organization_id", "")} if user.get("organization_id") else {}
    registros = await db.hh_registros.find(
        {"os_id": os_id, "deleted_at": None, **org_filter},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(500)
    return registros

@router.post("/os/{os_id}/hh")
async def create_hh_registro(os_id: str, data: HHRegistroCreate, user: Dict = Depends(get_current_user)):
    """Record an HH time event (INICIAR, PAUSAR, RETORNAR, FINALIZAR, TRANSFERIR)."""
    check_write_permission(user)
    
    # Get OS for context enrichment
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")
    
    # Enrich OS with area info
    ativo = await db.ativos.find_one({"id": os_doc.get("ativo_id")}, {"_id": 0, "sector_id": 1})
    if ativo:
        sector = await db.sectors.find_one({"id": ativo.get("sector_id")}, {"_id": 0, "planta_id": 1})
        os_doc["area_id"] = ativo.get("sector_id", "")
        os_doc["planta_id"] = sector.get("planta_id", "") if sector else ""
    
    # Validate event sequence
    last_event = await db.hh_registros.find_one(
        {"os_id": os_id, "user_id": user["id"], "deleted_at": None},
        {"_id": 0, "evento": 1},
        sort=[("timestamp", -1)]
    )
    last_ev = last_event.get("evento") if last_event else None
    
    valid_transitions = {
        None: ["iniciar"],
        "iniciar": ["pausar", "finalizar"],
        "pausar": ["retornar", "finalizar"],
        "retornar": ["pausar", "finalizar"],
        "finalizar": ["iniciar"],  # Allow restart
    }
    
    if data.evento not in valid_transitions.get(last_ev, []):
        raise HTTPException(
            status_code=400,
            detail=f"Transição inválida: {last_ev or 'nenhum'} → {data.evento}. Permitidos: {valid_transitions.get(last_ev, [])}"
        )
    
    doc = build_hh_registro(user, os_doc, data.evento, data.observacao)
    await db.hh_registros.insert_one(doc)
    doc.pop("_id", None)
    
    # Also record as OS event
    await db.os_eventos.insert_one(build_os_evento(
        user, os_id,
        {"iniciar": "trabalho_iniciado", "pausar": "pausa", "retornar": "retorno", "finalizar": "os_concluida"}.get(data.evento, data.evento),
        {"hh_evento": data.evento, "observacao": data.observacao}
    ))
    
    # Trigger daily metrics rebuild
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        await rebuild_daily_metrics(db, user.get("organization_id", ""), user["id"], today)
    except Exception as e:
        logger.warning(f"Metrics rebuild failed: {e}")
    
    return doc

@router.get("/hh/resumo/{os_id}")
async def hh_resumo(os_id: str, user: Dict = Depends(get_current_user)):
    """Calculate HH summary for an OS (all team members)."""
    org_filter = {"organization_id": user.get("organization_id", "")} if user.get("organization_id") else {}
    registros = await db.hh_registros.find(
        {"os_id": os_id, "deleted_at": None, **org_filter},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    # Group by user
    by_user = {}
    for r in registros:
        uid = r.get("user_id", "")
        if uid not in by_user:
            by_user[uid] = {"user_id": uid, "user_nome": r.get("user_nome", ""), "eventos": []}
        by_user[uid]["eventos"].append(r)
    
    # Calculate per user
    resumos = []
    for uid, data in by_user.items():
        events = data["eventos"]
        hh_liquida = 0
        work_start = None
        for evt in events:
            ev = evt.get("evento", "")
            ts = evt.get("timestamp", "")
            if ev in ("iniciar", "retornar"):
                work_start = ts
            elif ev in ("pausar", "finalizar") and work_start:
                try:
                    t1 = datetime.fromisoformat(work_start)
                    t2 = datetime.fromisoformat(ts)
                    hh_liquida += max(0, (t2 - t1).total_seconds() / 60)
                except Exception:
                    pass
                work_start = None
        
        hh_bruta = 0
        if events:
            try:
                first = datetime.fromisoformat(events[0]["timestamp"])
                last = datetime.fromisoformat(events[-1]["timestamp"])
                hh_bruta = max(0, (last - first).total_seconds() / 60)
            except Exception:
                pass
        
        resumos.append({
            "user_id": uid,
            "user_nome": data["user_nome"],
            "hh_bruta_min": round(hh_bruta, 1),
            "hh_liquida_min": round(hh_liquida, 1),
            "tempo_parado_min": round(max(0, hh_bruta - hh_liquida), 1),
            "total_eventos": len(events),
            "ultimo_evento": events[-1].get("evento") if events else None,
        })
    
    return {
        "os_id": os_id,
        "executantes": resumos,
        "hh_total_liquida_min": round(sum(r["hh_liquida_min"] for r in resumos), 1),
    }


@router.post("/os/{os_id}/hh-manual")
async def create_hh_manual(os_id: str, data: dict, user: Dict = Depends(get_current_user)):
    """Record manual HH entry (executante, inicio, fim, horas)."""
    check_write_permission(user, ['admin', 'master', 'pcm', 'supervisor', 'operador'] + ROLE_GROUPS['execucao'])
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")

    executante_id = data.get("executante_id") or user["id"]
    horas = data.get("horas", 0)
    data_inicio = data.get("data_inicio", "")
    data_fim = data.get("data_fim", "")
    descricao = data.get("descricao", "")

    # Calculate minutes: prefer explicit horas, fallback to date diff
    minutos = 0
    if horas and float(horas) > 0:
        minutos = float(horas) * 60
    elif data_inicio and data_fim:
        try:
            dt_ini = datetime.fromisoformat(data_inicio.replace('Z', '+00:00'))
            dt_fim = datetime.fromisoformat(data_fim.replace('Z', '+00:00'))
            minutos = (dt_fim - dt_ini).total_seconds() / 60
        except Exception:
            pass

    if minutos <= 0:
        raise HTTPException(status_code=400, detail="Informe as horas ou datas de início/fim")

    # Compute realistic timestamps when only horas is provided
    now_dt = datetime.now(timezone.utc)
    if not data_inicio or not data_fim:
        from datetime import timedelta
        data_fim = data_fim or now_dt.isoformat()
        data_inicio = data_inicio or (now_dt - timedelta(minutes=minutos)).isoformat()

    exec_user = await db.users.find_one({"id": executante_id}, {"_id": 0, "nome": 1})
    org_id = os_doc.get("organization_id", user.get("organization_id", ""))

    doc_inicio = {
        "id": str(uuid.uuid4()), "os_id": os_id, "organization_id": org_id,
        "user_id": executante_id, "user_nome": exec_user.get("nome", "") if exec_user else "",
        "evento": "iniciar", "observacao": descricao,
        "timestamp": data_inicio,
        "created_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None,
        "manual": True,
    }
    doc_fim = {
        "id": str(uuid.uuid4()), "os_id": os_id, "organization_id": org_id,
        "user_id": executante_id, "user_nome": exec_user.get("nome", "") if exec_user else "",
        "evento": "finalizar", "observacao": descricao,
        "timestamp": data_fim,
        "created_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None,
        "manual": True,
    }
    await db.hh_registros.insert_many([doc_inicio, doc_fim])

    await audit_log("hh_manual", "ordens_servico", os_id, user,
        f"HH manual: {exec_user.get('nome','?') if exec_user else '?'} — {round(minutos/60,1)}h ({descricao})")

    return {"success": True, "minutos": round(minutos, 1)}


# ============== OS EXECUTANTES (Team Members) ==============

@router.get("/os/{os_id}/executantes")
async def list_os_executantes(os_id: str, user: Dict = Depends(get_current_user)):
    """List team members for an OS."""
    org_filter = {"organization_id": user.get("organization_id", "")} if user.get("organization_id") else {}
    executantes = await db.os_executantes.find(
        {"os_id": os_id, "deleted_at": None, **org_filter},
        {"_id": 0}
    ).to_list(50)
    return executantes

@router.post("/os/{os_id}/executantes")
async def add_os_executante(os_id: str, data: OSExecutanteCreate, user: Dict = Depends(get_current_user)):
    """Add a team member to an OS."""
    check_write_permission(user, ["pcm", "supervisor"])
    
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")
    
    # Check if already active
    existing = await db.os_executantes.find_one({"os_id": os_id, "user_id": data.user_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já é executante desta OS")
    
    # Get target user info
    target_user = await db.users.find_one({"id": data.user_id}, {"_id": 0, "nome": 1})
    user_nome = target_user.get("nome", "") if target_user else ""
    
    # Check if soft-deleted — reactivate instead of insert
    soft_deleted = await db.os_executantes.find_one({"os_id": os_id, "user_id": data.user_id, "deleted_at": {"$ne": None}})
    if soft_deleted:
        now = datetime.now(timezone.utc).isoformat()
        await db.os_executantes.update_one(
            {"os_id": os_id, "user_id": data.user_id},
            {"$set": {"deleted_at": None, "funcao": data.funcao, "status": "ativo", "updated_at": now, "updated_by": user["id"]}}
        )
        soft_deleted.pop("_id", None)
        soft_deleted["deleted_at"] = None
        soft_deleted["funcao"] = data.funcao
        soft_deleted["status"] = "ativo"
        
        await db.ordens_servico.update_one({"id": os_id}, {"$addToSet": {"equipe": data.user_id}})
        await db.os_eventos.insert_one(build_os_evento(
            user, os_id, "equipe_alterada",
            {"acao": "reativado", "user_id": data.user_id, "user_nome": user_nome, "funcao": data.funcao}
        ))
        return soft_deleted
    
    doc = build_os_executante(user, os_id, data.user_id, user_nome, data.funcao)
    doc["organization_id"] = user.get("organization_id", "")
    await db.os_executantes.insert_one(doc)
    doc.pop("_id", None)
    
    # Also update equipe array on OS for backward compatibility
    await db.ordens_servico.update_one(
        {"id": os_id},
        {"$addToSet": {"equipe": data.user_id}}
    )
    
    # Record event
    await db.os_eventos.insert_one(build_os_evento(
        user, os_id, "equipe_alterada",
        {"acao": "adicionado", "user_id": data.user_id, "user_nome": user_nome, "funcao": data.funcao}
    ))
    
    return doc

@router.delete("/os/{os_id}/executantes/{user_id}")
async def remove_os_executante(os_id: str, user_id: str, user: Dict = Depends(get_current_user)):
    """Remove a team member from an OS."""
    check_write_permission(user, ["pcm", "supervisor"])
    
    result = await db.os_executantes.update_one(
        {"os_id": os_id, "user_id": user_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat(), "updated_by": user["id"]}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Executante não encontrado")
    
    # Update equipe array
    await db.ordens_servico.update_one(
        {"id": os_id},
        {"$pull": {"equipe": user_id}}
    )
    
    return {"success": True}


# ============== METRICS ==============

@router.get("/metricas/usuario/{user_id}")
async def get_user_metrics(
    user_id: str,
    periodo: str = "mes",
    user: Dict = Depends(get_current_user)
):
    """Get pre-aggregated metrics for a user. periodo: hoje, semana, mes, ano"""
    org_id = user.get("organization_id", "")
    now = datetime.now(timezone.utc)
    
    if periodo == "hoje":
        today = now.strftime("%Y-%m-%d")
        metric = await db.metricas_diarias.find_one(
            {"organization_id": org_id, "user_id": user_id, "data": today},
            {"_id": 0}
        )
        return metric or {"os_total": 0, "hh_liquida_min": 0, "inspecoes": 0}
    
    elif periodo == "semana":
        from datetime import timedelta
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        dailies = await db.metricas_diarias.find(
            {"organization_id": org_id, "user_id": user_id, "data": {"$gte": week_start}},
            {"_id": 0}
        ).to_list(7)
        return _aggregate_dailies(dailies)
    
    elif periodo == "mes":
        metric = await db.metricas_mensais.find_one(
            {"organization_id": org_id, "user_id": user_id, "ano": now.year, "mes": now.month},
            {"_id": 0}
        )
        return metric or {"os_total": 0, "hh_liquida_min": 0, "inspecoes": 0}
    
    elif periodo == "ano":
        mensais = await db.metricas_mensais.find(
            {"organization_id": org_id, "user_id": user_id, "ano": now.year},
            {"_id": 0}
        ).to_list(12)
        return _aggregate_monthlies(mensais)
    
    return {"error": "Período inválido"}

@router.get("/metricas/equipe")
async def get_team_metrics(
    periodo: str = "mes",
    user: Dict = Depends(get_current_user)
):
    """Get metrics for all team members (for ranking/dashboard)."""
    org_id = user.get("organization_id", "")
    now = datetime.now(timezone.utc)
    
    if periodo == "mes":
        mensais = await db.metricas_mensais.find(
            {"organization_id": org_id, "ano": now.year, "mes": now.month},
            {"_id": 0}
        ).to_list(200)
        
        # Enrich with user names
        user_ids = list(set(m.get("user_id") for m in mensais))
        users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "nome": 1, "role": 1}).to_list(200)
        user_map = {u["id"]: u for u in users}
        
        for m in mensais:
            u = user_map.get(m.get("user_id"), {})
            m["user_nome"] = u.get("nome", "")
            m["user_role"] = u.get("role", "")
        
        # Sort by os_total descending (ranking)
        mensais.sort(key=lambda x: x.get("os_total", 0), reverse=True)
        return mensais
    
    elif periodo == "semana":
        from datetime import timedelta
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        dailies = await db.metricas_diarias.find(
            {"organization_id": org_id, "data": {"$gte": week_start}},
            {"_id": 0}
        ).to_list(5000)
        
        # Group by user
        by_user = {}
        for d in dailies:
            uid = d.get("user_id", "")
            if uid not in by_user:
                by_user[uid] = []
            by_user[uid].append(d)
        
        result = []
        user_ids = list(by_user.keys())
        users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "nome": 1, "role": 1}).to_list(200)
        user_map = {u["id"]: u for u in users}
        
        for uid, days in by_user.items():
            agg = _aggregate_dailies(days)
            u = user_map.get(uid, {})
            agg["user_id"] = uid
            agg["user_nome"] = u.get("nome", "")
            agg["user_role"] = u.get("role", "")
            result.append(agg)
        
        result.sort(key=lambda x: x.get("os_total", 0), reverse=True)
        return result
    
    return []

@router.post("/metricas/rebuild")
async def trigger_metrics_rebuild(
    user_id: Optional[str] = None,
    data: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    """Admin/Master: Force rebuild of metrics."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    today = data or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc)
    
    if user_id:
        daily = await rebuild_daily_metrics(db, org_id, user_id, today)
        monthly = await rebuild_monthly_metrics(db, org_id, user_id, now.year, now.month)
        return {"daily": daily, "monthly": monthly}
    
    # Rebuild for all users in org
    users = await db.users.find(
        {"organization_id": org_id, "deleted_at": None},
        {"_id": 0, "id": 1}
    ).to_list(500)
    
    count = 0
    for u in users:
        await rebuild_daily_metrics(db, org_id, u["id"], today)
        await rebuild_monthly_metrics(db, org_id, u["id"], now.year, now.month)
        count += 1
    
    return {"rebuilt_users": count, "data": today}


# ============== HELPERS ==============

def _aggregate_dailies(dailies: list) -> dict:
    """Sum up daily metrics into a single aggregate."""
    totals = {
        "os_total": 0, "os_solo": 0, "os_compartilhada": 0,
        "hh_bruta_min": 0, "hh_liquida_min": 0, "tempo_parado_min": 0,
        "inspecoes": 0, "dias_trabalhados": len(dailies),
    }
    tipo_totals = {}
    for d in dailies:
        for k in ["os_total", "os_solo", "os_compartilhada", "hh_bruta_min", "hh_liquida_min", "tempo_parado_min", "inspecoes"]:
            totals[k] += d.get(k, 0)
        for tipo, count in d.get("os_por_tipo", {}).items():
            tipo_totals[tipo] = tipo_totals.get(tipo, 0) + count
    totals["os_por_tipo"] = tipo_totals
    totals["tempo_medio_os_min"] = round(totals["hh_liquida_min"] / totals["os_total"], 1) if totals["os_total"] > 0 else 0
    return totals

def _aggregate_monthlies(mensais: list) -> dict:
    """Sum up monthly metrics into a single aggregate."""
    totals = {
        "os_total": 0, "os_solo": 0, "os_compartilhada": 0,
        "hh_bruta_min": 0, "hh_liquida_min": 0, "tempo_parado_min": 0,
        "inspecoes": 0, "meses_trabalhados": len(mensais),
    }
    tipo_totals = {}
    for m in mensais:
        for k in ["os_total", "os_solo", "os_compartilhada", "hh_bruta_min", "hh_liquida_min", "tempo_parado_min", "inspecoes"]:
            totals[k] += m.get(k, 0)
        for tipo, count in m.get("os_por_tipo", {}).items():
            tipo_totals[tipo] = tipo_totals.get(tipo, 0) + count
    totals["os_por_tipo"] = tipo_totals
    totals["tempo_medio_os_min"] = round(totals["hh_liquida_min"] / totals["os_total"], 1) if totals["os_total"] > 0 else 0
    return totals
