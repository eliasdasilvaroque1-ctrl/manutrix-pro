"""Shared models, enums, and Pydantic schemas for MANUTRIX API"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime, timezone
import uuid


# ============== ENUMS ==============

class UserRole(str, Enum):
    ADMIN = "admin"
    GERENTE = "gerente"
    PCM = "pcm"
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
    CORREIA = "correia"
    VEDACAO = "vedacao"
    FILTRO = "filtro"
    ELETRICO = "eletrico"
    MECANICO = "mecanico"
    HIDRAULICO = "hidraulico"
    PNEUMATICO = "pneumatico"
    OUTRO = "outro"

class UnidadeEstoque(str, Enum):
    UN = "UN"
    KG = "KG"
    L = "L"
    M = "M"
    CX = "CX"
    PC = "PC"
    PAR = "PAR"

class NotificacaoTipo(str, Enum):
    OS_CRIADA = "os_criada"
    OS_ATUALIZADA = "os_atualizada"
    OS_CONCLUIDA = "os_concluida"
    INSPECAO_PENDENTE = "inspecao_pendente"
    INSPECAO_CONCLUIDA = "inspecao_concluida"
    ESTOQUE_CRITICO = "estoque_critico"
    ATIVO_PARADO = "ativo_parado"
    ANOMALIA = "anomalia"
    OS_ATRIBUIDA = "os_atribuida"


# ============== MODELS ==============

class UserBase(BaseModel):
    email: str
    nome: str
    role: UserRole = UserRole.TECNICO
    telefone: Optional[str] = None
    organization_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    cnpj: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlantCreate(BaseModel):
    codigo: str
    nome: str
    descricao: Optional[str] = None
    is_active: bool = True

class PlantUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    is_active: Optional[bool] = None

class SectorCreate(BaseModel):
    plant_id: str
    codigo: str
    nome: str
    descricao: Optional[str] = None
    cor: str = "#10b981"
    is_active: bool = True

class SectorUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    cor: Optional[str] = None
    is_active: Optional[bool] = None

class Area(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    planta_id: str
    cor: str = "#10b981"
    descricao: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AtivoCreate(BaseModel):
    tag: Optional[str] = None
    nome: str
    tipo_equipamento: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    plant_id: Optional[str] = None
    sector_id: Optional[str] = None
    area_id: Optional[str] = None
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
    plant_id: Optional[str] = None
    sector_id: Optional[str] = None
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

class EstoqueCreate(BaseModel):
    sku: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    categoria: CategoriaEstoque = CategoriaEstoque.OUTRO
    quantidade: float = 0
    unidade: UnidadeEstoque = UnidadeEstoque.UN
    estoque_minimo: float = 0
    custo_unitario: float = 0
    almoxarifado: str = "Principal"
    prateleira: Optional[str] = None
    fornecedor: Optional[str] = None
    item_critico: bool = False
    alertar_minimo: bool = True
    observacoes: Optional[str] = None

class EstoqueUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[CategoriaEstoque] = None
    quantidade: Optional[float] = None
    unidade: Optional[UnidadeEstoque] = None
    estoque_minimo: Optional[float] = None
    custo_unitario: Optional[float] = None
    almoxarifado: Optional[str] = None
    prateleira: Optional[str] = None
    fornecedor: Optional[str] = None
    item_critico: Optional[bool] = None
    alertar_minimo: Optional[bool] = None
    observacoes: Optional[str] = None

class OSCreate(BaseModel):
    ativo_id: str
    tipo: OSTipo
    prioridade: Criticidade = Criticidade.MEDIA
    titulo: str
    descricao: Optional[str] = None
    origem: OSOrigem = OSOrigem.MANUAL
    responsavel_id: Optional[str] = None
    equipe: List[str] = []
    data_planejada: Optional[str] = None
    custo_pecas: float = 0
    custo_mao_obra: float = 0

class OSUpdate(BaseModel):
    tipo: Optional[OSTipo] = None
    prioridade: Optional[Criticidade] = None
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    responsavel_id: Optional[str] = None
    equipe: Optional[List[str]] = None
    data_planejada: Optional[str] = None
    custo_pecas: Optional[float] = None
    custo_mao_obra: Optional[float] = None
    servicos_realizados: Optional[str] = None

class ChecklistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    descricao: str
    tipo: str = "boolean"
    tolerancia_min: Optional[float] = None
    tolerancia_max: Optional[float] = None
    unidade: Optional[str] = None
    obrigatorio: bool = True
    valor: Optional[str] = None
    conforme: Optional[bool] = None
    observacao: Optional[str] = None

class InspecaoCreate(BaseModel):
    ativo_id: str
    tipo: str = "rotina"
    frequencia: str = "diaria"
    responsavel_id: Optional[str] = None
    rota_id: Optional[str] = None
    checklist: List[ChecklistItem] = []
    observacoes: Optional[str] = None
    lubrificacao: Optional[dict] = None
    data_planejada: Optional[str] = None

class InspecaoUpdate(BaseModel):
    responsavel_id: Optional[str] = None
    observacoes: Optional[str] = None
    data_planejada: Optional[str] = None

class RotaInspecaoCreate(BaseModel):
    nome: str
    tipo_ativo: str
    frequencia: str = "diaria"
    itens: List[dict] = []
    tempo_estimado_minutos: int = 15
    ativa: bool = True

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

class MovimentacaoEstoque(BaseModel):
    tipo: str
    quantidade: float
    motivo: Optional[str] = None
    os_id: Optional[str] = None
    custo_unitario: Optional[float] = None

class KanbanMoveBody(BaseModel):
    new_status: str

class ConcluirOSBody(BaseModel):
    observacoes: Optional[str] = None
    servicos_realizados: Optional[str] = None
    tempo_execucao_minutos: Optional[int] = None
    custo_pecas: Optional[float] = None
    custo_mao_obra: Optional[float] = None

class ConcluirInspecaoBody(BaseModel):
    checklist: List[dict] = []
    observacoes: Optional[str] = None
    resultado: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ChatMessage(BaseModel):
    message: str
    ativo_id: Optional[str] = None
    session_id: Optional[str] = None

class SpareAssetCreate(BaseModel):
    sku: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    tipo_equipamento: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    quantidade: int = 0
    estoque_minimo: int = 0
    custo_unitario: float = 0
    localizacao: Optional[str] = None

class SpareAssetUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    tipo_equipamento: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    quantidade: Optional[int] = None
    estoque_minimo: Optional[int] = None
    custo_unitario: Optional[float] = None
    localizacao: Optional[str] = None

class SpareMovementCreate(BaseModel):
    spare_id: str
    tipo: str
    quantidade: int
    motivo: Optional[str] = None
    os_id: Optional[str] = None
    custo_unitario: Optional[float] = None

class AnomaliaCreate(BaseModel):
    ativo_id: str
    descricao: str
    severidade: str = "media"
    inspecao_id: Optional[str] = None
    gerar_os: bool = True

class KnowledgeBaseCreate(BaseModel):
    tipo_equipamento: str
    problema: str
    solucao: str
    tags: List[str] = []
    categoria: str = "geral"

class MovimentacaoCreateBody(BaseModel):
    tipo: str
    quantidade: float
    motivo: Optional[str] = None
    os_id: Optional[str] = None
    custo_unitario: Optional[float] = None
