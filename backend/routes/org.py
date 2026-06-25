"""
MANUTRIX ENTERPRISE — Organization Config Routes
CRUD for org_config, numbering preview, unidades management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid

from deps import (
    db, get_current_user, check_admin_only, check_master_only,
    verify_org_access, audit_log, logger
)
from org_config import (
    build_default_org_config, DEFAULT_TERMINOLOGY, DEFAULT_THEME,
    DEFAULT_NUMERACAO, DEFAULT_PREFERENCES, TIPO_ABREVIACOES, gerar_numero,
    CONFIG_INDEXES,
)
import storage as objstore

router = APIRouter()


# ============== ORG CONFIG ==============

@router.get("/org/config")
async def get_org_config(user: Dict = Depends(get_current_user)):
    """Get organization configuration. Creates default if not exists."""
    org_id = user.get("organization_id", "")
    config = await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})
    
    if not config:
        # Get org name
        org = await db.organizations.find_one({"id": org_id}, {"_id": 0, "nome": 1})
        org_nome = org.get("nome", "") if org else ""
        config = build_default_org_config(org_id, org_nome)
        await db.org_config.insert_one({**config})
        config.pop("_id", None)
    
    return config

@router.put("/org/config/identidade")
async def update_identidade(data: dict, user: Dict = Depends(get_current_user)):
    """Update organization identity (name, subtitle, footer, institutional text)."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    
    # Ensure config exists
    await get_or_create_config(org_id)
    
    update_fields = {}
    allowed = ["nome_sistema", "subtitulo", "rodape", "texto_institucional"]
    for k in allowed:
        if k in data:
            update_fields[f"identidade.{k}"] = data[k]
    
    if update_fields:
        update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.org_config.update_one({"organization_id": org_id}, {"$set": update_fields})
        await audit_log("update", "org_config", org_id, user, f"Identidade atualizada: {list(data.keys())}")
    
    return await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})

@router.put("/org/config/tema")
async def update_tema(data: dict, user: Dict = Depends(get_current_user)):
    """Update organization theme colors."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    await get_or_create_config(org_id)
    
    update_fields = {}
    allowed = ["cor_primaria", "cor_secundaria", "cor_fundo", "cor_texto", "cor_destaque", "cor_sucesso", "cor_alerta", "cor_erro"]
    for k in allowed:
        if k in data:
            update_fields[f"tema.{k}"] = data[k]
    
    if update_fields:
        update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.org_config.update_one({"organization_id": org_id}, {"$set": update_fields})
        await audit_log("update", "org_config", org_id, user, f"Tema atualizado")
    
    return await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})

@router.put("/org/config/terminologia")
async def update_terminologia(data: dict, user: Dict = Depends(get_current_user)):
    """Update organization terminology dictionary."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    await get_or_create_config(org_id)
    
    # Merge with existing (only update provided keys)
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for k, v in data.items():
        if isinstance(v, str) and k in DEFAULT_TERMINOLOGY:
            update_fields[f"terminologia.{k}"] = v
    
    await db.org_config.update_one({"organization_id": org_id}, {"$set": update_fields})
    await audit_log("update", "org_config", org_id, user, f"Terminologia atualizada: {len(data)} termos")
    
    return await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})

@router.put("/org/config/numeracao")
async def update_numeracao(data: dict, user: Dict = Depends(get_current_user)):
    """Update numbering patterns."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    await get_or_create_config(org_id)
    
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for entidade, cfg in data.items():
        if entidade in DEFAULT_NUMERACAO and isinstance(cfg, dict):
            for k in ["prefixo", "digitos"]:
                if k in cfg:
                    update_fields[f"numeracao.{entidade}.{k}"] = cfg[k]
    
    await db.org_config.update_one({"organization_id": org_id}, {"$set": update_fields})
    await audit_log("update", "org_config", org_id, user, f"Numeração atualizada")
    
    return await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})

@router.put("/org/config/preferencias")
async def update_preferencias(data: dict, user: Dict = Depends(get_current_user)):
    """Update organization preferences (work hours, shifts, holidays, etc.)."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    await get_or_create_config(org_id)
    
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    allowed = [
        "horario_trabalho", "turnos", "feriados", "unidade_tempo",
        "formato_data", "fuso_horario", "idioma", "moeda",
        "prefixo_empresa", "aprovacao_os", "fluxo_assinatura",
    ]
    for k in allowed:
        if k in data:
            update_fields[f"preferencias.{k}"] = data[k]
    
    await db.org_config.update_one({"organization_id": org_id}, {"$set": update_fields})
    await audit_log("update", "org_config", org_id, user, f"Preferências atualizadas: {list(data.keys())}")
    
    return await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})

