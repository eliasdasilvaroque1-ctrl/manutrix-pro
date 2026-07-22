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
    allowed = ["cor_primaria", "cor_secundaria", "cor_fundo", "cor_texto", "cor_destaque", "cor_sucesso", "cor_alerta", "cor_erro", "cor_menu", "cor_login", "cor_header"]
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
    # Register branding file as public
    await db.file_registry.update_one({"url": url}, {"$set": {"url": url, "organization_id": org_id, "uploaded_by": user.get('id',''), "is_public": True, "category": "branding", "registered_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
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
    await db.file_registry.update_one({"url": url}, {"$set": {"url": url, "organization_id": org_id, "uploaded_by": user.get('id',''), "is_public": True, "category": "branding", "registered_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
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
            "nome": ident.get('nome_empresa') or ident.get('nome_sistema', ''),
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
                "nome_sistema": "CMMS", "nome_empresa": "CMMS",
                "subtitulo": "Sistema de Gestão de Manutenção",
                "logo_url": None, "logo_branca_url": None, "favicon_url": None,
                "texto_login": "Sistema de Gestão de Manutenção Industrial",
                "mostrar_powered_by": True, "rodape": "",
            },
            "tema": {"cor_primaria": "#10b981", "cor_secundaria": "#3b82f6", "cor_fundo": "#020617",
                     "cor_texto": "#e2e8f0", "cor_destaque": "#f59e0b",
                     "cor_menu": "#0f172a", "cor_login": "#020617", "cor_header": "#0f172a"},
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

    sector = await db.sectors.find_one({"id": ativo.get('sector_id')}, {"_id": 0, "nome": 1, "codigo": 1, "unidade_id": 1})
    
    # Resolve unidade from sector or first unidade of org
    unidade = None
    if sector and sector.get('unidade_id'):
        unidade = await db.unidades.find_one({"id": sector['unidade_id'], "deleted_at": None}, {"_id": 0, "nome": 1, "codigo": 1})
    if not unidade:
        unidade = await db.unidades.find_one({"organization_id": org_id, "deleted_at": None}, {"_id": 0, "nome": 1, "codigo": 1})

    # Last 5 inspections
    last_inspecoes = await db.inspecoes.find(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0, "id": 1, "data_conclusao": 1, "plano_nome": 1, "resultado": 1, "tipo": 1, "status": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(5)

    # Last 5 OS
    last_os = await db.ordens_servico.find(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0, "id": 1, "numero": 1, "titulo": 1, "tipo": 1, "status": 1, "data_conclusao": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(5)

    # Last 5 maintenance events
    last_manut = await db.ordens_servico.find(
        {"ativo_id": ativo_id, "status": "concluida", "deleted_at": None},
        {"_id": 0, "id": 1, "numero": 1, "titulo": 1, "tipo": 1, "data_conclusao": 1}
    ).sort("data_conclusao", -1).to_list(5)

    manuais = await db.manuais.find(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0, "id": 1, "nome": 1, "url": 1, "tipo_arquivo": 1}
    ).to_list(20)

    # KPIs
    total_os = await db.ordens_servico.count_documents({"ativo_id": ativo_id, "deleted_at": None})
    total_insp = await db.inspecoes.count_documents({"ativo_id": ativo_id, "deleted_at": None})
    os_concluidas = await db.ordens_servico.count_documents({"ativo_id": ativo_id, "status": "concluida", "deleted_at": None})
    insp_conformes = await db.inspecoes.count_documents({"ativo_id": ativo_id, "resultado": "conforme", "deleted_at": None})
    disponibilidade = ativo.get('kpis', {}).get('disponibilidade_percent', 100) if isinstance(ativo.get('kpis'), dict) else 100

    ident = config.get('identidade', {}) if config else {}
    tema = config.get('tema', {}) if config else {}

    return {
        "ativo": {
            "id": ativo['id'], "tag": ativo.get('tag'), "nome": ativo.get('nome'),
            "tipo_equipamento": ativo.get('tipo_equipamento'), "fabricante": ativo.get('fabricante'),
            "modelo": ativo.get('modelo'), "numero_serie": ativo.get('numero_serie'),
            "criticidade": ativo.get('criticidade'), "status": ativo.get('status'),
            "foto_url": ativo.get('foto_url'),
        },
        "area": sector.get('nome') if sector else '',
        "unidade": unidade.get('nome') if unidade else '',
        "ultimas_inspecoes": last_inspecoes,
        "ultimas_os": last_os,
        "ultimas_manutencoes": last_manut,
        "manuais": manuais,
        "kpis": {
            "total_os": total_os, "total_inspecoes": total_insp,
            "os_concluidas": os_concluidas, "insp_conformes": insp_conformes,
            "disponibilidade": disponibilidade,
        },
        "branding": {
            "nome_empresa": ident.get('nome_empresa', ''),
            "logo_url": ident.get('logo_url'),
            "logo_branca_url": ident.get('logo_branca_url'),
            "cor_primaria": tema.get('cor_primaria', '#10b981'),
            "cor_secundaria": tema.get('cor_secundaria', '#3b82f6'),
            "cor_fundo": tema.get('cor_fundo', '#020617'),
            "cor_texto": tema.get('cor_texto', '#e2e8f0'),
            "cor_menu": tema.get('cor_menu', '#0f172a'),
            "mostrar_powered_by": ident.get('mostrar_powered_by', True),
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


# ============== MASTER WHITE LABEL ENDPOINTS ==============

@router.get("/master/organizations")
async def master_list_organizations(user: Dict = Depends(get_current_user)):
    """MASTER: List all organizations with their full config."""
    check_master_only(user)
    orgs = await db.organizations.find({"deleted_at": None}, {"_id": 0}).to_list(200)
    result = []
    for org in orgs:
        config = await db.org_config.find_one(
            {"organization_id": org["id"]}, {"_id": 0}
        )
        result.append({**org, "config": config})
    return result


@router.post("/master/organizations")
async def master_create_organization(data: dict, user: Dict = Depends(get_current_user)):
    """MASTER: Create a new organization."""
    check_master_only(user)
    nome = data.get("nome", "").strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Nome da empresa é obrigatório")

    org_id = str(uuid.uuid4())
    org = {
        "id": org_id,
        "nome": nome,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id", ""),
        "deleted_at": None,
    }
    await db.organizations.insert_one(org)

    # Create default org_config
    config = build_default_org_config(org_id, nome)
    await db.org_config.insert_one({**config})
    config.pop("_id", None)

    await audit_log("create", "organization", org_id, user, f"Organização criada: {nome}")
    org.pop("_id", None)
    return {**org, "config": config}


@router.get("/master/organizations/{org_id}/config")
async def master_get_org_config(org_id: str, user: Dict = Depends(get_current_user)):
    """MASTER: Get full config for any organization."""
    check_master_only(user)
    config = await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})
    if not config:
        org = await db.organizations.find_one({"id": org_id}, {"_id": 0, "nome": 1})
        if not org:
            raise HTTPException(status_code=404, detail="Organização não encontrada")
        config = build_default_org_config(org_id, org.get("nome", ""))
        await db.org_config.insert_one({**config})
        config.pop("_id", None)
    return config


@router.put("/master/organizations/{org_id}/config")
async def master_update_org_config(org_id: str, data: dict, user: Dict = Depends(get_current_user)):
    """MASTER: Update full branding config for any organization."""
    check_master_only(user)

    existing = await db.org_config.find_one({"organization_id": org_id})
    if not existing:
        org = await db.organizations.find_one({"id": org_id}, {"_id": 0, "nome": 1})
        if not org:
            raise HTTPException(status_code=404, detail="Organização não encontrada")
        config = build_default_org_config(org_id, org.get("nome", ""))
        await db.org_config.insert_one({**config})

    update = {"updated_at": datetime.now(timezone.utc).isoformat()}

    ident_fields = [
        "nome_sistema", "nome_empresa", "subtitulo", "rodape",
        "texto_institucional", "texto_login", "mostrar_powered_by",
        "wallpaper_url", "wallpaper_aplicacao", "wallpaper_intensidade", "wallpaper_blur",
    ]
    for k in ident_fields:
        if k in data:
            update[f"identidade.{k}"] = data[k]

    tema_fields = [
        "cor_primaria", "cor_secundaria", "cor_fundo", "cor_texto",
        "cor_destaque", "cor_menu", "cor_login", "cor_header",
        "cor_sucesso", "cor_alerta", "cor_erro",
        "cor_botoes", "cor_cards", "cor_indicadores",
    ]
    for k in tema_fields:
        if k in data:
            update[f"tema.{k}"] = data[k]

    if "subdominio" in data:
        update["dominio.subdominio"] = data["subdominio"].lower().strip()
    if "dominio_customizado" in data:
        update["dominio.dominio_customizado"] = data["dominio_customizado"].lower().strip()

    await db.org_config.update_one({"organization_id": org_id}, {"$set": update})
    await audit_log("update", "org_config", org_id, user, f"White Label MASTER: {list(data.keys())}")

    return await db.org_config.find_one({"organization_id": org_id}, {"_id": 0})


@router.post("/master/organizations/{org_id}/upload/{asset_type}")
async def master_upload_asset(
    org_id: str,
    asset_type: str,
    file: UploadFile = File(...),
    user: Dict = Depends(get_current_user),
):
    """MASTER: Upload logo/logo_branca/favicon/wallpaper for any org."""
    check_master_only(user)
    allowed_types = ["logo", "logo_branca", "favicon", "wallpaper"]
    if asset_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Tipo deve ser: {', '.join(allowed_types)}")

    org = await db.organizations.find_one({"id": org_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")

    content = await file.read()
    content_type = file.content_type or "image/png"

    if objstore.is_available():
        path = objstore.upload_file("org_assets", org_id, f"{asset_type}_{file.filename}", content, content_type)
        url = f"/api/storage/{path}"
    else:
        from pathlib import Path as PathLib
        from deps import UPLOAD_DIR
        import aiofiles
        ext = PathLib(file.filename).suffix or ".png"
        fname = f"{asset_type}_{org_id}_{uuid.uuid4().hex[:6]}{ext}"
        async with aiofiles.open(UPLOAD_DIR / fname, 'wb') as f:
            await f.write(content)
        url = f"/api/uploads/{fname}"

    field_map = {
        "logo": "identidade.logo_url",
        "logo_branca": "identidade.logo_branca_url",
        "favicon": "identidade.favicon_url",
        "wallpaper": "identidade.wallpaper_url",
    }
    await db.org_config.update_one(
        {"organization_id": org_id},
        {"$set": {field_map[asset_type]: url, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    await audit_log("upload", "org_config", org_id, user, f"Upload {asset_type}")
    await db.file_registry.update_one({"url": url}, {"$set": {"url": url, "organization_id": org_id, "uploaded_by": user.get('id',''), "is_public": True, "category": "branding", "registered_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    return {"url": url, "type": asset_type}
