"""Work Order routes: OS CRUD, Kanban, Statistics, History"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid

from deps import (
    db, get_current_user, check_admin_only, check_write_permission, check_not_gerente,
    audit_log, criar_notificacao, generate_os_numero, get_scoped_asset_ids, verify_org_access, audit_field_changes
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
        ativo = ativo_map.get(os.get('ativo_id'))
        if ativo and ativo.get('sector_id'):
            sector = await db.sectors.find_one({"id": ativo['sector_id']}, {"_id": 0, "nome": 1})
            ativo['sector'] = sector
        os['ativo'] = ativo
        os['responsavel'] = resp_map.get(os.get('responsavel_id'))
        # Enrich equipe names
        equipe_ids = os.get('equipe', [])
        if equipe_ids:
            equipe_users = await db.users.find({"id": {"$in": equipe_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(len(equipe_ids))
            os['equipe_nomes'] = [u.get('nome') for u in equipe_users]
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
    check_write_permission(user, ['admin', 'pcm', 'supervisor', 'tecnico'])
    check_not_gerente(user)
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
        "criado_por": user.get('id'),
        "planejado_por": None, "data_planejamento": None,
        "iniciado_por": None, "concluido_por": None,
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
    check_write_permission(user, ['admin', 'pcm'])
    existing = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, existing, "OS")

    update_data = {k: v.value if isinstance(v, Enum) else v for k, v in data.model_dump().items() if v is not None}
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
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "ordens_servico", os_id, user, f"OS #{existing.get('numero')} excluída")
    return {"success": True, "message": "OS excluída com sucesso"}


@router.post("/ordens-servico/{os_id}/iniciar")
async def iniciar_os(os_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor', 'tecnico'])
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"status": "em_execucao", "data_inicio": datetime.now(timezone.utc).isoformat(), "iniciado_por": user.get('id'), "alterado_por": user.get('id'), "updated_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("status_change", "ordens_servico", os_id, user, f"OS #{os.get('numero')} → em_execucao")
    return {"success": True, "message": "OS iniciada"}


@router.post("/ordens-servico/{os_id}/pausar")
async def pausar_os(os_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor', 'tecnico'])
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"status": "pausada", "alterado_por": user.get('id'), "updated_at": datetime.now(timezone.utc).isoformat()}})
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
    update = {"status": body.new_status, "alterado_por": user.get('id'), "updated_at": datetime.now(timezone.utc).isoformat()}
    if body.new_status == 'planejada' and not os_doc.get('planejado_por'):
        update['planejado_por'] = user.get('id')
        update['data_planejamento'] = datetime.now(timezone.utc).isoformat()
    if body.new_status == 'em_execucao' and not os_doc.get('data_inicio'):
        update['data_inicio'] = datetime.now(timezone.utc).isoformat()
        update['iniciado_por'] = user.get('id')
    await db.ordens_servico.update_one({"id": os_id}, {"$set": update})
    await audit_log("kanban_move", "ordens_servico", os_id, user, f"OS #{os_doc.get('numero')} → {body.new_status}")
    return {"success": True, "new_status": body.new_status}


@router.post("/ordens-servico/{os_id}/concluir")
async def concluir_os(os_id: str, body: ConcluirOSBody = ConcluirOSBody(), user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor', 'tecnico'])
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
        "concluido_por": user.get('id'), "alterado_por": user.get('id'),
        "observacoes": body.observacoes, "updated_at": datetime.now(timezone.utc).isoformat()
    }})
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
    check_write_permission(user, ['admin', 'pcm', 'supervisor', 'tecnico'])
    
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
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