@router.post("/org/config/logo")
async def upload_logo(file: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    """Upload organization logo."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    await get_or_create_config(org_id)
    
    content = await file.read()
    if objstore.is_available():
        path = objstore.upload_file("org_assets", org_id, file.filename, content, file.content_type or "image/png")
        url = f"/api/storage/{path}"
    else:
        from pathlib import Path
        from deps import UPLOAD_DIR
        import aiofiles
        fname = f"logo_{org_id}_{uuid.uuid4().hex[:6]}{Path(file.filename).suffix}"
        async with aiofiles.open(UPLOAD_DIR / fname, 'wb') as f:
            await f.write(content)
        url = f"/api/uploads/{fname}"
    
    await db.org_config.update_one(
        {"organization_id": org_id},
        {"$set": {"identidade.logo_url": url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"url": url}

@router.post("/org/config/favicon")
async def upload_favicon(file: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    """Upload organization favicon."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    await get_or_create_config(org_id)
    
    content = await file.read()
    if objstore.is_available():
        path = objstore.upload_file("org_assets", org_id, file.filename, content, file.content_type or "image/x-icon")
        url = f"/api/storage/{path}"
    else:
        from pathlib import Path
        from deps import UPLOAD_DIR
        import aiofiles
        fname = f"favicon_{org_id}_{uuid.uuid4().hex[:6]}{Path(file.filename).suffix}"
        async with aiofiles.open(UPLOAD_DIR / fname, 'wb') as f:
            await f.write(content)
        url = f"/api/uploads/{fname}"
    
    await db.org_config.update_one(
        {"organization_id": org_id},
        {"$set": {"identidade.favicon_url": url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"url": url}


# ============== NUMBERING PREVIEW ==============

@router.get("/org/config/numeracao/preview")
async def preview_numeracao(
    entidade: str = "ordens_servico",
    tipo: str = "corretiva",
    user: Dict = Depends(get_current_user),
):
    """Preview what the next number would look like (without incrementing)."""
    org_id = user.get("organization_id", "")
    config = await db.org_config.find_one({"organization_id": org_id}, {"_id": 0, "numeracao": 1, "preferencias": 1})
    config = config or {}
    
    numeracao = config.get("numeracao", DEFAULT_NUMERACAO)
    prefs = config.get("preferencias", DEFAULT_PREFERENCES)
    prefixo = prefs.get("prefixo_empresa", "MNT")
    ano = datetime.now().year
    
    pattern = numeracao.get(entidade, {})
    digitos = pattern.get("digitos", 5)
    padrao = pattern.get("prefixo", "")
    
    tipo_abrev = TIPO_ABREVIACOES.get(tipo, tipo[:4].upper()) if tipo else ""
    
    if padrao and prefixo:
        preview = padrao.format(empresa=prefixo, tipo_abrev=tipo_abrev, ano=ano, unidade="", area="") + "0" * digitos
    else:
        preview = f"{ano}-{'0' * 5}"
    
    return {
        "preview": preview,
        "padrao": padrao,
        "prefixo_empresa": prefixo,
        "tipo_abrev": tipo_abrev,
        "digitos": digitos,
    }


# ============== UNIDADES ==============

@router.get("/unidades")
async def list_unidades(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get("organization_id"):
        query["organization_id"] = user["organization_id"]
    return await db.unidades.find(query, {"_id": 0}).sort("nome", 1).to_list(100)

@router.post("/unidades")
async def create_unidade(data: dict, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    doc = {
        "id": str(uuid.uuid4()),
        "organization_id": user.get("organization_id", ""),
        "codigo": data.get("codigo", ""),
        "nome": data.get("nome", ""),
        "descricao": data.get("descricao", ""),
        "endereco": data.get("endereco", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id", ""),
        "updated_by": user.get("id", ""),
        "deleted_at": None,
    }
    await db.unidades.insert_one(doc)
    await audit_log("create", "unidade", doc["id"], user, f"Unidade criada: {data.get('nome')}")
    doc.pop("_id", None)
    return doc

@router.put("/unidades/{unidade_id}")
async def update_unidade(unidade_id: str, data: dict, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    existing = await db.unidades.find_one({"id": unidade_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    verify_org_access(user, existing, "Unidade")
    updates = {k: v for k, v in data.items() if k in ("codigo", "nome", "descricao", "endereco") and v is not None}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        updates["updated_by"] = user.get("id", "")
        await db.unidades.update_one({"id": unidade_id}, {"$set": updates})
        await audit_log("update", "unidade", unidade_id, user, f"Unidade atualizada: {list(updates.keys())}")
    return await db.unidades.find_one({"id": unidade_id}, {"_id": 0})

@router.delete("/unidades/{unidade_id}")
async def delete_unidade(unidade_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    existing = await db.unidades.find_one({"id": unidade_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    verify_org_access(user, existing, "Unidade")
    await db.unidades.update_one({"id": unidade_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "unidade", unidade_id, user, f"Unidade excluída: {existing.get('nome')}")
    return {"success": True}


# ============== HELPERS ==============

async def get_or_create_config(org_id: str) -> dict:
    """Get org config, create default if missing."""
    config = await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})
    if not config:
        org = await db.organizations.find_one({"id": org_id}, {"_id": 0, "nome": 1})
        org_nome = org.get("nome", "") if org else ""
        config = build_default_org_config(org_id, org_nome)
        await db.org_config.insert_one({**config})
    return config
