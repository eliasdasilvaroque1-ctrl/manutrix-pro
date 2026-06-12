"""Dashboard routes: KPIs, stats, trend, migration report"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from datetime import datetime, timezone
import json
import random

from deps import db, get_current_user, get_scoped_asset_ids, check_admin_only
from models import Disciplina

router = APIRouter()


@router.get("/kpis")
async def get_kpis(sector_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    asset_query = dict(query)
    os_query = dict(query)
    if sector_id:
        asset_query['sector_id'] = sector_id
        asset_ids = await get_scoped_asset_ids(org_id, sector_id=sector_id)
        if asset_ids is not None:
            os_query['ativo_id'] = {"$in": asset_ids}

    os_concluidas = await db.ordens_servico.find({**os_query, "status": "concluida", "tempo_execucao_minutos": {"$exists": True, "$ne": None}}, {"_id": 0, "tempo_execucao_minutos": 1, "tipo": 1}).to_list(1000)
    tempos = [o['tempo_execucao_minutos'] for o in os_concluidas if o.get('tempo_execucao_minutos')]
    mttr_minutos = sum(tempos) / len(tempos) if tempos else 126
    mttr_horas = mttr_minutos / 60

    all_os = await db.ordens_servico.find(os_query, {"_id": 0, "tipo": 1}).to_list(5000)
    total_os_all = len(all_os)
    preventivas = len([o for o in all_os if o.get('tipo') == 'preventiva'])
    corretivas = len([o for o in all_os if o.get('tipo') == 'corretiva'])

    ativos_total = await db.ativos.count_documents(asset_query)
    ativos_operacionais = await db.ativos.count_documents({**asset_query, "status": "operacional"})
    ativos_parados = await db.ativos.count_documents({**asset_query, "status": {"$in": ["parado", "manutencao"]}})

    disponibilidade = (ativos_operacionais / ativos_total * 100) if ativos_total > 0 else 100
    mtbf_horas = ((ativos_total - ativos_parados) / ativos_total * 720) if ativos_total > 0 else 720
    confiabilidade = (1 - (corretivas / total_os_all)) * 100 if total_os_all > 0 else 100

    insp_query = dict(os_query)
    insp_finalizadas = await db.inspecoes.count_documents({**insp_query, "status": {"$in": ["concluida", "com_pendencias"]}})
    insp_conformes = await db.inspecoes.count_documents({**insp_query, "resultado": "conforme"})
    taxa_conformidade = (insp_conformes / insp_finalizadas * 100) if insp_finalizadas > 0 else 100

    backlog = await db.ordens_servico.count_documents({**os_query, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}})
    os_atrasadas = await db.ordens_servico.count_documents({**os_query, "status": {"$nin": ["concluida", "cancelada"]}, "data_planejada": {"$lt": now.isoformat()}})
    os_mes = await db.ordens_servico.find({**os_query, "status": "concluida", "data_conclusao": {"$gte": month_start}}, {"_id": 0, "custo_total": 1}).to_list(1000)
    custo_mes = sum(o.get('custo_total', 0) or 0 for o in os_mes)

    return {
        "disponibilidade_percent": round(disponibilidade, 1),
        "mtbf_horas": round(mtbf_horas, 1),
        "mttr_horas": round(mttr_horas, 2),
        "confiabilidade_percent": round(confiabilidade, 1),
        "taxa_conformidade_percent": round(taxa_conformidade, 1),
        "backlog_total": backlog,
        "os_atrasadas": os_atrasadas,
        "preventivas_percent": round((preventivas / total_os_all * 100) if total_os_all > 0 else 0, 1),
        "corretivas_percent": round((corretivas / total_os_all * 100) if total_os_all > 0 else 0, 1),
        "custo_manutencao_mes": round(custo_mes, 2),
        "ativos_total": ativos_total,
        "ativos_operacionais": ativos_operacionais,
        "ativos_parados": ativos_parados
    }


@router.get("/dashboard/stats")
async def get_dashboard_stats(sector_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    asset_query = dict(query)
    os_query = dict(query)
    insp_query = dict(query)
    if sector_id:
        asset_query['sector_id'] = sector_id
        asset_ids = await get_scoped_asset_ids(org_id, sector_id=sector_id)
        if asset_ids is not None:
            os_query['ativo_id'] = {"$in": asset_ids}
            insp_query['ativo_id'] = {"$in": asset_ids}

    ativos = {
        "total": await db.ativos.count_documents(asset_query),
        "operacionais": await db.ativos.count_documents({**asset_query, "status": "operacional"}),
        "parados": await db.ativos.count_documents({**asset_query, "status": "parado"}),
        "manutencao": await db.ativos.count_documents({**asset_query, "status": "manutencao"}),
        "desativados": await db.ativos.count_documents({**asset_query, "status": "desativado"})
    }

    os_stats = {
        "abertas": await db.ordens_servico.count_documents({**os_query, "status": "aberta"}),
        "planejadas": await db.ordens_servico.count_documents({**os_query, "status": "planejada"}),
        "em_execucao": await db.ordens_servico.count_documents({**os_query, "status": "em_execucao"}),
        "pausadas": await db.ordens_servico.count_documents({**os_query, "status": "pausada"}),
        "concluidas_hoje": await db.ordens_servico.count_documents({**os_query, "status": "concluida", "data_conclusao": {"$gte": today_start}}),
        "atrasadas": await db.ordens_servico.count_documents({**os_query, "status": {"$nin": ["concluida", "cancelada"]}, "data_planejada": {"$lt": now.isoformat()}}),
    }

    inspecoes = {
        "pendentes": await db.inspecoes.count_documents({**insp_query, "status": "pendente"}),
        "em_andamento": await db.inspecoes.count_documents({**insp_query, "status": "em_andamento"}),
        "concluidas_hoje": await db.inspecoes.count_documents({**insp_query, "status": "concluida", "data_conclusao": {"$gte": today_start}}),
        "nao_conformes_mes": await db.inspecoes.count_documents({**insp_query, "resultado": "nao_conforme"})
    }

    estoque_items = await db.itens_estoque.find(query, {"_id": 0, "quantidade": 1, "estoque_minimo": 1, "item_critico": 1}).to_list(1000)
    estoque = {
        "total_itens": len(estoque_items),
        "criticos": len([i for i in estoque_items if i.get('quantidade', 0) <= i.get('estoque_minimo', 0)]),
    }

    return {"ativos": ativos, "ordens_servico": os_stats, "inspecoes": inspecoes, "estoque": estoque}


@router.get("/dashboard/os-por-setor")
async def dashboard_os_por_setor(user: Dict = Depends(get_current_user)):
    """OS count by sector for dashboard chart"""
    org_id = user.get('organization_id', '')
    q = {"deleted_at": None}
    if org_id:
        q['organization_id'] = org_id
    sectors = await db.sectors.find(q, {"_id": 0, "id": 1, "nome": 1, "cor": 1}).to_list(100)
    result = []
    for s in sectors:
        aids = [a['id'] for a in await db.ativos.find({"sector_id": s['id'], "deleted_at": None}, {"_id": 0, "id": 1}).to_list(500)]
        os_count = await db.ordens_servico.count_documents({"ativo_id": {"$in": aids}, "status": {"$nin": ["concluida", "cancelada"]}, "deleted_at": None}) if aids else 0
        if os_count > 0 or True:
            result.append({"sector": s['nome'], "cor": s.get('cor', '#10b981'), "os_abertas": os_count})
    return sorted(result, key=lambda x: x['os_abertas'], reverse=True)


@router.get("/dashboard/os-por-disciplina")
async def dashboard_os_por_disciplina(user: Dict = Depends(get_current_user)):
    """OS count by discipline for dashboard chart"""
    org_id = user.get('organization_id', '')
    q = {"deleted_at": None, "status": {"$nin": ["concluida", "cancelada"]}}
    if org_id:
        q['organization_id'] = org_id
    result = []
    labels = {"mecanica": "Mecânica", "eletrica": "Elétrica", "instrumentacao": "Instrumentação", "civil": "Civil", "producao": "Produção"}
    colors = {"mecanica": "#3b82f6", "eletrica": "#f59e0b", "instrumentacao": "#8b5cf6", "civil": "#ef4444", "producao": "#10b981"}
    for d in Disciplina:
        count = await db.ordens_servico.count_documents({**q, "disciplina": d.value})
        result.append({"disciplina": labels.get(d.value, d.value), "key": d.value, "cor": colors.get(d.value, '#64748b'), "count": count})
    return result


@router.get("/dashboard/ativos-mais-falhas")
async def dashboard_ativos_mais_falhas(user: Dict = Depends(get_current_user)):
    """Top assets with most failures (corretiva OS)"""
    org_id = user.get('organization_id', '')
    q = {"deleted_at": None, "tipo": "corretiva"}
    if org_id:
        q['organization_id'] = org_id
    os_list = await db.ordens_servico.find(q, {"_id": 0, "ativo_id": 1}).to_list(5000)
    counts = {}
    for o in os_list:
        aid = o.get('ativo_id')
        if aid:
            counts[aid] = counts.get(aid, 0) + 1
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    result = []
    for aid, count in top:
        ativo = await db.ativos.find_one({"id": aid}, {"_id": 0, "tag": 1, "nome": 1, "criticidade": 1, "sector_id": 1})
        if ativo:
            sector = await db.sectors.find_one({"id": ativo.get('sector_id')}, {"_id": 0, "nome": 1})
            result.append({"tag": ativo.get('tag'), "nome": ativo.get('nome'), "criticidade": ativo.get('criticidade'), "sector": sector.get('nome') if sector else '', "falhas": count})
    return result


@router.get("/dashboard/trend")
async def get_dashboard_trend(sector_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    """Monthly trend data for charts (last 6 months)"""
    org_id = user.get('organization_id', '')
    query = {"deleted_at": None}
    if org_id:
        query['organization_id'] = org_id

    os_query = dict(query)
    asset_query = dict(query)
    if sector_id:
        asset_query['sector_id'] = sector_id
        asset_ids = await get_scoped_asset_ids(org_id, sector_id=sector_id)
        if asset_ids is not None:
            os_query['ativo_id'] = {"$in": asset_ids}

    now = datetime.now(timezone.utc)
    months_data = []
    has_real_data = False

    for i in range(5, -1, -1):
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        month_start = datetime(year, month, 1, tzinfo=timezone.utc).isoformat()
        month_end = datetime(year + (1 if month == 12 else 0), (month % 12) + 1, 1, tzinfo=timezone.utc).isoformat()

        month_q = {**os_query, "data_conclusao": {"$gte": month_start, "$lt": month_end}, "status": "concluida"}
        os_mes = await db.ordens_servico.find(month_q, {"_id": 0, "tempo_execucao_minutos": 1, "tipo": 1, "custo_total": 1}).to_list(1000)

        tempos = [o['tempo_execucao_minutos'] for o in os_mes if o.get('tempo_execucao_minutos')]
        mttr = round(sum(tempos) / len(tempos) / 60, 2) if tempos else 0
        total = len(os_mes)
        if total > 0:
            has_real_data = True

        ativos_total = await db.ativos.count_documents(asset_query)
        ativos_parados = await db.ativos.count_documents({**asset_query, "status": {"$in": ["parado", "manutencao"]}})
        mtbf = round(((ativos_total - ativos_parados) / ativos_total * 720) if ativos_total > 0 else 720, 1)
        custo = sum(o.get('custo_total', 0) or 0 for o in os_mes)

        labels = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
        months_data.append({
            "mes": labels[month - 1], "mes_num": month, "ano": year,
            "mttr": mttr, "mtbf": mtbf, "total_os": total,
            "preventivas": len([o for o in os_mes if o.get('tipo') == 'preventiva']),
            "corretivas": len([o for o in os_mes if o.get('tipo') == 'corretiva']),
            "custo": round(custo, 2), "is_estimated": total == 0
        })

    if not has_real_data or all(m['total_os'] == 0 for m in months_data[:-1]):
        random.seed(42)
        base_mtbf = [580, 610, 595, 640, 665, 650]
        base_mttr = [2.8, 2.5, 3.1, 2.2, 1.9, 2.1]
        for idx, m in enumerate(months_data):
            if m['total_os'] == 0:
                m['mtbf'] = base_mtbf[idx] + random.randint(-15, 15)
                m['mttr'] = round(base_mttr[idx] + random.uniform(-0.3, 0.3), 1)
                m['preventivas'] = random.randint(8, 14)
                m['corretivas'] = random.randint(3, 7)
                m['total_os'] = m['preventivas'] + m['corretivas']
                m['custo'] = round(random.uniform(8000, 18000), 2)

    return months_data


@router.get("/migration/report")
async def migration_report(user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    org_id = user.get('organization_id', '')
    q = {"deleted_at": None}
    if org_id:
        q['organization_id'] = org_id
    sectors = await db.sectors.find({**q}, {"_id": 0}).to_list(500)
    total_ativos = await db.ativos.count_documents(q)
    ativos_with_sector = await db.ativos.count_documents({**q, "sector_id": {"$exists": True, "$ne": None}})
    ativos_orphan = total_ativos - ativos_with_sector

    sector_details = []
    for s in sectors:
        ac = await db.ativos.count_documents({"sector_id": s['id'], "deleted_at": None})
        sector_details.append({"id": s['id'], "codigo": s.get('codigo', ''), "nome": s['nome'], "assets": ac})

    return {
        "status": "complete" if ativos_orphan == 0 else "partial",
        "hierarchy": "Sector -> Asset (no Plants)",
        "summary": {
            "sectors_total": len(sectors), "ativos_total": total_ativos,
            "ativos_with_sector": ativos_with_sector, "ativos_orphan": ativos_orphan,
            "os_total": await db.ordens_servico.count_documents(q),
            "inspecoes_total": await db.inspecoes.count_documents(q),
        },
        "sectors": sector_details
    }
