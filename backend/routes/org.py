"""
MAINTRIX ENTERPRISE — Organization Config Routes
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


# ============== PUBLIC ENDPOINTS (no auth) ==============

@router.get("/public/organizations")
async def list_organizations_public():
    """Public: list organizations for login company selector."""
    configs = await db.org_config.find(
        {}, {"_id": 0, "organization_id": 1, "identidade": 1, "tema": 1, "dominio": 1}
    ).to_list(100)
    orgs = []
    for c in configs:
        ident = c.get('identidade', {})
        orgs.append({
            "id": c['organization_id'],
            "nome": ident.get('nome_empresa') or ident.get('nome_sistema', 'MAINTRIX'),
            "logo_url": ident.get('logo_url'),
            "cor_primaria": c.get('tema', {}).get('cor_primaria', '#10b981'),
            "subdominio": c.get('dominio', {}).get('subdominio', ''),
        })
    return orgs


@router.get("/public/branding/{identifier}")
async def get_public_branding(identifier: str):
    """Public: get branding by org_id or subdomain. No auth required."""
    config = await db.org_config.find_one(
        {"$or": [
            {"organization_id": identifier},
            {"dominio.subdominio": identifier},
            {"dominio.dominio_customizado": identifier},
        ]},
        {"_id": 0, "identidade": 1, "tema": 1, "dominio": 1, "organization_id": 1}
    )
    if not config:
        return {
            "organization_id": None,
            "identidade": {
                "nome_sistema": "MAINTRIX", "nome_empresa": "MAINTRIX",
                "logo_url": None, "logo_branca_url": None, "favicon_url": None,
                "texto_login": "Sistema de Gestão de Manutenção Industrial",
                "mostrar_powered_by": False, "rodape": "© 2026 MAINTRIX",
            },
            "tema": {"cor_primaria": "#10b981", "cor_secundaria": "#3b82f6", "cor_fundo": "#020617",
                     "cor_menu": "#0f172a", "cor_login": "#020617"},
        }
    return config


@router.get("/public/ativo/{ativo_id}")
async def get_public_ativo(ativo_id: str):
    """Public: equipment portal via QR code. Read-only, no auth."""
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")

    org_id = ativo.get('organization_id', '')
    config = await db.org_config.find_one({"organization_id": org_id}, {"_id": 0, "identidade": 1, "tema": 1})

    # Sector info
    sector = await db.sectors.find_one({"id": ativo.get('sector_id')}, {"_id": 0, "nome": 1, "codigo": 1})

    # Last events (public - limited info)
    last_insp = await db.inspecoes.find_one(
        {"ativo_id": ativo_id, "status": "concluida", "deleted_at": None},
        {"_id": 0, "data_conclusao": 1, "plano_nome": 1, "resultado": 1, "tipo": 1},
        sort=[("data_conclusao", -1)]
    )
    last_os = await db.ordens_servico.find_one(
        {"ativo_id": ativo_id, "status": "concluida", "deleted_at": None},
        {"_id": 0, "data_conclusao": 1, "titulo": 1, "tipo": 1},
        sort=[("data_conclusao", -1)]
    )

    # Manuais (public)
    manuais = await db.manuais.find(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0, "id": 1, "nome": 1, "url": 1, "tipo_arquivo": 1}
    ).to_list(20)

    # KPIs
    total_os = await db.ordens_servico.count_documents({"ativo_id": ativo_id, "deleted_at": None})
    total_insp = await db.inspecoes.count_documents({"ativo_id": ativo_id, "deleted_at": None})

    return {
        "ativo": {
            "id": ativo['id'], "tag": ativo.get('tag'), "nome": ativo.get('nome'),
            "tipo_equipamento": ativo.get('tipo_equipamento'), "fabricante": ativo.get('fabricante'),
            "modelo": ativo.get('modelo'), "numero_serie": ativo.get('numero_serie'),
            "criticidade": ativo.get('criticidade'), "status": ativo.get('status'),
            "foto_url": ativo.get('foto_url'),
        },
        "area": sector.get('nome') if sector else '',
        "ultima_inspecao": last_insp,
        "ultima_os": last_os,
        "manuais": manuais,
        "kpis": {"total_os": total_os, "total_inspecoes": total_insp},
        "branding": {
            "nome_empresa": config.get('identidade', {}).get('nome_empresa', 'MAINTRIX') if config else 'MAINTRIX',
            "logo_url": config.get('identidade', {}).get('logo_url') if config else None,
            "cor_primaria": config.get('tema', {}).get('cor_primaria', '#10b981') if config else '#10b981',
        },
    }


@router.put("/org/config/branding")
async def update_branding_completo(data: dict, user: Dict = Depends(get_current_user)):
    """Update complete branding configuration (White Label admin)."""
    check_admin_only(user)
    org_id = user.get("organization_id", "")
    await get_or_create_config(org_id)

    update = {"updated_at": datetime.now(timezone.utc).isoformat()}

    # Identidade fields
    ident_fields = ["nome_sistema", "nome_empresa", "subtitulo", "rodape",
                    "texto_institucional", "texto_login", "mostrar_powered_by"]
    for k in ident_fields:
        if k in data:
            update[f"identidade.{k}"] = data[k]

    # Tema fields
    tema_fields = ["cor_primaria", "cor_secundaria", "cor_fundo", "cor_texto",
                   "cor_destaque", "cor_menu", "cor_login", "cor_header",
                   "cor_sucesso", "cor_alerta", "cor_erro"]
    for k in tema_fields:
        if k in data:
            update[f"tema.{k}"] = data[k]

    # Domínio fields
    if "subdominio" in data:
        update["dominio.subdominio"] = data["subdominio"].lower().strip()
    if "dominio_customizado" in data:
        update["dominio.dominio_customizado"] = data["dominio_customizado"].lower().strip()

    await db.org_config.update_one({"organization_id": org_id}, {"$set": update})
    await audit_log("update", "org_config", org_id, user, f"Branding atualizado: {list(data.keys())}")

    return await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})
