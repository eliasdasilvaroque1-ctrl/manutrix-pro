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
    return user.get('role') in ('admin', 'master')

def is_master(user: Dict) -> bool:
    return user.get('role') == 'master'

def check_write_permission(user: Dict, allowed_roles: list = None):
    role = user.get('role', '')
    if role == 'gerente':
        raise HTTPException(status_code=403, detail="Perfil Gerente possui apenas acesso de leitura")
    if role in ('admin', 'master'):
        return True
    if allowed_roles and role in allowed_roles:
        return True
    raise HTTPException(status_code=403, detail="Sem permissão para esta operação")

def check_admin_only(user: Dict):
    if user.get('role') not in ['admin', 'master']:
        raise HTTPException(status_code=403, detail="Apenas administradores podem realizar esta operação")

def check_master_only(user: Dict):
    if user.get('role') != 'master':
        raise HTTPException(status_code=403, detail="Apenas o Administrador Master pode realizar esta operação")

def check_pcm_or_admin(user: Dict):
    """PCM: estoque, sobressalentes, templates, relatórios, exportações"""
    if user.get('role') not in ['admin', 'master', 'pcm']:
        raise HTTPException(status_code=403, detail="Apenas Admin ou PCM podem realizar esta operação")

def check_not_gerente(user: Dict):
    """Gerente: somente leitura"""
    if user.get('role') == 'gerente':
        raise HTTPException(status_code=403, detail="Perfil Gerente possui apenas acesso de leitura")

def verify_org_access(user: Dict, document: dict, entity_name: str = "Registro"):
    """Verify that the user's organization matches the document's organization.
    Skips check if user has no org (legacy) or document has no org."""
    user_org = user.get('organization_id', '')
    doc_org = document.get('organization_id', '')
    if user_org and doc_org and user_org != doc_org:
        raise HTTPException(status_code=404, detail=f"{entity_name} não encontrado")


def can_export(user: Dict) -> bool:
    return user.get('role') in ['admin', 'master', 'pcm', 'gerente', 'supervisor']

def can_view_dashboard(user: Dict) -> bool:
    return user.get('role') in ['admin', 'master', 'pcm', 'gerente', 'supervisor']

def get_user_disciplinas(user: Dict) -> list:
    """Get all disciplines a user can see (principal + secondary)."""
    disciplinas = []
    dp = user.get('disciplina_principal')
    if dp:
        disciplinas.append(dp)
    for d in (user.get('disciplinas_secundarias') or []):
        if d and d not in disciplinas:
            disciplinas.append(d)
    return disciplinas

def user_has_full_visibility(user: Dict) -> bool:
    """Roles that see ALL data regardless of discipline/area."""
    return user.get('role') in ('master', 'admin', 'pcm', 'gerente')

def build_disciplina_filter(user: Dict) -> dict:
    """Build MongoDB filter for discipline-scoped queries. Returns {} for full-visibility roles."""
    if user_has_full_visibility(user):
        return {}
    disciplinas = get_user_disciplinas(user)
    if not disciplinas:
        return {}
    return {"disciplina": {"$in": disciplinas + [None, ""]}}


# ============== VISIBILITY ENGINE ==============

async def _get_asset_ids_for_areas(org_id: str, area_ids: list) -> list:
    """Resolve area (sector) IDs to asset IDs."""
    if not area_ids:
        return None
    q = {"deleted_at": None, "sector_id": {"$in": area_ids}}
    if org_id:
        q['organization_id'] = org_id
    assets = await db.ativos.find(q, {"_id": 0, "id": 1}).to_list(10000)
    return [a['id'] for a in assets]


