from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import io
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import hashlib
import secrets
import jwt
from enum import Enum
import aiofiles
import random
import string
import json

# Import shared deps and models
from deps import (
    db, client, security, ROOT_DIR, UPLOAD_DIR, MANUALS_DIR,
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, supabase_client,
    hash_password, verify_password, create_token, get_current_user,
    is_admin, check_write_permission, check_admin_only, check_pcm_or_admin, check_not_gerente, can_export, can_view_dashboard,
    generate_tag, generate_sku, generate_os_numero,
    audit_log, audit_denial, criar_notificacao, verificar_estoque_critico, get_scoped_asset_ids,
    logger
)
from models import *

# Import route modules
from routes.dashboard import router as dashboard_router
from routes.assets import router as assets_router
from routes.work_orders import router as work_orders_router

app = FastAPI(title="MANUTRIX API", version="3.1.0")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Include modularized routers
app.include_router(dashboard_router, prefix="/api")
app.include_router(assets_router, prefix="/api")
app.include_router(work_orders_router, prefix="/api")

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    org_id = user_data.organization_id
    if not org_id and user_data.role == UserRole.ADMIN:
        org = Organization(nome=f"Org de {user_data.nome}")
        org_doc = org.model_dump()
        org_doc['created_at'] = org_doc['created_at'].isoformat()
        await db.organizations.insert_one(org_doc)
        org_id = org.id
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "nome": user_data.nome,
        "role": user_data.role.value,
        "organization_id": org_id,
        "telefone": user_data.telefone,
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user_data.role.value, org_id or "")
    return TokenResponse(
        access_token=token,
        user={"id": user_id, "email": user_data.email, "nome": user_data.nome, "role": user_data.role.value, "organization_id": org_id}
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    email = credentials.email.lower().strip()
    
    # Try Supabase Auth first
    if supabase_client:
        try:
            auth_response = supabase_client.auth.sign_in_with_password({
                "email": email,
                "password": credentials.password,
            })
            if auth_response.session and auth_response.user:
                user = await db.users.find_one({"email": email, "deleted_at": None}, {"_id": 0})
                if not user:
                    user_id = str(uuid.uuid4())
                    user = {
                        "id": user_id, "email": email,
                        "nome": auth_response.user.user_metadata.get('nome', email.split('@')[0]),
                        "role": "tecnico", "organization_id": "",
                        "supabase_id": auth_response.user.id,
                        "created_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None
                    }
                    await db.users.insert_one(user)
                    user.pop('_id', None)
                elif not user.get('supabase_id'):
                    await db.users.update_one({"id": user['id']}, {"$set": {"supabase_id": auth_response.user.id}})
                
                token = create_token(user['id'], user.get('role', 'tecnico'), user.get('organization_id', ''))
                await audit_log("login", "auth", user['id'], user, f"Login via Supabase: {email}")
                return TokenResponse(
                    access_token=token,
                    user={"id": user['id'], "email": user['email'], "nome": user.get('nome', ''),
                          "role": user.get('role', 'tecnico'), "organization_id": user.get('organization_id'),
                          "telefone": user.get('telefone'), "force_password_change": user.get('force_password_change', False)}
                )
        except Exception as e:
            logger.debug(f"Supabase auth failed: {e}")
    
    # Fallback to MongoDB auth
    user = await db.users.find_one({"email": email, "deleted_at": None}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Auto-sync user to Supabase
    if supabase_client and not user.get('supabase_id'):
        try:
            sb_resp = supabase_client.auth.admin.create_user({
                "email": email, "password": credentials.password,
                "email_confirm": True, "user_metadata": {"nome": user.get('nome', ''), "role": user.get('role', '')}
            })
            if sb_resp.user:
                await db.users.update_one({"id": user['id']}, {"$set": {"supabase_id": sb_resp.user.id}})
        except Exception as e:
            logger.warning(f"Supabase sync: {e}")
    
    token = create_token(user['id'], user['role'], user.get('organization_id', ''))
    await audit_log("login", "auth", user['id'], user, f"Login local: {email}")
    return TokenResponse(
        access_token=token,
        user={"id": user['id'], "email": user['email'], "nome": user['nome'],
              "role": user['role'], "organization_id": user.get('organization_id'),
              "telefone": user.get('telefone'), "force_password_change": user.get('force_password_change', False)}
    )

@api_router.get("/auth/me")
async def get_me(user: Dict = Depends(get_current_user)):
    return {k: v for k, v in user.items() if k not in ['password_hash']}

# ============== PASSWORD RESET ==============




@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Send password reset - via Supabase or local token"""
    email = data.email.lower().strip()
    
    if supabase_client:
        try:
            supabase_client.auth.reset_password_for_email(email)
            return {"success": True, "message": "Link de redefinição enviado para seu email", "method": "supabase"}
        except Exception as e:
            logger.warning(f"Supabase reset failed: {e}")
    
    # Fallback: local token
    user = await db.users.find_one({"email": email, "deleted_at": None}, {"_id": 0})
    if not user:
        return {"success": True, "message": "Se o email existir, um link de redefinição será gerado"}
    
    token = secrets.token_urlsafe(32)
    await db.password_reset_tokens.insert_one({
        "token": token, "user_id": user['id'], "email": email,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used": False, "created_at": datetime.now(timezone.utc).isoformat()
    })
    logger.info(f"PASSWORD RESET TOKEN for {email}: {token}")
    return {"success": True, "message": "Token de redefinição gerado. Verifique o console.", "token": token}

@api_router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password using token"""
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")
    
    reset_doc = await db.password_reset_tokens.find_one({
        "token": data.token,
        "used": False,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    
    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"id": reset_doc['user_id']},
        {"$set": {"password_hash": new_hash, "force_password_change": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    await db.password_reset_tokens.update_one({"token": data.token}, {"$set": {"used": True}})
    
    return {"success": True, "message": "Senha redefinida com sucesso"}

@api_router.post("/auth/change-password")
async def change_password(data: ChangePasswordRequest, user: Dict = Depends(get_current_user)):
    """Change own password (for forced change on first login)"""
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")
    
    # If user has force_password_change, skip current password check
    if not user.get('force_password_change'):
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Senha atual é obrigatória")
        full_user = await db.users.find_one({"id": user['id']}, {"_id": 0})
        if not verify_password(data.current_password, full_user.get('password_hash', '')):
            raise HTTPException(status_code=400, detail="Senha atual incorreta")
    
    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"id": user['id']},
        {"$set": {"password_hash": new_hash, "force_password_change": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"success": True, "message": "Senha alterada com sucesso"}

@api_router.post("/admin/users/{user_id}/reset-password")
async def admin_reset_password(user_id: str, user: Dict = Depends(get_current_user)):
    """Admin resets user password - generates temporary password"""
    check_admin_only(user)
    
    target = await db.users.find_one({"id": user_id, "deleted_at": None}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Generate temporary password
    temp_password = secrets.token_urlsafe(8)
    new_hash = hash_password(temp_password)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": new_hash,
            "force_password_change": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "temp_password": temp_password, "message": f"Senha temporária gerada. O usuário será obrigado a trocar no próximo login."}

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, data: dict, user: Dict = Depends(get_current_user)):
    """Admin edits user (name, email, role, phone, active status)"""
    check_admin_only(user)
    
    target = await db.users.find_one({"id": user_id, "deleted_at": None}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    allowed_fields = {'nome', 'email', 'role', 'telefone', 'active'}
    update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return updated

# ============== UPLOAD ==============

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf']:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido")
    
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return {"url": f"/api/uploads/{filename}", "filename": filename}

@api_router.get("/uploads/{filename}")
async def get_upload(filename: str):
    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(filepath)

# ============== ESTOQUE - CRUD COMPLETO ==============

@api_router.get("/estoque")
async def list_estoque(
    categoria: Optional[str] = None,
    critico: Optional[bool] = None,
    search: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if categoria:
        query['categoria'] = categoria
    
    items = await db.itens_estoque.find(query, {"_id": 0}).sort("nome", 1).to_list(1000)
    
    # Filter critical items
    if critico:
        items = [i for i in items if i.get('quantidade', 0) <= i.get('estoque_minimo', 0)]
    
    # Search filter
    if search:
        search_lower = search.lower()
        items = [i for i in items if search_lower in i.get('nome', '').lower() or search_lower in i.get('sku', '').lower()]
    
    # Add critical flag
    for item in items:
        item['is_critico'] = item.get('quantidade', 0) <= item.get('estoque_minimo', 0)
    
    return items

@api_router.get("/estoque/categorias")
async def list_categorias(user: Dict = Depends(get_current_user)):
    """List all stock categories with count"""
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    
    items = await db.itens_estoque.find(query, {"_id": 0, "categoria": 1}).to_list(1000)
    
    categorias = {}
    for item in items:
        cat = item.get('categoria', 'outros')
        categorias[cat] = categorias.get(cat, 0) + 1
    
    return categorias

@api_router.get("/estoque/{item_id}")
async def get_estoque_item(item_id: str, user: Dict = Depends(get_current_user)):
    item = await db.itens_estoque.find_one({"id": item_id, "deleted_at": None}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Get recent movements
    item['movimentacoes'] = await db.movimentacoes_estoque.find(
        {"item_id": item_id}, {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    item['is_critico'] = item.get('quantidade', 0) <= item.get('estoque_minimo', 0)
    return item

@api_router.post("/estoque")
async def create_estoque(data: EstoqueCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm', 'supervisor'])
    org_id = user.get('organization_id', '')
    
    # Generate SKU if not provided
    sku = data.sku.upper() if data.sku else generate_sku()
    
    # Check SKU uniqueness
    existing = await db.itens_estoque.find_one({"sku": sku, "organization_id": org_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="SKU já existe")
    
    item_id = str(uuid.uuid4())
    item_doc = {
        "id": item_id,
        "sku": sku,
        "nome": data.nome,
        "descricao": data.descricao,
        "categoria": data.categoria or "outro",
        "quantidade": data.quantidade,
        "estoque_minimo": data.estoque_minimo,
        "estoque_maximo": data.estoque_maximo,
        "unidade": data.unidade or "UN",
        "custo_unitario": data.custo_unitario,
        "valor_total": data.quantidade * data.custo_unitario,
        "fornecedor": data.fornecedor,
        "almoxarifado": data.almoxarifado,
        "prateleira": data.prateleira,
        "posicao": data.posicao,
        "alertar_minimo": data.alertar_minimo,
        "item_critico": data.item_critico,
        "organization_id": org_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    
    await db.itens_estoque.insert_one(item_doc)
    await audit_log("create", "estoque", item_id, user, f"Estoque: {item_doc.get('sku','')} {data.nome}")
    
    # Register initial movement if quantity > 0
    if data.quantidade > 0:
        mov_doc = {
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "tipo": "entrada",
            "quantidade": data.quantidade,
            "custo_unitario": data.custo_unitario,
            "motivo": "Estoque inicial",
            "usuario_id": user['id'],
            "organization_id": org_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.movimentacoes_estoque.insert_one(mov_doc)
    
    item_doc.pop('_id', None)
    return item_doc

@api_router.put("/estoque/{item_id}")
async def update_estoque(item_id: str, data: EstoqueUpdate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm', 'supervisor'])
    existing = await db.itens_estoque.find_one({"id": item_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    update_data = {k: v.value if isinstance(v, Enum) else v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Recalculate total value
    if 'quantidade' in update_data or 'custo_unitario' in update_data:
        qty = update_data.get('quantidade', existing.get('quantidade', 0))
        cost = update_data.get('custo_unitario', existing.get('custo_unitario', 0))
        update_data['valor_total'] = qty * cost
    
    await db.itens_estoque.update_one({"id": item_id}, {"$set": update_data})
    
    # Check critical stock
    await verificar_estoque_critico(item_id, existing.get('organization_id', ''))
    
    return await db.itens_estoque.find_one({"id": item_id}, {"_id": 0})

@api_router.delete("/estoque/{item_id}")
async def delete_estoque(item_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    existing = await db.itens_estoque.find_one({"id": item_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    await db.itens_estoque.update_one(
        {"id": item_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    await audit_log("delete", "estoque", item_id, user, f"Item {existing.get('sku')} - {existing.get('nome')} excluído")
    return {"success": True, "message": "Item excluído com sucesso"}


@api_router.get("/movimentacoes")
async def list_movimentacoes(
    item_id: Optional[str] = None,
    ativo_id: Optional[str] = None,
    usuario_id: Optional[str] = None,
    os_id: Optional[str] = None,
    tipo: Optional[str] = None,
    limit: int = 200,
    user: Dict = Depends(get_current_user)
):
    """List stock movements with filters (by item, equipment, user, OS, type)"""
    query = {"organization_id": user.get('organization_id', '')} if user.get('organization_id') else {}
    if item_id:
        query['item_id'] = item_id
    if ativo_id:
        query['ativo_id'] = ativo_id
    if usuario_id:
        query['usuario_id'] = usuario_id
    if os_id:
        query['os_id'] = os_id
    if tipo:
        query['tipo'] = tipo
    
    movs = await db.movimentacoes_estoque.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return movs



@api_router.post("/estoque/{item_id}/movimentacao")
async def criar_movimentacao(
    item_id: str,
    body: MovimentacaoCreateBody,
    user: Dict = Depends(get_current_user)
):
    """Create stock movement (entrada/saida/ajuste)"""
    tipo = body.tipo
    quantidade = body.quantidade
    custo_unitario = body.custo_unitario
    motivo = body.motivo
    item = await db.itens_estoque.find_one({"id": item_id, "deleted_at": None}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    current_qty = item.get('quantidade', 0)
    new_qty = current_qty  # default
    
    if tipo == "entrada":
        new_qty = current_qty + quantidade
    elif tipo == "saida":
        if quantidade > current_qty:
            raise HTTPException(status_code=400, detail="Quantidade insuficiente em estoque")
        new_qty = current_qty - quantidade
    else:  # ajuste
        new_qty = quantidade
    
    # Update stock
    cost = custo_unitario or item.get('custo_unitario', 0)
    await db.itens_estoque.update_one(
        {"id": item_id},
        {"$set": {
            "quantidade": new_qty,
            "valor_total": new_qty * cost,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Register movement
    mov_doc = {
        "id": str(uuid.uuid4()),
        "item_id": item_id,
        "tipo": tipo,
        "quantidade": quantidade if tipo != "saida" else -quantidade,
        "custo_unitario": cost,
        "motivo": motivo,
        "usuario_id": user['id'],
        "organization_id": item.get('organization_id', ''),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.movimentacoes_estoque.insert_one(mov_doc)
    
    # Check critical stock
    await verificar_estoque_critico(item_id, item.get('organization_id', ''))
    
    return {"success": True, "new_quantity": new_qty}


# Default checklist templates
DEFAULT_CHECKLISTS = {
    "mecanica": {
        "nome": "Inspeção Mecânica",
        "itens": [
            {"descricao": "Verificar vibração anormal", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Temperatura do equipamento (°C)", "tipo": "numerico", "unidade": "°C", "tolerancia_min": 20, "tolerancia_max": 80, "obrigatorio": True},
            {"descricao": "Verificar ruídos anormais", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Verificar folgas mecânicas", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Estado das correias/correntes", "tipo": "opcao", "obrigatorio": True},
            {"descricao": "Verificar alinhamento", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Verificar vazamentos", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Estado dos rolamentos", "tipo": "opcao", "obrigatorio": True},
            {"descricao": "Verificar fixação/parafusos", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Observações gerais", "tipo": "texto", "obrigatorio": False},
        ]
    },
    "eletrica": {
        "nome": "Inspeção Elétrica",
        "itens": [
            {"descricao": "Tensão de alimentação (V)", "tipo": "numerico", "unidade": "V", "tolerancia_min": 380, "tolerancia_max": 440, "obrigatorio": True},
            {"descricao": "Corrente de operação (A)", "tipo": "numerico", "unidade": "A", "obrigatorio": True},
            {"descricao": "Verificar aquecimento de cabos", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Estado das conexões elétricas", "tipo": "opcao", "obrigatorio": True},
            {"descricao": "Verificar isolamento", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Estado do quadro elétrico", "tipo": "opcao", "obrigatorio": True},
            {"descricao": "Verificar aterramento", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Testar dispositivos de proteção", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Verificar sinalização", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Observações gerais", "tipo": "texto", "obrigatorio": False},
        ]
    },
    "lubrificacao": {
        "nome": "Inspeção de Lubrificação",
        "itens": [
            {"descricao": "Nível de óleo/graxa", "tipo": "opcao", "obrigatorio": True},
            {"descricao": "Verificar contaminação do lubrificante", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Temperatura do óleo (°C)", "tipo": "numerico", "unidade": "°C", "tolerancia_min": 30, "tolerancia_max": 70, "obrigatorio": True},
            {"descricao": "Ponto de lubrificação acessível", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Tipo de lubrificante correto", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Verificar vazamento de lubrificante", "tipo": "boolean", "obrigatorio": True},
            {"descricao": "Quantidade aplicada (ml/g)", "tipo": "numerico", "unidade": "ml", "obrigatorio": False},
            {"descricao": "Estado dos pontos de graxa (graxeiras)", "tipo": "opcao", "obrigatorio": True},
            {"descricao": "Observações gerais", "tipo": "texto", "obrigatorio": False},
        ]
    }
}

@api_router.get("/checklists/templates")
async def get_checklist_templates(user: Dict = Depends(get_current_user)):
    """Get default editable checklist templates"""
    org_id = user.get('organization_id', '')
    # Check for custom templates first
    custom = await db.checklist_templates.find({"organization_id": org_id, "deleted_at": None}, {"_id": 0}).to_list(10)
    if custom:
        return {t['tipo']: t for t in custom}
    # Return defaults with IDs
    result = {}
    for tipo, template in DEFAULT_CHECKLISTS.items():
        itens = []
        for item in template['itens']:
            itens.append({"id": str(uuid.uuid4()), **item, "valor": None, "conforme": None, "observacao": None})
        result[tipo] = {"tipo": tipo, "nome": template['nome'], "itens": itens}
    return result

@api_router.put("/checklists/templates/{tipo}")
async def update_checklist_template(tipo: str, body: dict, user: Dict = Depends(get_current_user)):
    """Save custom checklist template"""
    check_admin_only(user)
    org_id = user.get('organization_id', '')
    await db.checklist_templates.update_one(
        {"organization_id": org_id, "tipo": tipo},
        {"$set": {"organization_id": org_id, "tipo": tipo, "nome": body.get('nome', ''), "itens": body.get('itens', []), "updated_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None}},
        upsert=True
    )
    return {"success": True}


# ============== TEMPLATES DE INSPEÇÃO POR EQUIPAMENTO ==============

@api_router.get("/inspection-templates")
async def list_inspection_templates(tipo_equipamento: Optional[str] = None, user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None}
    if tipo_equipamento:
        query["tipo_equipamento"] = tipo_equipamento
    templates = await db.inspection_templates.find(query, {"_id": 0}).sort("nome", 1).to_list(200)
    return templates

@api_router.post("/inspection-templates")
async def create_inspection_template(data: InspectionTemplateCreate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    org_id = user.get('organization_id', '')
    itens = []
    for item in data.itens:
        d = item.model_dump()
        d['id'] = str(uuid.uuid4())
        itens.append(d)
    doc = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "nome": data.nome,
        "tipo_equipamento": data.tipo_equipamento,
        "descricao": data.descricao,
        "itens": itens,
        "created_by": user.get('id'),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.inspection_templates.insert_one(doc)
    doc.pop('_id', None)
    return doc

@api_router.get("/inspection-templates/{template_id}")
async def get_inspection_template(template_id: str, user: Dict = Depends(get_current_user)):
    t = await db.inspection_templates.find_one({"id": template_id, "deleted_at": None}, {"_id": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return t

@api_router.put("/inspection-templates/{template_id}")
async def update_inspection_template(template_id: str, data: InspectionTemplateUpdate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    t = await db.inspection_templates.find_one({"id": template_id, "deleted_at": None})
    if not t:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.nome is not None: update['nome'] = data.nome
    if data.tipo_equipamento is not None: update['tipo_equipamento'] = data.tipo_equipamento
    if data.descricao is not None: update['descricao'] = data.descricao
    if data.itens is not None:
        itens = []
        for item in data.itens:
            d = item.model_dump()
            if not d.get('id'): d['id'] = str(uuid.uuid4())
            itens.append(d)
        update['itens'] = itens
    await db.inspection_templates.update_one({"id": template_id}, {"$set": update})
    return await db.inspection_templates.find_one({"id": template_id}, {"_id": 0})

@api_router.delete("/inspection-templates/{template_id}")
async def delete_inspection_template(template_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    await db.inspection_templates.update_one({"id": template_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    return {"success": True}

@api_router.post("/inspection-templates/{template_id}/duplicate")
async def duplicate_inspection_template(template_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    org_id = user.get('organization_id', '')
    original = await db.inspection_templates.find_one({"id": template_id, "deleted_at": None}, {"_id": 0})
    if not original:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    itens = []
    for item in original.get('itens', []):
        itens.append({**item, "id": str(uuid.uuid4())})
    doc = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "nome": f"{original['nome']} (Cópia)",
        "tipo_equipamento": original.get('tipo_equipamento', ''),
        "descricao": original.get('descricao'),
        "itens": itens,
        "created_by": user.get('id'),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.inspection_templates.insert_one(doc)
    doc.pop('_id', None)
    return doc

@api_router.get("/equipment-types")
async def list_equipment_types(user: Dict = Depends(get_current_user)):
    """List distinct equipment types from ativos"""
    org_id = user.get('organization_id', '')
    types = await db.ativos.distinct("tipo_equipamento", {"organization_id": org_id, "deleted_at": None})
    return [t for t in types if t]

# ============== PLANOS DE INSPEÇÃO (Novo Sistema) ==============

@api_router.get("/planos-inspecao")
async def list_planos_inspecao(
    tipo_equipamento: Optional[str] = None,
    ativo_id: Optional[str] = None,
    categoria: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None}
    if tipo_equipamento:
        query['tipo_equipamento'] = tipo_equipamento
    if ativo_id:
        query['ativo_id'] = ativo_id
    if categoria:
        query['categoria'] = categoria
    planos = await db.planos_inspecao.find(query, {"_id": 0}).sort("categoria", 1).to_list(500)
    return planos

@api_router.post("/planos-inspecao")
async def create_plano_inspecao(data: PlanoInspecaoCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    org_id = user.get('organization_id', '')
    perguntas = []
    for i, p in enumerate(data.perguntas):
        d = p.model_dump()
        d['id'] = str(uuid.uuid4())
        d['ordem'] = d.get('ordem', 0) or i
        perguntas.append(d)
    doc = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "tipo_equipamento": data.tipo_equipamento,
        "ativo_id": data.ativo_id,
        "categoria": data.categoria,
        "nome": data.nome,
        "perguntas": perguntas,
        "created_by": user.get('id'),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.planos_inspecao.insert_one(doc)
    await audit_log("create", "plano_inspecao", doc['id'], user, f"Plano: {data.nome} ({data.categoria})")
    doc.pop('_id', None)
    return doc

@api_router.put("/planos-inspecao/{plano_id}")
async def update_plano_inspecao(plano_id: str, data: PlanoInspecaoUpdate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    existing = await db.planos_inspecao.find_one({"id": plano_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.nome is not None:
        update['nome'] = data.nome
    if data.perguntas is not None:
        perguntas = []
        for i, p in enumerate(data.perguntas):
            d = p.model_dump()
            if not d.get('id'):
                d['id'] = str(uuid.uuid4())
            d['ordem'] = d.get('ordem', 0) or i
            perguntas.append(d)
        update['perguntas'] = perguntas
    await db.planos_inspecao.update_one({"id": plano_id}, {"$set": update})
    await audit_log("update", "plano_inspecao", plano_id, user, f"Plano editado: {existing.get('nome','')}")
    return await db.planos_inspecao.find_one({"id": plano_id}, {"_id": 0})

@api_router.delete("/planos-inspecao/{plano_id}")
async def delete_plano_inspecao(plano_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    await db.planos_inspecao.update_one({"id": plano_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "plano_inspecao", plano_id, user, "Plano excluído")
    return {"success": True}

@api_router.get("/planos-inspecao/resolver")
async def resolver_plano_inspecao(ativo_id: str, categoria: str, user: Dict = Depends(get_current_user)):
    """Resolve inspection plan: merges equipment-type plan (Level 1) + asset-specific plan (Level 2)"""
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    org_id = user.get('organization_id', '')
    tipo_equip = ativo.get('tipo_equipamento', '')
    
    # Level 1: Plan by equipment type
    plano_tipo = await db.planos_inspecao.find_one(
        {"organization_id": org_id, "tipo_equipamento": tipo_equip, "ativo_id": None, "categoria": categoria, "deleted_at": None},
        {"_id": 0}
    )
    
    # Level 2: Asset-specific plan  
    plano_ativo = await db.planos_inspecao.find_one(
        {"organization_id": org_id, "ativo_id": ativo_id, "categoria": categoria, "deleted_at": None},
        {"_id": 0}
    )
    
    # Merge questions
    perguntas = []
    if plano_tipo:
        for p in plano_tipo.get('perguntas', []):
            perguntas.append({**p, "origem": "tipo_equipamento", "plano_id": plano_tipo['id']})
    if plano_ativo:
        for p in plano_ativo.get('perguntas', []):
            perguntas.append({**p, "origem": "ativo_especifico", "plano_id": plano_ativo['id']})
    
    # Fallback to default checklists if no plans exist
    if not perguntas and categoria in DEFAULT_CHECKLISTS:
        for item in DEFAULT_CHECKLISTS[categoria]['itens']:
            perguntas.append({"id": str(uuid.uuid4()), **item, "origem": "padrao", "plano_id": None,
                "periodicidade": None, "foto_obrigatoria_nc": False, "limite_normal": None, "limite_alerta": None, "limite_critico": None, "opcoes": None, "ordem": 0})
    
    # Sort by ordem
    perguntas.sort(key=lambda x: x.get('ordem', 0))
    
    return {
        "ativo_id": ativo_id,
        "ativo_tag": ativo.get('tag'),
        "tipo_equipamento": tipo_equip,
        "categoria": categoria,
        "plano_tipo": plano_tipo.get('id') if plano_tipo else None,
        "plano_ativo": plano_ativo.get('id') if plano_ativo else None,
        "perguntas": perguntas,
        "total_perguntas": len(perguntas)
    }

@api_router.post("/planos-inspecao/migrar")
async def migrar_templates_para_planos(user: Dict = Depends(get_current_user)):
    """Migrate DEFAULT_CHECKLISTS and existing inspection_templates to planos_inspecao"""
    check_write_permission(user, ['admin'])
    org_id = user.get('organization_id', '')
    migrated = 0
    
    # Migrate DEFAULT_CHECKLISTS as universal plans (no tipo_equipamento)
    for cat, template in DEFAULT_CHECKLISTS.items():
        existing = await db.planos_inspecao.find_one(
            {"organization_id": org_id, "categoria": cat, "tipo_equipamento": None, "ativo_id": None, "deleted_at": None}
        )
        if not existing:
            perguntas = []
            for i, item in enumerate(template['itens']):
                perguntas.append({
                    "id": str(uuid.uuid4()), "descricao": item['descricao'], "tipo": item.get('tipo', 'boolean'),
                    "obrigatorio": item.get('obrigatorio', True), "unidade": item.get('unidade'),
                    "limite_normal": item.get('tolerancia_max'), "limite_alerta": None, "limite_critico": None,
                    "periodicidade": None, "foto_obrigatoria_nc": False,
                    "opcoes": None, "ordem": i
                })
            doc = {
                "id": str(uuid.uuid4()), "organization_id": org_id,
                "tipo_equipamento": None, "ativo_id": None,
                "categoria": cat, "nome": template['nome'],
                "perguntas": perguntas,
                "created_by": user.get('id'),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "deleted_at": None
            }
            await db.planos_inspecao.insert_one(doc)
            migrated += 1
    
    # Migrate existing inspection_templates
    old_templates = await db.inspection_templates.find({"organization_id": org_id, "deleted_at": None}, {"_id": 0}).to_list(200)
    for tmpl in old_templates:
        perguntas = []
        for i, item in enumerate(tmpl.get('itens', [])):
            perguntas.append({
                "id": item.get('id', str(uuid.uuid4())), "descricao": item.get('descricao', ''),
                "tipo": item.get('tipo', 'boolean'), "obrigatorio": item.get('obrigatorio', True),
                "unidade": item.get('unidade'), "limite_normal": item.get('tolerancia_max'),
                "limite_alerta": None, "limite_critico": None,
                "periodicidade": None, "foto_obrigatoria_nc": False,
                "opcoes": item.get('opcoes'), "ordem": i
            })
        doc = {
            "id": str(uuid.uuid4()), "organization_id": org_id,
            "tipo_equipamento": tmpl.get('tipo_equipamento'), "ativo_id": None,
            "categoria": tmpl.get('categoria', 'mecanica'), "nome": tmpl.get('nome', ''),
            "perguntas": perguntas,
            "created_by": user.get('id'),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.planos_inspecao.insert_one(doc)
        migrated += 1
    
    await audit_log("migrate", "plano_inspecao", "all", user, f"Migração: {migrated} planos criados")
    return {"migrated": migrated}

@api_router.get("/planos-inspecao/categorias-disponiveis")
async def categorias_disponiveis(ativo_id: str, user: Dict = Depends(get_current_user)):
    """List which inspection categories are available for an asset (has plans configured)"""
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        return []
    org_id = user.get('organization_id', '')
    tipo_equip = ativo.get('tipo_equipamento', '')
    
    result = []
    for cat in ['mecanica', 'eletrica', 'lubrificacao']:
        has_plan = await db.planos_inspecao.find_one(
            {"organization_id": org_id, "deleted_at": None, "categoria": cat,
             "$or": [{"tipo_equipamento": tipo_equip, "ativo_id": None}, {"ativo_id": ativo_id}]},
            {"_id": 0, "id": 1}
        )
        # Also check defaults
        has_default = cat in DEFAULT_CHECKLISTS
        result.append({"categoria": cat, "disponivel": bool(has_plan) or has_default})
    return result

@api_router.get("/inspecoes")
async def list_inspecoes(
    status: Optional[InspecaoStatus] = None,
    ativo_id: Optional[str] = None,
    responsavel_id: Optional[str] = None,
    sector_id: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if status:
        query['status'] = status.value
    if ativo_id:
        query['ativo_id'] = ativo_id
    if responsavel_id:
        query['responsavel_id'] = responsavel_id
    
    if sector_id:
        asset_ids = await get_scoped_asset_ids(user.get('organization_id', ''), sector_id=sector_id)
        if asset_ids is not None:
            query['ativo_id'] = {"$in": asset_ids}
    
    inspecoes = await db.inspecoes.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    for insp in inspecoes:
        ativo = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1, "sector_id": 1})
        if ativo and ativo.get('sector_id'):
            sector = await db.sectors.find_one({"id": ativo['sector_id']}, {"_id": 0, "nome": 1})
            ativo['sector'] = sector
        insp['ativo'] = ativo
        if insp.get('responsavel_id'):
            resp = await db.users.find_one({"id": insp['responsavel_id']}, {"_id": 0, "nome": 1})
            insp['responsavel'] = resp
        if insp.get('rota_id'):
            rota = await db.rotas_inspecao.find_one({"id": insp['rota_id']}, {"_id": 0, "nome": 1})
            insp['rota'] = rota
    
    return inspecoes

@api_router.get("/inspecoes/{inspecao_id}")
async def get_inspecao(inspecao_id: str, user: Dict = Depends(get_current_user)):
    insp = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None}, {"_id": 0})
    if not insp:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    
    insp['ativo'] = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0})
    if insp.get('ativo') and insp['ativo'].get('sector_id'):
        insp['ativo']['sector'] = await db.sectors.find_one({"id": insp['ativo']['sector_id']}, {"_id": 0, "nome": 1})
    if insp.get('responsavel_id'):
        insp['responsavel'] = await db.users.find_one({"id": insp['responsavel_id']}, {"_id": 0, "nome": 1, "email": 1})
    if insp.get('rota_id'):
        insp['rota'] = await db.rotas_inspecao.find_one({"id": insp['rota_id']}, {"_id": 0})
    if insp.get('os_gerada_id'):
        os_gerada = await db.ordens_servico.find_one({"id": insp['os_gerada_id']}, {"_id": 0, "id": 1, "numero": 1, "status": 1, "titulo": 1, "responsavel_id": 1})
        if os_gerada and os_gerada.get('responsavel_id'):
            resp = await db.users.find_one({"id": os_gerada['responsavel_id']}, {"_id": 0, "nome": 1})
            os_gerada['responsavel_nome'] = resp.get('nome') if resp else None
        insp['os_gerada'] = os_gerada
    # Also find all OS linked to this inspection (via inspecao_origem_id)
    os_vinculadas = await db.ordens_servico.find(
        {"inspecao_origem_id": inspecao_id, "deleted_at": None},
        {"_id": 0, "id": 1, "numero": 1, "status": 1, "titulo": 1, "responsavel_id": 1}
    ).to_list(50)
    for os_v in os_vinculadas:
        if os_v.get('responsavel_id'):
            resp = await db.users.find_one({"id": os_v['responsavel_id']}, {"_id": 0, "nome": 1})
            os_v['responsavel_nome'] = resp.get('nome') if resp else None
    insp['os_vinculadas'] = os_vinculadas
    # Anomalias vinculadas ao ativo (from this inspection period)
    # Histórico (audit log)
    insp['historico'] = await db.audit_logs.find(
        {"entity_type": "inspecoes", "entity_id": inspecao_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    # Enrich actor names
    for field in ['criado_por', 'iniciado_por', 'concluido_por', 'alterado_por']:
        uid = insp.get(field)
        if uid:
            u = await db.users.find_one({"id": uid}, {"_id": 0, "nome": 1})
            insp[f'{field}_nome'] = u.get('nome') if u else uid
    # Enrich executantes
    exec_ids = insp.get('executantes', [])
    if exec_ids:
        exec_users = await db.users.find({"id": {"$in": exec_ids}}, {"_id": 0, "id": 1, "nome": 1}).to_list(len(exec_ids))
        insp['executantes_nomes'] = {u['id']: u.get('nome') for u in exec_users}
    
    return insp

@api_router.post("/inspecoes")
async def create_inspecao(data: InspecaoCreate, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    org_id = ativo.get('organization_id', user.get('organization_id', ''))
    
    tipo_str = data.tipo.value if hasattr(data.tipo, 'value') else str(data.tipo)
    checklist = data.checklist or []
    
    # Check if checklist has user responses (from Ronda mode)
    has_responses = any(
        item.get('conforme') is not None or item.get('valor') is not None
        for item in (c.model_dump() if hasattr(c, 'model_dump') else c for c in checklist)
    ) if checklist else False

    if tipo_str == "lubrificacao" and not has_responses:
        # Only build default lubrificação checklist if no user responses
        checklist = [
            {"id": str(uuid.uuid4()), "descricao": "Ponto de lubrificação acessível", "tipo": "boolean", "obrigatorio": True},
            {"id": str(uuid.uuid4()), "descricao": "Área limpa antes da aplicação", "tipo": "boolean", "obrigatorio": True},
            {"id": str(uuid.uuid4()), "descricao": "Lubrificante aplicado corretamente", "tipo": "boolean", "obrigatorio": True},
            {"id": str(uuid.uuid4()), "descricao": "Sem vazamentos após aplicação", "tipo": "boolean", "obrigatorio": True},
            {"id": str(uuid.uuid4()), "descricao": "Quantidade aplicada (ml/g)", "tipo": "numero", "unidade": data.quantidade_lubrificante or "ml", "obrigatorio": False},
            {"id": str(uuid.uuid4()), "descricao": "Observações", "tipo": "texto", "obrigatorio": False},
        ]
    elif data.rota_id and not checklist:
        rota = await db.rotas_inspecao.find_one({"id": data.rota_id}, {"_id": 0})
        if rota:
            checklist = rota.get('itens', [])
    
    # Default checklist for regular inspection if none
    if not checklist:
        if data.frequencia == "diaria":
            checklist = [
                {"id": str(uuid.uuid4()), "descricao": "Vibração normal", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Temperatura normal", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Sem ruídos anormais", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Sem vazamentos", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        elif data.frequencia == "quinzenal":
            checklist = [
                {"id": str(uuid.uuid4()), "descricao": "Vibração normal", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Temperatura normal", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Sem ruídos anormais", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Sem vazamentos", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Nível de óleo adequado", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Fixações e parafusos OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        elif data.frequencia == "mensal":
            checklist = [
                {"id": str(uuid.uuid4()), "descricao": "Vibração (mm/s)", "tipo": "numero", "tolerancia_min": 0, "tolerancia_max": 4.5, "unidade": "mm/s", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Temperatura (°C)", "tipo": "numero", "tolerancia_min": 20, "tolerancia_max": 80, "unidade": "°C", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Sem ruídos anormais", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Sem vazamentos", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Nível de óleo adequado", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Alinhamento verificado", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Fixações e parafusos OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Correias/acoplamentos OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        else:
            checklist = [
                {"id": str(uuid.uuid4()), "descricao": "Vibração OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Temperatura OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Ruído OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Vazamento OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
    
    # Serialize checklist items to dicts
    checklist_dicts = []
    for item in checklist:
        if hasattr(item, 'model_dump'):
            checklist_dicts.append(item.model_dump())
        elif isinstance(item, dict):
            checklist_dicts.append(item)
        else:
            checklist_dicts.append(dict(item))
    checklist = checklist_dicts
    
    # Auto-conclude if checklist has user responses (Ronda mode)
    nao_conformes = [item for item in checklist if item.get('conforme') is False]
    if has_responses:
        resultado = "nao_conforme" if nao_conformes else "conforme"
        status = "com_pendencias" if nao_conformes else "concluida"
        data_conclusao = datetime.now(timezone.utc).isoformat()
    else:
        resultado = "pendente"
        status = "pendente"
        data_conclusao = None
    
    insp_id = str(uuid.uuid4())
    insp_doc = {
        "id": insp_id,
        "ativo_id": data.ativo_id,
        "rota_id": data.rota_id,
        "responsavel_id": data.responsavel_id,
        "organization_id": org_id,
        "tipo": tipo_str,
        "frequencia": data.frequencia,
        "status": status,
        "resultado": resultado,
        "checklist": checklist,
        "data_programada": data.data_planejada or datetime.now(timezone.utc).isoformat(),
        "data_inicio": datetime.now(timezone.utc).isoformat() if has_responses else None,
        "data_conclusao": data_conclusao,
        "duracao_minutos": None,
        "observacoes": data.observacoes,
        "fotos": [],
        "os_gerada_id": None,
        "tipo_lubrificante": data.tipo_lubrificante,
        "quantidade_lubrificante": data.quantidade_lubrificante,
        "ponto_lubrificacao": data.ponto_lubrificacao,
        "metodo_aplicacao": data.metodo_aplicacao,
        "observacoes_lubrificacao": data.observacoes_lubrificacao,
        "criado_por": user.get('id'),
        "concluido_por": user.get('id') if has_responses else None,
        "executantes": data.executantes or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    
    await db.inspecoes.insert_one(insp_doc)
    await audit_log("create", "inspecoes", insp_id, user, f"Inspeção {tipo_str}: {ativo.get('tag','')}")
    
    # Auto-generate OS for non-conformities in Ronda mode
    if has_responses and nao_conformes:
        numero = await generate_os_numero(org_id)
        descricao_itens = "\n".join([f"- {item.get('descricao', '')}: {item.get('observacao', 'Não conforme')}" for item in nao_conformes])
        os_id = str(uuid.uuid4())
        os_doc = {
            "id": os_id, "numero": numero, "ativo_id": data.ativo_id,
            "organization_id": org_id, "tipo": "corretiva", "prioridade": "media",
            "titulo": f"Correção - Inspeção {ativo.get('tag', '')}",
            "descricao": f"OS gerada automaticamente por inspeção não conforme.\n\nItens não conformes:\n{descricao_itens}",
            "status": "aberta", "responsavel_id": None, "inspecao_origem_id": insp_id,
            "data_abertura": datetime.now(timezone.utc).isoformat(),
            "custo_pecas": 0, "custo_mao_obra": 0, "custo_total": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(), "deleted_at": None
        }
        await db.ordens_servico.insert_one(os_doc)
        await db.inspecoes.update_one({"id": insp_id}, {"$set": {"os_gerada_id": os_id}})
        insp_doc['os_gerada_id'] = os_id
    
    # Notify responsible (only if assigned and not auto-concluded)
    if data.responsavel_id and not has_responses:
        await criar_notificacao(
            data.responsavel_id, org_id, NotificacaoTipo.INSPECAO_PENDENTE,
            f"Nova inspeção: {ativo.get('tag', '')}",
            f"Inspeção programada para {ativo.get('nome', '')}",
            f"/inspecoes/{insp_id}"
        )
    
    insp_doc.pop('_id', None)
    return insp_doc

@api_router.put("/inspecoes/{inspecao_id}")
async def update_inspecao(inspecao_id: str, data: InspecaoUpdate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    existing = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    
    update_data = {k: v.value if isinstance(v, Enum) else v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['alterado_por'] = user.get('id')
    
    await db.inspecoes.update_one({"id": inspecao_id}, {"$set": update_data})
    return await db.inspecoes.find_one({"id": inspecao_id}, {"_id": 0})

@api_router.delete("/inspecoes/{inspecao_id}")
async def delete_inspecao(inspecao_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor'])
    existing = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    
    await db.inspecoes.update_one(
        {"id": inspecao_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "message": "Inspeção excluída com sucesso"}

@api_router.post("/inspecoes/{inspecao_id}/iniciar")
async def iniciar_inspecao(inspecao_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor', 'tecnico'])
    await db.inspecoes.update_one(
        {"id": inspecao_id},
        {"$set": {
            "status": "em_andamento",
            "data_inicio": datetime.now(timezone.utc).isoformat(),
            "iniciado_por": user.get('id'),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"success": True}


@api_router.post("/inspecoes/{inspecao_id}/concluir")
async def concluir_inspecao(
    inspecao_id: str,
    body: ConcluirInspecaoBody,
    user: Dict = Depends(get_current_user)
):
    check_write_permission(user, ['admin', 'supervisor', 'tecnico'])
    checklist = body.checklist
    observacoes = body.observacoes
    insp = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None}, {"_id": 0})
    if not insp:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    
    # Determine result
    # Safely check conforme - treat missing/None as neutral
    nao_conformes = [item for item in checklist if item.get('conforme') is False]
    resultado = "nao_conforme" if nao_conformes else "conforme"
    status = "com_pendencias" if nao_conformes else "concluida"
    
    # Calculate duration
    duracao = None
    if insp.get('data_inicio'):
        try:
            start_str = insp['data_inicio']
            if isinstance(start_str, str):
                start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                duracao = int((datetime.now(timezone.utc) - start).total_seconds() / 60)
        except (ValueError, TypeError):
            duracao = None
    
    update_data = {
        "status": status,
        "resultado": resultado,
        "checklist": checklist,
        "observacoes": observacoes,
        "data_conclusao": datetime.now(timezone.utc).isoformat(),
        "duracao_minutos": duracao,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    os_gerada_id = None
    
    # Create OS if non-conformities found
    if nao_conformes:
        ativo = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0})
        org_id = insp.get('organization_id', '')
        numero = await generate_os_numero(org_id)
        
        descricao_itens = "\n".join([f"- {item.get('descricao', '')}: {item.get('observacao', 'Não conforme')}" for item in nao_conformes])
        
        os_id = str(uuid.uuid4())
        os_doc = {
            "id": os_id,
            "numero": numero,
            "ativo_id": insp.get('ativo_id'),
            "organization_id": org_id,
            "tipo": "corretiva",
            "prioridade": "media",
            "titulo": f"Correção - Inspeção #{inspecao_id[:8]}",
            "descricao": f"OS gerada automaticamente por inspeção não conforme.\n\nItens não conformes:\n{descricao_itens}",
            "status": "aberta",
            "responsavel_id": None,
            "inspecao_origem_id": inspecao_id,
            "data_abertura": datetime.now(timezone.utc).isoformat(),
            "custo_pecas": 0,
            "custo_mao_obra": 0,
            "custo_total": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        
        await db.ordens_servico.insert_one(os_doc)
        os_gerada_id = os_id
        update_data['os_gerada_id'] = os_id
        
        # Update asset status
        # Notify admins about non-conformity
        admins = await db.users.find(
            {"organization_id": org_id, "role": {"$in": ["admin", "supervisor"]}, "deleted_at": None},
            {"_id": 0, "id": 1}
        ).to_list(10)
        for admin in admins:
            await criar_notificacao(
                admin['id'], org_id, NotificacaoTipo.ANOMALIA,
                f"Falha detectada: {ativo.get('tag', '')}",
                f"Inspeção não conforme - OS #{numero} gerada",
                f"/os/{os_id}"
            )
    
    update_data['concluido_por'] = user.get('id')
    
    await db.inspecoes.update_one({"id": inspecao_id}, {"$set": update_data})
    
    return {
        "success": True,
        "resultado": resultado,
        "nao_conformes": len(nao_conformes),
        "os_gerada_id": os_gerada_id,
        "duracao_minutos": duracao
    }

# ============== ROTAS DE INSPEÇÃO ==============

@api_router.get("/rotas-inspecao")
async def list_rotas(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None, "ativa": True}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    return await db.rotas_inspecao.find(query, {"_id": 0}).to_list(100)

@api_router.get("/rotas-inspecao/{rota_id}")
async def get_rota(rota_id: str, user: Dict = Depends(get_current_user)):
    rota = await db.rotas_inspecao.find_one({"id": rota_id, "deleted_at": None}, {"_id": 0})
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    return rota

@api_router.post("/rotas-inspecao")
async def create_rota(data: RotaInspecaoCreate, user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    
    rota_id = str(uuid.uuid4())
    rota_doc = {
        "id": rota_id,
        "nome": data.nome,
        "descricao": data.descricao,
        "tipo_ativo": data.tipo_ativo,
        "frequencia": data.frequencia,
        "tempo_estimado_minutos": data.tempo_estimado_minutos,
        "itens": [item if isinstance(item, dict) else item for item in data.itens],
        "ativa": data.ativa,
        "organization_id": org_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    
    await db.rotas_inspecao.insert_one(rota_doc)
    rota_doc.pop('_id', None)
    return rota_doc

# ============== RONDA ==============

@api_router.get("/rondas")
async def list_rondas(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None, "is_active": {"$ne": False}}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    sectors = await db.sectors.find(query, {"_id": 0}).sort("nome", 1).to_list(100)
    
    result = []
    for sector in sectors:
        ativos_count = await db.ativos.count_documents({"sector_id": sector['id'], "deleted_at": None})
        # Count pending inspections for assets in this sector
        asset_ids = [a['id'] for a in await db.ativos.find({"sector_id": sector['id'], "deleted_at": None}, {"_id": 0, "id": 1}).to_list(500)]
        insp_pendentes = 0
        if asset_ids:
            insp_pendentes = await db.inspecoes.count_documents({
                "ativo_id": {"$in": asset_ids},
                "status": {"$in": ["pendente", "em_andamento"]},
                "deleted_at": None
            })
        result.append({"area": sector, "total_ativos": ativos_count, "inspecoes_pendentes": insp_pendentes})
    
    return result

@api_router.get("/ronda/{area_id}")
async def get_ronda(area_id: str, user: Dict = Depends(get_current_user)):
    area = await db.sectors.find_one({"id": area_id, "deleted_at": None}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    
    ativos = await db.ativos.find({"sector_id": area_id, "deleted_at": None}, {"_id": 0}).sort("tag", 1).to_list(500)
    
    ronda_ativos = []
    for idx, ativo in enumerate(ativos):
        ultima_insp = await db.inspecoes.find_one(
            {"ativo_id": ativo['id'], "deleted_at": None},
            {"_id": 0, "tipo": 1, "status": 1, "resultado": 1, "created_at": 1},
            sort=[("created_at", -1)]
        )
        insp_pendente = await db.inspecoes.find_one(
            {"ativo_id": ativo['id'], "status": {"$in": ["pendente", "em_andamento"]}, "deleted_at": None}
        )
        ronda_ativos.append({
            "ativo": ativo,
            "ultima_inspecao": ultima_insp,
            "tem_pendente": insp_pendente is not None,
            "ordem": idx + 1
        })
    
    # Sort: pending first, then by tag
    ronda_ativos.sort(key=lambda x: (0 if x['tem_pendente'] else 1, x['ativo'].get('tag', '')))
    
    return {"area_id": area_id, "area_nome": area['nome'], "total_ativos": len(ronda_ativos), "ativos": ronda_ativos}

# ============== NOTIFICAÇÕES ==============

@api_router.get("/notificacoes")
async def list_notificacoes(lida: Optional[bool] = None, user: Dict = Depends(get_current_user)):
    query = {"usuario_id": user['id']}
    if lida is not None:
        query['lida'] = lida
    return await db.notificacoes.find(query, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)

@api_router.get("/notificacoes/count")
async def count_notificacoes(user: Dict = Depends(get_current_user)):
    count = await db.notificacoes.count_documents({"usuario_id": user['id'], "lida": False})
    return {"count": count}

@api_router.put("/notificacoes/{notif_id}/lida")
async def marcar_lida(notif_id: str, user: Dict = Depends(get_current_user)):
    await db.notificacoes.update_one({"id": notif_id, "usuario_id": user['id']}, {"$set": {"lida": True}})
    return {"success": True}

@api_router.put("/notificacoes/marcar-todas-lidas")
async def marcar_todas_lidas(user: Dict = Depends(get_current_user)):
    await db.notificacoes.update_many({"usuario_id": user['id'], "lida": False}, {"$set": {"lida": True}})
    return {"success": True}

# ============== USERS ==============

@api_router.get("/users")
async def list_users(role: Optional[UserRole] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if role:
        query['role'] = role.value
    return await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(100)

@api_router.get("/users/tecnicos")
async def list_tecnicos(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None, "role": {"$in": ["tecnico", "inspetor", "supervisor"]}}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    return await db.users.find(query, {"_id": 0, "id": 1, "nome": 1, "email": 1, "telefone": 1, "role": 1}).to_list(100)

# ============== SEED ==============

@api_router.post("/seed")
async def seed_data():
    existing = await db.organizations.find_one({"nome": "Indústria Demo"})
    if existing:
        return {"message": "Dados já existem"}
    
    # Organization
    org = Organization(nome="Indústria Demo", cnpj="00.000.000/0001-00")
    org_doc = org.model_dump()
    org_doc['created_at'] = org_doc['created_at'].isoformat()
    await db.organizations.insert_one(org_doc)
    
    # Users
    users_data = [
        {"email": "admin@manutrix.com", "nome": "Carlos Administrador", "role": "admin", "password": "admin123"},
        {"email": "supervisor@manutrix.com", "nome": "Maria Supervisora", "role": "supervisor", "password": "supervisor123", "telefone": "(11) 98765-4321"},
        {"email": "tecnico@manutrix.com", "nome": "João Técnico", "role": "tecnico", "password": "tecnico123", "telefone": "(11) 91234-5678"},
        {"email": "pedro@manutrix.com", "nome": "Pedro Santos", "role": "tecnico", "password": "pedro123", "telefone": "(11) 99999-8888"},
    ]
    
    users = []
    for ud in users_data:
        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "email": ud['email'],
            "nome": ud['nome'],
            "role": ud['role'],
            "organization_id": org.id,
            "telefone": ud.get('telefone'),
            "password_hash": hash_password(ud['password']),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.users.insert_one(user_doc)
        users.append(user_doc)
    
    # Sectors (top-level, no Plants)
    sectors_data = [
        {"nome": "Britagem Primária", "codigo": "BRIT1", "cor": "#ef4444", "descricao": "Britagem primária de minério"},
        {"nome": "Moagem", "codigo": "MOAG", "cor": "#3b82f6", "descricao": "Moagem e classificação"},
        {"nome": "Oficina Mecânica", "codigo": "OFMEC", "cor": "#f59e0b", "descricao": "Oficina de manutenção mecânica"},
        {"nome": "Utilidades", "codigo": "UTIL", "cor": "#10b981", "descricao": "Sistemas de água, ar e energia"},
    ]
    
    sectors = []
    for sd in sectors_data:
        sector_id = str(uuid.uuid4())
        sector_doc = {
            "id": sector_id,
            "organization_id": org.id,
            "codigo": sd['codigo'],
            "nome": sd['nome'],
            "descricao": sd['descricao'],
            "cor": sd['cor'],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.sectors.insert_one(sector_doc)
        sectors.append(sector_doc)
    
    # Ativos
    ativos_data = [
        {"tag": "BOM-001", "nome": "Bomba Centrífuga 01", "tipo": "Bomba", "fabricante": "KSB", "modelo": "Meganorm 50-200", "area_idx": 0},
        {"tag": "BOM-002", "nome": "Bomba Centrífuga 02", "tipo": "Bomba", "fabricante": "KSB", "modelo": "Meganorm 40-160", "area_idx": 0},
        {"tag": "CMP-001", "nome": "Compressor de Ar", "tipo": "Compressor", "fabricante": "Atlas Copco", "modelo": "GA 30+", "area_idx": 3},
        {"tag": "EST-001", "nome": "Esteira Transportadora 01", "tipo": "Esteira", "fabricante": "Rexnord", "modelo": "FlatTop 2010", "area_idx": 1},
        {"tag": "MIS-001", "nome": "Misturador Industrial", "tipo": "Misturador", "fabricante": "Ekato", "modelo": "HWL", "area_idx": 1},
        {"tag": "TOR-001", "nome": "Torno Mecânico", "tipo": "Máquina Ferramenta", "fabricante": "Romi", "modelo": "Tormax 30A", "area_idx": 2},
        {"tag": "FRE-001", "nome": "Fresadora CNC", "tipo": "Máquina Ferramenta", "fabricante": "Romi", "modelo": "D 800", "area_idx": 2},
    ]
    
    ativos = []
    for ad in ativos_data:
        ativo_id = str(uuid.uuid4())
        sector = sectors[ad['area_idx']]
        ativo_doc = {
            "id": ativo_id,
            "tag": ad['tag'],
            "qr_code": str(uuid.uuid4()),
            "nome": ad['nome'],
            "tipo_equipamento": ad['tipo'],
            "fabricante": ad.get('fabricante'),
            "modelo": ad.get('modelo'),
            "sector_id": sector['id'],
            "organization_id": org.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.ativos.insert_one(ativo_doc)
        ativos.append(ativo_doc)
    
    # Rotas de Inspeção
    rotas_data = [
        {
            "nome": "Inspeção Diária - Bomba",
            "tipo_ativo": "bomba",
            "frequencia": "diaria",
            "tempo": 10,
            "itens": [
                {"id": str(uuid.uuid4()), "descricao": "Vibração normal", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Sem vazamentos", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Ruído normal", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Temperatura OK", "tipo": "boolean", "obrigatorio": True},
            ]
        },
        {
            "nome": "Inspeção Mensal - Bomba",
            "tipo_ativo": "bomba",
            "frequencia": "mensal",
            "tempo": 30,
            "itens": [
                {"id": str(uuid.uuid4()), "descricao": "Vibração (mm/s)", "tipo": "numero", "tolerancia_min": 0, "tolerancia_max": 4.5, "unidade": "mm/s", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Temperatura motor (°C)", "tipo": "numero", "tolerancia_min": 40, "tolerancia_max": 80, "unidade": "°C", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Nível de óleo OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Alinhamento OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        },
        {
            "nome": "Inspeção Semanal - Compressor",
            "tipo_ativo": "compressor",
            "frequencia": "semanal",
            "tempo": 20,
            "itens": [
                {"id": str(uuid.uuid4()), "descricao": "Pressão de trabalho (bar)", "tipo": "numero", "tolerancia_min": 7, "tolerancia_max": 10, "unidade": "bar", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Nível de óleo OK", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Purgar condensado", "tipo": "boolean", "obrigatorio": True},
                {"id": str(uuid.uuid4()), "descricao": "Filtro de ar limpo", "tipo": "boolean", "obrigatorio": True},
            ]
        },
    ]
    
    for rd in rotas_data:
        rota_id = str(uuid.uuid4())
        rota_doc = {
            "id": rota_id,
            "nome": rd['nome'],
            "tipo_ativo": rd['tipo_ativo'],
            "frequencia": rd['frequencia'],
            "tempo_estimado_minutos": rd['tempo'],
            "itens": rd['itens'],
            "ativa": True,
            "organization_id": org.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.rotas_inspecao.insert_one(rota_doc)
    
    # Estoque
    estoque_data = [
        {"sku": "ROL-6205", "nome": "Rolamento 6205-2RS", "categoria": "rolamento", "qtd": 15, "min": 5, "custo": 45, "local": "A-01"},
        {"sku": "ROL-6305", "nome": "Rolamento 6305-2RS", "categoria": "rolamento", "qtd": 8, "min": 3, "custo": 65, "local": "A-01"},
        {"sku": "OLE-HID", "nome": "Óleo Hidráulico 20L", "categoria": "lubrificante", "qtd": 8, "min": 3, "custo": 180, "local": "B-02"},
        {"sku": "OLE-MOT", "nome": "Óleo Motor SAE 40 5L", "categoria": "lubrificante", "qtd": 12, "min": 4, "custo": 85, "local": "B-02"},
        {"sku": "VED-BOM", "nome": "Kit Vedação Bomba KSB", "categoria": "vedacao", "qtd": 10, "min": 4, "custo": 120, "local": "C-03"},
        {"sku": "COR-A68", "nome": "Correia V A-68", "categoria": "correia", "qtd": 6, "min": 2, "custo": 35, "local": "D-01"},
        {"sku": "COR-B75", "nome": "Correia V B-75", "categoria": "correia", "qtd": 4, "min": 2, "custo": 42, "local": "D-01"},
        {"sku": "FIL-AR", "nome": "Filtro de Ar Compressor", "categoria": "filtro", "qtd": 3, "min": 2, "custo": 250, "local": "E-01"},
        {"sku": "FIL-OLE", "nome": "Filtro de Óleo Compressor", "categoria": "filtro", "qtd": 2, "min": 2, "custo": 180, "local": "E-01", "critico": True},
        {"sku": "GRX-MP2", "nome": "Graxa MP2 Multiuso 1kg", "categoria": "lubrificante", "qtd": 20, "min": 5, "custo": 35, "local": "B-03"},
    ]
    
    for ed in estoque_data:
        item_id = str(uuid.uuid4())
        item_doc = {
            "id": item_id,
            "sku": ed['sku'],
            "nome": ed['nome'],
            "categoria": ed['categoria'],
            "quantidade": ed['qtd'],
            "estoque_minimo": ed['min'],
            "unidade": "UN",
            "custo_unitario": ed['custo'],
            "valor_total": ed['qtd'] * ed['custo'],
            "almoxarifado": "Principal",
            "prateleira": ed['local'],
            "alertar_minimo": True,
            "item_critico": ed.get('critico', False),
            "organization_id": org.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.itens_estoque.insert_one(item_doc)
    
    # Sample OS (with new types and disciplina)
    os_data = [
        {"ativo_idx": 0, "titulo": "Troca de rolamento", "tipo": "preventiva", "disciplina": "mecanica", "prioridade": "alta", "status": "aberta"},
        {"ativo_idx": 2, "titulo": "Lubrificação geral", "tipo": "lubrificacao", "disciplina": "mecanica", "prioridade": "media", "status": "planejada"},
        {"ativo_idx": 4, "titulo": "Reparo motor elétrico", "tipo": "corretiva", "disciplina": "eletrica", "prioridade": "critica", "status": "em_execucao"},
    ]
    
    for idx, od in enumerate(os_data):
        os_id = str(uuid.uuid4())
        numero = f"2026-{str(idx + 1).zfill(5)}"
        os_doc = {
            "id": os_id,
            "numero": numero,
            "ativo_id": ativos[od['ativo_idx']]['id'],
            "organization_id": org.id,
            "tipo": od['tipo'],
            "disciplina": od['disciplina'],
            "prioridade": od['prioridade'],
            "titulo": od['titulo'],
            "status": od['status'],
            "responsavel_id": users[2]['id'] if od['status'] == 'em_execucao' else None,
            "data_abertura": datetime.now(timezone.utc).isoformat(),
            "data_inicio": datetime.now(timezone.utc).isoformat() if od['status'] == 'em_execucao' else None,
            "custo_pecas": 0,
            "custo_mao_obra": 0,
            "custo_total": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.ordens_servico.insert_one(os_doc)
    
    return {
        "message": "Dados de demonstração criados com sucesso!",
        "credentials": {
            "admin": {"email": "admin@manutrix.com", "password": "admin123"},
            "supervisor": {"email": "supervisor@manutrix.com", "password": "supervisor123"},
            "tecnico": {"email": "tecnico@manutrix.com", "password": "tecnico123"}
        }
    }


# ============== MANUAL PDF UPLOAD ==============

MANUALS_DIR = ROOT_DIR / 'uploads' / 'manuals'
MANUALS_DIR.mkdir(parents=True, exist_ok=True)

@api_router.post("/ativos/{ativo_id}/manual")
async def upload_manual(ativo_id: str, file: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin'])
    
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    ext = Path(file.filename).suffix.lower()
    if ext != '.pdf':
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos")
    
    filename = f"{ativo_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = MANUALS_DIR / filename
    
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Extract text from PDF for AI context
    extracted_text = ""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(filepath))
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    except Exception as e:
        logger.warning(f"PDF text extraction failed: {e}")
    
    manual_doc = {
        "id": str(uuid.uuid4()),
        "ativo_id": ativo_id,
        "filename": file.filename,
        "filepath": str(filepath),
        "url": f"/api/uploads/manuals/{filename}",
        "extracted_text": extracted_text[:50000],  # Limit to 50k chars
        "size_bytes": len(content),
        "uploaded_by": user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.manuais.insert_one(manual_doc)
    manual_doc.pop('_id', None)
    
    # Update ativo with manual ref
    await db.ativos.update_one({"id": ativo_id}, {"$set": {"manual_url": manual_doc['url'], "updated_at": datetime.now(timezone.utc).isoformat()}})
    
    return {"success": True, "manual": {k: v for k, v in manual_doc.items() if k != 'extracted_text'}}

@api_router.get("/ativos/{ativo_id}/manuais")
async def list_manuais(ativo_id: str, user: Dict = Depends(get_current_user)):
    manuais = await db.manuais.find({"ativo_id": ativo_id}, {"_id": 0, "extracted_text": 0}).sort("created_at", -1).to_list(50)
    return manuais

@api_router.delete("/manuais/{manual_id}")
async def delete_manual(manual_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    manual = await db.manuais.find_one({"id": manual_id})
    if not manual:
        raise HTTPException(status_code=404, detail="Manual não encontrado")
    try:
        Path(manual['filepath']).unlink(missing_ok=True)
    except Exception:
        pass
    await db.manuais.delete_one({"id": manual_id})
    return {"success": True}

@api_router.get("/uploads/manuals/{filename}")
async def get_manual_file(filename: str):
    filepath = MANUALS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(filepath, media_type="application/pdf")

# ============== AI ASSISTANT ==============


@api_router.post("/assistente/chat")
async def assistente_chat(data: ChatMessage, user: Dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    llm_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_key:
        raise HTTPException(status_code=500, detail="Chave de IA não configurada")
    
    # Build context from manuals
    context_parts = []
    if data.ativo_id:
        manuais = await db.manuais.find({"ativo_id": data.ativo_id}, {"_id": 0}).to_list(10)
        ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
        if ativo:
            context_parts.append(f"Ativo: {ativo.get('tag', '')} - {ativo.get('nome', '')} | Tipo: {ativo.get('tipo_equipamento', 'N/A')} | Fabricante: {ativo.get('fabricante', 'N/A')} | Modelo: {ativo.get('modelo', 'N/A')}")
        for m in manuais:
            if m.get('extracted_text'):
                context_parts.append(f"Manual '{m.get('filename', '')}': {m['extracted_text'][:15000]}")
    else:
        # Get all manuals for general questions
        manuais = await db.manuais.find({}, {"_id": 0, "extracted_text": 1, "filename": 1, "ativo_id": 1}).to_list(20)
        for m in manuais:
            if m.get('extracted_text'):
                ativo = await db.ativos.find_one({"id": m.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
                label = f"{ativo.get('tag', '')} - {ativo.get('nome', '')}" if ativo else m.get('filename', '')
                context_parts.append(f"Manual de {label}: {m['extracted_text'][:8000]}")
    
    manual_context = "\n\n".join(context_parts) if context_parts else "Nenhum manual carregado no sistema."
    
    system_msg = f"""Você é o Assistente Técnico MANUTRIX, especialista em manutenção industrial.
Responda em português do Brasil, de forma clara e objetiva.
Seu papel é ajudar mecânicos e eletricistas a resolver problemas e tirar dúvidas sobre equipamentos.
Use as informações dos manuais técnicos disponíveis como referência.
Se não souber a resposta ou não encontrar nos manuais, diga honestamente e sugira verificar o manual físico.

=== MANUAIS DISPONÍVEIS ===
{manual_context}
"""
    
    session_id = data.session_id or f"manutrix_{user['id']}_{uuid.uuid4().hex[:8]}"
    
    # Load chat history from DB
    history = await db.chat_history.find({"session_id": session_id}, {"_id": 0}).sort("created_at", 1).to_list(20)
    
    chat = LlmChat(
        api_key=llm_key,
        session_id=session_id,
        system_message=system_msg
    ).with_model("gemini", "gemini-2.5-flash")
    
    # Replay history
    for h in history:
        if h.get('role') == 'user':
            chat.messages.append({"role": "user", "content": h['content']})
        elif h.get('role') == 'assistant':
            chat.messages.append({"role": "assistant", "content": h['content']})
    
    try:
        response = await chat.send_message(UserMessage(text=data.message))
        
        # Save to history
        now = datetime.now(timezone.utc).isoformat()
        await db.chat_history.insert_many([
            {"session_id": session_id, "role": "user", "content": data.message, "ativo_id": data.ativo_id, "user_id": user['id'], "created_at": now},
            {"session_id": session_id, "role": "assistant", "content": response, "ativo_id": data.ativo_id, "created_at": now}
        ])
        
        return {"response": response, "session_id": session_id}
    except Exception as e:
        logger.error(f"AI Assistant error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no assistente: {str(e)}")

@api_router.get("/assistente/historico")
async def get_chat_history(session_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    query = {"user_id": user['id']}
    if session_id:
        query['session_id'] = session_id
    history = await db.chat_history.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return history

@api_router.get("/assistente/sessoes")
async def list_chat_sessions(user: Dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": user['id'], "role": "user"}},
        {"$group": {"_id": "$session_id", "last_message": {"$last": "$content"}, "ativo_id": {"$last": "$ativo_id"}, "created_at": {"$last": "$created_at"}}},
        {"$sort": {"created_at": -1}},
        {"$limit": 20}
    ]
    sessions = await db.chat_history.aggregate(pipeline).to_list(20)
    result = []
    for s in sessions:
        ativo = None
        if s.get('ativo_id'):
            ativo = await db.ativos.find_one({"id": s['ativo_id']}, {"_id": 0, "tag": 1, "nome": 1})
        result.append({"session_id": s['_id'], "last_message": s.get('last_message', '')[:80], "ativo": ativo, "created_at": s.get('created_at')})
    return result

# ============== EXPORT ENDPOINTS ==============

@api_router.get("/export/ativos")
async def export_ativos(format: str = "excel", user: Dict = Depends(get_current_user)):
    if not can_export(user):
        raise HTTPException(status_code=403, detail="Sem permissão para exportar")
    
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    ativos = await db.ativos.find(query, {"_id": 0}).to_list(5000)
    
    if format == "excel":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ativos"
        # Enrich with area names
        sid_list = list(set(a.get('sector_id') for a in ativos if a.get('sector_id')))
        sectors = await db.sectors.find({"id": {"$in": sid_list}}, {"_id": 0}).to_list(len(sid_list)) if sid_list else []
        sector_map = {s['id']: s.get('nome','') for s in sectors}
        headers = ["Área", "TAG", "Nome", "Tipo", "Fabricante", "Modelo", "Número de Série", "Observações"]
        ws.append(headers)
        for a in ativos:
            ws.append([sector_map.get(a.get('sector_id',''),''), a.get('tag',''), a.get('nome',''), a.get('tipo_equipamento',''), a.get('fabricante',''), a.get('modelo',''), a.get('numero_serie',''), a.get('observacoes','')])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=ativos_manutrix.xlsx"})
    
    elif format == "pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        # Enrich with area names
        sid_list = list(set(a.get('sector_id') for a in ativos if a.get('sector_id')))
        sectors = await db.sectors.find({"id": {"$in": sid_list}}, {"_id": 0}).to_list(len(sid_list)) if sid_list else []
        sector_map = {s['id']: s.get('nome','') for s in sectors}
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [Paragraph("MANUTRIX - Relatório de Ativos", styles['Title']), Spacer(1, 12)]
        data = [["Área", "TAG", "Nome", "Tipo", "Fabricante", "Modelo"]]
        for a in ativos:
            data.append([sector_map.get(a.get('sector_id',''),''), a.get('tag','') or '', (a.get('nome','') or '')[:30], (a.get('tipo_equipamento','') or '')[:20], (a.get('fabricante','') or '')[:20], (a.get('modelo','') or '')[:20]])
        t = Table(data)
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#10b981')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('FONTSIZE', (0,0), (-1,-1), 8), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=ativos_manutrix.pdf"})

@api_router.get("/export/ordens-servico")
async def export_os(format: str = "excel", user: Dict = Depends(get_current_user)):
    if not can_export(user):
        raise HTTPException(status_code=403, detail="Sem permissão para exportar")
    
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    
    for os_item in os_list:
        ativo = await db.ativos.find_one({"id": os_item.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        os_item['ativo_tag'] = ativo.get('tag', '') if ativo else ''
        os_item['ativo_nome'] = ativo.get('nome', '') if ativo else ''
    
    if format == "excel":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ordens de Serviço"
        headers = ["Número", "Ativo TAG", "Ativo", "Tipo", "Prioridade", "Status", "Título", "Data Abertura", "Data Conclusão", "Tempo (min)", "Custo Total"]
        ws.append(headers)
        for o in os_list:
            ws.append([o.get('numero',''), o.get('ativo_tag',''), o.get('ativo_nome',''), o.get('tipo',''), o.get('prioridade',''), o.get('status',''), o.get('titulo',''), o.get('data_abertura',''), o.get('data_conclusao',''), o.get('tempo_execucao_minutos',''), o.get('custo_total',0)])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=ordens_servico_manutrix.xlsx"})
    
    elif format == "pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [Paragraph("MANUTRIX - Relatório de Ordens de Serviço", styles['Title']), Spacer(1, 12)]
        data = [["Nº", "TAG", "Tipo", "Prioridade", "Status", "Título", "Custo"]]
        for o in os_list:
            custo = o.get('custo_total') or 0
            data.append([str(o.get('numero','')), str(o.get('ativo_tag','')), str(o.get('tipo','')), str(o.get('prioridade','')), str(o.get('status','')), str(o.get('titulo',''))[:25], f"R${float(custo):.2f}"])
        t = Table(data)
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('FONTSIZE', (0,0), (-1,-1), 8), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=ordens_servico_manutrix.pdf"})

@api_router.get("/export/estoque")
async def export_estoque(format: str = "excel", user: Dict = Depends(get_current_user)):
    if not can_export(user):
        raise HTTPException(status_code=403, detail="Sem permissão para exportar")
    
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    items = await db.itens_estoque.find(query, {"_id": 0}).to_list(5000)
    
    if format == "excel":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Estoque"
        headers = ["Código", "Nome", "Categoria", "Quantidade", "Unidade", "Mínimo", "Custo Unit.", "Almoxarifado"]
        ws.append(headers)
        for i in items:
            ws.append([i.get('sku',''), i.get('nome',''), i.get('categoria',''), i.get('quantidade',0), i.get('unidade',''), i.get('estoque_minimo',0), i.get('custo_unitario',0), i.get('almoxarifado','')])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=estoque_manutrix.xlsx"})
    
    elif format == "pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [Paragraph("MANUTRIX - Relatório de Estoque", styles['Title']), Spacer(1, 12)]
        data = [["Código", "Nome", "Categoria", "Qtd", "Un", "Mín", "Custo Unit."]]
        for i in items:
            data.append([i.get('sku',''), (i.get('nome','') or '')[:25], i.get('categoria',''), i.get('quantidade',0), i.get('unidade',''), i.get('estoque_minimo',0), f"R${i.get('custo_unitario',0):.2f}"])
        t = Table(data)
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8b5cf6')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('FONTSIZE', (0,0), (-1,-1), 8), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=estoque_manutrix.pdf"})

@api_router.get("/export/inspecoes")
async def export_inspecoes(format: str = "excel", user: Dict = Depends(get_current_user)):
    if not can_export(user):
        raise HTTPException(status_code=403, detail="Sem permissão para exportar")
    
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    inspecoes = await db.inspecoes.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    
    for insp in inspecoes:
        ativo = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        insp['ativo_tag'] = ativo.get('tag', '') if ativo else ''
        insp['ativo_nome'] = ativo.get('nome', '') if ativo else ''
    
    if format == "excel":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inspeções"
        headers = ["Ativo TAG", "Ativo", "Tipo", "Frequência", "Status", "Resultado", "Data Programada", "Data Conclusão", "Duração (min)", "Lubrificante", "Ponto Lubrificação"]
        ws.append(headers)
        for i in inspecoes:
            ws.append([i.get('ativo_tag',''), i.get('ativo_nome',''), i.get('tipo',''), i.get('frequencia',''), i.get('status',''), i.get('resultado',''), i.get('data_programada',''), i.get('data_conclusao',''), i.get('duracao_minutos',''), i.get('tipo_lubrificante',''), i.get('ponto_lubrificacao','')])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=inspecoes_manutrix.xlsx"})
    
    elif format == "pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [Paragraph("MANUTRIX - Relatório de Inspeções", styles['Title']), Spacer(1, 12)]
        data = [["TAG", "Ativo", "Tipo", "Freq.", "Status", "Resultado", "Data"]]
        for i in inspecoes:
            data.append([i.get('ativo_tag',''), i.get('ativo_nome','')[:20], i.get('tipo',''), i.get('frequencia',''), i.get('status',''), i.get('resultado',''), i.get('data_programada','')[:10]])
        t = Table(data)
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f59e0b')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('FONTSIZE', (0,0), (-1,-1), 8), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=inspecoes_manutrix.pdf"})

# ============== ATTACHMENTS ==============

@api_router.post("/attachments")
async def upload_attachment(
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    categoria: str = Form("foto"),
    file: UploadFile = File(...),
    user: Dict = Depends(get_current_user)
):
    """Upload attachment for any entity (inspection, work_order, anomaly, spare_asset)"""
    ext = Path(file.filename).suffix.lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf']:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido")
    
    filename = f"{entity_type}_{entity_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    attach_doc = {
        "id": str(uuid.uuid4()),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "categoria": categoria,
        "filename": file.filename,
        "file_url": f"/api/uploads/{filename}",
        "size_bytes": len(content),
        "mime_type": file.content_type,
        "uploaded_by": user['id'],
        "organization_id": user.get('organization_id', ''),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.attachments.insert_one(attach_doc)
    attach_doc.pop('_id', None)
    return attach_doc

@api_router.get("/attachments/{entity_type}/{entity_id}")
async def list_attachments(entity_type: str, entity_id: str, user: Dict = Depends(get_current_user)):
    attachments = await db.attachments.find(
        {"entity_type": entity_type, "entity_id": entity_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return attachments

@api_router.delete("/attachments/{attach_id}")
async def delete_attachment(attach_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    attach = await db.attachments.find_one({"id": attach_id})
    if not attach:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    try:
        filepath = UPLOAD_DIR / Path(attach['file_url']).name
        filepath.unlink(missing_ok=True)
    except Exception:
        pass
    await db.attachments.delete_one({"id": attach_id})
    return {"success": True}

# ============== SOBRESSALENTES (SPARE PARTS) ==============




@api_router.get("/sobressalentes")
async def list_spares(
    status: Optional[str] = None,
    search: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if status:
        query['status'] = status
    
    spares = await db.spare_assets.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    if search:
        s = search.lower()
        spares = [sp for sp in spares if s in sp.get('tag', '').lower() or s in sp.get('descricao', '').lower()]
    
    for sp in spares:
        if sp.get('ativo_vinculado_id'):
            ativo = await db.ativos.find_one({"id": sp['ativo_vinculado_id']}, {"_id": 0, "tag": 1, "nome": 1})
            sp['ativo_vinculado'] = ativo
        sp['attachments_count'] = await db.attachments.count_documents({"entity_type": "spare_asset", "entity_id": sp['id']})
    
    return spares

@api_router.get("/sobressalentes/{spare_id}")
async def get_spare(spare_id: str, user: Dict = Depends(get_current_user)):
    sp = await db.spare_assets.find_one({"id": spare_id, "deleted_at": None}, {"_id": 0})
    if not sp:
        raise HTTPException(status_code=404, detail="Sobressalente não encontrado")
    
    sp['movimentacoes'] = await db.spare_movements.find({"spare_id": spare_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    sp['attachments'] = await db.attachments.find({"entity_type": "spare_asset", "entity_id": spare_id}, {"_id": 0}).to_list(50)
    sp['reformas'] = await db.spare_reformas.find({"spare_id": spare_id, "deleted_at": None}, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    if sp.get('ativo_vinculado_id'):
        sp['ativo_vinculado'] = await db.ativos.find_one({"id": sp['ativo_vinculado_id']}, {"_id": 0, "tag": 1, "nome": 1})
    
    return sp

@api_router.post("/sobressalentes")
async def create_spare(data: SpareAssetCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    
    org_id = user.get('organization_id', '')
    tag = data.tag or f"SP-{uuid.uuid4().hex[:6].upper()}"
    
    spare_id = str(uuid.uuid4())
    spare_doc = {
        "id": spare_id,
        "tag": tag,
        "descricao": data.descricao,
        "modelo": data.modelo,
        "fabricante": data.fabricante,
        "numero_serie": data.numero_serie,
        "status": data.status,
        "localizacao": data.localizacao,
        "ativo_vinculado_id": data.ativo_vinculado_id,
        "custo": data.custo,
        "observacoes": data.observacoes,
        "origem": data.origem,
        "condicoes": data.condicoes or {"novo": 0, "reformado": 0, "em_reforma": 0, "reservado": 0, "instalado": 0, "descartado": 0},
        "quantidade_total": sum((data.condicoes or {}).values()) if data.condicoes else 0,
        "organization_id": org_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.spare_assets.insert_one(spare_doc)
    await audit_log("create", "sobressalentes", spare_doc['id'], user, f"Sobressalente: {spare_doc.get('tag','')} {data.nome}")
    spare_doc.pop('_id', None)
    return spare_doc

@api_router.put("/sobressalentes/{spare_id}")
async def update_spare(spare_id: str, data: SpareAssetUpdate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    existing = await db.spare_assets.find_one({"id": spare_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Sobressalente não encontrado")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['alterado_por'] = user.get('id')
    if 'condicoes' in update_data and update_data['condicoes']:
        update_data['quantidade_total'] = sum(update_data['condicoes'].values())
    await db.spare_assets.update_one({"id": spare_id}, {"$set": update_data})
    await audit_log("update", "sobressalentes", spare_id, user, f"Sobressalente editado: {existing.get('tag','')} {existing.get('descricao','')}")
    return await db.spare_assets.find_one({"id": spare_id}, {"_id": 0})

@api_router.delete("/sobressalentes/{spare_id}")
async def delete_spare(spare_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    existing = await db.spare_assets.find_one({"id": spare_id, "deleted_at": None}, {"_id": 0})
    await db.spare_assets.update_one({"id": spare_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "sobressalentes", spare_id, user, f"Sobressalente excluído: {(existing or {}).get('tag','')} {(existing or {}).get('descricao','')}")
    return {"success": True}

# ============== HISTÓRICO DE REFORMA ==============

@api_router.get("/sobressalentes/{spare_id}/reformas")
async def list_spare_reformas(spare_id: str, user: Dict = Depends(get_current_user)):
    reformas = await db.spare_reformas.find(
        {"spare_id": spare_id, "deleted_at": None}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return reformas

@api_router.post("/sobressalentes/{spare_id}/reformas")
async def create_spare_reforma(spare_id: str, body: dict, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    spare = await db.spare_assets.find_one({"id": spare_id, "deleted_at": None}, {"_id": 0})
    if not spare:
        raise HTTPException(status_code=404, detail="Sobressalente não encontrado")
    
    reforma_doc = {
        "id": str(uuid.uuid4()),
        "spare_id": spare_id,
        "spare_tag": spare.get('tag', ''),
        "empresa_reparadora": body.get('empresa_reparadora', ''),
        "data_envio": body.get('data_envio'),
        "data_retorno": body.get('data_retorno'),
        "observacao": body.get('observacao', ''),
        "valor": body.get('valor'),
        "usuario_id": user.get('id'),
        "usuario_nome": user.get('nome', user.get('email', '')),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.spare_reformas.insert_one(reforma_doc)
    await audit_log("create", "spare_reforma", reforma_doc['id'], user,
        f"Reforma registrada: {spare.get('tag','')} — {body.get('empresa_reparadora','')}")
    reforma_doc.pop('_id', None)
    return reforma_doc

@api_router.delete("/sobressalentes/{spare_id}/reformas/{reforma_id}")
async def delete_spare_reforma(spare_id: str, reforma_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    await db.spare_reformas.update_one({"id": reforma_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    await audit_log("delete", "spare_reforma", reforma_id, user, f"Reforma excluída do sobressalente {spare_id}")
    return {"success": True}

@api_router.post("/sobressalentes/movimentacao")
async def create_spare_movement(data: SpareMovementCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm', 'supervisor'])
    
    spare = await db.spare_assets.find_one({"id": data.spare_id, "deleted_at": None}, {"_id": 0})
    if not spare:
        raise HTTPException(status_code=404, detail="Sobressalente não encontrado")
    
    # Update spare status based on movement
    new_status = spare.get('status', 'estoque')
    if data.tipo == 'saida':
        new_status = 'em_uso'
    elif data.tipo == 'entrada' or data.tipo == 'retorno':
        new_status = 'estoque'
    elif data.tipo == 'reforma':
        new_status = 'em_reforma'
    
    mov_doc = {
        "id": str(uuid.uuid4()),
        "spare_id": data.spare_id,
        "tipo": data.tipo,
        "quantidade": data.quantidade,
        "motivo": data.motivo,
        "os_id": data.os_id,
        "nota_fiscal": data.nota_fiscal,
        "observacoes": data.observacoes,
        "usuario_id": user['id'],
        "organization_id": user.get('organization_id', ''),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.spare_movements.insert_one(mov_doc)
    await db.spare_assets.update_one({"id": data.spare_id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    
    return {"success": True, "new_status": new_status}

# ============== ANOMALIAS ==============


@api_router.get("/anomalias")
async def list_anomalias(sector_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    
    # Scope by sector
    if sector_id:
        asset_ids = await get_scoped_asset_ids(user.get('organization_id', ''), sector_id=sector_id)
        if asset_ids is not None:
            query['ativo_id'] = {"$in": asset_ids}
    
    anomalias = await db.anomalias.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    for a in anomalias:
        ativo = await db.ativos.find_one({"id": a.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1, "sector_id": 1})
        if ativo and ativo.get('sector_id'):
            sector = await db.sectors.find_one({"id": ativo['sector_id']}, {"_id": 0, "nome": 1})
            ativo['sector'] = sector
        a['ativo'] = ativo
    return anomalias

@api_router.post("/anomalias")
async def create_anomalia(data: AnomaliaCreate, user: Dict = Depends(get_current_user)):
    """Técnico pode abrir anomalia. Se gerar_os=True, cria OS automaticamente com prioridade inteligente."""
    ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    org_id = ativo.get('organization_id', user.get('organization_id', ''))
    
    # PRIORIZAÇÃO INTELIGENTE: severidade anomalia × criticidade ativo
    severidade_peso = {'baixa': 1, 'media': 2, 'alta': 3, 'critica': 4}
    criticidade_peso = {'baixa': 1, 'media': 2, 'alta': 3, 'critica': 4}
    score = severidade_peso.get(data.severidade, 2) * criticidade_peso.get(ativo.get('criticidade', 'media'), 2)
    
    prioridade_os = 'media'  # default
    if score >= 12:
        prioridade_os = 'critica'
    elif score >= 6:
        prioridade_os = 'alta'
    elif score >= 3:
        prioridade_os = 'media'
    else:
        prioridade_os = 'baixa'
    
    anomalia_id = str(uuid.uuid4())
    anomalia_doc = {
        "id": anomalia_id,
        "ativo_id": data.ativo_id,
        "descricao": data.descricao,
        "severidade": data.severidade,
        "prioridade_calculada": prioridade_os,
        "score_prioridade": score,
        "inspecao_id": data.inspecao_id,
        "status": "aberta",
        "os_gerada_id": None,
        "reportado_por": user['id'],
        "organization_id": org_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    
    os_id = None
    if data.gerar_os:
        numero = await generate_os_numero(org_id)
        os_id = str(uuid.uuid4())
        os_doc = {
            "id": os_id,
            "numero": numero,
            "ativo_id": data.ativo_id,
            "organization_id": org_id,
            "tipo": "corretiva",
            "origem": "falha",
            "prioridade": prioridade_os,
            "titulo": f"Anomalia - {ativo.get('tag', '')}",
            "descricao": data.descricao,
            "status": "aberta",
            "responsavel_id": None,
            "equipe": [],
            "data_abertura": datetime.now(timezone.utc).isoformat(),
            "custo_pecas": 0, "custo_mao_obra": 0, "custo_total": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.ordens_servico.insert_one(os_doc)
        anomalia_doc['os_gerada_id'] = os_id
    
    await db.anomalias.insert_one(anomalia_doc)
    await audit_log("create", "anomalias", anomalia_doc.get('id',''), user, f"Anomalia: {ativo.get('tag','')}")
    anomalia_doc.pop('_id', None)
    return {**anomalia_doc, "os_gerada_id": os_id, "prioridade_os": prioridade_os}

@api_router.get("/anomalias/{anomalia_id}")
async def get_anomalia(anomalia_id: str, user: Dict = Depends(get_current_user)):
    a = await db.anomalias.find_one({"id": anomalia_id, "deleted_at": None}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="Anomalia não encontrada")
    ativo = await db.ativos.find_one({"id": a.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1, "sector_id": 1})
    if ativo and ativo.get('sector_id'):
        ativo['sector'] = await db.sectors.find_one({"id": ativo['sector_id']}, {"_id": 0, "nome": 1})
    a['ativo'] = ativo
    # Enrich actor names
    for field in ['criado_por', 'resolvido_por', 'encerrado_por', 'alterado_por']:
        uid = a.get(field)
        if uid:
            u = await db.users.find_one({"id": uid}, {"_id": 0, "nome": 1})
            a[f'{field}_nome'] = u.get('nome') if u else uid
    a['comentarios'] = await db.anomalia_comentarios.find({"anomalia_id": anomalia_id}, {"_id": 0}).sort("created_at", 1).to_list(100)
    # Resolve user names for comments
    for c in a['comentarios']:
        if c.get('usuario_id'):
            u = await db.users.find_one({"id": c['usuario_id']}, {"_id": 0, "nome": 1})
            c['usuario_nome'] = u.get('nome') if u else None
    a['historico'] = await db.anomalia_historico.find({"anomalia_id": anomalia_id}, {"_id": 0}).sort("created_at", 1).to_list(100)
    return a

@api_router.put("/anomalias/{anomalia_id}")
async def update_anomalia(anomalia_id: str, body: dict, user: Dict = Depends(get_current_user)):
    a = await db.anomalias.find_one({"id": anomalia_id, "deleted_at": None})
    if not a:
        raise HTTPException(status_code=404, detail="Anomalia não encontrada")
    update = {"updated_at": datetime.now(timezone.utc).isoformat(), "alterado_por": user.get('id')}
    for field in ['descricao', 'severidade']:
        if field in body: update[field] = body[field]
    await db.anomalias.update_one({"id": anomalia_id}, {"$set": update})
    await db.anomalia_historico.insert_one({
        "id": str(uuid.uuid4()), "anomalia_id": anomalia_id,
        "tipo": "edicao", "descricao": f"Anomalia editada por {user.get('nome', user.get('email'))}",
        "usuario_id": user['id'], "created_at": datetime.now(timezone.utc).isoformat()
    })
    return await db.anomalias.find_one({"id": anomalia_id}, {"_id": 0})

@api_router.post("/anomalias/{anomalia_id}/status")
async def change_anomalia_status(anomalia_id: str, body: dict, user: Dict = Depends(get_current_user)):
    """Workflow: aberta → em_analise → os_gerada → aguardando_execucao → resolvida → encerrada"""
    VALID_TRANSITIONS = {
        'aberta': ['em_analise', 'encerrada'],
        'em_analise': ['os_gerada', 'resolvida', 'encerrada'],
        'os_gerada': ['aguardando_execucao', 'resolvida', 'encerrada'],
        'aguardando_execucao': ['resolvida', 'encerrada'],
        'resolvida': ['encerrada'],
        'encerrada': ['aberta'],  # reabrir
    }
    a = await db.anomalias.find_one({"id": anomalia_id, "deleted_at": None})
    if not a:
        raise HTTPException(status_code=404, detail="Anomalia não encontrada")
    new_status = body.get('status')
    if not new_status:
        raise HTTPException(status_code=400, detail="Status é obrigatório")
    current = a.get('status', 'aberta')
    if new_status not in VALID_TRANSITIONS.get(current, []):
        raise HTTPException(status_code=400, detail=f"Transição inválida: {current} → {new_status}")
    # Permission: encerrar e reabrir apenas supervisor/admin
    if new_status in ['encerrada'] or (current == 'encerrada' and new_status == 'aberta'):
        if user.get('role') not in ['admin', 'supervisor', 'pcm']:
            raise HTTPException(status_code=403, detail="Apenas supervisor/admin pode encerrar ou reabrir")
    update = {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if new_status == 'encerrada':
        update['data_encerramento'] = datetime.now(timezone.utc).isoformat()
        update['encerrado_por'] = user['id']
    if new_status == 'aberta' and current == 'encerrada':
        update['data_encerramento'] = None
        update['encerrado_por'] = None
    await db.anomalias.update_one({"id": anomalia_id}, {"$set": update})
    descricao = f"Status: {current} → {new_status}"
    if new_status == 'aberta' and current == 'encerrada':
        descricao = f"Anomalia reaberta por {user.get('nome', user.get('email'))}"
    await db.anomalia_historico.insert_one({
        "id": str(uuid.uuid4()), "anomalia_id": anomalia_id,
        "tipo": "status", "descricao": descricao,
        "usuario_id": user['id'], "created_at": datetime.now(timezone.utc).isoformat()
    })
    return await db.anomalias.find_one({"id": anomalia_id}, {"_id": 0})

@api_router.delete("/anomalias/{anomalia_id}")
async def delete_anomalia(anomalia_id: str, user: Dict = Depends(get_current_user)):
    """Soft delete anomalia (admin/supervisor only)"""
    if user.get('role') not in ['admin', 'supervisor', 'pcm']:
        raise HTTPException(status_code=403, detail="Sem permissão")
    a = await db.anomalias.find_one({"id": anomalia_id, "deleted_at": None})
    if not a:
        raise HTTPException(status_code=404, detail="Anomalia não encontrada")
    await db.anomalias.update_one({"id": anomalia_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    return {"success": True}

@api_router.post("/anomalias/{anomalia_id}/comentarios")
async def add_anomalia_comment(anomalia_id: str, body: dict, user: Dict = Depends(get_current_user)):
    a = await db.anomalias.find_one({"id": anomalia_id, "deleted_at": None})
    if not a:
        raise HTTPException(status_code=404, detail="Anomalia não encontrada")
    texto = body.get('texto', '').strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Comentário vazio")
    doc = {
        "id": str(uuid.uuid4()), "anomalia_id": anomalia_id,
        "texto": texto, "usuario_id": user['id'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.anomalia_comentarios.insert_one(doc)
    doc.pop('_id', None)
    u = await db.users.find_one({"id": user['id']}, {"_id": 0, "nome": 1})
    doc['usuario_nome'] = u.get('nome') if u else None
    return doc

# ============== KNOWLEDGE BASE (ESTRUTURA) ==============


@api_router.get("/knowledge-base")
async def list_knowledge(
    tipo_equipamento: Optional[str] = None,
    search: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {}
    if tipo_equipamento:
        query['tipo_equipamento'] = tipo_equipamento
    items = await db.knowledge_base.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    if search:
        s = search.lower()
        items = [i for i in items if s in i.get('problema', '').lower() or s in i.get('solucao', '').lower() or s in i.get('tipo_equipamento', '').lower()]
    return items

@api_router.post("/knowledge-base")
async def create_knowledge(data: KnowledgeBaseCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'pcm'])
    doc = {
        "id": str(uuid.uuid4()),
        "tipo_equipamento": data.tipo_equipamento,
        "problema": data.problema,
        "solucao": data.solucao,
        "tags": data.tags or [],
        "created_by": user['id'],
        "organization_id": user.get('organization_id', ''),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.knowledge_base.insert_one(doc)
    doc.pop('_id', None)
    return doc

@api_router.delete("/knowledge-base/{kb_id}")
async def delete_knowledge(kb_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    await db.knowledge_base.delete_one({"id": kb_id})
    return {"success": True}

# ============== GESTÃO DE USUÁRIOS (ADMIN) ==============

@api_router.get("/admin/users")
async def admin_list_users(user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    return await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(200)

@api_router.post("/admin/users")
async def admin_create_user(data: UserCreate, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    email_normalized = data.email.lower().strip()
    existing = await db.users.find_one({"email": email_normalized, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": email_normalized,
        "nome": data.nome,
        "role": data.role.value,
        "organization_id": data.organization_id or user.get('organization_id', ''),
        "telefone": data.telefone,
        "password_hash": hash_password(data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    
    # Sync to Supabase Auth
    if supabase_client:
        try:
            sb_resp = supabase_client.auth.admin.create_user({
                "email": email_normalized, "password": data.password,
                "email_confirm": True, "user_metadata": {"nome": data.nome, "role": data.role.value}
            })
            if sb_resp.user:
                user_doc['supabase_id'] = sb_resp.user.id
        except Exception as e:
            logger.warning(f"Supabase user create: {e}")
    
    await db.users.insert_one(user_doc)
    return {k: v for k, v in user_doc.items() if k not in ['password_hash', '_id']}

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, user: Dict = Depends(get_current_user)):
    check_admin_only(user)
    await db.users.update_one({"id": user_id}, {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}})
    return {"success": True}

# ============== EXPORT SOBRESSALENTES ==============

@api_router.get("/export/sobressalentes")
async def export_spares(format: str = "excel", user: Dict = Depends(get_current_user)):
    if not can_export(user):
        raise HTTPException(status_code=403, detail="Sem permissão para exportar")
    
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    spares = await db.spare_assets.find(query, {"_id": 0}).to_list(5000)
    
    if format == "excel":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sobressalentes"
        ws.append(["Código", "Descrição", "Modelo", "Fabricante", "Série", "Status", "Localização", "Custo"])
        for s in spares:
            ws.append([s.get('tag',''), s.get('descricao',''), s.get('modelo',''), s.get('fabricante',''), s.get('numero_serie',''), s.get('status',''), s.get('localizacao',''), s.get('custo','')])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=sobressalentes_manutrix.xlsx"})
    
    elif format == "pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=15*mm, bottomMargin=15*mm, leftMargin=10*mm, rightMargin=10*mm)
        styles = getSampleStyleSheet()
        elements = []
        elements.append(Paragraph("MANUTRIX — Sobressalentes", styles['Title']))
        elements.append(Paragraph(f"Total: {len(spares)} registro(s) — {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 6*mm))
        
        data = [["Código", "Descrição", "Modelo", "Fabricante", "Status", "Localização", "Custo"]]
        for s in spares:
            custo = f"R$ {s['custo']:.2f}" if s.get('custo') else ""
            data.append([
                s.get('tag',''), s.get('descricao','')[:40], s.get('modelo','') or '',
                s.get('fabricante','') or '', s.get('status',''),
                s.get('localizacao','') or '', custo
            ])
        
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('FONTSIZE', (0,1), (-1,-1), 7),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#334155')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(table)
        doc.build(elements)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=sobressalentes_manutrix.pdf"})

# ============== POWER BI DATA ENDPOINTS ==============

@api_router.get("/powerbi/ativos")
async def powerbi_ativos(api_key: Optional[str] = None, user: Dict = Depends(get_current_user)):
    """Flat JSON data optimized for Power BI import"""
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    ativos = await db.ativos.find(query, {"_id": 0}).to_list(10000)
    result = []
    for a in ativos:
        area = await db.areas.find_one({"id": a.get('area_id')}, {"_id": 0, "nome": 1})
        result.append({
            "tag": a.get('tag'), "nome": a.get('nome'), "tipo_equipamento": a.get('tipo_equipamento'),
            "fabricante": a.get('fabricante'), "modelo": a.get('modelo'), "criticidade": a.get('criticidade'),
            "status": a.get('status'), "area": area.get('nome') if area else '', "centro_custo": a.get('centro_custo'),
            "mtbf_horas": a.get('mtbf_horas'), "mttr_horas": a.get('mttr_horas'),
            "valor_aquisicao": a.get('valor_aquisicao'), "data_instalacao": a.get('data_instalacao'),
            "created_at": a.get('created_at')
        })
    return result

@api_router.get("/powerbi/ordens-servico")
async def powerbi_os(user: Dict = Depends(get_current_user)):
    """Flat JSON data for Power BI - Ordens de Serviço"""
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    os_list = await db.ordens_servico.find(query, {"_id": 0}).to_list(10000)
    result = []
    for o in os_list:
        ativo = await db.ativos.find_one({"id": o.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        resp = await db.users.find_one({"id": o.get('responsavel_id')}, {"_id": 0, "nome": 1}) if o.get('responsavel_id') else None
        result.append({
            "numero": o.get('numero'), "ativo_tag": ativo.get('tag') if ativo else '', "ativo_nome": ativo.get('nome') if ativo else '',
            "ativo_criticidade": ativo.get('criticidade') if ativo else '', "tipo": o.get('tipo'), "origem": o.get('origem'),
            "prioridade": o.get('prioridade'), "status": o.get('status'), "titulo": o.get('titulo'),
            "responsavel": resp.get('nome') if resp else '', "data_abertura": o.get('data_abertura'),
            "data_inicio": o.get('data_inicio'), "data_conclusao": o.get('data_conclusao'),
            "tempo_execucao_minutos": o.get('tempo_execucao_minutos'), "custo_pecas": o.get('custo_pecas', 0),
            "custo_mao_obra": o.get('custo_mao_obra', 0), "custo_total": o.get('custo_total', 0),
            "created_at": o.get('created_at')
        })
    return result

@api_router.get("/powerbi/inspecoes")
async def powerbi_inspecoes(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    inspecoes = await db.inspecoes.find(query, {"_id": 0, "checklist": 0}).to_list(10000)
    result = []
    for i in inspecoes:
        ativo = await db.ativos.find_one({"id": i.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        result.append({
            "ativo_tag": ativo.get('tag') if ativo else '', "ativo_nome": ativo.get('nome') if ativo else '',
            "tipo": i.get('tipo'), "frequencia": i.get('frequencia'), "status": i.get('status'),
            "resultado": i.get('resultado'), "data_programada": i.get('data_programada'),
            "data_inicio": i.get('data_inicio'), "data_conclusao": i.get('data_conclusao'),
            "duracao_minutos": i.get('duracao_minutos'), "tipo_lubrificante": i.get('tipo_lubrificante'),
            "created_at": i.get('created_at')
        })
    return result

@api_router.get("/powerbi/kpis-historico")
async def powerbi_kpis(user: Dict = Depends(get_current_user)):
    """KPIs snapshot for Power BI dashboard"""
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
    
    ativos_total = await db.ativos.count_documents(query)
    ativos_op = await db.ativos.count_documents({**query, "status": "operacional"})
    ativos_parados = await db.ativos.count_documents({**query, "status": {"$in": ["parado", "manutencao"]}})
    
    os_concluidas = await db.ordens_servico.find({**query, "status": "concluida", "tempo_execucao_minutos": {"$exists": True, "$ne": None}}, {"_id": 0, "tempo_execucao_minutos": 1, "tipo": 1}).to_list(5000)
    tempos = [o['tempo_execucao_minutos'] for o in os_concluidas if o.get('tempo_execucao_minutos')]
    
    backlog = await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}})
    total_insp = await db.inspecoes.count_documents(query)
    insp_conformes = await db.inspecoes.count_documents({**query, "resultado": "conforme"})
    
    return {
        "data_snapshot": datetime.now(timezone.utc).isoformat(),
        "ativos_total": ativos_total, "ativos_operacionais": ativos_op, "ativos_parados": ativos_parados,
        "disponibilidade_pct": round((ativos_op / ativos_total * 100) if ativos_total > 0 else 100, 1),
        "mttr_horas": round((sum(tempos) / len(tempos) / 60) if tempos else 0, 2),
        "mtbf_horas": round(((ativos_total - ativos_parados) / ativos_total * 720) if ativos_total > 0 else 720, 1),
        "backlog_total": backlog,
        "taxa_conformidade_pct": round((insp_conformes / total_insp * 100) if total_insp > 0 else 100, 1),
        "os_concluidas_total": len(os_concluidas),
        "preventivas": len([o for o in os_concluidas if o.get('tipo') == 'preventiva']),
        "corretivas": len([o for o in os_concluidas if o.get('tipo') == 'corretiva']),
    }

@api_router.get("/admin/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 200,
    user: Dict = Depends(get_current_user)
):
    """Audit logs with filters. Admin, PCM, Gerente can view."""
    if user.get('role') not in ['admin', 'gerente', 'pcm']:
        raise HTTPException(status_code=403, detail="Sem permissão para visualizar auditoria")
    query = {}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if user_id:
        query['user_id'] = user_id
    if entity_type:
        query['entity_type'] = entity_type
    if action:
        query['action'] = action
    if date_from:
        query['created_at'] = {"$gte": date_from}
    if date_to:
        query.setdefault('created_at', {})
        if isinstance(query['created_at'], dict):
            query['created_at']['$lte'] = date_to + 'T23:59:59'
        else:
            query['created_at'] = {"$gte": query['created_at'], "$lte": date_to + 'T23:59:59'}
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    # Normalize old format logs
    result = []
    for log in logs:
        result.append({
            "id": log.get('id', ''),
            "action": log.get('action') or log.get('acao', ''),
            "entity_type": log.get('entity_type') or log.get('entidade', ''),
            "entity_id": log.get('entity_id') or log.get('entidade_id', ''),
            "user_id": log.get('user_id') or log.get('usuario_id', ''),
            "user_nome": log.get('user_nome', ''),
            "user_role": log.get('user_role', ''),
            "details": log.get('details') or log.get('acao', ''),
            "created_at": log.get('created_at', ''),
        })
    return result

@api_router.get("/admin/audit-logs/stats")
async def get_audit_stats(user: Dict = Depends(get_current_user)):
    if user.get('role') not in ['admin', 'gerente', 'pcm']:
        raise HTTPException(status_code=403, detail="Sem permissão")
    pipeline = [
        {"$group": {"_id": "$entity_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    modules = await db.audit_logs.aggregate(pipeline).to_list(50)
    total = await db.audit_logs.count_documents({})
    return {"total": total, "by_module": {m['_id']: m['count'] for m in modules if m['_id']}}

@api_router.get("/export/audit")
async def export_audit(format: str = "excel", user: Dict = Depends(get_current_user)):
    if user.get('role') not in ['admin', 'gerente', 'pcm']:
        raise HTTPException(status_code=403, detail="Sem permissão")
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    if format == "excel":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Auditoria"
        ws.append(["Data/Hora", "Usuário", "Perfil", "Módulo", "Operação", "Detalhes"])
        for l in logs:
            ws.append([
                (l.get('created_at', '') or '')[:19].replace('T', ' '),
                l.get('user_nome', ''), l.get('user_role', ''),
                l.get('entity_type', ''), l.get('action', ''), l.get('details', '')
            ])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=auditoria_manutrix.xlsx"})
    elif format == "pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [Paragraph("MANUTRIX - Auditoria", styles['Title']), Spacer(1, 12)]
        data = [["Data/Hora", "Usuário", "Perfil", "Módulo", "Operação", "Detalhes"]]
        for l in logs[:200]:
            data.append([
                (l.get('created_at', '') or '')[:16].replace('T', ' '),
                (l.get('user_nome', '') or '')[:15], l.get('user_role', ''),
                l.get('entity_type', ''), l.get('action', ''),
                (l.get('details', '') or '')[:40]
            ])
        t = Table(data)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#10b981')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTSIZE',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),0.5,colors.grey)]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=auditoria_manutrix.pdf"})

# ============== ROOT ==============

@api_router.get("/")
async def root():
    return {"message": "MANUTRIX API v3.0.0", "status": "online"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def run_migrations():
    """Run all startup migrations"""
    try:
        # Create indexes
        await db.users.create_index("email")
        await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
        await db.password_reset_tokens.create_index("token")
        await db.sectors.create_index("organization_id")
        await db.ativos.create_index("sector_id")
        await db.ativos.create_index(
            [("tag", 1), ("sector_id", 1)],
            unique=True,
            partialFilterExpression={"deleted_at": None},
            name="unique_tag_per_area"
        )
        
        # Migration 1: checklist tipo field
        inspecoes = await db.inspecoes.find({"deleted_at": None, "checklist": {"$exists": True}}).to_list(1000)
        for insp in inspecoes:
            updated = False
            checklist = insp.get('checklist', [])
            for item in checklist:
                if 'tipo' not in item or not item['tipo']:
                    item['tipo'] = 'boolean'
                    updated = True
                if 'obrigatorio' not in item:
                    item['obrigatorio'] = True
                    updated = True
            if updated:
                await db.inspecoes.update_one({"_id": insp["_id"]}, {"$set": {"checklist": checklist}})
        
        rotas = await db.rotas_inspecao.find({"deleted_at": None, "itens": {"$exists": True}}).to_list(100)
        for rota in rotas:
            updated = False
            itens = rota.get('itens', [])
            for item in itens:
                if 'tipo' not in item or not item['tipo']:
                    item['tipo'] = 'boolean'
                    updated = True
            if updated:
                await db.rotas_inspecao.update_one({"_id": rota["_id"]}, {"$set": {"itens": itens}})
        logger.info("Migration: checklist tipo field verified")
        
        # Migration 2: Remove plant_id from sectors and ativos (Sector is now top-level)
        await db.sectors.update_many({}, {"$unset": {"plant_id": ""}})
        await db.ativos.update_many({}, {"$unset": {"plant_id": "", "area_id": ""}})
        logger.info("Migration: plant_id removed from sectors and ativos")
        
    except Exception as e:
        logger.error(f"Migration error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
