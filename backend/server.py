from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# Create the main app
app = FastAPI(title="MANUTRIX API", version="1.0.0")

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

# ============== MODELS ==============

class UserBase(BaseModel):
    email: EmailStr
    nome: str
    role: UserRole = UserRole.TECNICO
    organization_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

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
    ano_aquisicao: Optional[int] = None
    localizacao_fisica: Optional[str] = None
    datasheet_url: Optional[str] = None
    manual_url: Optional[str] = None

class AtivoCreate(AtivoBase):
    pass

class Ativo(AtivoBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qr_code: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
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
    obrigatorio: bool = True
    ordem: int = 0

class RotaInspecaoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    tipo_ativo: str  # Ex: "bomba_centrifuga"
    frequencia: Frequencia
    itens: List[ItemInspecaoTemplate] = []

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
    geolocalizacao: Optional[Dict[str, float]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class FinalizarInspecao(BaseModel):
    respostas: List[RespostaInspecao]
    geolocalizacao: Optional[Dict[str, float]] = None

# Ordem de Serviço
class PecaUtilizada(BaseModel):
    item_id: str
    quantidade: float
    custo_unitario: Optional[float] = None

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
    observacoes: Optional[str] = None
    fotos: List[str] = []
    start_at: Optional[datetime] = None
    finish_at: Optional[datetime] = None
    tempo_efetivo_minutos: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class OSUpdate(BaseModel):
    status: Optional[OSStatus] = None
    tecnico_id: Optional[str] = None
    observacoes: Optional[str] = None
    pecas_utilizadas: Optional[List[PecaUtilizada]] = None

# Estoque
class ItemEstoqueBase(BaseModel):
    sku: str
    nome: str
    descricao: Optional[str] = None
    unidade: str = "UN"
    estoque_minimo: float = 0
    localizacao: Optional[str] = None

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# KPIs
class KPIResponse(BaseModel):
    mttr_horas: float = 0
    mtbf_horas: float = 0
    disponibilidade_percent: float = 100
    taxa_conformidade_percent: float = 100
    backlog_total: int = 0
    os_abertas: int = 0
    inspecoes_pendentes: int = 0

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
        organization_id=org_id
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
            "organization_id": user.get('organization_id')
        }
    )

@api_router.get("/auth/me")
async def get_me(user: Dict = Depends(get_current_user)):
    return {
        "id": user['id'],
        "email": user['email'],
        "nome": user['nome'],
        "role": user['role'],
        "organization_id": user.get('organization_id')
    }

# ============== ORGANIZATION ROUTES ==============