async def build_visibility_query(user: Dict, entity_type: str = "os") -> dict:
    """Build MongoDB query filter enforcing role-based visibility.

    Visibility rules:
    - master:       All data across all organizations
    - admin:        All records of their organization
    - pcm:          All disciplines of their organization
    - gerente:      All records (read-only enforced elsewhere)
    - supervisor:   Only their disciplines + their areas
    - tecnico:      Only their disciplines + their areas + assigned activities
    - inspetor:     Same as tecnico for inspections
    - operador:     Only operational (NEVER mechanical/electrical OS)
    - viewer:       Only assigned items
    """
    role = user.get('role', '')
    org_id = user.get('organization_id', '')
    user_id = user.get('id', '')

    base = {"deleted_at": None}
    if org_id:
        base['organization_id'] = org_id

    # --- Full visibility roles ---
    if role == 'master':
        return base
    if role in ('admin', 'pcm', 'gerente'):
        return base

    # --- Supervisor: disciplines AND areas (combined), plus direct assignments ---
    if role == 'supervisor':
        disciplinas = get_user_disciplinas(user)
        area_ids = user.get('area_ids') or []

        # Build scope filter (discipline AND area)
        scope_filter = {}
        if disciplinas:
            scope_filter["disciplina"] = {"$in": disciplinas}
        if area_ids:
            asset_ids = await _get_asset_ids_for_areas(org_id, area_ids)
            if asset_ids is not None:
                scope_filter["ativo_id"] = {"$in": asset_ids}

        # OR: in scope, OR directly assigned
        or_conditions = []
        if scope_filter:
            or_conditions.append(scope_filter)
        or_conditions.append({"responsavel_id": user_id})
        if entity_type == "os":
            or_conditions.append({"equipe": user_id})
        elif entity_type == "inspecao":
            or_conditions.append({"executantes": user_id})

        if or_conditions:
            base["$or"] = or_conditions
        return base

    # --- Técnico / Inspetor: disciplines AND areas (combined), plus direct assignments ---
    if role in ('tecnico', 'inspetor'):
        disciplinas = get_user_disciplinas(user)
        area_ids = user.get('area_ids') or []

        # Build scope filter (discipline AND area)
        scope_filter = {}
        if disciplinas:
            scope_filter["disciplina"] = {"$in": disciplinas}
        if area_ids:
            asset_ids = await _get_asset_ids_for_areas(org_id, area_ids)
            if asset_ids is not None:
                scope_filter["ativo_id"] = {"$in": asset_ids}

        # OR: in scope, OR directly assigned
        or_conditions = []
        if scope_filter:
            or_conditions.append(scope_filter)
        or_conditions.append({"responsavel_id": user_id})
        if entity_type == "os":
            or_conditions.append({"equipe": user_id})
        elif entity_type == "inspecao":
            or_conditions.append({"executantes": user_id})

        if or_conditions:
            base["$or"] = or_conditions
        else:
            base["$or"] = [
                {"responsavel_id": user_id},
                {"equipe": user_id} if entity_type == "os" else {"executantes": user_id},
                {"criado_por": user_id},
            ]
        return base

    # --- Operador: NEVER sees mechanical/electrical/instrumentation OS ---
    if role == 'operador':
        if entity_type == "os":
            base["$or"] = [
                {"disciplina": {"$in": ["producao", "civil", None, ""]}},
                {"responsavel_id": user_id},
                {"equipe": user_id},
            ]
        elif entity_type == "inspecao":
            base["$or"] = [
                {"disciplina": {"$in": ["producao", "civil", None, ""]}},
                {"responsavel_id": user_id},
                {"executantes": user_id},
            ]
        elif entity_type == "ativo":
            area_ids = user.get('area_ids') or []
            if area_ids:
                base["sector_id"] = {"$in": area_ids}
        return base

    # --- Viewer / unknown: own assignments only ---
    own_conditions = [{"criado_por": user_id}]
    if entity_type == "os":
        own_conditions.extend([{"responsavel_id": user_id}, {"equipe": user_id}])
    elif entity_type == "inspecao":
        own_conditions.extend([{"responsavel_id": user_id}, {"executantes": user_id}])
    base["$or"] = own_conditions
    return base


