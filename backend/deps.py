"""Shared dependencies: DB, auth, permissions, helpers"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict
from datetime import datetime, timezone, timedelta
import os
import logging
import hashlib
import secrets
import string
import uuid
import jwt as pyjwt
import bcrypt

from models import Notificacao, NotificacaoTipo

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

supabase_client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    from supabase import create_client
    supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Supabase client initialized")

# Uploads
UPLOAD_DIR = ROOT_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
MANUALS_DIR = ROOT_DIR / 'uploads' / 'manuals'
MANUALS_DIR.mkdir(parents=True, exist_ok=True)

security = HTTPBearer()


# ============== AUTH HELPERS ==============

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def create_token(user_id: str, role: str, org_id: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "org": org_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    try:
        payload = pyjwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"], "deleted_at": None}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return user
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


# ============== PERMISSION HELPERS ==============

def is_admin(user: Dict) -> bool:
    return user.get('role') == 'admin'

def check_write_permission(user: Dict, allowed_roles: list = None):
    if is_admin(user):
        return True
    if allowed_roles and user.get('role') in allowed_roles:
        return True
    raise HTTPException(status_code=403, detail="Sem permissão para esta operação")

def check_admin_only(user: Dict):
    if user.get('role') not in ['admin']:
        raise HTTPException(status_code=403, detail="Apenas administradores podem realizar esta operação")

def check_pcm_or_admin(user: Dict):
    """PCM: estoque, sobressalentes, templates, relatórios, exportações"""
    if user.get('role') not in ['admin', 'pcm']:
        raise HTTPException(status_code=403, detail="Apenas Admin ou PCM podem realizar esta operação")

def check_not_gerente(user: Dict):
    """Gerente: somente leitura"""
    if user.get('role') == 'gerente':
        raise HTTPException(status_code=403, detail="Perfil Gerente possui apenas acesso de leitura")

def can_export(user: Dict) -> bool:
    return user.get('role') in ['admin', 'pcm', 'gerente', 'supervisor']

def can_view_dashboard(user: Dict) -> bool:
    return user.get('role') in ['admin', 'pcm', 'gerente', 'supervisor']


# ============== UTILITY HELPERS ==============

def generate_tag(prefix: str = "EQP") -> str:
    suffix = ''.join(secrets.choice(string.digits) for _ in range(3))
    return f"{prefix}-{suffix}"

def generate_sku(prefix: str = "SKU") -> str:
    suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{suffix}"

async def generate_os_numero(org_id: str) -> str:
    ano = datetime.now().year
    count = await db.ordens_servico.count_documents({"organization_id": org_id})
    return f"{ano}-{str(count + 1).zfill(5)}"

async def audit_log(action: str, entity_type: str, entity_id: str, user: Dict, details: str = ""):
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user.get('id'),
        "user_nome": user.get('nome'),
        "user_role": user.get('role'),
        "details": details,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

async def criar_notificacao(usuario_id: str, org_id: str, tipo: NotificacaoTipo, titulo: str, mensagem: str, link: str = None):
    notif = Notificacao(
        usuario_id=usuario_id,
        organization_id=org_id,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        link=link
    )
    doc = notif.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.notificacoes.insert_one(doc)

async def verificar_estoque_critico(item_id: str, org_id: str):
    item = await db.itens_estoque.find_one({"id": item_id}, {"_id": 0})
    if item and item.get('alertar_minimo') and item.get('quantidade', 0) <= item.get('estoque_minimo', 0):
        admins = await db.users.find(
            {"organization_id": org_id, "role": {"$in": ["admin", "supervisor"]}, "deleted_at": None},
            {"_id": 0, "id": 1}
        ).to_list(10)
        for admin in admins:
            await criar_notificacao(
                admin['id'], org_id, NotificacaoTipo.ESTOQUE_CRITICO,
                f"Estoque Crítico: {item.get('nome', '')}",
                f"Quantidade: {item.get('quantidade')} {item.get('unidade', 'UN')} (Mínimo: {item.get('estoque_minimo')})",
                "/estoque"
            )

async def get_scoped_asset_ids(org_id: str, sector_id: str = None) -> list:
    if not sector_id:
        return None
    q = {"deleted_at": None}
    if org_id:
        q['organization_id'] = org_id
    if sector_id:
        q['sector_id'] = sector_id
    matching = await db.ativos.find(q, {"_id": 0, "id": 1}).to_list(5000)
    return [a['id'] for a in matching]