@api_router.get("/organizations", response_model=List[Organization])
async def list_organizations(user: Dict = Depends(get_current_user)):
    orgs = await db.organizations.find({"deleted_at": None}, {"_id": 0}).to_list(100)
    return orgs

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
async def list_ativos(area_id: Optional[str] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if area_id:
        query['area_id'] = area_id
    ativos = await db.ativos.find(query, {"_id": 0}).to_list(1000)
    return ativos

@api_router.get("/ativos/{ativo_id}", response_model=Ativo)
async def get_ativo(ativo_id: str, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return ativo

@api_router.get("/ativos/qr/{qr_code}", response_model=Ativo)
async def get_ativo_by_qr(qr_code: str, user: Dict = Depends(get_current_user)):
    ativo = await db.ativos.find_one({"qr_code": qr_code, "deleted_at": None}, {"_id": 0})
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
    existing = await db.ativos.find_one({"tag": data.tag, "organization_id": org_id, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=400, detail="TAG já existe nesta organização")
    
    ativo = Ativo(**data.model_dump())
    ativo.organization_id = org_id
    
    doc = ativo.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.ativos.insert_one(doc)
    await auditar("ativo", ativo.id, "create", user['id'], org_id, depois=doc)
    return ativo

@api_router.put("/ativos/{ativo_id}", response_model=Ativo)
async def update_ativo(ativo_id: str, data: AtivoCreate, user: Dict = Depends(get_current_user)):
    existing = await db.ativos.find_one({"id": ativo_id, "deleted_at": None}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    update_data = data.model_dump()
    await db.ativos.update_one({"id": ativo_id}, {"$set": update_data})
    
    updated = await db.ativos.find_one({"id": ativo_id}, {"_id": 0})
    await auditar("ativo", ativo_id, "update", user['id'], existing.get('organization_id', ''), antes=existing, depois=updated)
    return updated

# ============== ROTA INSPECAO ROUTES ==============

@api_router.get("/rotas-inspecao", response_model=List[RotaInspecao])
async def list_rotas_inspecao(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    rotas = await db.rotas_inspecao.find(query, {"_id": 0}).to_list(100)
    return rotas

@api_router.post("/rotas-inspecao", response_model=RotaInspecao)
async def create_rota_inspecao(data: RotaInspecaoCreate, user: Dict = Depends(get_current_user)):
    rota = RotaInspecao(**data.model_dump())
    doc = rota.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.rotas_inspecao.insert_one(doc)
    return rota

# ============== INSPECAO ROUTES ==============

@api_router.get("/inspecoes", response_model=List[Inspecao])
async def list_inspecoes(status: Optional[InspecaoStatus] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if status:
        query['status'] = status.value
    inspecoes = await db.inspecoes.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return inspecoes

@api_router.get("/inspecoes/{inspecao_id}", response_model=Inspecao)
async def get_inspecao(inspecao_id: str, user: Dict = Depends(get_current_user)):
    inspecao = await db.inspecoes.find_one({"id": inspecao_id, "deleted_at": None}, {"_id": 0})
    if not inspecao:
        raise HTTPException(status_code=404, detail="Inspeção não encontrada")
    return inspecao

@api_router.post("/inspecoes", response_model=Inspecao)
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
    
    return inspecao

@api_router.post("/inspecoes/{inspecao_id}/finalizar")
async def finalizar_inspecao(inspecao_id: str, data: FinalizarInspecao, user: Dict = Depends(get_current_user)):
    """
    RPC Atômico para fechamento de inspeção:
    1. Valida respostas
    2. Atualiza status da inspeção
    3. Gera OS de correção para falhas
    4. Atualiza status do ativo
    5. Grava auditoria
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
                descricao=f"Não conformidade detectada em inspeção. {resposta.observacao or ''}",
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
    
    # Determine final status
    status_final = InspecaoStatus.CONCLUIDA if not nao_conformes else InspecaoStatus.COM_PENDENCIAS
    
    # Update ativo status
    novo_status_ativo = AssetStatus.OPERACIONAL if not nao_conformes else AssetStatus.FALHA
    await db.ativos.update_one(
        {"id": inspecao['ativo_id']},
        {"$set": {"status": novo_status_ativo.value}}
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
        "total_nao_conformes": len(nao_conformes)
    }

# ============== ORDEM DE SERVICO ROUTES ==============

@api_router.get("/ordens-servico", response_model=List[OrdemServico])
async def list_ordens_servico(status: Optional[OSStatus] = None, user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    if status:
        query['status'] = status.value
    os_list = await db.ordens_servico.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
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

@api_router.get("/ordens-servico/{os_id}", response_model=OrdemServico)
async def get_ordem_servico(os_id: str, user: Dict = Depends(get_current_user)):
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    return os

@api_router.post("/ordens-servico", response_model=OrdemServico)
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
    await auditar("ordem_servico", os.id, "create", user['id'], org_id, depois=doc)
    return os

@api_router.put("/ordens-servico/{os_id}", response_model=OrdemServico)
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
    
    await db.ordens_servico.update_one({"id": os_id}, {"$set": update_data})
    updated = await db.ordens_servico.find_one({"id": os_id}, {"_id": 0})
    await auditar("ordem_servico", os_id, "update", user['id'], existing.get('organization_id', ''), antes=existing, depois=updated)
    return updated

@api_router.post("/ordens-servico/{os_id}/finalizar")
async def finalizar_ordem_servico(os_id: str, pecas: List[PecaUtilizada] = [], user: Dict = Depends(get_current_user)):
    """
    RPC Atômico para fechamento de OS:
    1. Atualiza OS para CONCLUÍDA
    2. Atualiza status do ativo
    3. Abate estoque das peças
    4. Grava auditoria
    """
    os = await db.ordens_servico.find_one({"id": os_id, "deleted_at": None}, {"_id": 0})
    if not os:
        raise HTTPException(status_code=404, detail="OS não encontrada")
    
    # Abater estoque
    for peca in pecas:
        item = await db.itens_estoque.find_one({"id": peca.item_id}, {"_id": 0})
        if item:
            novo_saldo = item.get('saldo', 0) - peca.quantidade
            await db.itens_estoque.update_one({"id": peca.item_id}, {"$set": {"saldo": novo_saldo}})
            
            # Registrar movimentação
            mov = MovimentacaoEstoque(
                item_id=peca.item_id,
                tipo=MovimentacaoTipo.SAIDA_OS,
                quantidade=-peca.quantidade,
                custo_unitario=peca.custo_unitario,
                os_id=os_id,
                usuario_id=user['id'],
                organization_id=os.get('organization_id', '')
            )
            mov_doc = mov.model_dump()
            mov_doc['created_at'] = mov_doc['created_at'].isoformat()
            await db.movimentacoes_estoque.insert_one(mov_doc)
    
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
        "pecas_utilizadas": pecas_dict
    }
    
    await db.ordens_servico.update_one({"id": os_id}, {"$set": update_data})
    
    # Update ativo status
    await db.ativos.update_one(
        {"id": os['ativo_id']},
        {"$set": {"status": AssetStatus.OPERACIONAL.value}}
    )
    
    await auditar("ordem_servico", os_id, "finalizar", user['id'], os.get('organization_id', ''), antes=os, depois={**os, **update_data})
    
    return {"success": True, "tempo_efetivo_minutos": tempo_efetivo}

# ============== ESTOQUE ROUTES ==============

@api_router.get("/estoque", response_model=List[ItemEstoque])
async def list_estoque(user: Dict = Depends(get_current_user)):
    query = {"deleted_at": None}
    if user.get('organization_id'):
        query['organization_id'] = user['organization_id']
    items = await db.itens_estoque.find(query, {"_id": 0}).to_list(500)
    return items

@api_router.post("/estoque", response_model=ItemEstoque)
async def create_item_estoque(data: ItemEstoqueCreate, user: Dict = Depends(get_current_user)):
    item = ItemEstoque(
        sku=data.sku,
        nome=data.nome,
        descricao=data.descricao,
        unidade=data.unidade,
        estoque_minimo=data.estoque_minimo,
        localizacao=data.localizacao,
        organization_id=data.organization_id,
        saldo=data.saldo_inicial,
        custo_medio=data.custo_unitario
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

# ============== KPI ROUTES ==============

@api_router.get("/kpis", response_model=KPIResponse)
async def get_kpis(user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
    
    # OS stats
    os_abertas = await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "iniciada", "pausada"]}})
    os_concluidas = await db.ordens_servico.find({**query, "status": "concluida", "tempo_efetivo_minutos": {"$exists": True}}, {"_id": 0, "tempo_efetivo_minutos": 1}).to_list(1000)
    
    # Calculate MTTR (Mean Time To Repair)
    tempos = [os['tempo_efetivo_minutos'] for os in os_concluidas if os.get('tempo_efetivo_minutos')]
    mttr_minutos = sum(tempos) / len(tempos) if tempos else 0
    mttr_horas = mttr_minutos / 60
    
    # Inspeções
    total_inspecoes = await db.inspecoes.count_documents(query)
    inspecoes_ok = await db.inspecoes.count_documents({**query, "status": "concluida"})
    inspecoes_pendentes = await db.inspecoes.count_documents({**query, "status": "em_andamento"})
    
    taxa_conformidade = (inspecoes_ok / total_inspecoes * 100) if total_inspecoes > 0 else 100
    
    # Backlog
    backlog_total = await db.ordens_servico.count_documents({**query, "status": {"$in": ["aberta", "iniciada", "pausada"]}})
    
    # MTBF (simplified - days between failures)
    # In a real system, this would be calculated from failure history
    ativos_total = await db.ativos.count_documents(query)
    ativos_falha = await db.ativos.count_documents({**query, "status": "falha"})
    mtbf_horas = ((ativos_total - ativos_falha) / ativos_total * 720) if ativos_total > 0 else 720  # ~30 days in hours
    
    # Disponibilidade
    disponibilidade = (mtbf_horas / (mtbf_horas + mttr_horas) * 100) if (mtbf_horas + mttr_horas) > 0 else 100
    
    return KPIResponse(
        mttr_horas=round(mttr_horas, 2),
        mtbf_horas=round(mtbf_horas, 2),
        disponibilidade_percent=round(disponibilidade, 2),
        taxa_conformidade_percent=round(taxa_conformidade, 2),
        backlog_total=backlog_total,
        os_abertas=os_abertas,
        inspecoes_pendentes=inspecoes_pendentes
    )

# ============== DASHBOARD STATS ==============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: Dict = Depends(get_current_user)):
    org_id = user.get('organization_id', '')
    query = {"organization_id": org_id, "deleted_at": None} if org_id else {"deleted_at": None}
    
    ativos_total = await db.ativos.count_documents(query)
    ativos_operacionais = await db.ativos.count_documents({**query, "status": "operacional"})
    ativos_falha = await db.ativos.count_documents({**query, "status": "falha"})
    
    os_abertas = await db.ordens_servico.count_documents({**query, "status": "aberta"})
    os_em_andamento = await db.ordens_servico.count_documents({**query, "status": "iniciada"})
    os_concluidas_hoje = await db.ordens_servico.count_documents({
        **query,
        "status": "concluida",
        "finish_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()}
    })
    
    inspecoes_hoje = await db.inspecoes.count_documents({
        **query,
        "created_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()}
    })
    
    # Itens estoque crítico
    estoque_critico = await db.itens_estoque.count_documents({
        **query,
        "$expr": {"$lte": ["$saldo", "$estoque_minimo"]}
    })
    
    return {
        "ativos": {
            "total": ativos_total,
            "operacionais": ativos_operacionais,
            "em_falha": ativos_falha
        },
        "ordens_servico": {
            "abertas": os_abertas,
            "em_andamento": os_em_andamento,
            "concluidas_hoje": os_concluidas_hoje
        },
        "inspecoes_hoje": inspecoes_hoje,
        "estoque_critico": estoque_critico
    }

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
    
    # Create technician
    tecnico = User(
        email="tecnico@manutrix.com",
        nome="João Silva",
        role=UserRole.TECNICO,
        organization_id=org.id
    )
    tecnico_doc = tecnico.model_dump()
    tecnico_doc['password_hash'] = hash_password("tecnico123")
    tecnico_doc['created_at'] = tecnico_doc['created_at'].isoformat()
    await db.users.insert_one(tecnico_doc)
    
    # Create planta
    planta = Planta(nome="Planta Principal", endereco="Rua Industrial, 1000", organization_id=org.id)
    planta_doc = planta.model_dump()
    planta_doc['created_at'] = planta_doc['created_at'].isoformat()
    await db.plantas.insert_one(planta_doc)
    
    # Create areas
    areas_data = ["Utilidades", "Produção", "Embalagem", "Manutenção"]
    areas = []
    for nome in areas_data:
        area = Area(nome=nome, planta_id=planta.id)
        area_doc = area.model_dump()
        area_doc['created_at'] = area_doc['created_at'].isoformat()
        await db.areas.insert_one(area_doc)
        areas.append(area)
    
    # Create ativos
    ativos_data = [
        {"tag": "BOM-001", "nome": "Bomba Centrífuga 01", "criticidade": "A", "area_idx": 0},
        {"tag": "BOM-002", "nome": "Bomba Centrífuga 02", "criticidade": "B", "area_idx": 0},
        {"tag": "CMP-001", "nome": "Compressor de Ar", "criticidade": "A", "area_idx": 0},
        {"tag": "EST-001", "nome": "Esteira Transportadora 01", "criticidade": "B", "area_idx": 1},
        {"tag": "MIS-001", "nome": "Misturador Industrial", "criticidade": "A", "area_idx": 1},
        {"tag": "EMB-001", "nome": "Encaixotadora Automática", "criticidade": "B", "area_idx": 2},
        {"tag": "TOR-001", "nome": "Torno Mecânico", "criticidade": "C", "area_idx": 3},
    ]
    
    ativos = []
    for ativo_data in ativos_data:
        ativo = Ativo(
            tag=ativo_data['tag'],
            nome=ativo_data['nome'],
            criticidade=Criticidade(ativo_data['criticidade']),
            area_id=areas[ativo_data['area_idx']].id,
            organization_id=org.id,
            fabricante="Fabricante Demo",
            modelo="Modelo X-100"
        )
        ativo_doc = ativo.model_dump()
        ativo_doc['created_at'] = ativo_doc['created_at'].isoformat()
        await db.ativos.insert_one(ativo_doc)
        ativos.append(ativo)
    
    # Create rota de inspeção
    rota = RotaInspecao(
        nome="Inspeção Mensal - Bomba Centrífuga",
        descricao="Checklist padrão para bombas centrífugas",
        tipo_ativo="bomba_centrifuga",
        frequencia=Frequencia.MENSAL,
        organization_id=org.id,
        itens=[
            ItemInspecaoTemplate(descricao="Verificar ruído anormal", tipo_resposta=TipoResposta.BOOLEAN, ordem=1),
            ItemInspecaoTemplate(descricao="Verificar vazamentos", tipo_resposta=TipoResposta.BOOLEAN, ordem=2),
            ItemInspecaoTemplate(descricao="Medir temperatura do motor (°C)", tipo_resposta=TipoResposta.NUMERO, valor_esperado="60", tolerancia_min=40, tolerancia_max=80, ordem=3),
            ItemInspecaoTemplate(descricao="Verificar vibração excessiva", tipo_resposta=TipoResposta.BOOLEAN, ordem=4),
            ItemInspecaoTemplate(descricao="Verificar nível de óleo", tipo_resposta=TipoResposta.BOOLEAN, ordem=5),
            ItemInspecaoTemplate(descricao="Observações gerais", tipo_resposta=TipoResposta.TEXTO, obrigatorio=False, ordem=6),
        ]
    )
    rota_doc = rota.model_dump()
    rota_doc['created_at'] = rota_doc['created_at'].isoformat()
    await db.rotas_inspecao.insert_one(rota_doc)
    
    # Create sample OS
    os1 = OrdemServico(
        ativo_id=ativos[0].id,
        titulo="Troca de rolamento",
        descricao="Rolamento apresentando ruído anormal",
        tipo=OSOrigem.PREVENTIVA,
        prioridade=Criticidade.B,
        organization_id=org.id,
        numero="2026-00001",
        tecnico_id=tecnico.id
    )
    os1_doc = os1.model_dump()
    os1_doc['created_at'] = os1_doc['created_at'].isoformat()
    await db.ordens_servico.insert_one(os1_doc)
    
    # Create estoque items
    estoque_data = [
        {"sku": "ROL-6205", "nome": "Rolamento 6205", "saldo": 15, "minimo": 5, "custo": 45.00},
        {"sku": "OLE-HID", "nome": "Óleo Hidráulico 20L", "saldo": 8, "minimo": 3, "custo": 180.00},
        {"sku": "VED-BOM", "nome": "Kit Vedação Bomba", "saldo": 10, "minimo": 4, "custo": 120.00},
        {"sku": "COR-V", "nome": "Correia V A-68", "saldo": 6, "minimo": 2, "custo": 35.00},
    ]
    
    for item_data in estoque_data:
        item = ItemEstoque(
            sku=item_data['sku'],
            nome=item_data['nome'],
            saldo=item_data['saldo'],
            estoque_minimo=item_data['minimo'],
            custo_medio=item_data['custo'],
            organization_id=org.id
        )
        item_doc = item.model_dump()
        item_doc['created_at'] = item_doc['created_at'].isoformat()
        await db.itens_estoque.insert_one(item_doc)
    
    return {
        "message": "Dados de demonstração criados com sucesso!",
        "credentials": {
            "admin": {"email": "admin@manutrix.com", "password": "admin123"},
            "tecnico": {"email": "tecnico@manutrix.com", "password": "tecnico123"}
        }
    }

# ============== ROOT ==============

@api_router.get("/")
async def root():
    return {"message": "MANUTRIX API v1.0.0", "status": "online"}

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