async def build_dashboard_visibility(user: Dict) -> dict:
    """Build base query for dashboard/KPI/stats endpoints."""
    role = user.get('role', '')
    org_id = user.get('organization_id', '')

    base = {"deleted_at": None}
    if org_id:
        base['organization_id'] = org_id

    if role in ('master', 'admin', 'pcm', 'gerente'):
        return base

    # Supervisor: scope to their disciplines and areas
    if role == 'supervisor':
        conditions = {}
        disciplinas = get_user_disciplinas(user)
        area_ids = user.get('area_ids') or []
        if disciplinas:
            conditions["disciplina"] = {"$in": disciplinas}
        if area_ids:
            asset_ids = await _get_asset_ids_for_areas(org_id, area_ids)
            if asset_ids is not None:
                conditions["ativo_id"] = {"$in": asset_ids}
        base.update(conditions)
        return base

    # Técnico/Inspetor: scope to their disciplines and areas
    if role in ('tecnico', 'inspetor'):
        disciplinas = get_user_disciplinas(user)
        area_ids = user.get('area_ids') or []
        if disciplinas:
            base["disciplina"] = {"$in": disciplinas}
        if area_ids:
            asset_ids = await _get_asset_ids_for_areas(org_id, area_ids)
            if asset_ids is not None:
                base["ativo_id"] = {"$in": asset_ids}
        return base

    # Operador: only producao, never mecanica/eletrica
    if role == 'operador':
        base["disciplina"] = {"$in": ["producao", "civil", None, ""]}
        return base

    return base


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
        "user_nome": user.get('nome') or user.get('email', ''),
        "user_role": user.get('role'),
        "organization_id": user.get('organization_id'),
        "details": details,
        "changes": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

AUDIT_FIELD_LABELS = {
    'prioridade': 'Prioridade', 'status': 'Status', 'titulo': 'Título', 'descricao': 'Descrição',
    'descricao_servico': 'Serviço Executado', 'observacoes': 'Observações', 'causa_falha': 'Causa da Falha',
    'responsavel_id': 'Responsável', 'equipe': 'Executantes', 'data_planejada': 'Data Planejada',
    'tipo': 'Tipo', 'disciplina': 'Disciplina', 'severidade': 'Severidade',
    'nome': 'Nome', 'tag': 'TAG', 'fabricante': 'Fabricante', 'modelo': 'Modelo',
    'numero_serie': 'Nº Série', 'tipo_equipamento': 'Tipo Equipamento', 'sector_id': 'Área',
    'localizacao': 'Localização', 'quantidade': 'Quantidade', 'custo_unitario': 'Custo Unitário',
    'custo': 'Custo', 'custo_pecas': 'Custo Peças', 'custo_mao_obra': 'Custo M.O.',
    'origem': 'Origem', 'condicoes': 'Condições', 'categoria': 'Categoria',
    'sku': 'Código', 'unidade': 'Unidade', 'estoque_minimo': 'Estoque Mínimo',
    'frequencia': 'Frequência', 'resultado': 'Resultado',
}

SKIP_AUDIT_FIELDS = {'updated_at', 'alterado_por', 'deleted_at', '_id', 'id', 'organization_id', 'created_at'}

async def audit_field_changes(entity_type: str, entity_id: str, entity_label: str, old_doc: dict, new_data: dict, user: Dict, motivo: str = ""):
    """Compare old document with new data and log each field change"""
    changes = []
    for field, new_val in new_data.items():
        if field in SKIP_AUDIT_FIELDS:
            continue
        old_val = old_doc.get(field)
        # Normalize for comparison
        if old_val is None and new_val is None:
            continue
        if isinstance(old_val, float) and isinstance(new_val, (int, float)):
            if abs(old_val - new_val) < 0.001:
                continue
        if str(old_val) == str(new_val):
            continue
        label = AUDIT_FIELD_LABELS.get(field, field)
        changes.append({
            "campo": label,
            "campo_raw": field,
            "valor_anterior": old_val,
            "valor_novo": new_val
        })
    
    if not changes:
        return
    
    details_parts = [f"{c['campo']}: {c['valor_anterior']} → {c['valor_novo']}" for c in changes[:10]]
    details_text = f"{entity_label} — " + "; ".join(details_parts)
    if motivo:
        details_text += f" | Motivo: {motivo}"
    
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "field_change",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user.get('id'),
        "user_nome": user.get('nome') or user.get('email', ''),
        "user_role": user.get('role'),
        "organization_id": user.get('organization_id'),
        "details": details_text,
        "changes": changes,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

async def audit_denial(user: Dict, endpoint: str, reason: str):
    """Log 403 permission denials"""
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": "access_denied",
        "entity_type": "security",
        "entity_id": endpoint,
        "user_id": user.get('id'),
        "user_nome": user.get('nome') or user.get('email', ''),
        "user_role": user.get('role'),
        "organization_id": user.get('organization_id'),
        "details": f"403 - {reason}",
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
