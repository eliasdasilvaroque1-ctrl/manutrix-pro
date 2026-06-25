"""
MANUTRIX PRO — Data Architecture Module
Event-sourced collections, indexes, and aggregation infrastructure.

Collections:
  - os_eventos: Immutable event log for every OS state change
  - hh_registros: Labor time tracking per OS per user  
  - os_executantes: Team members per OS with individual roles/HH
  - metricas_diarias: Pre-aggregated daily metrics per user
  - metricas_mensais: Pre-aggregated monthly metrics per user

Design principles:
  - Every query starts with organization_id (multi-tenant)
  - Event-sourcing: never lose history, reconstruct any state
  - Pre-aggregated metrics for dashboard speed at scale
  - Prepared for 500 companies, millions of OS, tens of millions of HH records
"""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid


# ============== ENUMS ==============

class HHEvento(str, Enum):
    INICIAR = "iniciar"
    PAUSAR = "pausar"
    RETORNAR = "retornar"
    FINALIZAR = "finalizar"
    TRANSFERIR = "transferir"

class OSEventoTipo(str, Enum):
    CRIADA = "os_criada"
    PLANEJADA = "os_planejada"
    TECNICO_ATRIBUIDO = "tecnico_atribuido"
    TRABALHO_INICIADO = "trabalho_iniciado"
    PAUSA = "pausa"
    RETORNO = "retorno"
    MATERIAL_UTILIZADO = "material_utilizado"
    FOTO_ANEXADA = "foto_anexada"
    CONCLUIDA = "os_concluida"
    REABERTA = "os_reaberta"
    CANCELADA = "os_cancelada"
    CAMPO_ALTERADO = "campo_alterado"
    EQUIPE_ALTERADA = "equipe_alterada"
    TRANSFERIDA = "os_transferida"

class FuncaoExecutante(str, Enum):
    EXECUTOR = "executor"
    APOIO = "apoio"
    SUPERVISOR = "supervisor_exec"
    INSPETOR = "inspetor_exec"
    LIDER = "lider"


# ============== MODELS ==============

class HHRegistroCreate(BaseModel):
    os_id: str
    evento: HHEvento
    observacao: Optional[str] = None

class OSExecutanteCreate(BaseModel):
    os_id: str
    user_id: str
    funcao: FuncaoExecutante = FuncaoExecutante.EXECUTOR


# ============== DOCUMENT BUILDERS ==============

