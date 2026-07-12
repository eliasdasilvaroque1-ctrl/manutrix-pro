"""Shared models, enums, and Pydantic schemas for MAINTRIX API"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime, timezone
import uuid


# ============== ENUMS ==============

class UserRole(str, Enum):
    MASTER = "master"
    ADMIN = "admin"
    GERENTE = "gerente"
    PCM = "pcm"
    SUPERVISOR = "supervisor"
    TEC_MECANICO = "tec_mecanico"
    TEC_ELETRICO = "tec_eletrico"
    INSTRUMENTISTA = "instrumentista"
    LUBRIFICADOR = "lubrificador"
    OPERADOR = "operador"
    INSPETOR = "inspetor"
    VISUALIZADOR = "visualizador"
    # Backward compat
    TECNICO = "tecnico"
    VIEWER = "viewer"

class AssetStatus(str, Enum):
    OPERACIONAL = "operacional"
    PARADO = "parado"
    MANUTENCAO = "manutencao"
    DESATIVADO = "desativado"

class Prioridade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    EMERGENCIA = "emergencia"

class OSStatus(str, Enum):
    SOLICITADA = "solicitada"
    EM_ANALISE = "em_analise"
    AGUARDANDO_APROVACAO = "aguardando_aprovacao"
    AGUARDANDO_MATERIAL = "aguardando_material"
    PROGRAMADA = "programada"
    DISPONIVEL = "disponivel"
    EM_EXECUCAO = "em_execucao"
    PAUSADA = "pausada"
    CONCLUIDA = "concluida"
    ENCERRADA = "encerrada"
    CANCELADA = "cancelada"
    # Backward compat aliases
    ABERTA = "aberta"
    PLANEJADA = "planejada"

# Tipos de OS — valores configuráveis por empresa via org_config.tipos_os
# Defaults: corretiva, preventiva, melhoria, projeto, seguranca, meio_ambiente, lubrificacao, calibracao
# Mantidos como referência, mas NÃO validados por enum — aceita qualquer string

OS_TIPOS_PADRAO = [
    "corretiva", "preventiva", "melhoria", "projeto",
    "seguranca", "meio_ambiente", "lubrificacao", "calibracao",
    # Backward compat
    "inspecao", "fabricacao", "preparacao_material", "instalacao",
    "reforma", "emergencial", "limpeza_organizacao",
]

OS_ORIGENS_PADRAO = [
    "operador", "supervisor", "pcm", "inspecao",
    "preventiva", "lubrificacao", "qr_code", "manual",
]

class Disciplina(str, Enum):
    MECANICA = "mecanica"
    ELETRICA = "eletrica"
    INSTRUMENTACAO = "instrumentacao"
    CIVIL = "civil"
    PRODUCAO = "producao"

# OSOrigem removido como enum — valores livres (ver OS_ORIGENS_PADRAO)

class InspecaoTipo(str, Enum):
    INSPECAO = "inspecao"
    PREVENTIVA = "preventiva"
    LUBRIFICACAO = "lubrificacao"
    LIMPEZA = "limpeza"
    MELHORIA = "melhoria"
    # backward compat
    MECANICA = "mecanica"
    ELETRICA = "eletrica"

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
    OS_ATRIBUIDA = "os_atribuida"
    INSPECAO_PENDENTE = "inspecao_pendente"
    INSPECAO_CONCLUIDA = "inspecao_concluida"
    ESTOQUE_CRITICO = "estoque_critico"
    ATIVO_PARADO = "ativo_parado"


# ============== MODELS ==============

class UserBase(BaseModel):
    email: str
    nome: str
    role: UserRole = UserRole.TECNICO
    telefone: Optional[str] = None
    organization_id: Optional[str] = None
    disciplina_principal: Optional[str] = None  # mecanica, eletrica, instrumentacao, operacao, civil, producao
    disciplinas_secundarias: Optional[List[str]] = []
    turno: Optional[str] = None  # A, B, C, D, ADM
    unidade_ids: Optional[List[str]] = []  # unidades de atuação
    area_ids: Optional[List[str]] = []  # áreas de atuação

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
    organization_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    cnpj: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Planta (between Organization and Sector)
class PlantaCreate(BaseModel):
    codigo: str
    nome: str
    descricao: Optional[str] = None
    endereco: Optional[str] = None

class PlantaUpdate(BaseModel):
    codigo: Optional[str] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None
    endereco: Optional[str] = None

# Sector (belongs to a Planta)
class SectorCreate(BaseModel):
    codigo: str
    nome: str
    planta_id: Optional[str] = None
    descricao: Optional[str] = None
    cor: str = "#10b981"
    is_active: bool = True

class SectorUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    cor: Optional[str] = None
    is_active: Optional[bool] = None

# Ativo
# Ativo (simplified for field use)
class AtivoCreate(BaseModel):
    sector_id: str
    tag: Optional[str] = None
    nome: str
    tipo_equipamento: str
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[str] = "operacional"

class AtivoUpdate(BaseModel):
    sector_id: Optional[str] = None
    nome: Optional[str] = None
    tipo_equipamento: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[str] = None

# Materiais por Equipamento
class AtivoMaterialCreate(BaseModel):
    nome: str
    codigo: Optional[str] = None
    quantidade: float = 1
    unidade: str = "UN"
    observacoes: Optional[str] = None

# OS
class OSCreate(BaseModel):
    ativo_id: str
    tipo: str = "corretiva"
    disciplina: Optional[str] = None
    prioridade: str = "media"
    titulo: str
    descricao: Optional[str] = None
    justificativa: Optional[str] = None
    origem: str = "manual"
    execucao_direta: bool = False
    responsavel_id: Optional[str] = None
    equipe: List[str] = []
    data_planejada: Optional[str] = None
    custo_pecas: float = 0
    custo_mao_obra: float = 0
    causa_falha: Optional[str] = None
    equipamento_parado: bool = False
    horas_parada: Optional[float] = None

class OSUpdate(BaseModel):
    tipo: Optional[str] = None
    disciplina: Optional[str] = None
    prioridade: Optional[str] = None
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    justificativa: Optional[str] = None
    responsavel_id: Optional[str] = None
    equipe: Optional[List[str]] = None
    data_planejada: Optional[str] = None
    custo_pecas: Optional[float] = None
    custo_mao_obra: Optional[float] = None
    servicos_realizados: Optional[str] = None
    causa_falha: Optional[str] = None
    equipamento_parado: Optional[bool] = None
    horas_parada: Optional[float] = None
    status: Optional[str] = None

class KanbanMoveBody(BaseModel):
    new_status: str

class ConcluirOSBody(BaseModel):
    observacoes: Optional[str] = None
    servicos_realizados: Optional[str] = None
    tempo_execucao_minutos: Optional[int] = None
    custo_pecas: Optional[float] = None
    custo_mao_obra: Optional[float] = None
    skip_foto_check: Optional[bool] = False
    data_inicio: Optional[str] = None
    data_conclusao: Optional[str] = None

# Inspections
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
    plano_id: str  # OBRIGATÓRIO — toda execução deve vir de um plano aprovado
    tipo: Optional[str] = None  # derivado do plano se não informado
    disciplina: Optional[str] = None  # derivado do plano se não informado
    frequencia: Optional[str] = "diaria"
    responsavel_id: Optional[str] = None
    executantes: List[str] = []
    rota_id: Optional[str] = None
    checklist: List[ChecklistItem] = []
    observacoes: Optional[str] = None
    data_planejada: Optional[str] = None
    tipo_lubrificante: Optional[str] = None
    quantidade_lubrificante: Optional[str] = None
    ponto_lubrificacao: Optional[str] = None
    metodo_aplicacao: Optional[str] = None
    observacoes_lubrificacao: Optional[str] = None

class InspecaoUpdate(BaseModel):
    responsavel_id: Optional[str] = None
    executantes: Optional[List[str]] = None
    observacoes: Optional[str] = None
    data_planejada: Optional[str] = None

class ConcluirInspecaoBody(BaseModel):
    checklist: List[dict] = []
    observacoes: Optional[str] = None
    resultado: Optional[str] = None

class RotaInspecaoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    tipo: InspecaoTipo = InspecaoTipo.MECANICA
    tipo_ativo: str
    frequencia: Optional[str] = "diaria"
    itens: List[dict] = []
    tempo_estimado_minutos: int = 15
    ativa: bool = True

# Estoque
class EstoqueCreate(BaseModel):
    sku: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    categoria: str = "outro"
    quantidade: float = 0
    unidade: str = "UN"
    estoque_minimo: float = 0
    estoque_maximo: Optional[float] = None
    custo_unitario: float = 0
    almoxarifado: str = "Principal"
    prateleira: Optional[str] = None
    posicao: Optional[str] = None
    fornecedor: Optional[str] = None
    item_critico: bool = False
    alertar_minimo: bool = True
    observacoes: Optional[str] = None
    images: Optional[List[str]] = None

class EstoqueUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    quantidade: Optional[float] = None
    unidade: Optional[str] = None
    estoque_minimo: Optional[float] = None
    estoque_maximo: Optional[float] = None
    custo_unitario: Optional[float] = None
    almoxarifado: Optional[str] = None
    prateleira: Optional[str] = None
    posicao: Optional[str] = None
    fornecedor: Optional[str] = None
    item_critico: Optional[bool] = None
    alertar_minimo: Optional[bool] = None
    observacoes: Optional[str] = None
    images: Optional[List[str]] = None

class MovimentacaoCreateBody(BaseModel):
    tipo: str
    quantidade: float
    motivo: Optional[str] = None
    os_id: Optional[str] = None
    custo_unitario: Optional[float] = None

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

class ForgotPasswordRequest(BaseModel):
    email: str
    organization_id: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None  # Optional when force_password_change=true
    new_password: str

class ChatMessage(BaseModel):
    message: str
    ativo_id: Optional[str] = None
    session_id: Optional[str] = None

class SpareAssetCreate(BaseModel):
    tag: Optional[str] = None
    sku: Optional[str] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None
    tipo_equipamento: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    quantidade: int = 0
    estoque_minimo: int = 0
    custo_unitario: float = 0
    custo: Optional[float] = None
    localizacao: Optional[str] = None
    status: Optional[str] = "disponivel"
    ativo_vinculado_id: Optional[str] = None
    observacoes: Optional[str] = None
    origem: Optional[str] = None
    condicoes: Optional[dict] = None
    images: Optional[List[str]] = None

class SpareAssetUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    tipo_equipamento: Optional[str] = None
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    quantidade: Optional[int] = None
    estoque_minimo: Optional[int] = None
    custo_unitario: Optional[float] = None
    custo: Optional[float] = None
    localizacao: Optional[str] = None
    status: Optional[str] = None
    ativo_vinculado_id: Optional[str] = None
    observacoes: Optional[str] = None
    origem: Optional[str] = None
    condicoes: Optional[dict] = None
    images: Optional[List[str]] = None

class SpareMovementCreate(BaseModel):
    spare_id: str
    tipo: str
    quantidade: int
    motivo: Optional[str] = None
    os_id: Optional[str] = None
    custo_unitario: Optional[float] = None

class KnowledgeBaseCreate(BaseModel):
    tipo_equipamento: str
    problema: str
    solucao: str
    tags: List[str] = []
    categoria: str = "geral"


# ============== PLANOS DE INSPEÇÃO (Enterprise) ==============

class PlanoPerguntaCreate(BaseModel):
    texto: Optional[str] = None
    descricao: Optional[str] = None  # backward compat
    tipo_campo: str = "boolean"  # boolean, numero, texto, lista, escala_4, faixa, foto, comentario
    tipo: Optional[str] = None  # backward compat alias
    obrigatoria: bool = True
    obrigatorio: Optional[bool] = None  # backward compat
    foto_obrigatoria: bool = False
    foto_obrigatoria_nc: Optional[bool] = None  # backward compat
    comentario_obrigatorio: bool = False
    unidade: Optional[str] = None
    valor_min: Optional[float] = None
    valor_max: Optional[float] = None
    limite_normal: Optional[float] = None  # backward compat
    limite_alerta: Optional[float] = None  # backward compat
    limite_critico: Optional[float] = None  # backward compat
    opcoes: Optional[List[str]] = None
    periodicidade: Optional[str] = None
    ordem: int = 0

class PlanoInspecaoCreate(BaseModel):
    nome: str
    tipo: str = "inspecao"  # inspecao, preventiva, lubrificacao, limpeza, melhoria
    ativo_id: Optional[str] = None  # opcional — planos genéricos (por tipo_equipamento) não precisam de ativo
    frequencia: Optional[str] = None  # diaria, semanal, quinzenal, mensal, trimestral, semestral, anual
    responsavel_id: Optional[str] = None
    disciplina: Optional[str] = None  # mecanica, eletrica, instrumentacao (informativo)
    status: str = "rascunho"  # rascunho, aprovado, inativo
    versao: int = 1
    perguntas: List[PlanoPerguntaCreate] = []
    # backward compat fields
    tipo_equipamento: Optional[str] = None
    categoria: Optional[str] = None
    force_override: Optional[bool] = False  # bypass duplicate check

class PlanoInspecaoUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None
    ativo_id: Optional[str] = None
    frequencia: Optional[str] = None
    responsavel_id: Optional[str] = None
    disciplina: Optional[str] = None
    status: Optional[str] = None
    versao: Optional[int] = None
    perguntas: Optional[List[PlanoPerguntaCreate]] = None

class ParadaProgramadaCreate(BaseModel):
    area_id: str
    data_inicio: str
    data_fim: str
    duracao_horas: Optional[float] = None
    tipo: str = "preventiva"  # preventiva, corretiva, grande_parada, parada_geral
    responsavel_id: Optional[str] = None
    descricao: Optional[str] = None
    observacoes: Optional[str] = None
    os_vinculadas: List[str] = []

class ParadaProgramadaUpdate(BaseModel):
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    duracao_horas: Optional[float] = None
    tipo: Optional[str] = None
    responsavel_id: Optional[str] = None
    descricao: Optional[str] = None
    observacoes: Optional[str] = None
    os_vinculadas: Optional[List[str]] = None
    status: Optional[str] = None


# ============== TEMPLATES DE INSPEÇÃO (legacy) ==============

class TemplateItemCreate(BaseModel):
    descricao: str
    tipo: str = "boolean"  # boolean, numerico, texto, opcao, temperatura, vibracao, observacao
    obrigatorio: bool = True
    unidade: Optional[str] = None
    tolerancia_min: Optional[float] = None
    tolerancia_max: Optional[float] = None
    opcoes: Optional[List[str]] = None  # For 'opcao' type custom options

class InspectionTemplateCreate(BaseModel):
    nome: str
    tipo_equipamento: str  # e.g. "Alimentador Vibratório", "Britador", "Motor"
    descricao: Optional[str] = None
    itens: List[TemplateItemCreate] = []

class InspectionTemplateUpdate(BaseModel):
    nome: Optional[str] = None
    tipo_equipamento: Optional[str] = None
    descricao: Optional[str] = None
    itens: Optional[List[TemplateItemCreate]] = None
