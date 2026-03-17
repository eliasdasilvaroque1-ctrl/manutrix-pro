from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
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
import base64
import aiofiles

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

# Create the main app
app = FastAPI(title="MANUTRIX API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    PARADO_PROGRAMADO = "parado_programado"
    FALHA = "falha"
    MANUTENCAO = "manutencao"
    INSPECAO_PENDENTE = "inspecao_pendente"

class Criticidade(str, Enum):
    A = "A"  # Crítico
    B = "B"  # Importante
    C = "C"  # Moderado
    D = "D"  # Baixo

class OSStatus(str, Enum):
    ABERTA = "aberta"
    INICIADA = "iniciada"
    PAUSADA = "pausada"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"

class OSOrigem(str, Enum):
    INSPECAO = "inspecao"
    MANUAL = "manual"
    PREVENTIVA = "preventiva"
    PREDITIVA = "preditiva"
    EMERGENCIA = "emergencia"

class InspecaoStatus(str, Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    COM_PENDENCIAS = "com_pendencias"

class TipoResposta(str, Enum):
    BOOLEAN = "boolean"
    NUMERO = "numero"
    TEXTO = "texto"
    FOTO = "foto"
    SELECAO = "selecao"

class Frequencia(str, Enum):
    DIARIA = "diaria"
    SEMANAL = "semanal"
    MENSAL = "mensal"
    TRIMESTRAL = "trimestral"
    ANUAL = "anual"

class MovimentacaoTipo(str, Enum):
    ENTRADA_COMPRA = "entrada_compra"
    ENTRADA_DEVOLUCAO = "entrada_devolucao"
    SAIDA_OS = "saida_os"
    SAIDA_AJUSTE = "saida_ajuste"
    TRANSFERENCIA = "transferencia"

class NotificacaoTipo(str, Enum):
    OS_CRIADA = "os_criada"
    OS_ATRIBUIDA = "os_atribuida"
    INSPECAO_PENDENTE = "inspecao_pendente"
    ESTOQUE_CRITICO = "estoque_critico"
    FALHA_DETECTADA = "falha_detectada"

# ============== MODELS ==============

class UserBase(BaseModel):
    email: EmailStr
    nome: str
    role: UserRole = UserRole.TECNICO
    organization_id: Optional[str] = None
    avatar_url: Optional[str] = None
    telefone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    avatar_url: Optional[str] = None

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# Organization
class OrganizationBase(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    logo_url: Optional[str] = None
    configuracoes: Optional[Dict[str, Any]] = None

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

# Planta
class PlantaBase(BaseModel):
    nome: str
    endereco: Optional[str] = None
    organization_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    imagem_url: Optional[str] = None

class PlantaCreate(PlantaBase):
    pass

class Planta(PlantaBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

# Area
class AreaBase(BaseModel):
    nome: str
    planta_id: str
    descricao: Optional[str] = None
    cor: Optional[str] = "#10b981"

class AreaCreate(AreaBase):
    pass

class Area(AreaBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

# Ativo (Asset)
class AtivoBase(BaseModel):
    tag: str  # Código único
    nome: str
    descricao: Optional[str] = None
    area_id: str
    parent_id: Optional[str] = None  # Para hierarquia
    criticidade: Criticidade = Criticidade.C
    status: AssetStatus = AssetStatus.OPERACIONAL
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    ano_aquisicao: Optional[int] = None
    localizacao_fisica: Optional[str] = None
    datasheet_url: Optional[str] = None
    manual_url: Optional[str] = None
    imagem_url: Optional[str] = None
    potencia: Optional[str] = None
    tensao: Optional[str] = None
    rpm: Optional[int] = None
    especificacoes: Optional[Dict[str, Any]] = None

class AtivoCreate(AtivoBase):
    pass

class AtivoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    criticidade: Optional[Criticidade] = None
    status: Optional[AssetStatus] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    localizacao_fisica: Optional[str] = None
    imagem_url: Optional[str] = None

class Ativo(AtivoBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qr_code: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    ultima_inspecao: Optional[datetime] = None
    proxima_inspecao: Optional[datetime] = None
    total_os: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

# Rota de Inspeção (Template de Checklist)
class ItemInspecaoTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    descricao: str
    tipo_resposta: TipoResposta
    valor_esperado: Optional[str] = None
    tolerancia_min: Optional[float] = None
    tolerancia_max: Optional[float] = None
    unidade: Optional[str] = None
    opcoes: Optional[List[str]] = None  # Para tipo SELECAO
    obrigatorio: bool = True
    requer_foto_se_nok: bool = False
    ordem: int = 0
    categoria: Optional[str] = None

class RotaInspecaoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    tipo_ativo: str  # Ex: "bomba_centrifuga"
    frequencia: Frequencia
    tempo_estimado_minutos: int = 15
    itens: List[ItemInspecaoTemplate] = []
    ativa: bool = True

class RotaInspecaoCreate(RotaInspecaoBase):
    organization_id: str

class RotaInspecao(RotaInspecaoBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

# Inspeção (Execução)
class RespostaInspecao(BaseModel):
    item_id: str
    valor: Any
    conforme: bool = True
    observacao: Optional[str] = None
    foto_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InspecaoBase(BaseModel):
    ativo_id: str
    rota_id: str
    tecnico_id: str

class InspecaoCreate(InspecaoBase):
    pass

class Inspecao(InspecaoBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    status: InspecaoStatus = InspecaoStatus.EM_ANDAMENTO
    respostas: List[RespostaInspecao] = []
    os_geradas: List[str] = []  # IDs das OS geradas
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    duracao_minutos: Optional[int] = None
    geolocalizacao: Optional[Dict[str, float]] = None
    offline_sync: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class FinalizarInspecao(BaseModel):
    respostas: List[RespostaInspecao]
    geolocalizacao: Optional[Dict[str, float]] = None

# Ordem de Serviço
class PecaUtilizada(BaseModel):
    item_id: str
    nome: Optional[str] = None
    quantidade: float
    custo_unitario: Optional[float] = None

class ChecklistOS(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    descricao: str
    concluido: bool = False
    obrigatorio: bool = True

class OSBase(BaseModel):
    ativo_id: str
    titulo: str
    descricao: Optional[str] = None
    tipo: OSOrigem = OSOrigem.MANUAL
    prioridade: Criticidade = Criticidade.C

class OSCreate(OSBase):
    tecnico_id: Optional[str] = None

class OrdemServico(OSBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero: str = ""  # Será gerado
    organization_id: str = ""
    status: OSStatus = OSStatus.ABERTA
    tecnico_id: Optional[str] = None
    inspecao_origem_id: Optional[str] = None
    pecas_utilizadas: List[PecaUtilizada] = []
    checklist: List[ChecklistOS] = []
    observacoes: Optional[str] = None
    fotos: List[str] = []
    start_at: Optional[datetime] = None
    finish_at: Optional[datetime] = None
    tempo_efetivo_minutos: Optional[int] = None
    custo_total: Optional[float] = None
    assinatura_tecnico: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class OSUpdate(BaseModel):
    status: Optional[OSStatus] = None
    tecnico_id: Optional[str] = None
    observacoes: Optional[str] = None
    pecas_utilizadas: Optional[List[PecaUtilizada]] = None
    fotos: Optional[List[str]] = None

# Estoque
class ItemEstoqueBase(BaseModel):
    sku: str
    nome: str
    descricao: Optional[str] = None
    unidade: str = "UN"
    estoque_minimo: float = 0
    estoque_maximo: Optional[float] = None
    localizacao: Optional[str] = None
    categoria: Optional[str] = None
    fornecedor: Optional[str] = None
    codigo_barras: Optional[str] = None

class ItemEstoqueCreate(ItemEstoqueBase):
    organization_id: str
    saldo_inicial: float = 0
    custo_unitario: float = 0

class ItemEstoque(ItemEstoqueBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    saldo: float = 0
    custo_medio: float = 0
    valor_total: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class MovimentacaoEstoque(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    tipo: MovimentacaoTipo
    quantidade: float
    custo_unitario: Optional[float] = None
    os_id: Optional[str] = None
    observacao: Optional[str] = None
    usuario_id: str
    organization_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Notificações
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

# Auditoria
class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entidade: str
    entidade_id: str
    acao: str
    usuario_id: str
    organization_id: str
    dados_antes: Optional[Dict[str, Any]] = None
    dados_depois: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# KPIs
class KPIResponse(BaseModel):
    mttr_horas: float = 0
    mtbf_horas: float = 0
    disponibilidade_percent: float = 100
    taxa_conformidade_percent: float = 100
    backlog_total: int = 0
    os_abertas: int = 0
    os_concluidas_mes: int = 0
    inspecoes_pendentes: int = 0
    inspecoes_realizadas_mes: int = 0
    ativos_em_falha: int = 0
    custo_manutencao_mes: float = 0

# Ronda
class RondaAtivo(BaseModel):
    ativo: Dict[str, Any]
    rota: Dict[str, Any]
    inspecao_pendente: bool = True
    ordem: int = 0

class RondaResponse(BaseModel):
    area_id: str
    area_nome: str
    total_ativos: int
    ativos: List[RondaAtivo]

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

async def auditar(entidade: str, entidade_id: str, acao: str, usuario_id: str, org_id: str, antes: Dict = None, depois: Dict = None):
    log = AuditLog(
        entidade=entidade,
        entidade_id=entidade_id,
        acao=acao,
        usuario_id=usuario_id,
        organization_id=org_id,
        dados_antes=antes,
        dados_depois=depois
    )
    doc = log.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.audit_logs.insert_one(doc)

async def gerar_numero_os(org_id: str) -> str:
    ano = datetime.now().year
    count = await db.ordens_servico.count_documents({"organization_id": org_id})
    return f"{ano}-{str(count + 1).zfill(5)}"

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

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Create organization if admin
    org_id = user_data.organization_id
    if not org_id and user_data.role == UserRole.ADMIN:
        org = Organization(nome=f"Org de {user_data.nome}")
        org_doc = org.model_dump()
        org_doc['created_at'] = org_doc['created_at'].isoformat()
        await db.organizations.insert_one(org_doc)
        org_id = org.id
    
    # Create user
    user = User(
        email=user_data.email,
        nome=user_data.nome,
        role=user_data.role,
        organization_id=org_id,
        telefone=user_data.telefone
    )
    
    user_doc = user.model_dump()
    user_doc['password_hash'] = hash_password(user_data.password)
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user.id, user.role.value, org_id or "")
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "nome": user.nome,
            "role": user.role.value,
            "organization_id": org_id
        }
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
            "id": user['id'],
            "email": user['email'],
            "nome": user['nome'],
            "role": user['role'],
            "organization_id": user.get('organization_id'),
            "avatar_url": user.get('avatar_url'),
            "telefone": user.get('telefone')
        }
    )

@api_router.get("/auth/me")
async def get_me(user: Dict = Depends(get_current_user)):
    return {
        "id": user['id'],
        "email": user['email'],
        "nome": user['nome'],
        "role": user['role'],
        "organization_id": user.get('organization_id'),
        "avatar_url": user.get('avatar_url'),
        "telefone": user.get('telefone')
    }

@api_router.put("/auth/me")
async def update_me(data: UserUpdate, user: Dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        await db.users.update_one({"id": user['id']}, {"$set": update_data})
    updated = await db.users.find_one({"id": user['id']}, {"_id": 0, "password_hash": 0})
    return updated

# ============== UPLOAD ROUTES ==============

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    # Generate unique filename
    ext = Path(file.filename).suffix.lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
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

# ============== ORGANIZATION ROUTES ==============

@api_router.get("/organizations", response_model=List[Organization])
async def list_organizations(user: Dict = Depends(get_current_user)):
    orgs = await db.organizations.find({"deleted_at": None}, {"_id": 0}).to_list(100)
    return orgs

@api_router.get("/organizations/{org_id}")
async def get_organization(org_id: str, user: Dict = Depends(get_current_user)):
    org = await db.organizations.find_one({"id": org_id, "deleted_at": None}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    return org

@api_router.post("/organizations", response_model=Organization)
async def create_organization(data: OrganizationCreate, user: Dict = Depends(get_current_user)):
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Apenas admins podem criar organizações")
    
    org = Organization(**data.model_dump())
    doc = org.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.organizations.insert_one(doc)
    return org

# ============== PLANTA ROUTES ==============

@api_router.get("/plantas", response_model=List[Planta])
async def list_plantas(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    plantas = await db.plantas.find(query, {"_id": 0}).to_list(100)
    return plantas

@api_router.post("/plantas", response_model=Planta)
async def create_planta(data: PlantaCreate, user: Dict = Depends(get_current_user)):
    planta = Planta(**data.model_dump())
    doc = planta.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.plantas.insert_one(doc)
    await auditar("planta", planta.id, "create", user['id'], data.organization_id, depois=doc)
    return planta

# ============== AREA ROUTES ==============

@api_router.get("/areas", response_model=List[Area])
async def list_areas(planta_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if planta_id:
        query['planta_id'] = planta_id
    areas = await db.areas.find(query, {"_id": 0}).to_list(100)
    return areas

@api_router.get("/areas/{area_id}")
async def get_area(area_id: str, user: Dict = Depends(get_current_user)):
    area = await db.areas.find_one({"id": area_id, "deleted_at": None}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    return area

@api_router.post("/areas", response_model=Area)
async def create_area(data: AreaCreate, user: Dict = Depends(get_current_user)):
    area = Area(**data.model_dump())
    doc = area.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.areas.insert_one(doc)
    await auditar("area", area.id, "create", user['id'], user.get('organization_id', ''), depois=doc)
    return area

# ============== ATIVO ROUTES ==============

@api_router.get("/ativos", response_model=List[Ativo])
async def list_ativos(area_id: Optional[str] = None, status: Optional[AssetStatus] = None, criticidade: Optional[Criticidade] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if area_id:
        query['area_id'] = area_id
    if status:
        query['status'] = status.value
    if criticidade:
        query['criticidade'] = criticidade.value
    ativos = await db.ativos.find(query, {"_id": 0}).to_list(1000)
    return ativos

@api_router.get("/ativos/{ativo_id}")
async def get_ativo(ativo_id: str, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    # Get area info
    area = await db.areas.find_one({"id": ativo['area_id']}, {"_id": 0})
    ativo['area'] = area
    
    # Get recent OS
    os_list = await db.ordens_servico.find(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    ativo['ordens_servico_recentes'] = os_list
    
    # Get recent inspections
    inspecoes = await db.inspecoes.find(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    ativo['inspecoes_recentes'] = inspecoes
    
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

@api_router.post("/ativos", response_model=Ativo)
async def create_ativo(data: AtivoCreate, user: Dict = Depends(get_current_user)):
    # Get area to find organization
    area = await db.areas.find_one({"id": data.area_id}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    
    planta = await db.plantas.find_one({"id": area['planta_id']}, {"_id": 0})
    org_id = planta['organization_id'] if planta else user.get('organization_id', '')
    
    # Check TAG uniqueness
    existing = await db.ativos.find_one({"tag": data.tag.upper(), "organization_id": org_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="TAG já existe nesta organização")
    
    ativo = Ativo(**data.model_dump())
    ativo.tag = ativo.tag.upper()
    ativo.organization_id = org_id
    
    doc = ativo.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.ativos.insert_one(doc)
    await auditar("ativo", ativo.id, "create", user['id'], org_id, depois=doc)
    return ativo

@api_router.put("/ativos/{ativo_id}")
async def update_ativo(ativo_id: str, data: AtivoUpdate, user: Dict = Depends(get_current_user)):
    existing = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        await db.ativos.update_one({"id": ativo_id}, {"$set": update_data})
    
    updated = await db.ativos.find_one({"id": ativo_id}, {"_id": 0})
    await auditar("ativo", ativo_id, "update", user['id'], existing.get('organization_id', ''), antes=existing, depois=updated)
    return updated

@api_router.get("/ativos/{ativo_id}/historico")
async def get_ativo_historico(ativo_id: str, user: Dict = Depends(get_current_user)):
    # Get all OS for this asset
    os_list = await db.ordens_servico.find(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get all inspections
    inspecoes = await db.inspecoes.find(
        {"ativo_id": ativo_id, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Combine and sort by date
    historico = []
    for os in os_list:
        historico.append({
            "tipo": "os",
            "data": os.get('created_at'),
            "item": os
        })
    for insp in inspecoes:
        historico.append({
            "tipo": "inspecao",
            "data": insp.get('created_at'),
            "item": insp
        })
    
    historico.sort(key=lambda x: x['data'] or '', reverse=True)
    
    return historico

# ============== ROTA INSPECAO ROUTES ==============

@api_router.get("/rotas-inspecao", response_model=List[RotaInspecao])
async def list_rotas_inspecao(tipo_ativo: Optional[str] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None, "ativa": True}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if tipo_ativo:
        query['tipo_ativo'] = tipo_ativo
    rotas = await db.rotas_inspecao.find(query, {"_id": 0}).to_list(100)
    return rotas

@api_router.get("/rotas-inspecao/{rota_id}")
async def get_rota_inspecao(rota_id: str, user: Dict = Depends(get_current_user)):
    rota = await db.rotas_inspecao.find_one({"id": rota_id, "deleted_at": None}, {"_id": 0})
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    return rota

@api_router.post("/rotas-inspecao", response_model=RotaInspecao)
async def create_rota_inspecao(data: RotaInspecaoCreate, user: Dict = Depends(get_current_user)):
    rota = RotaInspecao(**data.model_dump())
    doc = rota.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.rotas_inspecao.insert_one(doc)
    return rota

# ============== RONDA ROUTES ==============

@api_router.get("/ronda/{area_id}")
async def get_ronda(area_id: str, user: Dict = Depends(get_current_user)):
    """Get inspection round for an area - list of assets to inspect"""
    area = await db.areas.find_one({"id": area_id, "deleted_at": None}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    
    # Get all assets in this area
    ativos = await db.ativos.find(
        {"area_id": area_id, "deleted_at": None},
        {"_id": 0}
    ).to_list(500)
    
    # Get all active inspection routes
    rotas = await db.rotas_inspecao.find({"deleted_at": None, "ativa": True}, {"_id": 0}).to_list(100)
    rotas_dict = {r['tipo_ativo']: r for r in rotas}
    
    # Build ronda list
    ronda_ativos = []
    for idx, ativo in enumerate(ativos):
        # Find matching route (simplified - in real app would match by asset type)
        rota = rotas[0] if rotas else None
        
        # Check if inspection is pending (simplified logic)
        ultima_inspecao = await db.inspecoes.find_one(
            {"ativo_id": ativo['id'], "status": {"$ne": "em_andamento"}, "deleted_at": None},
            {"_id": 0}
        )
        
        ronda_ativos.append({
            "ativo": ativo,
            "rota": rota,
            "inspecao_pendente": ultima_inspecao is None,
            "ordem": idx + 1
        })
    
    # Sort by criticality (A first) and pending inspections
    ronda_ativos.sort(key=lambda x: (
        0 if x['inspecao_pendente'] else 1,
        {'A': 0, 'B': 1, 'C': 2, 'D': 3}.get(x['ativo'].get('criticidade', 'C'), 2)
    ))
    
    return {
        "area_id": area_id,
        "area_nome": area['nome'],
        "total_ativos": len(ronda_ativos),
        "ativos": ronda_ativos
    }

@api_router.get("/rondas")
async def list_rondas(user: Dict = Depends(get_current_user)):
    """List all areas with inspection status"""
    query = {"deleted_at": None}
    areas = await db.areas.find(query, {"_id": 0}).to_list(100)
    
    result = []
    for area in areas:
        ativos_count = await db.ativos.count_documents({"area_id": area['id'], "deleted_at": None})
        
        # Count pending inspections (simplified)
        inspecoes_pendentes = await db.inspecoes.count_documents({
            "status": "em_andamento",
            "deleted_at": None
        })
        
        result.append({
            "area": area,
            "total_ativos": ativos_count,
            "inspecoes_pendentes": inspecoes_pendentes
        })
    
    return result

# ============== INSPECAO ROUTES ==============

@api_router.get("/inspecoes")
async def list_inspecoes(status: Optional[InspecaoStatus] = None, limit: int = 50, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if status:
        query['status'] = status.value
    
    inspecoes = await db.inspecoes.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Enrich with ativo and rota info
    for insp in inspecoes:
        ativo = await db.ativos.find_one({"id": insp['ativo_id']}, {"_id": 0, "tag": 1, "nome": 1})
        insp['ativo'] = ativo
        rota = await db.rotas_inspecao.find_one({"id": insp['rota_id']}, {"_id": 0, "nome": 1})
        insp['rota'] = rota
    
    return inspecoes

@api_router.get("/inspecoes/{inspecao_id}")
async def get_inspecao(inspecao_id: str, user: Dict = Depends(get_current_user)):
    inspecao = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None}, {"_id": 0})
    if not inspecao:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    
    # Get ativo
    ativo = await db.ativos.find_one({"id": inspecao['ativo_id']}, {"_id": 0})
    inspecao['ativo'] = ativo
    
    # Get rota
    rota = await db.rotas_inspecao.find_one({"id": inspecao['rota_id']}, {"_id": 0})
    inspecao['rota'] = rota
    
    # Get tecnico
    tecnico = await db.users.find_one({"id": inspecao['tecnico_id']}, {"_id": 0, "nome": 1, "email": 1})
    inspecao['tecnico'] = tecnico
    
    return inspecao

@api_router.post("/inspecoes")
async def create_inspecao(data: InspecaoCreate, user: Dict = Depends(get_current_user)):
    # Validate ativo
    ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    # Validate rota
    rota = await db.rotas_inspecao.find_one({"id": data.rota_id, "deleted_at": None}, {"_id": 0})
    if not rota:
        raise HTTPException(status_code=404, detail="Rota de inspeção não encontrada")
    
    inspecao = Inspecao(**data.model_dump())
    inspecao.organization_id = ativo.get('organization_id', '')
    
    doc = inspecao.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['started_at'] = doc['started_at'].isoformat()
    await db.inspecoes.insert_one(doc)
    
    # Update ativo status
    await db.ativos.update_one(
        {"id": data.ativo_id},
        {"$set": {"status": AssetStatus.INSPECAO_PENDENTE.value}}
    )
    
    return doc

@api_router.post("/inspecoes/{inspecao_id}/finalizar")
async def finalizar_inspecao(inspecao_id: str, data: FinalizarInspecao, user: Dict = Depends(get_current_user)):
    """
    RPC Atômico para fechamento de inspeção:
    1. Valida respostas
    2. Atualiza status da inspeção
    3. Gera OS de correção para falhas
    4. Atualiza status do ativo
    5. Grava auditoria
    6. Cria notificações
    """
    inspecao = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None}, {"_id": 0})
    if not inspecao:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    
    # Get rota to validate items
    rota = await db.rotas_inspecao.find_one({"id": inspecao['rota_id']}, {"_id": 0})
    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    
    # Get ativo
    ativo = await db.ativos.find_one({"id": inspecao['ativo_id']}, {"_id": 0})
    
    # Check required items
    itens_obrigatorios = [item['id'] for item in rota.get('itens', []) if item.get('obrigatorio', True)]
    respostas_ids = [r.item_id for r in data.respostas]
    
    for item_id in itens_obrigatorios:
        if item_id not in respostas_ids:
            raise HTTPException(status_code=400, detail=f"Item obrigatório {item_id} não respondido")
    
    # Check for non-conformities
    nao_conformes = [r for r in data.respostas if not r.conforme]
    os_geradas = []
    
    # Generate OS for each non-conformity
    for resposta in nao_conformes:
        item = next((i for i in rota.get('itens', []) if i['id'] == resposta.item_id), None)
        if item:
            numero = await gerar_numero_os(inspecao.get('organization_id', ''))
            os = OrdemServico(
                ativo_id=inspecao['ativo_id'],
                titulo=f"Correção: {item['descricao']}",
                descricao=f"Não conformidade detectada em inspeção.\n\nObservação: {resposta.observacao or 'Sem observação'}",
                tipo=OSOrigem.INSPECAO,
                prioridade=ativo.get('criticidade', Criticidade.C),
                inspecao_origem_id=inspecao_id,
                organization_id=inspecao.get('organization_id', ''),
                numero=numero
            )
            
            os_doc = os.model_dump()
            os_doc['created_at'] = os_doc['created_at'].isoformat()
            await db.ordens_servico.insert_one(os_doc)
            os_geradas.append(os.id)
            
            # Create notification for supervisors
            supervisors = await db.users.find(
                {"organization_id": inspecao.get('organization_id'), "role": "supervisor", "deleted_at": None},
                {"_id": 0, "id": 1}
            ).to_list(100)
            
            for sup in supervisors:
                await criar_notificacao(
                    sup['id'],
                    inspecao.get('organization_id', ''),
                    NotificacaoTipo.FALHA_DETECTADA,
                    f"Falha detectada: {ativo.get('tag', '')}",
                    f"Nova OS #{numero} gerada automaticamente",
                    f"/os/{os.id}"
                )
    
    # Determine final status
    status_final = InspecaoStatus.CONCLUIDA if not nao_conformes else InspecaoStatus.COM_PENDENCIAS
    
    # Calculate duration
    started_at = inspecao.get('started_at')
    duracao = None
    if started_at:
        start = datetime.fromisoformat(started_at.replace('Z', '+00:00')) if isinstance(started_at, str) else started_at
        duracao = int((datetime.now(timezone.utc) - start).total_seconds() / 60)
    
    # Update ativo status
    novo_status_ativo = AssetStatus.OPERACIONAL if not nao_conformes else AssetStatus.FALHA
    await db.ativos.update_one(
        {"id": inspecao['ativo_id']},
        {
            "$set": {
                "status": novo_status_ativo.value,
                "ultima_inspecao": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Serialize respostas
    respostas_dict = []
    for r in data.respostas:
        rd = r.model_dump()
        rd['timestamp'] = rd['timestamp'].isoformat()
        respostas_dict.append(rd)
    
    # Update inspecao
    update_data = {
        "status": status_final.value,
        "respostas": respostas_dict,
        "os_geradas": os_geradas,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duracao_minutos": duracao,
        "geolocalizacao": data.geolocalizacao
    }
    
    await db.inspecoes.update_one({"id": inspecao_id}, {"$set": update_data})
    
    # Audit
    await auditar(
        "inspecao", inspecao_id, "finalizar",
        user['id'], inspecao.get('organization_id', ''),
        antes=inspecao, depois={**inspecao, **update_data}
    )
    
    return {
        "success": True,
        "status": status_final.value,
        "os_geradas": os_geradas,
        "total_nao_conformes": len(nao_conformes),
        "duracao_minutos": duracao
    }

# ============== ORDEM DE SERVICO ROUTES ==============

@api_router.get("/ordens-servico")
async def list_ordens_servico(
    status: Optional[OSStatus] = None,
    tipo: Optional[OSOrigem] = None,
    prioridade: Optional[Criticidade] = None,
    tecnico_id: Optional[str] = None,
    limit: int = 100,
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
    if tecnico_id:
        query['tecnico_id'] = tecnico_id
    
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Enrich with ativo info
    for os in os_list:
        ativo = await db.ativos.find_one({"id": os['ativo_id']}, {"_id": 0, "tag": 1, "nome": 1})
        os['ativo'] = ativo
        if os.get('tecnico_id'):
            tecnico = await db.users.find_one({"id": os['tecnico_id']}, {"_id": 0, "nome": 1})
            os['tecnico'] = tecnico
    
    return os_list

@api_router.get("/ordens-servico/backlog")
async def get_backlog(user: Dict = Depends(get_current_user)):
    query = {
        "deleted_at": None,
        "status": {"$in": [OSStatus.ABERTA.value, OSStatus.INICIADA.value, OSStatus.PAUSADA.value]}
    }
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", 1).to_list(500)
    
    # Enrich with ativo info and calculate priority color
    enriched = []
    for os in os_list:
        ativo = await db.ativos.find_one({"id": os['ativo_id']}, {"_id": 0})
        
        # Calculate days since creation
        created = datetime.fromisoformat(os['created_at'].replace('Z', '+00:00')) if isinstance(os['created_at'], str) else os['created_at']
        days_open = (datetime.now(timezone.utc) - created).days
        
        # Priority color based on days and criticality
        prioridade = os.get('prioridade', 'C')
        if days_open > 7 or prioridade == 'A':
            cor = 'vermelho'
        elif days_open > 3 or prioridade == 'B':
            cor = 'amarelo'
        else:
            cor = 'verde'
        
        enriched.append({
            **os,
            "ativo": ativo,
            "dias_aberto": days_open,
            "cor_prioridade": cor
        })
    
    return enriched

@api_router.get("/ordens-servico/minhas")
async def get_minhas_os(user: Dict = Depends(get_current_user)):
    """Get OS assigned to current user"""
    query = {
        "tecnico_id": user['id'],
        "deleted_at": None,
        "status": {"$in": ["aberta", "iniciada", "pausada"]}
    }
    
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for os in os_list:
        ativo = await db.ativos.find_one({"id": os['ativo_id']}, {"_id": 0, "tag": 1, "nome": 1})
        os['ativo'] = ativo
    
    return os_list

@api_router.get("/ordens-servico/{os_id}")
async def get_ordem_servico(os_id: str, user: Dict = Depends(get_current_user)):
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    # Get ativo
    ativo = await db.ativos.find_one({"id": os['ativo_id']}, {"_id": 0})
    os['ativo'] = ativo
    
    # Get tecnico
    if os.get('tecnico_id'):
        tecnico = await db.users.find_one({"id": os['tecnico_id']}, {"_id": 0, "nome": 1, "email": 1, "telefone": 1})
        os['tecnico'] = tecnico
    
    # Get origin inspection if exists
    if os.get('inspecao_origem_id'):
        inspecao = await db.inspecoes.find_one({"id": os['inspecao_origem_id']}, {"_id": 0})
        os['inspecao_origem'] = inspecao
    
    return os

@api_router.post("/ordens-servico")
async def create_ordem_servico(data: OSCreate, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"id": data.ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    org_id = ativo.get('organization_id', user.get('organization_id', ''))
    numero = await gerar_numero_os(org_id)
    
    os = OrdemServico(**data.model_dump())
    os.organization_id = org_id
    os.numero = numero
    
    doc = os.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.ordens_servico.insert_one(doc)
    
    # Update ativo total_os
    await db.ativos.update_one(
        {"id": data.ativo_id},
        {"$inc": {"total_os": 1}}
    )
    
    # Create notification for assigned technician
    if data.tecnico_id:
        await criar_notificacao(
            data.tecnico_id,
            org_id,
            NotificacaoTipo.OS_ATRIBUIDA,
            f"Nova OS atribuída: #{numero}",
            f"Ativo: {ativo.get('tag', '')} - {data.titulo}",
            f"/os/{os.id}"
        )
    
    await auditar("ordem_servico", os.id, "create", user['id'], org_id, depois=doc)
    return doc

@api_router.put("/ordens-servico/{os_id}")
async def update_ordem_servico(os_id: str, data: OSUpdate, user: Dict = Depends(get_current_user)):
    existing = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Handle status transitions
    if 'status' in update_data:
        new_status = update_data['status']
        if new_status == OSStatus.INICIADA.value and not existing.get('start_at'):
            update_data['start_at'] = datetime.now(timezone.utc).isoformat()
        elif new_status == OSStatus.CONCLUIDA.value:
            update_data['finish_at'] = datetime.now(timezone.utc).isoformat()
            if existing.get('start_at'):
                start = datetime.fromisoformat(existing['start_at'].replace('Z', '+00:00')) if isinstance(existing['start_at'], str) else existing['start_at']
                finish = datetime.now(timezone.utc)
                update_data['tempo_efetivo_minutos'] = int((finish - start).total_seconds() / 60)
    
    # Handle pecas_utilizadas serialization
    if 'pecas_utilizadas' in update_data and update_data['pecas_utilizadas']:
        update_data['pecas_utilizadas'] = [p.model_dump() if hasattr(p, 'model_dump') else p for p in update_data['pecas_utilizadas']]
    
    await db.ordens_servico.update_one({"id": os_id}, {"$set": update_data})
    updated = await db.ordens_servico.find_one({"id": os_id}, {"_id": 0})
    await auditar("ordem_servico", os_id, "update", user['id'], existing.get('organization_id', ''), antes=existing, depois=updated)
    return updated

@api_router.post("/ordens-servico/{os_id}/finalizar")
async def finalizar_ordem_servico(os_id: str, pecas: List[PecaUtilizada] = [], observacoes: str = "", user: Dict = Depends(get_current_user)):
    """
    RPC Atômico para fechamento de OS:
    1. Atualiza OS para CONCLUÍDA
    2. Atualiza status do ativo
    3. Abate estoque das peças
    4. Calcula custo total
    5. Grava auditoria
    """
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
    custo_total = 0.0
    
    # Abater estoque
    for peca in pecas:
        item = await db.itens_estoque.find_one({"id": peca.item_id}, {"_id": 0})
        if item:
            novo_saldo = item.get('saldo', 0) - peca.quantidade
            custo_unitario = peca.custo_unitario or item.get('custo_medio', 0)
            custo_total += peca.quantidade * custo_unitario
            
            await db.itens_estoque.update_one(
                {"id": peca.item_id},
                {
                    "$set": {"saldo": novo_saldo},
                    "$inc": {"valor_total": -(peca.quantidade * custo_unitario)}
                }
            )
            
            # Registrar movimentação
            mov = MovimentacaoEstoque(
                item_id=peca.item_id,
                tipo=MovimentacaoTipo.SAIDA_OS,
                quantidade=-peca.quantidade,
                custo_unitario=custo_unitario,
                os_id=os_id,
                usuario_id=user['id'],
                organization_id=os.get('organization_id', '')
            )
            mov_doc = mov.model_dump()
            mov_doc['created_at'] = mov_doc['created_at'].isoformat()
            await db.movimentacoes_estoque.insert_one(mov_doc)
            
            # Check if stock is critical
            if novo_saldo <= item.get('estoque_minimo', 0):
                # Notify admin
                admins = await db.users.find(
                    {"organization_id": os.get('organization_id'), "role": "admin", "deleted_at": None},
                    {"_id": 0, "id": 1}
                ).to_list(10)
                for admin in admins:
                    await criar_notificacao(
                        admin['id'],
                        os.get('organization_id', ''),
                        NotificacaoTipo.ESTOQUE_CRITICO,
                        f"Estoque crítico: {item.get('nome', '')}",
                        f"Saldo atual: {novo_saldo} {item.get('unidade', 'UN')}",
                        "/estoque"
                    )
    
    # Update OS
    finish_at = datetime.now(timezone.utc)
    start_at = os.get('start_at')
    tempo_efetivo = None
    if start_at:
        start = datetime.fromisoformat(start_at.replace('Z', '+00:00')) if isinstance(start_at, str) else start_at
        tempo_efetivo = int((finish_at - start).total_seconds() / 60)
    
    pecas_dict = [p.model_dump() for p in pecas]
    
    update_data = {
        "status": OSStatus.CONCLUIDA.value,
        "finish_at": finish_at.isoformat(),
        "tempo_efetivo_minutos": tempo_efetivo,
        "pecas_utilizadas": pecas_dict,
        "custo_total": custo_total,
        "observacoes": observacoes or os.get('observacoes', '')
    }
    
    await db.ordens_servico.update_one({"id": os_id}, {"$set": update_data})
    
    # Update ativo status
    await db.ativos.update_one(
        {"id": os['ativo_id']},
        {"$set": {"status": AssetStatus.OPERACIONAL.value}}
    )
    
    await auditar("ordem_servico", os_id, "finalizar", user['id'], os.get('organization_id', ''), antes=os, depois={**os, **update_data})
    
    return {
        "success": True,
        "tempo_efetivo_minutos": tempo_efetivo,
        "custo_total": custo_total
    }

@api_router.post("/ordens-servico/{os_id}/foto")
async def add_foto_os(os_id: str, file: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
    # Upload file
    ext = Path(file.filename).suffix.lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido")
    
    filename = f"os_{os_id}_{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    url = f"/api/uploads/{filename}"
    
    # Update OS
    fotos = os.get('fotos', [])
    fotos.append(url)
    await db.ordens_servico.update_one({"id": os_id}, {"$set": {"fotos": fotos}})
    
    return {"url": url}

# ============== ESTOQUE ROUTES ==============

@api_router.get("/estoque")
async def list_estoque(categoria: Optional[str] = None, critico: Optional[bool] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if categoria:
        query['categoria'] = categoria
    
    items = await db.itens_estoque.find(query, {"_id": 0}).to_list(500)
    
    # Filter critical items
    if critico:
        items = [i for i in items if i.get('saldo', 0) <= i.get('estoque_minimo', 0)]
    
    return items

@api_router.get("/estoque/{item_id}")
async def get_item_estoque(item_id: str, user: Dict = Depends(get_current_user)):
    item = await db.itens_estoque.find_one({"id": item_id, "deleted_at": None}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Get recent movements
    movs = await db.movimentacoes_estoque.find(
        {"item_id": item_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    item['movimentacoes'] = movs
    
    return item

@api_router.post("/estoque")
async def create_item_estoque(data: ItemEstoqueCreate, user: Dict = Depends(get_current_user)):
    # Check SKU uniqueness
    existing = await db.itens_estoque.find_one(
        {"sku": data.sku.upper(), "organization_id": data.organization_id, "deleted_at": None}
    )
    if existing:
        raise HTTPException(status_code=400, detail="SKU já existe")
    
    item = ItemEstoque(
        sku=data.sku.upper(),
        nome=data.nome,
        descricao=data.descricao,
        unidade=data.unidade,
        estoque_minimo=data.estoque_minimo,
        estoque_maximo=data.estoque_maximo,
        localizacao=data.localizacao,
        categoria=data.categoria,
        fornecedor=data.fornecedor,
        codigo_barras=data.codigo_barras,
        organization_id=data.organization_id,
        saldo=data.saldo_inicial,
        custo_medio=data.custo_unitario,
        valor_total=data.saldo_inicial * data.custo_unitario
    )
    doc = item.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.itens_estoque.insert_one(doc)
    
    # Registrar entrada inicial
    if data.saldo_inicial > 0:
        mov = MovimentacaoEstoque(
            item_id=item.id,
            tipo=MovimentacaoTipo.ENTRADA_COMPRA,
            quantidade=data.saldo_inicial,
            custo_unitario=data.custo_unitario,
            usuario_id=user['id'],
            organization_id=data.organization_id
        )
        mov_doc = mov.model_dump()
        mov_doc['created_at'] = mov_doc['created_at'].isoformat()
        await db.movimentacoes_estoque.insert_one(mov_doc)
    
    return item

@api_router.post("/estoque/{item_id}/entrada")
async def entrada_estoque(item_id: str, quantidade: float, custo_unitario: float, observacao: str = "", user: Dict = Depends(get_current_user)):
    item = await db.itens_estoque.find_one({"id": item_id, "deleted_at": None}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    # Calculate new average cost
    saldo_atual = item.get('saldo', 0)
    custo_atual = item.get('custo_medio', 0)
    novo_saldo = saldo_atual + quantidade
    novo_custo = ((saldo_atual * custo_atual) + (quantidade * custo_unitario)) / novo_saldo if novo_saldo > 0 else custo_unitario
    
    await db.itens_estoque.update_one(
        {"id": item_id},
        {
            "$set": {
                "saldo": novo_saldo,
                "custo_medio": novo_custo,
                "valor_total": novo_saldo * novo_custo
            }
        }
    )
    
    # Register movement
    mov = MovimentacaoEstoque(
        item_id=item_id,
        tipo=MovimentacaoTipo.ENTRADA_COMPRA,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        observacao=observacao,
        usuario_id=user['id'],
        organization_id=item.get('organization_id', '')
    )
    mov_doc = mov.model_dump()
    mov_doc['created_at'] = mov_doc['created_at'].isoformat()
    await db.movimentacoes_estoque.insert_one(mov_doc)
    
    return {"saldo": novo_saldo, "custo_medio": novo_custo}

# ============== NOTIFICACOES ROUTES ==============

@api_router.get("/notificacoes")
async def list_notificacoes(lida: Optional[bool] = None, user: Dict = Depends(get_current_user)):
    query = {"usuario_id": user['id']}
    if lida is not None:
        query['lida'] = lida
    
    notifs = await db.notificacoes.find(query, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return notifs

@api_router.get("/notificacoes/count")
async def count_notificacoes(user: Dict = Depends(get_current_user)):
    count = await db.notificacoes.count_documents({"usuario_id": user['id'], "lida": False})
    return {"count": count}

@api_router.put("/notificacoes/{notif_id}/lida")
async def marcar_lida(notif_id: str, user: Dict = Depends(get_current_user)):
    await db.notificacoes.update_one(
        {"id": notif_id, "usuario_id": user['id']},
        {"$set": {"lida": True}}
    )
    return {"success": True}

@api_router.put("/notificacoes/marcar-todas-lidas")
async def marcar_todas_lidas(user: Dict = Depends(get_current_user)):
    await db.notificacoes.update_many(
        {"usuario_id": user['id'], "lida": False},
        {"$set": {"lida": True}}
    )
    return {"success": True}

# ============== KPI ROUTES ==============

@api_router.get("/kpis", response_model=KPIResponse)
async def get_kpis(user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
    
    # Current month dates
    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # OS stats
    os_abertas = await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "iniciada", "pausada"]}})
    os_concluidas = await db.ordens_servico.find({**query, "status": "concluida", "tempo_efetivo_minutos": {"$exists": True}}, {"_id": 0, "tempo_efetivo_minutos": 1}).to_list(1000)
    
    os_concluidas_mes = await db.ordens_servico.count_documents({
        **query,
        "status": "concluida",
        "finish_at": {"$gte": first_of_month.isoformat()}
    })
    
    # Calculate MTTR (Mean Time To Repair)
    tempos = [os['tempo_efetivo_minutos'] for os in os_concluidas if os.get('tempo_efetivo_minutos')]
    mttr_minutos = sum(tempos) / len(tempos) if tempos else 0
    mttr_horas = mttr_minutos / 60
    
    # Inspeções
    total_inspecoes = await db.inspecoes.count_documents(query)
    inspecoes_ok = await db.inspecoes.count_documents({**query, "status": "concluida"})
    inspecoes_pendentes = await db.inspecoes.count_documents({**query, "status": "em_andamento"})
    
    inspecoes_mes = await db.inspecoes.count_documents({
        **query,
        "created_at": {"$gte": first_of_month.isoformat()}
    })
    
    taxa_conformidade = (inspecoes_ok / total_inspecoes * 100) if total_inspecoes > 0 else 100
    
    # Backlog
    backlog_total = await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "iniciada", "pausada"]}})
    
    # Assets
    ativos_total = await db.ativos.count_documents(query)
    ativos_falha = await db.ativos.count_documents({**query, "status": "falha"})
    
    # MTBF (simplified - days between failures)
    mtbf_horas = ((ativos_total - ativos_falha) / ativos_total * 720) if ativos_total > 0 else 720  # ~30 days in hours
    
    # Disponibilidade
    disponibilidade = (mtbf_horas / (mtbf_horas + mttr_horas) * 100) if (mtbf_horas + mttr_horas) > 0 else 100
    
    # Custo de manutenção do mês
    os_mes = await db.ordens_servico.find({
        **query,
        "status": "concluida",
        "finish_at": {"$gte": first_of_month.isoformat()},
        "custo_total": {"$exists": True}
    }, {"_id": 0, "custo_total": 1}).to_list(1000)
    custo_mes = sum(os.get('custo_total', 0) for os in os_mes)
    
    return KPIResponse(
        mttr_horas=round(mttr_horas, 2),
        mtbf_horas=round(mtbf_horas, 2),
        disponibilidade_percent=round(disponibilidade, 2),
        taxa_conformidade_percent=round(taxa_conformidade, 2),
        backlog_total=backlog_total,
        os_abertas=os_abertas,
        os_concluidas_mes=os_concluidas_mes,
        inspecoes_pendentes=inspecoes_pendentes,
        inspecoes_realizadas_mes=inspecoes_mes,
        ativos_em_falha=ativos_falha,
        custo_manutencao_mes=round(custo_mes, 2)
    )

# ============== DASHBOARD STATS ==============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
    
    ativos_total = await db.ativos.count_documents(query)
    ativos_operacionais = await db.ativos.count_documents({**query, "status": "operacional"})
    ativos_falha = await db.ativos.count_documents({**query, "status": "falha"})
    ativos_manutencao = await db.ativos.count_documents({**query, "status": "manutencao"})
    
    os_abertas = await db.ordens_servico.count_documents({**query, "status": "aberta"})
    os_em_andamento = await db.ordens_servico.count_documents({**query, "status": "iniciada"})
    os_pausadas = await db.ordens_servico.count_documents({**query, "status": "pausada"})
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    os_concluidas_hoje = await db.ordens_servico.count_documents({
        **query,
        "status": "concluida",
        "finish_at": {"$gte": today_start.isoformat()}
    })
    
    inspecoes_hoje = await db.inspecoes.count_documents({
        **query,
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    inspecoes_pendentes = await db.inspecoes.count_documents({**query, "status": "em_andamento"})
    
    # Itens estoque crítico
    estoque_items = await db.itens_estoque.find(query, {"_id": 0, "saldo": 1, "estoque_minimo": 1}).to_list(1000)
    estoque_critico = sum(1 for i in estoque_items if i.get('saldo', 0) <= i.get('estoque_minimo', 0))
    
    # OS by priority
    os_by_priority = {
        "A": await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "iniciada"]}, "prioridade": "A"}),
        "B": await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "iniciada"]}, "prioridade": "B"}),
        "C": await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "iniciada"]}, "prioridade": "C"}),
        "D": await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "iniciada"]}, "prioridade": "D"}),
    }
    
    return {
        "ativos": {
            "total": ativos_total,
            "operacionais": ativos_operacionais,
            "em_falha": ativos_falha,
            "em_manutencao": ativos_manutencao
        },
        "ordens_servico": {
            "abertas": os_abertas,
            "em_andamento": os_em_andamento,
            "pausadas": os_pausadas,
            "concluidas_hoje": os_concluidas_hoje,
            "por_prioridade": os_by_priority
        },
        "inspecoes": {
            "hoje": inspecoes_hoje,
            "pendentes": inspecoes_pendentes
        },
        "estoque_critico": estoque_critico
    }

# ============== USERS ROUTES ==============

@api_router.get("/users")
async def list_users(role: Optional[UserRole] = None, user: Dict = Depends(get_current_user)):
    if user['role'] not in ['admin', 'supervisor']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if role:
        query['role'] = role.value
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(100)
    return users

@api_router.get("/users/tecnicos")
async def list_tecnicos(user: Dict = Depends(get_current_user)):
    """List all technicians for OS assignment"""
    query = {"deleted_at": None, "role": {"$in": ["tecnico", "inspetor"]}}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    
    tecnicos = await db.users.find(query, {"_id": 0, "id": 1, "nome": 1, "email": 1, "telefone": 1}).to_list(100)
    return tecnicos

# ============== SEED DATA ==============

@api_router.post("/seed")
async def seed_data():
    """Seed initial data for testing"""
    # Check if already seeded
    existing = await db.organizations.find_one({"nome": "Indústria Demo"})
    if existing:
        return {"message": "Dados já existem"}
    
    # Create organization
    org = Organization(nome="Indústria Demo", cnpj="00.000.000/0001-00")
    org_doc = org.model_dump()
    org_doc['created_at'] = org_doc['created_at'].isoformat()
    await db.organizations.insert_one(org_doc)
    
    # Create admin user
    admin = User(
        email="admin@manutrix.com",
        nome="Administrador",
        role=UserRole.ADMIN,
        organization_id=org.id
    )
    admin_doc = admin.model_dump()
    admin_doc['password_hash'] = hash_password("admin123")
    admin_doc['created_at'] = admin_doc['created_at'].isoformat()
    await db.users.insert_one(admin_doc)
    
    # Create supervisor
    supervisor = User(
        email="supervisor@manutrix.com",
        nome="Maria Supervisora",
        role=UserRole.SUPERVISOR,
        organization_id=org.id,
        telefone="(11) 98765-4321"
    )
    supervisor_doc = supervisor.model_dump()
    supervisor_doc['password_hash'] = hash_password("supervisor123")
    supervisor_doc['created_at'] = supervisor_doc['created_at'].isoformat()
    await db.users.insert_one(supervisor_doc)
    
    # Create technician
    tecnico = User(
        email="tecnico@manutrix.com",
        nome="João Silva",
        role=UserRole.TECNICO,
        organization_id=org.id,
        telefone="(11) 91234-5678"
    )
    tecnico_doc = tecnico.model_dump()
    tecnico_doc['password_hash'] = hash_password("tecnico123")
    tecnico_doc['created_at'] = tecnico_doc['created_at'].isoformat()
    await db.users.insert_one(tecnico_doc)
    
    # Create second technician
    tecnico2 = User(
        email="pedro@manutrix.com",
        nome="Pedro Santos",
        role=UserRole.TECNICO,
        organization_id=org.id,
        telefone="(11) 99999-8888"
    )
    tecnico2_doc = tecnico2.model_dump()
    tecnico2_doc['password_hash'] = hash_password("pedro123")
    tecnico2_doc['created_at'] = tecnico2_doc['created_at'].isoformat()
    await db.users.insert_one(tecnico2_doc)
    
    # Create planta
    planta = Planta(nome="Planta Principal", endereco="Rua Industrial, 1000 - São Paulo, SP", organization_id=org.id, latitude=-23.550520, longitude=-46.633308)
    planta_doc = planta.model_dump()
    planta_doc['created_at'] = planta_doc['created_at'].isoformat()
    await db.plantas.insert_one(planta_doc)
    
    # Create areas
    areas_data = [
        {"nome": "Utilidades", "cor": "#10b981", "descricao": "Sistemas de água, ar comprimido e energia"},
        {"nome": "Produção", "cor": "#3b82f6", "descricao": "Linha de produção principal"},
        {"nome": "Embalagem", "cor": "#f59e0b", "descricao": "Área de embalagem e expedição"},
        {"nome": "Manutenção", "cor": "#8b5cf6", "descricao": "Oficina de manutenção"}
    ]
    areas = []
    for ad in areas_data:
        area = Area(nome=ad['nome'], planta_id=planta.id, cor=ad['cor'], descricao=ad['descricao'])
        area_doc = area.model_dump()
        area_doc['created_at'] = area_doc['created_at'].isoformat()
        await db.areas.insert_one(area_doc)
        areas.append(area)
    
    # Create ativos with more details
    ativos_data = [
        {"tag": "BOM-001", "nome": "Bomba Centrífuga 01", "criticidade": "A", "area_idx": 0, "fabricante": "KSB", "modelo": "Meganorm 50-200", "potencia": "15 kW", "rpm": 3500},
        {"tag": "BOM-002", "nome": "Bomba Centrífuga 02", "criticidade": "B", "area_idx": 0, "fabricante": "KSB", "modelo": "Meganorm 40-160", "potencia": "7.5 kW", "rpm": 3500},
        {"tag": "CMP-001", "nome": "Compressor de Ar", "criticidade": "A", "area_idx": 0, "fabricante": "Atlas Copco", "modelo": "GA 30+", "potencia": "30 kW"},
        {"tag": "EST-001", "nome": "Esteira Transportadora 01", "criticidade": "B", "area_idx": 1, "fabricante": "Rexnord", "modelo": "FlatTop 2010"},
        {"tag": "EST-002", "nome": "Esteira Transportadora 02", "criticidade": "C", "area_idx": 1, "fabricante": "Rexnord", "modelo": "FlatTop 2010"},
        {"tag": "MIS-001", "nome": "Misturador Industrial", "criticidade": "A", "area_idx": 1, "fabricante": "Ekato", "modelo": "HWL", "potencia": "22 kW"},
        {"tag": "EMB-001", "nome": "Encaixotadora Automática", "criticidade": "B", "area_idx": 2, "fabricante": "Bosch", "modelo": "CUC 3001"},
        {"tag": "EMB-002", "nome": "Paletizadora", "criticidade": "B", "area_idx": 2, "fabricante": "KUKA", "modelo": "KR 180 PA"},
        {"tag": "TOR-001", "nome": "Torno Mecânico", "criticidade": "C", "area_idx": 3, "fabricante": "Romi", "modelo": "Tormax 30A"},
        {"tag": "FRE-001", "nome": "Fresadora CNC", "criticidade": "B", "area_idx": 3, "fabricante": "Romi", "modelo": "D 800"},
    ]
    
    ativos = []
    for ativo_data in ativos_data:
        ativo = Ativo(
            tag=ativo_data['tag'],
            nome=ativo_data['nome'],
            criticidade=Criticidade(ativo_data['criticidade']),
            area_id=areas[ativo_data['area_idx']].id,
            organization_id=org.id,
            fabricante=ativo_data.get('fabricante'),
            modelo=ativo_data.get('modelo'),
            potencia=ativo_data.get('potencia'),
            rpm=ativo_data.get('rpm')
        )
        ativo_doc = ativo.model_dump()
        ativo_doc['created_at'] = ativo_doc['created_at'].isoformat()
        await db.ativos.insert_one(ativo_doc)
        ativos.append(ativo)
    
    # Create multiple rotas de inspeção
    rotas_data = [
        {
            "nome": "Inspeção Diária - Bomba Centrífuga",
            "tipo_ativo": "bomba_centrifuga",
            "frequencia": Frequencia.DIARIA,
            "tempo_estimado_minutos": 10,
            "itens": [
                ItemInspecaoTemplate(descricao="Verificar ruído anormal", tipo_resposta=TipoResposta.BOOLEAN, ordem=1, categoria="Operação"),
                ItemInspecaoTemplate(descricao="Verificar vazamentos", tipo_resposta=TipoResposta.BOOLEAN, ordem=2, categoria="Operação", requer_foto_se_nok=True),
                ItemInspecaoTemplate(descricao="Verificar vibração excessiva", tipo_resposta=TipoResposta.BOOLEAN, ordem=3, categoria="Operação"),
                ItemInspecaoTemplate(descricao="Verificar nível de óleo", tipo_resposta=TipoResposta.BOOLEAN, ordem=4, categoria="Lubrificação"),
            ]
        },
        {
            "nome": "Inspeção Mensal - Bomba Centrífuga",
            "tipo_ativo": "bomba_centrifuga",
            "frequencia": Frequencia.MENSAL,
            "tempo_estimado_minutos": 30,
            "itens": [
                ItemInspecaoTemplate(descricao="Verificar ruído anormal", tipo_resposta=TipoResposta.BOOLEAN, ordem=1, categoria="Operação"),
                ItemInspecaoTemplate(descricao="Verificar vazamentos", tipo_resposta=TipoResposta.BOOLEAN, ordem=2, categoria="Operação", requer_foto_se_nok=True),
                ItemInspecaoTemplate(descricao="Medir temperatura do motor (°C)", tipo_resposta=TipoResposta.NUMERO, valor_esperado="60", tolerancia_min=40, tolerancia_max=80, unidade="°C", ordem=3, categoria="Temperatura"),
                ItemInspecaoTemplate(descricao="Medir vibração (mm/s)", tipo_resposta=TipoResposta.NUMERO, tolerancia_min=0, tolerancia_max=4.5, unidade="mm/s", ordem=4, categoria="Vibração"),
                ItemInspecaoTemplate(descricao="Verificar alinhamento", tipo_resposta=TipoResposta.BOOLEAN, ordem=5, categoria="Mecânica"),
                ItemInspecaoTemplate(descricao="Verificar nível de óleo", tipo_resposta=TipoResposta.BOOLEAN, ordem=6, categoria="Lubrificação"),
                ItemInspecaoTemplate(descricao="Estado geral do equipamento", tipo_resposta=TipoResposta.SELECAO, opcoes=["Bom", "Regular", "Ruim"], ordem=7, categoria="Geral"),
                ItemInspecaoTemplate(descricao="Observações gerais", tipo_resposta=TipoResposta.TEXTO, obrigatorio=False, ordem=8, categoria="Geral"),
                ItemInspecaoTemplate(descricao="Foto do equipamento", tipo_resposta=TipoResposta.FOTO, obrigatorio=False, ordem=9, categoria="Documentação"),
            ]
        },
        {
            "nome": "Inspeção Semanal - Compressor",
            "tipo_ativo": "compressor",
            "frequencia": Frequencia.SEMANAL,
            "tempo_estimado_minutos": 20,
            "itens": [
                ItemInspecaoTemplate(descricao="Verificar pressão de trabalho (bar)", tipo_resposta=TipoResposta.NUMERO, valor_esperado="8", tolerancia_min=7, tolerancia_max=10, unidade="bar", ordem=1),
                ItemInspecaoTemplate(descricao="Verificar nível de óleo", tipo_resposta=TipoResposta.BOOLEAN, ordem=2),
                ItemInspecaoTemplate(descricao="Purgar condensado", tipo_resposta=TipoResposta.BOOLEAN, ordem=3),
                ItemInspecaoTemplate(descricao="Verificar filtro de ar", tipo_resposta=TipoResposta.SELECAO, opcoes=["Limpo", "Sujo - trocar", "Recém trocado"], ordem=4),
                ItemInspecaoTemplate(descricao="Medir temperatura do óleo (°C)", tipo_resposta=TipoResposta.NUMERO, tolerancia_min=40, tolerancia_max=90, unidade="°C", ordem=5),
            ]
        },
        {
            "nome": "Inspeção Diária - Esteira",
            "tipo_ativo": "esteira",
            "frequencia": Frequencia.DIARIA,
            "tempo_estimado_minutos": 5,
            "itens": [
                ItemInspecaoTemplate(descricao="Verificar tensão da correia", tipo_resposta=TipoResposta.BOOLEAN, ordem=1),
                ItemInspecaoTemplate(descricao="Verificar alinhamento", tipo_resposta=TipoResposta.BOOLEAN, ordem=2),
                ItemInspecaoTemplate(descricao="Limpar sensores", tipo_resposta=TipoResposta.BOOLEAN, ordem=3),
            ]
        },
    ]
    
    for rota_data in rotas_data:
        rota = RotaInspecao(
            nome=rota_data['nome'],
            tipo_ativo=rota_data['tipo_ativo'],
            frequencia=rota_data['frequencia'],
            tempo_estimado_minutos=rota_data['tempo_estimado_minutos'],
            organization_id=org.id,
            itens=rota_data['itens']
        )
        rota_doc = rota.model_dump()
        rota_doc['created_at'] = rota_doc['created_at'].isoformat()
        await db.rotas_inspecao.insert_one(rota_doc)
    
    # Create sample OS
    os_data = [
        {"ativo_idx": 0, "titulo": "Troca de rolamento", "descricao": "Rolamento apresentando ruído anormal. Substituir conforme procedimento PM-BOM-001.", "tipo": OSOrigem.PREVENTIVA, "prioridade": Criticidade.B, "status": OSStatus.ABERTA},
        {"ativo_idx": 2, "titulo": "Vazamento de óleo", "descricao": "Vazamento detectado na junta do cabeçote.", "tipo": OSOrigem.INSPECAO, "prioridade": Criticidade.A, "status": OSStatus.INICIADA},
        {"ativo_idx": 5, "titulo": "Calibração de sensores", "descricao": "Calibração anual dos sensores de temperatura e pressão.", "tipo": OSOrigem.PREVENTIVA, "prioridade": Criticidade.C, "status": OSStatus.ABERTA},
    ]
    
    for idx, os_d in enumerate(os_data):
        numero = await gerar_numero_os(org.id)
        os_obj = OrdemServico(
            ativo_id=ativos[os_d['ativo_idx']].id,
            titulo=os_d['titulo'],
            descricao=os_d['descricao'],
            tipo=os_d['tipo'],
            prioridade=os_d['prioridade'],
            organization_id=org.id,
            numero=numero,
            tecnico_id=tecnico.id if idx == 1 else None,
            status=os_d['status']
        )
        os_doc = os_obj.model_dump()
        os_doc['created_at'] = os_doc['created_at'].isoformat()
        if os_d['status'] == OSStatus.INICIADA:
            os_doc['start_at'] = datetime.now(timezone.utc).isoformat()
        await db.ordens_servico.insert_one(os_doc)
    
    # Create estoque items with more details
    estoque_data = [
        {"sku": "ROL-6205", "nome": "Rolamento 6205-2RS", "saldo": 15, "minimo": 5, "custo": 45.00, "categoria": "Rolamentos", "localizacao": "Prateleira A-01"},
        {"sku": "ROL-6305", "nome": "Rolamento 6305-2RS", "saldo": 8, "minimo": 3, "custo": 65.00, "categoria": "Rolamentos", "localizacao": "Prateleira A-01"},
        {"sku": "OLE-HID", "nome": "Óleo Hidráulico 20L", "saldo": 8, "minimo": 3, "custo": 180.00, "categoria": "Lubrificantes", "localizacao": "Prateleira B-02"},
        {"sku": "OLE-MOT", "nome": "Óleo Motor SAE 40 5L", "saldo": 12, "minimo": 4, "custo": 85.00, "categoria": "Lubrificantes", "localizacao": "Prateleira B-02"},
        {"sku": "VED-BOM", "nome": "Kit Vedação Bomba KSB", "saldo": 10, "minimo": 4, "custo": 120.00, "categoria": "Vedações", "localizacao": "Prateleira C-03"},
        {"sku": "COR-V-A68", "nome": "Correia V A-68", "saldo": 6, "minimo": 2, "custo": 35.00, "categoria": "Correias", "localizacao": "Prateleira D-01"},
        {"sku": "COR-V-B75", "nome": "Correia V B-75", "saldo": 4, "minimo": 2, "custo": 42.00, "categoria": "Correias", "localizacao": "Prateleira D-01"},
        {"sku": "FIL-AR-001", "nome": "Filtro de Ar Compressor", "saldo": 3, "minimo": 2, "custo": 250.00, "categoria": "Filtros", "localizacao": "Prateleira E-01"},
        {"sku": "FIL-OLE-001", "nome": "Filtro de Óleo Compressor", "saldo": 2, "minimo": 2, "custo": 180.00, "categoria": "Filtros", "localizacao": "Prateleira E-01"},
        {"sku": "GRX-MP2", "nome": "Graxa MP2 Multiuso 1kg", "saldo": 20, "minimo": 5, "custo": 35.00, "categoria": "Lubrificantes", "localizacao": "Prateleira B-03"},
    ]
    
    for item_data in estoque_data:
        item = ItemEstoque(
            sku=item_data['sku'],
            nome=item_data['nome'],
            saldo=item_data['saldo'],
            estoque_minimo=item_data['minimo'],
            custo_medio=item_data['custo'],
            valor_total=item_data['saldo'] * item_data['custo'],
            organization_id=org.id,
            categoria=item_data.get('categoria'),
            localizacao=item_data.get('localizacao')
        )
        item_doc = item.model_dump()
        item_doc['created_at'] = item_doc['created_at'].isoformat()
        await db.itens_estoque.insert_one(item_doc)
    
    return {
        "message": "Dados de demonstração criados com sucesso!",
        "credentials": {
            "admin": {"email": "admin@manutrix.com", "password": "admin123"},
            "supervisor": {"email": "supervisor@manutrix.com", "password": "supervisor123"},
            "tecnico": {"email": "tecnico@manutrix.com", "password": "tecnico123"},
            "tecnico2": {"email": "pedro@manutrix.com", "password": "pedro123"}
        },
        "data": {
            "organizacao": org.nome,
            "planta": planta.nome,
            "areas": len(areas),
            "ativos": len(ativos),
            "rotas_inspecao": len(rotas_data),
            "itens_estoque": len(estoque_data)
        }
    }

# ============== ROOT ==============

@api_router.get("/")
async def root():
    return {"message": "MANUTRIX API v2.0.0", "status": "online"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
