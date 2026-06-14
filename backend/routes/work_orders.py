"""Work Order routes: OS CRUD, Kanban, Statistics, History"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid

from deps import (
    db, get_current_user, check_admin_only, check_write_permission,
    audit_log, criar_notificacao, generate_os_numero, get_scoped_asset_ids
)
from models import (
    OSCreate, OSUpdate, OSStatus, OSTipo, Prioridade, Disciplina,
    NotificacaoTipo, KanbanMoveBody, ConcluirOSBody
)

router = APIRouter()


@router.get("/ordens-servico")
async def list_os(
    status: Optional[OSStatus] = None,
    tipo: Optional[OSTipo] = None,
    disciplina: Optional[Disciplina] = None,
    prioridade: Optional[Prioridade] = None,
    responsavel_id: Optional[str] = None,
    ativo_id: Optional[str] = None,
    sector_id: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if status:
        query['status'] = status.value
    if tipo:
        query['tipo'] = tipo.value
    if disciplina:
        query['disciplina'] = disciplina.value
    if prioridade:
        query['prioridade'] = prioridade.value
    if responsavel_id:
        query['responsavel_id'] = responsavel_id
    if ativo_id:
        query['ativo_id'] = ativo_id

    if sector_id:
        asset_ids = await get_scoped_asset_ids(user.get('organization_id', ''), sector_id=sector_id)
        if asset_ids is not None:
            query['ativo_id'] = {"$in": asset_ids}

    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)

    ativo_ids = list(set(o.get('ativo_id') for o in os_list if o.get('ativo_id')))
    resp_ids = list(set(o.get('responsavel_id') for o in os_list if o.get('responsavel_id')))
    ativos_batch = await db.ativos.find({"id": {"$in": ativo_ids}}, {"_id": 0, "id": 1, "tag": 1, "nome": 1, "sector_id": 1}).to_list(len(ativo_ids)) if ativo_ids else []
    resp_batch = await db.users.find({"id": {"$in": resp_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(len(resp_ids)) if resp_ids else []
    ativo_map = {a['id']: a for a in ativos_batch}
    resp_map = {r['id']: r for r in resp_batch}

    for os in os_list:
        os['ativo'] = ativo_map.get(os.get('ativo_id'))
        os['responsavel'] = resp_map.get(os.get('responsavel_id'))
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
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']

    status_counts = {}
    for s in OSStatus:
        status_counts[s.value] = await db.ordens_servico.count_documents({**query, "status": s.value})

    tipo_counts = {}
    for t in OSTipo:
        tipo_counts[t.value] = await db.ordens_servico.count_documents({**query, "tipo": t.value})

    disciplina_counts = {}
    for d in Disciplina:
        disciplina_counts[d.value] = await db.ordens_servico.count_documents({**query, "disciplina": d.value})

    now = datetime.now(timezone.utc).isoformat()
    atrasadas = await db.ordens_servico.count_documents({**query, "status": {"$nin": ["concluida", "cancelada"]}, "data_planejada": {"$lt": now}})
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0).isoformat()
    concluidas_mes = await db.ordens_servico.count_documents({**query, "status": "concluida", "data_conclusao": {"$gte": month_start}})

    return {
        "por_status": status_counts, "por_tipo": tipo_counts,
        "por_disciplina": disciplina_counts,
        "atrasadas": atrasadas, "concluidas_mes": concluidas_mes,
        "total_abertas": sum(status_counts.get(s, 0) for s in ['aberta', 'planejada', 'em_execucao', 'pausada'])
    }


@router.get("/ordens-servico/backlog")
async def get_backlog(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
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
    os['ativo'] = await db.ativos.find_one({"id": os.get('ativo_id')}, {"_id": 0})
    if os.get('ativo') and os['ativo'].get('sector_id'):
        os['ativo']['sector'] = await db.sectors.find_one({"id": os['ativo']['sector_id']}, {"_id": 0, "nome": 1})
    if os.get('responsavel_id'):
        os['responsavel'] = await db.users.find_one({"id": os['responsavel_id']}, {"_id": 0, "nome": 1, "email": 1, "telefone": 1})
    # Materiais sugeridos do ativo
    os['materiais_sugeridos'] = await db.ativo_materiais.find({"ativo_id": os.get('ativo_id'), "deleted_at": None}, {"_id": 0}).to_list(50)
    return os


@router.post("/ordens-servico")
async def create_os(data: OSCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor', 'tecnico'])
    ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")

    org_id = ativo.get('organization_id', user.get('organization_id', ''))
    numero = await generate_os_numero(org_id)

    # Suggest materials from asset's BOM
    materiais = await db.ativo_materiais.find({"ativo_id": data.ativo_id, "deleted_at": None}, {"_id": 0}).to_list(50)

    os_id = str(uuid.uuid4())
    os_doc = {
        "id": os_id, "numero": numero, "ativo_id": data.ativo_id,
        "organization_id": org_id, "tipo": data.tipo.value,
        "disciplina": data.disciplina.value,
        "origem": data.origem.value,
        "prioridade": data.prioridade.value, "titulo": data.titulo,
        "descricao": data.descricao, "status": "aberta",
        "responsavel_id": data.responsavel_id, "equipe": data.equipe or [],
        "data_abertura": datetime.now(timezone.utc).isoformat(),
        "data_planejada": data.data_planejada, "data_inicio": None, "data_conclusao": None,
        "custo_pecas": data.custo_pecas, "custo_mao_obra": data.custo_mao_obra,
        "custo_total": data.custo_pecas + data.custo_mao_obra,
        "causa_falha": data.causa_falha,
        "equipamento_parado": data.equipamento_parado,
        "horas_parada": data.horas_parada,
        "tempo_execucao_minutos": None, "observacoes": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None
    }

    await db.ordens_servico.insert_one(os_doc)
    if data.responsavel_id:
        await criar_notificacao(data.responsavel_id, org_id, NotificacaoTipo.OS_ATRIBUIDA,
            f"Nova OS atribuída: #{numero}", f"Ativo: {ativo.get('tag', '')} - {data.titulo}", f"/os/{os_id}")
    os_doc.pop('_id', None)
    return os_doc


@router.put("/ordens-servico/{os_id}")
async def update_os(os_id: str, data: OSUpdate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    existing = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="OS não encontrada")

    update_data = {k: v.value if isinstance(v, Enum) else v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()

    if 'custo_pecas' in update_data or 'custo_mao_obra' in update_data:
        pecas = update_data.get('custo_pecas', existing.get('custo_pecas', 0))
        mao_obra = update_data.get('custo_mao_obra', existing.get('custo_mao_obra', 0))
        update_data['custo_total'] = pecas + mao_obra

    await db.ordens_servico.update_one({"id": os_id}, {"$set": update_data})
    return await db.ordens_servico.find_one({"id": os_id}, {"_id": 0})


@router.delete("/ordens-servico/{os_id}")
async def delete_os(os_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    existing = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "ordens_servico", os_id, user, f"OS #{existing.get('numero')} excluída")
    return {"success": True, "message": "OS excluída com sucesso"}


@router.post("/ordens-servico/{os_id}/iniciar")
async def iniciar_os(os_id: str, user: Dict = Depends(get_current_user)):
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"status": "em_execucao", "data_inicio": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("status_change", "ordens_servico", os_id, user, f"OS #{os.get('numero')} → em_execucao")
    return {"success": True, "message": "OS iniciada"}


@router.post("/ordens-servico/{os_id}/pausar")
async def pausar_os(os_id: str, user: Dict = Depends(get_current_user)):
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"status": "pausada", "updated_at": datetime.now(timezone.utc).isoformat()}})
    if os_doc:
        await audit_log("status_change", "ordens_servico", os_id, user, f"OS #{os_doc.get('numero')} → pausada")
    return {"success": True, "message": "OS pausada"}


@router.patch("/ordens-servico/{os_id}/status")
async def update_os_status(os_id: str, body: KanbanMoveBody, user: Dict = Depends(get_current_user)):
    """Kanban drag-and-drop status update"""
    check_write_permission(user, ['admin', 'pcm', 'supervisor'])
    valid = ['aberta', 'planejada', 'em_execucao', 'pausada']
    if body.new_status not in valid:
        raise HTTPException(status_code=400, detail=f"Status inválido. Use: {', '.join(valid)}.")
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    if os_doc.get('status') == 'concluida':
        raise HTTPException(status_code=400, detail="OS concluída não pode ser reaberta via Kanban")
    update = {"status": body.new_status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if body.new_status == 'em_execucao' and not os_doc.get('data_inicio'):
        update['data_inicio'] = datetime.now(timezone.utc).isoformat()
    await db.ordens_servico.update_one({"id": os_id}, {"$set": update})
    await audit_log("kanban_move", "ordens_servico", os_id, user, f"OS #{os_doc.get('numero')} → {body.new_status}")
    return {"success": True, "new_status": body.new_status}


@router.post("/ordens-servico/{os_id}/concluir")
async def concluir_os(os_id: str, body: ConcluirOSBody = ConcluirOSBody(), user: Dict = Depends(get_current_user)):
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    descricao = body.servicos_realizados or body.observacoes or os_doc.get('descricao')
    if not descricao:
        raise HTTPException(status_code=400, detail="Descrição do serviço é obrigatória para fechar a OS")
    if os_doc.get('tipo') in ['corretiva']:
        attachments = await db.attachments.count_documents({"entity_type": "work_order", "entity_id": os_id})
        if attachments == 0:
            raise HTTPException(status_code=400, detail="OS corretiva exige pelo menos uma foto/evidência anexada")
    tempo = body.tempo_execucao_minutos
    if not tempo and os_doc.get('data_inicio'):
        start = datetime.fromisoformat(os_doc['data_inicio'].replace('Z', '+00:00'))
        tempo = int((datetime.now(timezone.utc) - start).total_seconds() / 60)
    if not tempo:
        raise HTTPException(status_code=400, detail="Tempo gasto é obrigatório para fechar a OS")
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {
        "status": "concluida", "data_conclusao": datetime.now(timezone.utc).isoformat(),
        "tempo_execucao_minutos": tempo, "descricao_servico": descricao,
        "observacoes": body.observacoes, "updated_at": datetime.now(timezone.utc).isoformat()
    }})
    await db.ativos.update_one({"id": os_doc.get('ativo_id')}, {"$set": {"status": "operacional", "updated_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("status_change", "ordens_servico", os_id, user, f"OS #{os_doc.get('numero')} → concluida (tempo: {tempo}min)")
    return {"success": True, "tempo_execucao_minutos": tempo}


@router.get("/ordens-servico/{os_id}/historico")
async def get_os_historico(os_id: str, user: Dict = Depends(get_current_user)):
    """Get transition history for a specific OS"""
    logs = await db.audit_logs.find(
        {"entity_type": "ordens_servico", "entity_id": os_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return logs
