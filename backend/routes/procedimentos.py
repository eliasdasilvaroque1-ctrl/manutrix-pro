"""
Procedimentos Operacionais — CRUD + Execução + Auditoria
RC5.2 — Piloto ASTEC
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional, List
from datetime import datetime, timezone
import uuid

from deps import db, get_current_user, check_write_permission, verify_org_access

router = APIRouter(tags=["procedimentos"])


# ==================== CRUD PROCEDIMENTOS ====================

@router.get("/procedimentos")
async def list_procedimentos(
    status: Optional[str] = None,
    search: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None}
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"nome": {"$regex": search, "$options": "i"}},
            {"codigo": {"$regex": search, "$options": "i"}},
        ]
    docs = await db.procedimentos.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return docs


@router.post("/procedimentos")
async def create_procedimento(data: dict, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm', 'master'])
    org_id = user.get('organization_id', '')

    if not data.get('nome'):
        raise HTTPException(status_code=400, detail="Nome é obrigatório")

    etapas_raw = data.get('etapas', [])
    if len(etapas_raw) == 0:
        raise HTTPException(status_code=400, detail="Procedimento precisa ter pelo menos uma etapa")

    # Auto-generate code if not provided
    code = data.get('codigo', '').strip()
    if not code:
        count = await db.procedimentos.count_documents({"organization_id": org_id})
        code = f"PROC-{count + 1:04d}"

    # Check duplicate code
    existing_code = await db.procedimentos.find_one({"organization_id": org_id, "codigo": code, "deleted_at": None})
    if existing_code:
        raise HTTPException(status_code=400, detail=f"Código '{code}' já existe")

    # Validate steps — enforce unique order, require title
    etapas = []
    seen_ordens = set()
    for i, step in enumerate(etapas_raw):
        titulo = step.get('titulo', '').strip()
        if not titulo:
            raise HTTPException(status_code=400, detail=f"Etapa {i+1}: título é obrigatório")
        ordem = i + 1
        if ordem in seen_ordens:
            raise HTTPException(status_code=400, detail=f"Etapa com ordem {ordem} duplicada")
        seen_ordens.add(ordem)
        etapas.append({
            "id": str(uuid.uuid4()),
            "ordem": ordem,
            "titulo": titulo,
            "descricao": step.get('descricao', '').strip(),
            "obrigatoria": step.get('obrigatoria', True),
        })

    doc = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "codigo": code,
        "nome": data.get('nome', '').strip(),
        "descricao": data.get('descricao', '').strip(),
        "revisao": data.get('revisao', '01'),
        "versao": data.get('versao', 1),
        "status": data.get('status', 'rascunho'),
        "tempo_estimado_minutos": data.get('tempo_estimado_minutos'),
        "observacoes": data.get('observacoes', '').strip(),
        "etapas": etapas,
        "created_by": user.get('id', ''),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None,
    }
    await db.procedimentos.insert_one(doc)

    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "user_id": user.get('id', ''),
        "user_name": user.get('nome', ''),
        "action": "create",
        "entity_type": "procedimento",
        "entity_id": doc["id"],
        "details": {"codigo": code, "nome": doc["nome"], "etapas": len(etapas)},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {k: v for k, v in doc.items() if k != '_id'}


@router.get("/procedimentos/{proc_id}")
async def get_procedimento(proc_id: str, user: Dict = Depends(get_current_user)):
    doc = await db.procedimentos.find_one({"id": proc_id, "deleted_at": None}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    verify_org_access(user, doc, "Procedimento")
    return doc


@router.put("/procedimentos/{proc_id}")
async def update_procedimento(proc_id: str, data: dict, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm', 'master'])
    doc = await db.procedimentos.find_one({"id": proc_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    verify_org_access(user, doc, "Procedimento")

    etapas = []
    etapas_raw = data.get('etapas', doc.get('etapas', []))
    if len(etapas_raw) == 0:
        raise HTTPException(status_code=400, detail="Procedimento precisa ter pelo menos uma etapa")
    for i, step in enumerate(etapas_raw):
        titulo = step.get('titulo', '').strip()
        if not titulo:
            raise HTTPException(status_code=400, detail=f"Etapa {i+1}: título é obrigatório")
        etapas.append({
            "id": step.get('id', str(uuid.uuid4())),
            "ordem": i + 1,
            "titulo": titulo,
            "descricao": step.get('descricao', '').strip(),
            "obrigatoria": step.get('obrigatoria', True),
        })

    updates = {
        "nome": data.get('nome', doc.get('nome', '')).strip(),
        "descricao": data.get('descricao', doc.get('descricao', '')).strip(),
        "revisao": data.get('revisao', doc.get('revisao', '01')),
        "versao": data.get('versao', doc.get('versao', 1)),
        "status": data.get('status', doc.get('status', 'rascunho')),
        "tempo_estimado_minutos": data.get('tempo_estimado_minutos', doc.get('tempo_estimado_minutos')),
        "observacoes": data.get('observacoes', doc.get('observacoes', '')).strip(),
        "etapas": etapas,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user.get('id', ''),
    }
    if data.get('codigo'):
        new_code = data['codigo'].strip()
        if new_code != doc.get('codigo'):
            existing = await db.procedimentos.find_one({"organization_id": user.get('organization_id',''), "codigo": new_code, "deleted_at": None, "id": {"$ne": proc_id}})
            if existing:
                raise HTTPException(status_code=400, detail=f"Código '{new_code}' já existe")
        updates["codigo"] = new_code

    await db.procedimentos.update_one({"id": proc_id}, {"$set": updates})

    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "organization_id": user.get('organization_id', ''),
        "user_id": user.get('id', ''),
        "user_name": user.get('nome', ''),
        "action": "update",
        "entity_type": "procedimento",
        "entity_id": proc_id,
        "details": {"nome": updates["nome"], "etapas": len(etapas)},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    updated = await db.procedimentos.find_one({"id": proc_id}, {"_id": 0})
    return updated


@router.delete("/procedimentos/{proc_id}")
async def delete_procedimento(proc_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm', 'master'])
    doc = await db.procedimentos.find_one({"id": proc_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Procedimento não encontrado")
    verify_org_access(user, doc, "Procedimento")

    await db.procedimentos.update_one(
        {"id": proc_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat(), "deleted_by": user.get('id', '')}}
    )

    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "organization_id": user.get('organization_id', ''),
        "user_id": user.get('id', ''),
        "user_name": user.get('nome', ''),
        "action": "delete",
        "entity_type": "procedimento",
        "entity_id": proc_id,
        "details": {"codigo": doc.get('codigo'), "nome": doc.get('nome')},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"status": "deleted"}


# ==================== EXECUÇÃO NA OS ====================

@router.get("/ordens-servico/{os_id}/procedimento-execucao")
async def get_procedimento_execucao(os_id: str, user: Dict = Depends(get_current_user)):
    """Get procedure execution state for a work order."""
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")

    proc_id = os_doc.get('procedimento_id')
    if not proc_id:
        return {"procedimento": None, "execucao": None}

    proc = await db.procedimentos.find_one({"id": proc_id, "deleted_at": None}, {"_id": 0})
    if not proc:
        return {"procedimento": None, "execucao": None}

    execucao = await db.procedimento_execucoes.find_one(
        {"os_id": os_id, "procedimento_id": proc_id}, {"_id": 0}
    )

    return {"procedimento": proc, "execucao": execucao}


@router.post("/ordens-servico/{os_id}/procedimento-execucao/etapa")
async def registrar_etapa(os_id: str, data: dict, user: Dict = Depends(get_current_user)):
    """Mark a step as completed/uncompleted with optional observation."""
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")

    proc_id = os_doc.get('procedimento_id')
    if not proc_id:
        raise HTTPException(status_code=400, detail="OS não possui procedimento vinculado")

    etapa_id = data.get('etapa_id')
    concluida = data.get('concluida', True)
    observacao = data.get('observacao', '').strip()

    if not etapa_id:
        raise HTTPException(status_code=400, detail="etapa_id é obrigatório")

    now = datetime.now(timezone.utc).isoformat()

    execucao = await db.procedimento_execucoes.find_one({"os_id": os_id, "procedimento_id": proc_id})

    if not execucao:
        execucao = {
            "id": str(uuid.uuid4()),
            "os_id": os_id,
            "procedimento_id": proc_id,
            "organization_id": user.get('organization_id', ''),
            "etapas_executadas": {},
            "created_at": now,
            "updated_at": now,
        }
        await db.procedimento_execucoes.insert_one(execucao)

    etapa_data = {
        "concluida": concluida,
        "observacao": observacao,
        "executado_por": user.get('id', ''),
        "executado_por_nome": user.get('nome', ''),
        "executado_em": now if concluida else None,
    }

    await db.procedimento_execucoes.update_one(
        {"os_id": os_id, "procedimento_id": proc_id},
        {"$set": {
            f"etapas_executadas.{etapa_id}": etapa_data,
            "updated_at": now,
        }}
    )

    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "organization_id": user.get('organization_id', ''),
        "user_id": user.get('id', ''),
        "user_name": user.get('nome', ''),
        "action": "etapa_concluida" if concluida else "etapa_reaberta",
        "entity_type": "procedimento_execucao",
        "entity_id": os_id,
        "details": {"etapa_id": etapa_id, "procedimento_id": proc_id, "observacao": observacao[:100]},
        "created_at": now,
    })

    return {"status": "ok", "etapa_id": etapa_id, "concluida": concluida}


# ==================== VINCULAR PROCEDIMENTO À OS ====================

@router.patch("/ordens-servico/{os_id}/procedimento")
async def vincular_procedimento(os_id: str, data: dict, user: Dict = Depends(get_current_user)):
    """Link or unlink a procedure to a work order."""
    check_write_permission(user, ['admin', 'pcm', 'master', 'supervisor'])
    os_doc = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None})
    if not os_doc:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    verify_org_access(user, os_doc, "OS")

    proc_id = data.get('procedimento_id')  # None to unlink

    if proc_id:
        proc = await db.procedimentos.find_one({"id": proc_id, "deleted_at": None})
        if not proc:
            raise HTTPException(status_code=404, detail="Procedimento não encontrado")
        verify_org_access(user, proc, "Procedimento")

    now = datetime.now(timezone.utc).isoformat()
    old_proc_id = os_doc.get('procedimento_id')

    await db.ordens_servico.update_one(
        {"id": os_id},
        {"$set": {"procedimento_id": proc_id, "updated_at": now}}
    )

    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "organization_id": user.get('organization_id', ''),
        "user_id": user.get('id', ''),
        "user_name": user.get('nome', ''),
        "action": "vincular_procedimento" if proc_id else "desvincular_procedimento",
        "entity_type": "ordem_servico",
        "entity_id": os_id,
        "details": {"procedimento_id": proc_id, "anterior": old_proc_id},
        "created_at": now,
    })

    return {"status": "ok", "procedimento_id": proc_id}


@router.get("/procedimentos-select")
async def list_procedimentos_select(user: Dict = Depends(get_current_user)):
    """Light list for select dropdowns — only approved procedures."""
    org_id = user.get('organization_id', '')
    docs = await db.procedimentos.find(
        {"organization_id": org_id, "status": "aprovado", "deleted_at": None},
        {"_id": 0, "id": 1, "codigo": 1, "nome": 1, "revisao": 1, "tempo_estimado_minutos": 1}
    ).sort("codigo", 1).to_list(200)
    return docs
