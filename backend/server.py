from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Upload directory
UPLOAD_DIR = ROOT_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="MANUTRIX API", version="3.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== ENUMS ==============

class UserRole(str, Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    TECNICO = "tecnico"
    INSPETOR = "inspetor"
    VIEWER = "viewer"

class AssetStatus(str, Enum):
    OPERACIONAL = "operacional"
    PARADO = "parado"
    MANUTENCAO = "manutencao"
    DESATIVADO = "desativado"

class Criticidade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class OSStatus(str, Enum):
    ABERTA = "aberta"
    PLANEJADA = "planejada"
    EM_EXECUCAO = "em_execucao"
    PAUSADA = "pausada"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"

class OSTipo(str, Enum):
    PREVENTIVA = "preventiva"
    CORRETIVA = "corretiva"
    PREDITIVA = "preditiva"
    EMERGENCIA = "emergencia"
    FALHA = "falha"

class OSOrigem(str, Enum):
    INSPECAO = "inspecao"
    MANUAL = "manual"
    PREVENTIVA = "preventiva"
    PREDITIVA = "preditiva"
    EMERGENCIA = "emergencia"
    AGENDAMENTO_IA = "agendamento_ia"
    FALHA = "falha"

class InspecaoStatus(str, Enum):
    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    COM_PENDENCIAS = "com_pendencias"

class InspecaoResultado(str, Enum):
    CONFORME = "conforme"
    NAO_CONFORME = "nao_conforme"
    PENDENTE = "pendente"

class CategoriaEstoque(str, Enum):
    ROLAMENTO = "rolamento"
    LUBRIFICANTE = "lubrificante"
    ELETRICA = "eletrica"
    MECANICA = "mecanica"
    INSTRUMENTACAO = "instrumentacao"
    VEDACAO = "vedacao"
    FILTRO = "filtro"
    CORREIA = "correia"
    OUTROS = "outros"

class UnidadeEstoque(str, Enum):
    UN = "UN"
    L = "L"
    KG = "KG"
    M = "M"
    PC = "PC"
    CX = "CX"

class NotificacaoTipo(str, Enum):
    OS_CRIADA = "os_criada"
    OS_ATRASADA = "os_atrasada"
    OS_ATRIBUIDA = "os_atribuida"
    INSPECAO_PENDENTE = "inspecao_pendente"
    ESTOQUE_CRITICO = "estoque_critico"
    FALHA_DETECTADA = "falha_detectada"
    ATIVO_PARADO = "ativo_parado"

# ============== MODELS ==============

# User Models
class UserBase(BaseModel):
    email: EmailStr
    nome: str
    role: UserRole = UserRole.TECNICO
    organization_id: Optional[str] = None
    telefone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# Organization
class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    cnpj: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Planta
class Planta(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    endereco: Optional[str] = None
    organization_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Area
class Area(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    planta_id: str
    cor: str = "#10b981"
    descricao: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Ativo - CRUD Completo
class AtivoCreate(BaseModel):
    tag: Optional[str] = None  # Auto-generate if not provided
    nome: str
    tipo_equipamento: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    area_id: str
    centro_custo: Optional[str] = None
    criticidade: Criticidade = Criticidade.MEDIA
    status: AssetStatus = AssetStatus.OPERACIONAL
    mtbf_horas: Optional[float] = None
    mttr_horas: Optional[float] = None
    data_instalacao: Optional[str] = None
    garantia_ate: Optional[str] = None
    valor_aquisicao: Optional[float] = None
    depreciacao_anual: Optional[float] = None
    fornecedor: Optional[str] = None
    foto_url: Optional[str] = None
    manual_url: Optional[str] = None
    observacoes: Optional[str] = None

class AtivoUpdate(BaseModel):
    nome: Optional[str] = None
    tipo_equipamento: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    area_id: Optional[str] = None
    centro_custo: Optional[str] = None
    criticidade: Optional[Criticidade] = None
    status: Optional[AssetStatus] = None
    mtbf_horas: Optional[float] = None
    mttr_horas: Optional[float] = None
    data_instalacao: Optional[str] = None
    garantia_ate: Optional[str] = None
    valor_aquisicao: Optional[float] = None
    depreciacao_anual: Optional[float] = None
    fornecedor: Optional[str] = None
    foto_url: Optional[str] = None
    manual_url: Optional[str] = None
    observacoes: Optional[str] = None

# Estoque - CRUD Completo
class EstoqueCreate(BaseModel):
    sku: Optional[str] = None  # Auto-generate if not provided
    nome: str
    descricao: Optional[str] = None
    categoria: CategoriaEstoque = CategoriaEstoque.OUTROS
    quantidade: float = 0
    estoque_minimo: float = 0
    estoque_maximo: Optional[float] = None
    unidade: UnidadeEstoque = UnidadeEstoque.UN
    custo_unitario: float = 0
    fornecedor: Optional[str] = None
    almoxarifado: Optional[str] = "Principal"
    prateleira: Optional[str] = None
    posicao: Optional[str] = None
    alertar_minimo: bool = True
    item_critico: bool = False

class EstoqueUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[CategoriaEstoque] = None
    quantidade: Optional[float] = None
    estoque_minimo: Optional[float] = None
    estoque_maximo: Optional[float] = None
    unidade: Optional[UnidadeEstoque] = None
    custo_unitario: Optional[float] = None
    fornecedor: Optional[str] = None
    almoxarifado: Optional[str] = None
    prateleira: Optional[str] = None
    posicao: Optional[str] = None
    alertar_minimo: Optional[bool] = None
    item_critico: Optional[bool] = None

# OS - CRUD Completo
class OSCreate(BaseModel):
    ativo_id: str
    tipo: OSTipo = OSTipo.CORRETIVA
    origem: OSOrigem = OSOrigem.MANUAL
    prioridade: Criticidade = Criticidade.MEDIA
    titulo: str
    descricao: Optional[str] = None
    responsavel_id: Optional[str] = None
    equipe: Optional[List[str]] = None
    data_planejada: Optional[str] = None
    custo_pecas: float = 0
    custo_mao_obra: float = 0

class OSUpdate(BaseModel):
    tipo: Optional[OSTipo] = None
    prioridade: Optional[Criticidade] = None
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[OSStatus] = None
    responsavel_id: Optional[str] = None
    equipe: Optional[List[str]] = None
    data_planejada: Optional[str] = None
    custo_pecas: Optional[float] = None
    custo_mao_obra: Optional[float] = None
    observacoes: Optional[str] = None

# Inspeção - CRUD Completo
class ChecklistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    descricao: str
    tipo: str = "boolean"  # boolean, numero, texto
    valor_esperado: Optional[str] = None
    tolerancia_min: Optional[float] = None
    tolerancia_max: Optional[float] = None
    unidade: Optional[str] = None
    obrigatorio: bool = True
    resultado: Optional[Any] = None
    conforme: Optional[bool] = None
    observacao: Optional[str] = None

class InspecaoCreate(BaseModel):
    ativo_id: str
    rota_id: Optional[str] = None
    responsavel_id: str
    tipo: str = "checklist"
    checklist: Optional[List[ChecklistItem]] = None

class InspecaoUpdate(BaseModel):
    status: Optional[InspecaoStatus] = None
    resultado: Optional[InspecaoResultado] = None
    checklist: Optional[List[Dict]] = None
    observacoes: Optional[str] = None

# Rota de Inspeção
class RotaInspecaoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    tipo_ativo: str
    frequencia: str = "mensal"
    tempo_estimado_minutos: int = 15
    itens: List[ChecklistItem] = []
    ativa: bool = True

# Notificação
class Notificacao(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    usuario_id: str
    organization_id: str
    tipo: NotificacaoTipo
    titulo: str
    mensagem: str
    link: Optional[str] = None
    lida: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Movimentação Estoque
class MovimentacaoEstoque(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    tipo: str  # entrada, saida, ajuste
    quantidade: float
    custo_unitario: Optional[float] = None
    motivo: Optional[str] = None
    os_id: Optional[str] = None
    usuario_id: str
    organization_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== HELPER FUNCTIONS ==============

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_token(user_id: str, role: str, org_id: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "org": org_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["sub"], "deleted_at": None}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def generate_tag(prefix: str = "EQP") -> str:
    """Generate unique TAG like EQP-001"""
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}-{suffix}"

def generate_sku(prefix: str = "SKU") -> str:
    """Generate unique SKU like SKU-A1B2C3"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{suffix}"

async def generate_os_numero(org_id: str) -> str:
    """Generate OS number like 2026-00001"""
    ano = datetime.now().year
    count = await db.ordens_servico.count_documents({"organization_id": org_id})
    return f"{ano}-{str(count + 1).zfill(5)}"

def is_admin(user: Dict) -> bool:
    """Admin bypass - admin can do everything"""
    return user.get('role') == 'admin'

def check_write_permission(user: Dict, allowed_roles: list = None):
    """Check if user has write permission. Admin always passes."""
    if is_admin(user):
        return True
    if allowed_roles and user.get('role') in allowed_roles:
        return True
    raise HTTPException(status_code=403, detail="Sem permissão para esta operação")

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
    """Check if stock is critical and create notification"""
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
    user = await db.users.find_one({"email": credentials.email, "deleted_at": None}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token = create_token(user['id'], user['role'], user.get('organization_id', ''))
    return TokenResponse(
        access_token=token,
        user={
            "id": user['id'], "email": user['email'], "nome": user['nome'],
            "role": user['role'], "organization_id": user.get('organization_id'),
            "telefone": user.get('telefone')
        }
    )

@api_router.get("/auth/me")
async def get_me(user: Dict = Depends(get_current_user)):
    return {k: v for k, v in user.items() if k != 'password_hash'}

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

# ============== AREAS ==============

@api_router.get("/areas")
async def list_areas(planta_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if planta_id:
        query['planta_id'] = planta_id
    return await db.areas.find(query, {"_id": 0}).to_list(100)

@api_router.get("/areas/{area_id}")
async def get_area(area_id: str, user: Dict = Depends(get_current_user)):
    area = await db.areas.find_one({"id": area_id, "deleted_at": None}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    return area

# ============== ATIVOS - CRUD COMPLETO ==============

@api_router.get("/ativos")
async def list_ativos(
    area_id: Optional[str] = None,
    status: Optional[AssetStatus] = None,
    criticidade: Optional[Criticidade] = None,
    search: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if area_id:
        query['area_id'] = area_id
    if status:
        query['status'] = status.value
    if criticidade:
        query['criticidade'] = criticidade.value
    
    ativos = await db.ativos.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    if search:
        search_lower = search.lower()
        ativos = [a for a in ativos if search_lower in a.get('tag', '').lower() or search_lower in a.get('nome', '').lower()]
    
    # Enrich with area info
    for ativo in ativos:
        area = await db.areas.find_one({"id": ativo.get('area_id')}, {"_id": 0, "nome": 1, "cor": 1})
        ativo['area'] = area
    
    return ativos

@api_router.get("/ativos/{ativo_id}")
async def get_ativo(ativo_id: str, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    # Enrich with area, recent OS, and inspections
    area = await db.areas.find_one({"id": ativo.get('area_id')}, {"_id": 0})
    ativo['area'] = area
    
    ativo['ordens_servico'] = await db.ordens_servico.find(
        {"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    ativo['inspecoes'] = await db.inspecoes.find(
        {"ativo_id": ativo_id, "deleted_at": None}, {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Calculate statistics
    os_total = await db.ordens_servico.count_documents({"ativo_id": ativo_id, "deleted_at": None})
    os_corretivas = await db.ordens_servico.count_documents({"ativo_id": ativo_id, "tipo": "corretiva", "deleted_at": None})
    ativo['estatisticas'] = {
        "total_os": os_total,
        "os_corretivas": os_corretivas,
        "os_preventivas": os_total - os_corretivas
    }
    
    return ativo

@api_router.get("/ativos/qr/{qr_code}")
async def get_ativo_by_qr(qr_code: str, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"qr_code": qr_code, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return ativo

@api_router.get("/ativos/tag/{tag}")
async def get_ativo_by_tag(tag: str, user: Dict = Depends(get_current_user)):
    query = {"tag": tag.upper(), "deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    ativo = await db.ativos.find_one(query, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return ativo

@api_router.post("/ativos")
async def create_ativo(data: AtivoCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor'])
    area = await db.areas.find_one({"id": data.area_id}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    
    planta = await db.plantas.find_one({"id": area.get('planta_id')}, {"_id": 0})
    org_id = planta.get('organization_id') if planta else user.get('organization_id', '')
    
    # Generate TAG if not provided
    tag = data.tag.upper() if data.tag else generate_tag()
    
    # Check TAG uniqueness
    existing = await db.ativos.find_one({"tag": tag, "organization_id": org_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="TAG já existe nesta organização")
    
    ativo_id = str(uuid.uuid4())
    ativo_doc = {
        "id": ativo_id,
        "tag": tag,
        "qr_code": str(uuid.uuid4()),
        "nome": data.nome,
        "tipo_equipamento": data.tipo_equipamento,
        "fabricante": data.fabricante,
        "modelo": data.modelo,
        "numero_serie": data.numero_serie,
        "area_id": data.area_id,
        "organization_id": org_id,
        "centro_custo": data.centro_custo,
        "criticidade": data.criticidade.value,
        "status": data.status.value,
        "mtbf_horas": data.mtbf_horas,
        "mttr_horas": data.mttr_horas,
        "data_instalacao": data.data_instalacao,
        "garantia_ate": data.garantia_ate,
        "valor_aquisicao": data.valor_aquisicao,
        "depreciacao_anual": data.depreciacao_anual,
        "fornecedor": data.fornecedor,
        "foto_url": data.foto_url,
        "manual_url": data.manual_url,
        "observacoes": data.observacoes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    
    await db.ativos.insert_one(ativo_doc)
    ativo_doc.pop('_id', None)
    return ativo_doc

@api_router.put("/ativos/{ativo_id}")
async def update_ativo(ativo_id: str, data: AtivoUpdate, user: Dict = Depends(get_current_user)):
    existing = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    update_data = {k: v.value if isinstance(v, Enum) else v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Check if status changed to PARADO and create notification
    if 'status' in update_data and update_data['status'] == 'parado' and existing.get('status') != 'parado':
        admins = await db.users.find(
            {"organization_id": existing.get('organization_id'), "role": {"$in": ["admin", "supervisor"]}, "deleted_at": None},
            {"_id": 0, "id": 1}
        ).to_list(10)
        for admin in admins:
            await criar_notificacao(
                admin['id'], existing.get('organization_id', ''), NotificacaoTipo.ATIVO_PARADO,
                f"Ativo Parado: {existing.get('tag', '')}",
                f"{existing.get('nome', '')} foi marcado como parado",
                f"/ativos/{ativo_id}"
            )
    
    await db.ativos.update_one({"id": ativo_id}, {"$set": update_data})
    return await db.ativos.find_one({"id": ativo_id}, {"_id": 0})

@api_router.delete("/ativos/{ativo_id}")
async def delete_ativo(ativo_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin'])
    existing = await db.ativos.find_one({"id": ativo_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    # Soft delete
    await db.ativos.update_one(
        {"id": ativo_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "message": "Ativo excluído com sucesso"}

# ============== ESTOQUE - CRUD COMPLETO ==============

@api_router.get("/estoque")
async def list_estoque(
    categoria: Optional[CategoriaEstoque] = None,
    critico: Optional[bool] = None,
    search: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if categoria:
        query['categoria'] = categoria.value
    
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
    check_write_permission(user, ['admin', 'supervisor'])
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
        "categoria": data.categoria.value,
        "quantidade": data.quantidade,
        "estoque_minimo": data.estoque_minimo,
        "estoque_maximo": data.estoque_maximo,
        "unidade": data.unidade.value,
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
    check_write_permission(user, ['admin'])
    existing = await db.itens_estoque.find_one({"id": item_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    await db.itens_estoque.update_one(
        {"id": item_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "message": "Item excluído com sucesso"}

class MovimentacaoCreateBody(BaseModel):
    tipo: str  # entrada, saida, ajuste
    quantidade: float
    motivo: Optional[str] = None
    custo_unitario: Optional[float] = None

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

# ============== ORDENS DE SERVIÇO - CRUD COMPLETO ==============

@api_router.get("/ordens-servico")
async def list_os(
    status: Optional[OSStatus] = None,
    tipo: Optional[OSTipo] = None,
    prioridade: Optional[Criticidade] = None,
    responsavel_id: Optional[str] = None,
    ativo_id: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if status:
        query['status'] = status.value
    if tipo:
        query['tipo'] = tipo.value
    if prioridade:
        query['prioridade'] = prioridade.value
    if responsavel_id:
        query['responsavel_id'] = responsavel_id
    if ativo_id:
        query['ativo_id'] = ativo_id
    
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Enrich with ativo and responsavel info
    for os in os_list:
        ativo = await db.ativos.find_one({"id": os.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
        os['ativo'] = ativo
        if os.get('responsavel_id'):
            resp = await db.users.find_one({"id": os['responsavel_id']}, {"_id": 0, "nome": 1})
            os['responsavel'] = resp
        
        # Check if overdue
        if os.get('data_planejada') and os.get('status') not in ['concluida', 'cancelada']:
            planned = datetime.fromisoformat(os['data_planejada'].replace('Z', '+00:00')) if isinstance(os['data_planejada'], str) else os['data_planejada']
            os['atrasada'] = datetime.now(timezone.utc) > planned
        else:
            os['atrasada'] = False
    
    return os_list

@api_router.get("/ordens-servico/estatisticas")
async def os_estatisticas(user: Dict = Depends(get_current_user)):
    """Get OS statistics for dashboard"""
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    
    # Count by status
    status_counts = {}
    for status in OSStatus:
        status_counts[status.value] = await db.ordens_servico.count_documents({**query, "status": status.value})
    
    # Count by type
    tipo_counts = {}
    for tipo in OSTipo:
        tipo_counts[tipo.value] = await db.ordens_servico.count_documents({**query, "tipo": tipo.value})
    
    # Count by priority
    prioridade_counts = {}
    for prio in Criticidade:
        prioridade_counts[prio.value] = await db.ordens_servico.count_documents({**query, "prioridade": prio.value})
    
    # Count overdue
    now = datetime.now(timezone.utc).isoformat()
    atrasadas = await db.ordens_servico.count_documents({
        **query,
        "status": {"$nin": ["concluida", "cancelada"]},
        "data_planejada": {"$lt": now}
    })
    
    # Monthly statistics
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0).isoformat()
    concluidas_mes = await db.ordens_servico.count_documents({
        **query, "status": "concluida", "data_conclusao": {"$gte": month_start}
    })
    
    return {
        "por_status": status_counts,
        "por_tipo": tipo_counts,
        "por_prioridade": prioridade_counts,
        "atrasadas": atrasadas,
        "concluidas_mes": concluidas_mes,
        "total_abertas": status_counts.get('aberta', 0) + status_counts.get('planejada', 0) + status_counts.get('em_execucao', 0) + status_counts.get('pausada', 0)
    }

@api_router.get("/ordens-servico/backlog")
async def get_backlog(user: Dict = Depends(get_current_user)):
    query = {
        "deleted_at": None,
        "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}
    }
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", 1).to_list(500)
    
    enriched = []
    for os in os_list:
        ativo = await db.ativos.find_one({"id": os.get('ativo_id')}, {"_id": 0})
        created = datetime.fromisoformat(os['created_at'].replace('Z', '+00:00')) if isinstance(os['created_at'], str) else os['created_at']
        days_open = (datetime.now(timezone.utc) - created).days
        
        # Priority color
        prio = os.get('prioridade', 'media')
        if days_open > 7 or prio == 'critica':
            cor = 'vermelho'
        elif days_open > 3 or prio == 'alta':
            cor = 'amarelo'
        else:
            cor = 'verde'
        
        enriched.append({**os, "ativo": ativo, "dias_aberto": days_open, "cor_prioridade": cor})
    
    return enriched

@api_router.get("/ordens-servico/{os_id}")
async def get_os(os_id: str, user: Dict = Depends(get_current_user)):
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
    # Enrich
    os['ativo'] = await db.ativos.find_one({"id": os.get('ativo_id')}, {"_id": 0})
    if os.get('responsavel_id'):
        os['responsavel'] = await db.users.find_one({"id": os['responsavel_id']}, {"_id": 0, "nome": 1, "email": 1, "telefone": 1})
    if os.get('inspecao_origem_id'):
        os['inspecao_origem'] = await db.inspecoes.find_one({"id": os['inspecao_origem_id']}, {"_id": 0})
    
    return os

@api_router.post("/ordens-servico")
async def create_os(data: OSCreate, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin', 'supervisor', 'tecnico'])
    ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    org_id = ativo.get('organization_id', user.get('organization_id', ''))
    numero = await generate_os_numero(org_id)
    
    os_id = str(uuid.uuid4())
    os_doc = {
        "id": os_id,
        "numero": numero,
        "ativo_id": data.ativo_id,
        "organization_id": org_id,
        "tipo": data.tipo.value,
        "origem": data.origem.value,
        "prioridade": data.prioridade.value,
        "titulo": data.titulo,
        "descricao": data.descricao,
        "status": "aberta",
        "responsavel_id": data.responsavel_id,
        "equipe": data.equipe or [],
        "data_abertura": datetime.now(timezone.utc).isoformat(),
        "data_planejada": data.data_planejada,
        "data_inicio": None,
        "data_conclusao": None,
        "custo_pecas": data.custo_pecas,
        "custo_mao_obra": data.custo_mao_obra,
        "custo_total": data.custo_pecas + data.custo_mao_obra,
        "tempo_execucao_minutos": None,
        "observacoes": None,
        "fotos": [],
        "pecas_utilizadas": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    
    await db.ordens_servico.insert_one(os_doc)
    
    # Notify assigned technician
    if data.responsavel_id:
        await criar_notificacao(
            data.responsavel_id, org_id, NotificacaoTipo.OS_ATRIBUIDA,
            f"Nova OS atribuída: #{numero}",
            f"Ativo: {ativo.get('tag', '')} - {data.titulo}",
            f"/os/{os_id}"
        )
    
    os_doc.pop('_id', None)
    return os_doc

@api_router.put("/ordens-servico/{os_id}")
async def update_os(os_id: str, data: OSUpdate, user: Dict = Depends(get_current_user)):
    existing = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
    update_data = {k: v.value if isinstance(v, Enum) else v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Handle status transitions
    if 'status' in update_data:
        new_status = update_data['status']
        if new_status == 'em_execucao' and not existing.get('data_inicio'):
            update_data['data_inicio'] = datetime.now(timezone.utc).isoformat()
        elif new_status == 'concluida':
            update_data['data_conclusao'] = datetime.now(timezone.utc).isoformat()
            if existing.get('data_inicio'):
                start = datetime.fromisoformat(existing['data_inicio'].replace('Z', '+00:00'))
                update_data['tempo_execucao_minutos'] = int((datetime.now(timezone.utc) - start).total_seconds() / 60)
    
    # Recalculate total cost
    if 'custo_pecas' in update_data or 'custo_mao_obra' in update_data:
        pecas = update_data.get('custo_pecas', existing.get('custo_pecas', 0))
        mao_obra = update_data.get('custo_mao_obra', existing.get('custo_mao_obra', 0))
        update_data['custo_total'] = pecas + mao_obra
    
    await db.ordens_servico.update_one({"id": os_id}, {"$set": update_data})
    return await db.ordens_servico.find_one({"id": os_id}, {"_id": 0})

@api_router.delete("/ordens-servico/{os_id}")
async def delete_os(os_id: str, user: Dict = Depends(get_current_user)):
    check_write_permission(user, ['admin'])
    existing = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None})
    if not existing:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
    await db.ordens_servico.update_one(
        {"id": os_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "message": "OS excluída com sucesso"}

@api_router.post("/ordens-servico/{os_id}/iniciar")
async def iniciar_os(os_id: str, user: Dict = Depends(get_current_user)):
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
    await db.ordens_servico.update_one(
        {"id": os_id},
        {"$set": {
            "status": "em_execucao",
            "data_inicio": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"success": True, "message": "OS iniciada"}

@api_router.post("/ordens-servico/{os_id}/pausar")
async def pausar_os(os_id: str, user: Dict = Depends(get_current_user)):
    await db.ordens_servico.update_one(
        {"id": os_id},
        {"$set": {"status": "pausada", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True, "message": "OS pausada"}

class ConcluirOSBody(BaseModel):
    observacoes: Optional[str] = None

@api_router.post("/ordens-servico/{os_id}/concluir")
async def concluir_os(os_id: str, body: ConcluirOSBody = ConcluirOSBody(), user: Dict = Depends(get_current_user)):
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
    tempo = None
    if os.get('data_inicio'):
        start = datetime.fromisoformat(os['data_inicio'].replace('Z', '+00:00'))
        tempo = int((datetime.now(timezone.utc) - start).total_seconds() / 60)
    
    await db.ordens_servico.update_one(
        {"id": os_id},
        {"$set": {
            "status": "concluida",
            "data_conclusao": datetime.now(timezone.utc).isoformat(),
            "tempo_execucao_minutos": tempo,
            "observacoes": body.observacoes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update asset status to operational
    await db.ativos.update_one(
        {"id": os.get('ativo_id')},
        {"$set": {"status": "operacional", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"success": True, "tempo_execucao_minutos": tempo}

# ============== INSPEÇÕES - CRUD COMPLETO ==============

@api_router.get("/inspecoes")
async def list_inspecoes(
    status: Optional[InspecaoStatus] = None,
    ativo_id: Optional[str] = None,
    responsavel_id: Optional[str] = None,
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
    
    inspecoes = await db.inspecoes.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    for insp in inspecoes:
        ativo = await db.ativos.find_one({"id": insp.get('ativo_id')}, {"_id": 0, "tag": 1, "nome": 1})
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
    if insp.get('responsavel_id'):
        insp['responsavel'] = await db.users.find_one({"id": insp['responsavel_id']}, {"_id": 0, "nome": 1, "email": 1})
    if insp.get('rota_id'):
        insp['rota'] = await db.rotas_inspecao.find_one({"id": insp['rota_id']}, {"_id": 0})
    if insp.get('os_gerada_id'):
        insp['os_gerada'] = await db.ordens_servico.find_one({"id": insp['os_gerada_id']}, {"_id": 0})
    
    return insp

@api_router.post("/inspecoes")
async def create_inspecao(data: InspecaoCreate, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    org_id = ativo.get('organization_id', user.get('organization_id', ''))
    
    # Get checklist from rota if provided
    checklist = data.checklist or []
    if data.rota_id and not checklist:
        rota = await db.rotas_inspecao.find_one({"id": data.rota_id}, {"_id": 0})
        if rota:
            checklist = rota.get('itens', [])
    
    # Default checklist if none
    if not checklist:
        checklist = [
            {"id": str(uuid.uuid4()), "descricao": "Vibração OK", "tipo": "boolean", "obrigatorio": True},
            {"id": str(uuid.uuid4()), "descricao": "Temperatura OK", "tipo": "boolean", "obrigatorio": True},
            {"id": str(uuid.uuid4()), "descricao": "Ruído OK", "tipo": "boolean", "obrigatorio": True},
            {"id": str(uuid.uuid4()), "descricao": "Vazamento OK", "tipo": "boolean", "obrigatorio": True},
            {"id": str(uuid.uuid4()), "descricao": "Observações", "tipo": "texto", "obrigatorio": False},
        ]
    
    insp_id = str(uuid.uuid4())
    insp_doc = {
        "id": insp_id,
        "ativo_id": data.ativo_id,
        "rota_id": data.rota_id,
        "responsavel_id": data.responsavel_id,
        "organization_id": org_id,
        "tipo": data.tipo,
        "status": "pendente",
        "resultado": "pendente",
        "checklist": checklist,
        "data_programada": datetime.now(timezone.utc).isoformat(),
        "data_inicio": None,
        "data_conclusao": None,
        "duracao_minutos": None,
        "observacoes": None,
        "fotos": [],
        "os_gerada_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    
    await db.inspecoes.insert_one(insp_doc)
    
    # Notify responsible
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
    existing = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    
    update_data = {k: v.value if isinstance(v, Enum) else v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
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
    await db.inspecoes.update_one(
        {"id": inspecao_id},
        {"$set": {
            "status": "em_andamento",
            "data_inicio": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"success": True}

class ConcluirInspecaoBody(BaseModel):
    checklist: List[Dict[str, Any]]
    observacoes: Optional[str] = None

@api_router.post("/inspecoes/{inspecao_id}/concluir")
async def concluir_inspecao(
    inspecao_id: str,
    body: ConcluirInspecaoBody,
    user: Dict = Depends(get_current_user)
):
    checklist = body.checklist
    observacoes = body.observacoes
    insp = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None}, {"_id": 0})
    if not insp:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    
    # Determine result
    nao_conformes = [item for item in checklist if item.get('conforme') == False]
    resultado = "nao_conforme" if nao_conformes else "conforme"
    status = "com_pendencias" if nao_conformes else "concluida"
    
    # Calculate duration
    duracao = None
    if insp.get('data_inicio'):
        start = datetime.fromisoformat(insp['data_inicio'].replace('Z', '+00:00'))
        duracao = int((datetime.now(timezone.utc) - start).total_seconds() / 60)
    
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
            "prioridade": ativo.get('criticidade', 'media'),
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
        await db.ativos.update_one(
            {"id": insp.get('ativo_id')},
            {"$set": {"status": "manutencao", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Notify
        admins = await db.users.find(
            {"organization_id": org_id, "role": {"$in": ["admin", "supervisor"]}, "deleted_at": None},
            {"_id": 0, "id": 1}
        ).to_list(10)
        for admin in admins:
            await criar_notificacao(
                admin['id'], org_id, NotificacaoTipo.FALHA_DETECTADA,
                f"Falha detectada: {ativo.get('tag', '')}",
                f"Inspeção não conforme - OS #{numero} gerada",
                f"/os/{os_id}"
            )
    else:
        # Update asset status to operational
        await db.ativos.update_one(
            {"id": insp.get('ativo_id')},
            {"$set": {"status": "operacional", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
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
        "itens": [item.model_dump() for item in data.itens],
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
    areas = await db.areas.find({"deleted_at": None}, {"_id": 0}).to_list(100)
    
    result = []
    for area in areas:
        ativos_count = await db.ativos.count_documents({"area_id": area['id'], "deleted_at": None})
        insp_pendentes = await db.inspecoes.count_documents({
            "status": {"$in": ["pendente", "em_andamento"]},
            "deleted_at": None
        })
        result.append({"area": area, "total_ativos": ativos_count, "inspecoes_pendentes": insp_pendentes})
    
    return result

@api_router.get("/ronda/{area_id}")
async def get_ronda(area_id: str, user: Dict = Depends(get_current_user)):
    area = await db.areas.find_one({"id": area_id, "deleted_at": None}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    
    ativos = await db.ativos.find({"area_id": area_id, "deleted_at": None}, {"_id": 0}).to_list(500)
    rotas = await db.rotas_inspecao.find({"deleted_at": None, "ativa": True}, {"_id": 0}).to_list(100)
    
    ronda_ativos = []
    for idx, ativo in enumerate(ativos):
        rota = rotas[0] if rotas else None
        ultima_insp = await db.inspecoes.find_one(
            {"ativo_id": ativo['id'], "status": {"$nin": ["pendente", "em_andamento"]}, "deleted_at": None},
            {"_id": 0}
        )
        ronda_ativos.append({
            "ativo": ativo,
            "rota": rota,
            "inspecao_pendente": ultima_insp is None,
            "ordem": idx + 1
        })
    
    ronda_ativos.sort(key=lambda x: (0 if x['inspecao_pendente'] else 1, {'critica': 0, 'alta': 1, 'media': 2, 'baixa': 3}.get(x['ativo'].get('criticidade', 'media'), 2)))
    
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

# ============== KPIs & DASHBOARD ==============

@api_router.get("/kpis")
async def get_kpis(user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
    
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    # OS Stats
    os_concluidas = await db.ordens_servico.find({**query, "status": "concluida", "tempo_execucao_minutos": {"$exists": True, "$ne": None}}, {"_id": 0, "tempo_execucao_minutos": 1, "tipo": 1}).to_list(1000)
    
    tempos = [os['tempo_execucao_minutos'] for os in os_concluidas if os.get('tempo_execucao_minutos')]
    mttr_minutos = sum(tempos) / len(tempos) if tempos else 0
    mttr_horas = mttr_minutos / 60
    
    # Preventiva vs Corretiva
    total_os = len(os_concluidas)
    preventivas = len([os for os in os_concluidas if os.get('tipo') == 'preventiva'])
    corretivas = len([os for os in os_concluidas if os.get('tipo') == 'corretiva'])
    
    # Assets
    ativos_total = await db.ativos.count_documents(query)
    ativos_operacionais = await db.ativos.count_documents({**query, "status": "operacional"})
    ativos_parados = await db.ativos.count_documents({**query, "status": {"$in": ["parado", "manutencao"]}})
    
    # Disponibilidade e MTBF
    disponibilidade = (ativos_operacionais / ativos_total * 100) if ativos_total > 0 else 100
    mtbf_horas = ((ativos_total - ativos_parados) / ativos_total * 720) if ativos_total > 0 else 720
    
    # Confiabilidade (simplified)
    confiabilidade = (1 - (corretivas / total_os)) * 100 if total_os > 0 else 100
    
    # Inspections
    total_insp = await db.inspecoes.count_documents(query)
    insp_conformes = await db.inspecoes.count_documents({**query, "resultado": "conforme"})
    taxa_conformidade = (insp_conformes / total_insp * 100) if total_insp > 0 else 100
    
    # Backlog
    backlog = await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "planejada", "em_execucao", "pausada"]}})
    
    # Overdue OS
    os_atrasadas = await db.ordens_servico.count_documents({
        **query, "status": {"$nin": ["concluida", "cancelada"]},
        "data_planejada": {"$lt": now.isoformat()}
    })
    
    # Monthly cost
    os_mes = await db.ordens_servico.find({**query, "status": "concluida", "data_conclusao": {"$gte": month_start}}, {"_id": 0, "custo_total": 1}).to_list(1000)
    custo_mes = sum(os.get('custo_total', 0) for os in os_mes)
    
    return {
        "disponibilidade_percent": round(disponibilidade, 1),
        "mtbf_horas": round(mtbf_horas, 1),
        "mttr_horas": round(mttr_horas, 2),
        "confiabilidade_percent": round(confiabilidade, 1),
        "taxa_conformidade_percent": round(taxa_conformidade, 1),
        "backlog_total": backlog,
        "os_atrasadas": os_atrasadas,
        "preventivas_percent": round((preventivas / total_os * 100) if total_os > 0 else 0, 1),
        "corretivas_percent": round((corretivas / total_os * 100) if total_os > 0 else 0, 1),
        "custo_manutencao_mes": round(custo_mes, 2),
        "ativos_total": ativos_total,
        "ativos_operacionais": ativos_operacionais,
        "ativos_parados": ativos_parados
    }

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    # Assets
    ativos = {
        "total": await db.ativos.count_documents(query),
        "operacionais": await db.ativos.count_documents({**query, "status": "operacional"}),
        "parados": await db.ativos.count_documents({**query, "status": "parado"}),
        "manutencao": await db.ativos.count_documents({**query, "status": "manutencao"}),
        "desativados": await db.ativos.count_documents({**query, "status": "desativado"})
    }
    
    # OS
    os_stats = {
        "abertas": await db.ordens_servico.count_documents({**query, "status": "aberta"}),
        "planejadas": await db.ordens_servico.count_documents({**query, "status": "planejada"}),
        "em_execucao": await db.ordens_servico.count_documents({**query, "status": "em_execucao"}),
        "pausadas": await db.ordens_servico.count_documents({**query, "status": "pausada"}),
        "concluidas_hoje": await db.ordens_servico.count_documents({**query, "status": "concluida", "data_conclusao": {"$gte": today_start}}),
        "atrasadas": await db.ordens_servico.count_documents({**query, "status": {"$nin": ["concluida", "cancelada"]}, "data_planejada": {"$lt": now.isoformat()}}),
        "por_tipo": {
            "preventiva": await db.ordens_servico.count_documents({**query, "tipo": "preventiva", "status": {"$nin": ["concluida", "cancelada"]}}),
            "corretiva": await db.ordens_servico.count_documents({**query, "tipo": "corretiva", "status": {"$nin": ["concluida", "cancelada"]}}),
            "preditiva": await db.ordens_servico.count_documents({**query, "tipo": "preditiva", "status": {"$nin": ["concluida", "cancelada"]}}),
            "emergencia": await db.ordens_servico.count_documents({**query, "tipo": "emergencia", "status": {"$nin": ["concluida", "cancelada"]}})
        },
        "por_prioridade": {
            "critica": await db.ordens_servico.count_documents({**query, "prioridade": "critica", "status": {"$nin": ["concluida", "cancelada"]}}),
            "alta": await db.ordens_servico.count_documents({**query, "prioridade": "alta", "status": {"$nin": ["concluida", "cancelada"]}}),
            "media": await db.ordens_servico.count_documents({**query, "prioridade": "media", "status": {"$nin": ["concluida", "cancelada"]}}),
            "baixa": await db.ordens_servico.count_documents({**query, "prioridade": "baixa", "status": {"$nin": ["concluida", "cancelada"]}})
        }
    }
    
    # Inspections
    inspecoes = {
        "pendentes": await db.inspecoes.count_documents({**query, "status": "pendente"}),
        "em_andamento": await db.inspecoes.count_documents({**query, "status": "em_andamento"}),
        "concluidas_hoje": await db.inspecoes.count_documents({**query, "status": "concluida", "data_conclusao": {"$gte": today_start}}),
        "nao_conformes_mes": await db.inspecoes.count_documents({**query, "resultado": "nao_conforme"})
    }
    
    # Stock
    estoque_items = await db.itens_estoque.find(query, {"_id": 0, "quantidade": 1, "estoque_minimo": 1, "item_critico": 1}).to_list(1000)
    estoque = {
        "total_itens": len(estoque_items),
        "criticos": len([i for i in estoque_items if i.get('quantidade', 0) <= i.get('estoque_minimo', 0)]),
        "itens_criticos_flag": len([i for i in estoque_items if i.get('item_critico', False)])
    }
    
    return {
        "ativos": ativos,
        "ordens_servico": os_stats,
        "inspecoes": inspecoes,
        "estoque": estoque
    }

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
    
    # Planta
    planta_id = str(uuid.uuid4())
    planta_doc = {
        "id": planta_id,
        "nome": "Planta Principal",
        "endereco": "Rua Industrial, 1000 - São Paulo, SP",
        "organization_id": org.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": None
    }
    await db.plantas.insert_one(planta_doc)
    
    # Areas
    areas_data = [
        {"nome": "Utilidades", "cor": "#10b981", "descricao": "Sistemas de água, ar comprimido e energia"},
        {"nome": "Produção", "cor": "#3b82f6", "descricao": "Linha de produção principal"},
        {"nome": "Embalagem", "cor": "#f59e0b", "descricao": "Área de embalagem e expedição"},
        {"nome": "Manutenção", "cor": "#8b5cf6", "descricao": "Oficina de manutenção"}
    ]
    
    areas = []
    for ad in areas_data:
        area_id = str(uuid.uuid4())
        area_doc = {
            "id": area_id,
            "nome": ad['nome'],
            "planta_id": planta_id,
            "cor": ad['cor'],
            "descricao": ad['descricao'],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        await db.areas.insert_one(area_doc)
        areas.append(area_doc)
    
    # Ativos
    ativos_data = [
        {"tag": "BOM-001", "nome": "Bomba Centrífuga 01", "tipo": "Bomba", "fabricante": "KSB", "modelo": "Meganorm 50-200", "criticidade": "critica", "area_idx": 0, "valor": 45000},
        {"tag": "BOM-002", "nome": "Bomba Centrífuga 02", "tipo": "Bomba", "fabricante": "KSB", "modelo": "Meganorm 40-160", "criticidade": "alta", "area_idx": 0, "valor": 35000},
        {"tag": "CMP-001", "nome": "Compressor de Ar", "tipo": "Compressor", "fabricante": "Atlas Copco", "modelo": "GA 30+", "criticidade": "critica", "area_idx": 0, "valor": 120000},
        {"tag": "EST-001", "nome": "Esteira Transportadora 01", "tipo": "Esteira", "fabricante": "Rexnord", "modelo": "FlatTop 2010", "criticidade": "alta", "area_idx": 1, "valor": 28000},
        {"tag": "EST-002", "nome": "Esteira Transportadora 02", "tipo": "Esteira", "fabricante": "Rexnord", "modelo": "FlatTop 2010", "criticidade": "media", "area_idx": 1, "valor": 28000},
        {"tag": "MIS-001", "nome": "Misturador Industrial", "tipo": "Misturador", "fabricante": "Ekato", "modelo": "HWL", "criticidade": "critica", "area_idx": 1, "valor": 85000},
        {"tag": "EMB-001", "nome": "Encaixotadora Automática", "tipo": "Embaladora", "fabricante": "Bosch", "modelo": "CUC 3001", "criticidade": "alta", "area_idx": 2, "valor": 150000},
        {"tag": "EMB-002", "nome": "Paletizadora", "tipo": "Paletizador", "fabricante": "KUKA", "modelo": "KR 180 PA", "criticidade": "alta", "area_idx": 2, "valor": 280000},
        {"tag": "TOR-001", "nome": "Torno Mecânico", "tipo": "Máquina Ferramenta", "fabricante": "Romi", "modelo": "Tormax 30A", "criticidade": "media", "area_idx": 3, "valor": 95000},
        {"tag": "FRE-001", "nome": "Fresadora CNC", "tipo": "Máquina Ferramenta", "fabricante": "Romi", "modelo": "D 800", "criticidade": "alta", "area_idx": 3, "valor": 320000},
    ]
    
    ativos = []
    for ad in ativos_data:
        ativo_id = str(uuid.uuid4())
        ativo_doc = {
            "id": ativo_id,
            "tag": ad['tag'],
            "qr_code": str(uuid.uuid4()),
            "nome": ad['nome'],
            "tipo_equipamento": ad['tipo'],
            "fabricante": ad['fabricante'],
            "modelo": ad['modelo'],
            "criticidade": ad['criticidade'],
            "status": "operacional",
            "area_id": areas[ad['area_idx']]['id'],
            "organization_id": org.id,
            "valor_aquisicao": ad['valor'],
            "data_instalacao": "2023-01-15",
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
    
    # Sample OS
    os_data = [
        {"ativo_idx": 0, "titulo": "Troca de rolamento", "tipo": "preventiva", "prioridade": "alta", "status": "aberta"},
        {"ativo_idx": 2, "titulo": "Vazamento de óleo", "tipo": "corretiva", "prioridade": "critica", "status": "em_execucao"},
        {"ativo_idx": 5, "titulo": "Calibração de sensores", "tipo": "preventiva", "prioridade": "media", "status": "planejada"},
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
async def migrate_checklist_tipo():
    """Migration: ensure all checklist items have 'tipo' field"""
    try:
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
    except Exception as e:
        logger.error(f"Migration error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