def build_base_doc(user: dict) -> dict:
    """Standard fields for all new documents."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(uuid.uuid4()),
        "organization_id": user.get("organization_id", ""),
        "created_at": now,
        "updated_at": now,
        "created_by": user.get("id", ""),
        "updated_by": user.get("id", ""),
        "deleted_at": None,
    }

def build_hh_registro(user: dict, os_doc: dict, evento: str, observacao: str = None) -> dict:
    """Build an HH time-tracking event document."""
    base = build_base_doc(user)
    base.update({
        "os_id": os_doc.get("id", ""),
        "planta_id": os_doc.get("planta_id", ""),
        "area_id": os_doc.get("area_id", ""),
        "ativo_id": os_doc.get("ativo_id", ""),
        "user_id": user.get("id", ""),
        "user_nome": user.get("nome", ""),
        "supervisor_id": os_doc.get("responsavel_id", ""),
        "tipo_os": os_doc.get("tipo", ""),
        "disciplina": os_doc.get("disciplina", ""),
        "evento": evento,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": None,
        "longitude": None,
        "dispositivo": None,
        "observacao": observacao,
    })
    return base

def build_os_evento(user: dict, os_id: str, tipo: str, detalhes: dict = None) -> dict:
    """Build an immutable OS event document."""
    base = build_base_doc(user)
    base.update({
        "os_id": os_id,
        "tipo": tipo,
        "user_id": user.get("id", ""),
        "user_nome": user.get("nome", ""),
        "user_role": user.get("role", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detalhes": detalhes or {},
    })
    return base

def build_os_executante(user: dict, os_id: str, user_id: str, user_nome: str, funcao: str) -> dict:
    """Build an OS team member document."""
    base = build_base_doc(user)
    base.update({
        "os_id": os_id,
        "user_id": user_id,
        "user_nome": user_nome,
        "funcao": funcao,
        "hh_minutos": 0,
        "status": "ativo",
    })
    return base


# ============== INDEX DEFINITIONS ==============

INDEXES = {
    "ordens_servico": [
        {"keys": [("organization_id", 1), ("status", 1)], "name": "org_status"},
        {"keys": [("organization_id", 1), ("tipo", 1), ("status", 1)], "name": "org_tipo_status"},
        {"keys": [("organization_id", 1), ("data_conclusao", -1)], "name": "org_data_conclusao"},
        {"keys": [("organization_id", 1), ("created_at", -1)], "name": "org_created"},
        {"keys": [("ativo_id", 1), ("status", 1)], "name": "ativo_status"},
        {"keys": [("responsavel_id", 1), ("status", 1)], "name": "responsavel_status"},
        {"keys": [("equipe", 1)], "name": "equipe"},
        {"keys": [("organization_id", 1), ("responsavel_id", 1), ("data_conclusao", -1)], "name": "org_resp_conclusao"},
    ],
    "inspecoes": [
        {"keys": [("organization_id", 1), ("status", 1)], "name": "org_status"},
        {"keys": [("organization_id", 1), ("created_at", -1)], "name": "org_created"},
        {"keys": [("ativo_id", 1), ("status", 1)], "name": "ativo_status"},
    ],
    "anomalias": [
        {"keys": [("organization_id", 1), ("status", 1)], "name": "org_status"},
        {"keys": [("ativo_id", 1)], "name": "ativo"},
        {"keys": [("organization_id", 1), ("created_at", -1)], "name": "org_created"},
    ],
    "hh_registros": [
        {"keys": [("os_id", 1), ("user_id", 1), ("timestamp", 1)], "name": "os_user_time"},
        {"keys": [("organization_id", 1), ("user_id", 1), ("timestamp", -1)], "name": "org_user_time"},
        {"keys": [("organization_id", 1), ("timestamp", -1)], "name": "org_time"},
        {"keys": [("organization_id", 1), ("ativo_id", 1), ("timestamp", -1)], "name": "org_ativo_time"},
    ],
    "os_eventos": [
        {"keys": [("os_id", 1), ("timestamp", 1)], "name": "os_time"},
        {"keys": [("organization_id", 1), ("tipo", 1), ("timestamp", -1)], "name": "org_tipo_time"},
        {"keys": [("organization_id", 1), ("user_id", 1), ("timestamp", -1)], "name": "org_user_time"},
    ],
    "os_executantes": [
        {"keys": [("os_id", 1), ("user_id", 1)], "name": "os_user", "unique": True},
        {"keys": [("organization_id", 1), ("user_id", 1)], "name": "org_user"},
        {"keys": [("user_id", 1), ("status", 1)], "name": "user_status"},
    ],
    "metricas_diarias": [
        {"keys": [("organization_id", 1), ("user_id", 1), ("data", 1)], "name": "org_user_data", "unique": True},
        {"keys": [("organization_id", 1), ("data", -1)], "name": "org_data"},
    ],
    "metricas_mensais": [
        {"keys": [("organization_id", 1), ("user_id", 1), ("ano", 1), ("mes", 1)], "name": "org_user_anomes", "unique": True},
        {"keys": [("organization_id", 1), ("ano", -1), ("mes", -1)], "name": "org_anomes"},
    ],
    "audit_logs": [
        {"keys": [("organization_id", 1), ("created_at", -1)], "name": "org_created"},
        {"keys": [("entity_type", 1), ("entity_id", 1)], "name": "entity"},
    ],
    "movimentacoes_estoque": [
        {"keys": [("organization_id", 1), ("created_at", -1)], "name": "org_created"},
        {"keys": [("item_id", 1)], "name": "item"},
        {"keys": [("os_id", 1)], "name": "os"},
    ],
    "plantas_v2": [
        {"keys": [("organization_id", 1)], "name": "org"},
    ],
    "paradas_programadas": [
        {"keys": [("organization_id", 1), ("data_inicio", -1)], "name": "org_data"},
    ],
    "admin_actions": [
        {"keys": [("organization_id", 1), ("created_at", -1)], "name": "org_created"},
    ],
}


async def create_all_indexes(db):
    """Create all indexes in background. Safe to call multiple times (idempotent)."""
    import logging
    logger = logging.getLogger(__name__)
    total = 0
    for collection_name, index_list in INDEXES.items():
        coll = db[collection_name]
        for idx in index_list:
            try:
                kwargs = {"name": idx["name"], "background": True}
                if idx.get("unique"):
                    kwargs["unique"] = True
                await coll.create_index(idx["keys"], **kwargs)
                total += 1
            except Exception as e:
                logger.warning(f"Index {idx['name']} on {collection_name}: {e}")
    logger.info(f"Indexes: {total} created/verified across {len(INDEXES)} collections")
    return total


# ============== METRICS AGGREGATION ==============

async def rebuild_daily_metrics(db, org_id: str, user_id: str, date_str: str):
    """Rebuild pre-aggregated daily metrics for one user on one day.
    Called after OS conclusion, HH event, or inspection completion."""
    from datetime import datetime
    day_start = f"{date_str}T00:00:00+00:00"
    day_end = f"{date_str}T23:59:59+00:00"
    base_match = {"organization_id": org_id, "deleted_at": None}
    
    # OS metrics for this user on this day
    os_match = {
        **base_match,
        "data_conclusao": {"$gte": day_start, "$lte": day_end},
        "$or": [
            {"responsavel_id": user_id},
            {"equipe": user_id},
            {"concluido_por": user_id},
            {"executado_por": user_id},
        ]
    }
    
    os_concluded = await db.ordens_servico.find(os_match, {"_id": 0, "tipo": 1, "tempo_execucao_minutos": 1, "equipe": 1, "responsavel_id": 1}).to_list(500)
    
    # Count by type
    tipo_counts = {}
    total_os = len(os_concluded)
    total_tempo = 0
    os_solo = 0
    os_compartilhada = 0
    
    for os_doc in os_concluded:
        tipo = os_doc.get("tipo", "corretiva")
        tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
        total_tempo += os_doc.get("tempo_execucao_minutos", 0) or 0
        equipe = os_doc.get("equipe", [])
        if len(equipe) > 1:
            os_compartilhada += 1
        else:
            os_solo += 1
    
    # HH from hh_registros
    hh_events = await db.hh_registros.find({
        "organization_id": org_id,
        "user_id": user_id,
        "timestamp": {"$gte": day_start, "$lte": day_end},
        "deleted_at": None,
    }, {"_id": 0, "evento": 1, "timestamp": 1}).sort("timestamp", 1).to_list(1000)
    
    hh_bruta_min = 0
    hh_liquida_min = 0
    work_start = None
    for evt in hh_events:
        ts = evt.get("timestamp", "")
        ev = evt.get("evento", "")
        if ev in ("iniciar", "retornar"):
            work_start = ts
        elif ev in ("pausar", "finalizar") and work_start:
            try:
                t1 = datetime.fromisoformat(work_start)
                t2 = datetime.fromisoformat(ts)
                delta = (t2 - t1).total_seconds() / 60
                hh_liquida_min += max(0, delta)
            except:
                pass
            work_start = None
    
    if hh_events:
        try:
            first_ts = datetime.fromisoformat(hh_events[0]["timestamp"])
            last_ts = datetime.fromisoformat(hh_events[-1]["timestamp"])
            hh_bruta_min = max(0, (last_ts - first_ts).total_seconds() / 60)
        except:
            pass
    
    # Inspections
    insp_match = {
        **base_match,
        "status": "concluida",
        "finished_at": {"$gte": day_start, "$lte": day_end},
        "$or": [{"tecnico_id": user_id}, {"executantes": user_id}],
    }
    insp_count = await db.inspecoes.count_documents(insp_match)
    
    # Build metric doc
    metric = {
        "organization_id": org_id,
        "user_id": user_id,
        "data": date_str,
        "os_total": total_os,
        "os_solo": os_solo,
        "os_compartilhada": os_compartilhada,
        "os_por_tipo": tipo_counts,
        "hh_bruta_min": round(hh_bruta_min, 1),
        "hh_liquida_min": round(hh_liquida_min, 1),
        "tempo_parado_min": round(max(0, hh_bruta_min - hh_liquida_min), 1),
        "tempo_medio_os_min": round(total_tempo / total_os, 1) if total_os > 0 else 0,
        "inspecoes": insp_count,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    await db.metricas_diarias.update_one(
        {"organization_id": org_id, "user_id": user_id, "data": date_str},
        {"$set": metric, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return metric


async def rebuild_monthly_metrics(db, org_id: str, user_id: str, ano: int, mes: int):
    """Aggregate daily metrics into monthly. Called after daily rebuild."""
    from datetime import datetime
    
    month_prefix = f"{ano}-{str(mes).zfill(2)}"
    dailies = await db.metricas_diarias.find({
        "organization_id": org_id,
        "user_id": user_id,
        "data": {"$regex": f"^{month_prefix}"},
    }, {"_id": 0}).to_list(31)
    
    if not dailies:
        return None
    
    tipo_totals = {}
    totals = {
        "os_total": 0, "os_solo": 0, "os_compartilhada": 0,
        "hh_bruta_min": 0, "hh_liquida_min": 0, "tempo_parado_min": 0,
        "inspecoes": 0, "dias_trabalhados": len(dailies),
    }
    
    for d in dailies:
        for k in ["os_total", "os_solo", "os_compartilhada", "hh_bruta_min", "hh_liquida_min", "tempo_parado_min", "inspecoes"]:
            totals[k] += d.get(k, 0)
        for tipo, count in d.get("os_por_tipo", {}).items():
            tipo_totals[tipo] = tipo_totals.get(tipo, 0) + count
    
    totals["os_por_tipo"] = tipo_totals
    totals["tempo_medio_os_min"] = round(totals["hh_liquida_min"] / totals["os_total"], 1) if totals["os_total"] > 0 else 0
    
    metric = {
        "organization_id": org_id,
        "user_id": user_id,
        "ano": ano,
        "mes": mes,
        **totals,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    await db.metricas_mensais.update_one(
        {"organization_id": org_id, "user_id": user_id, "ano": ano, "mes": mes},
        {"$set": metric, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return metric
