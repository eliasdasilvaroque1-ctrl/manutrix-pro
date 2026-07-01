"""Seed script for ASTEC Cedro plant homologation - Sprint de Homologação"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

# Run via: python3 seed_homologacao.py
# Or call via endpoint POST /api/seed/homologacao

AREAS_RENAME = {
    "PLANTA-01": {"nome": "Britagem Primária", "codigo": "BRIT-PRI"},
    "PLANTA-02": {"nome": "Britagem Secundária", "codigo": "BRIT-SEC"},
    "PLANTA-03": {"nome": "Pátio de Estocagem", "codigo": "PATIO"},
}

NEW_AREAS = [
    {"codigo": "EXPD", "nome": "Expedição", "cor": "#f59e0b"},
]

# Equipment to add per area (only in areas that need them)
NEW_EQUIPMENT = {
    "Britagem Primária": [
        {"tag": "MT-01", "nome": "Motor Britador Primário", "tipo_equipamento": "MOTOR ELÉTRICO", "fabricante": "WEG", "modelo": "W22 355M/L", "numero_serie": "WEG-2024-001", "criticidade": "A", "potencia": "250 CV"},
        {"tag": "RD-01", "nome": "Redutor Britador Primário", "tipo_equipamento": "REDUTOR", "fabricante": "SEW", "modelo": "MC3PLHT07", "numero_serie": "SEW-2024-001", "criticidade": "A"},
        {"tag": "BB-01", "nome": "Bomba Hidráulica Britador", "tipo_equipamento": "BOMBA HIDRÁULICA", "fabricante": "PARKER", "modelo": "PV180R1K", "numero_serie": "PKR-2024-001", "criticidade": "B"},
    ],
    "Britagem Secundária": [
        {"tag": "MT-02", "nome": "Motor Britador Cônico", "tipo_equipamento": "MOTOR ELÉTRICO", "fabricante": "WEG", "modelo": "W22 315M/L", "numero_serie": "WEG-2024-002", "criticidade": "A", "potencia": "200 CV"},
        {"tag": "RD-02", "nome": "Redutor Britador Cônico", "tipo_equipamento": "REDUTOR", "fabricante": "SEW", "modelo": "MC3PLHT05", "numero_serie": "SEW-2024-002", "criticidade": "A"},
        {"tag": "CP-01", "nome": "Compressor de Ar", "tipo_equipamento": "COMPRESSOR", "fabricante": "ATLAS COPCO", "modelo": "GA 90+", "numero_serie": "ATC-2024-001", "criticidade": "B"},
        {"tag": "BB-02", "nome": "Bomba Água Industrial", "tipo_equipamento": "BOMBA CENTRÍFUGA", "fabricante": "KSB", "modelo": "Meganorm 80-250", "numero_serie": "KSB-2024-001", "criticidade": "B"},
    ],
    "Pátio de Estocagem": [
        {"tag": "MT-10", "nome": "Motor Correia TC-10", "tipo_equipamento": "MOTOR ELÉTRICO", "fabricante": "WEG", "modelo": "W22 250M/L", "numero_serie": "WEG-2024-010", "criticidade": "B", "potencia": "100 CV"},
        {"tag": "BB-03", "nome": "Bomba Aspersão Pátio", "tipo_equipamento": "BOMBA CENTRÍFUGA", "fabricante": "SCHNEIDER", "modelo": "ME-2350", "numero_serie": "SCH-2024-001", "criticidade": "C"},
    ],
    "Expedição": [
        {"tag": "BL-01", "nome": "Balança Rodoviária", "tipo_equipamento": "BALANÇA", "fabricante": "TOLEDO", "modelo": "2191C", "numero_serie": "TLD-2024-001", "criticidade": "A"},
        {"tag": "CP-02", "nome": "Compressor Expedição", "tipo_equipamento": "COMPRESSOR", "fabricante": "SCHULZ", "modelo": "SRP 4030E", "numero_serie": "SCH-2024-002", "criticidade": "C"},
        {"tag": "TC-EX", "nome": "Correia Expedição", "tipo_equipamento": "CORREIA TRANSPORTADORA", "fabricante": "ASTEC", "modelo": "TC-600x20m", "numero_serie": "AST-2024-001", "criticidade": "B"},
    ],
}

# Inspection plans per equipment type
PLANOS = {
    "BRITADOR DE MANDIBULA": {
        "mecanica": {
            "nome": "Inspeção Mecânica Britador Mandíbula",
            "perguntas": [
                {"descricao": "Verificar folga da mandíbula fixa", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar mandíbula móvel (desgaste)", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar temperatura mancal excêntrico (°C)", "tipo": "numerico", "obrigatorio": True, "unidade": "°C", "valor_max": 85},
                {"descricao": "Verificar temperatura mancal fixo (°C)", "tipo": "numerico", "obrigatorio": True, "unidade": "°C", "valor_max": 85},
                {"descricao": "Nível de vibração (mm/s)", "tipo": "numerico", "obrigatorio": True, "unidade": "mm/s", "valor_max": 7.1},
                {"descricao": "Verificar cunhas de aperto", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar correias de transmissão", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar parafusos base/estrutura", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar proteções e guardas", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Observações gerais", "tipo": "texto", "obrigatorio": False},
            ]
        },
        "eletrica": {
            "nome": "Inspeção Elétrica Britador Mandíbula",
            "perguntas": [
                {"descricao": "Corrente motor (A)", "tipo": "numerico", "obrigatorio": True, "unidade": "A"},
                {"descricao": "Tensão alimentação (V)", "tipo": "numerico", "obrigatorio": True, "unidade": "V"},
                {"descricao": "Temperatura motor (°C)", "tipo": "numerico", "obrigatorio": True, "unidade": "°C", "valor_max": 80},
                {"descricao": "Verificar cabos e conexões", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar aterramento", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar painel de comando", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar sensores de proteção", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        },
        "lubrificacao": {
            "nome": "Lubrificação Britador Mandíbula",
            "perguntas": [
                {"descricao": "Nível reservatório óleo", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Qualidade do óleo (cor/contaminação)", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Pressão bomba lubrificação (bar)", "tipo": "numerico", "obrigatorio": True, "unidade": "bar"},
                {"descricao": "Graxar mancais excêntricos", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Graxar rolamentos placa toggle", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar vazamentos", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Quantidade graxa aplicada (g)", "tipo": "numerico", "obrigatorio": False, "unidade": "g"},
            ]
        },
    },
    "CORREIA TRANSPORTADORA": {
        "mecanica": {
            "nome": "Inspeção Mecânica Correia",
            "perguntas": [
                {"descricao": "Verificar alinhamento da correia", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar emendas", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar rolos de carga", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar rolos de retorno", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar tambor de acionamento", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar tambor de retorno", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar tensionamento", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar raspadores", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar chutes de alimentação", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        },
        "producao": {
            "nome": "Inspeção Operacional Correia",
            "perguntas": [
                {"descricao": "Correia rodando sem desalinhamento", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Sem acúmulo de material nos rolos", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Sem ruído anormal", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Sem vazamento de material", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Emergência funcionando", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Observações operacionais", "tipo": "texto", "obrigatorio": False},
            ]
        },
    },
    "PENEIRA VIBRATORIA": {
        "mecanica": {
            "nome": "Inspeção Mecânica Peneira",
            "perguntas": [
                {"descricao": "Verificar telas (desgaste/furos)", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar molas de apoio", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar eixo excêntrico", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar contrapesos", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar chute de alimentação", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Amplitude vibração (mm)", "tipo": "numerico", "obrigatorio": True, "unidade": "mm"},
                {"descricao": "Temperatura mancais (°C)", "tipo": "numerico", "obrigatorio": True, "unidade": "°C", "valor_max": 80},
                {"descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        },
    },
    "MOTOR ELÉTRICO": {
        "eletrica": {
            "nome": "Inspeção Elétrica Motor",
            "perguntas": [
                {"descricao": "Corrente fase R (A)", "tipo": "numerico", "obrigatorio": True, "unidade": "A"},
                {"descricao": "Corrente fase S (A)", "tipo": "numerico", "obrigatorio": True, "unidade": "A"},
                {"descricao": "Corrente fase T (A)", "tipo": "numerico", "obrigatorio": True, "unidade": "A"},
                {"descricao": "Temperatura carcaça (°C)", "tipo": "numerico", "obrigatorio": True, "unidade": "°C", "valor_max": 80},
                {"descricao": "Vibração (mm/s)", "tipo": "numerico", "obrigatorio": True, "unidade": "mm/s", "valor_max": 4.5},
                {"descricao": "Verificar ventilador", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar base/fixação", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Ruído anormal", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        },
        "lubrificacao": {
            "nome": "Lubrificação Motor",
            "perguntas": [
                {"descricao": "Graxar rolamento LA", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Graxar rolamento LOA", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Tipo graxa utilizada", "tipo": "texto", "obrigatorio": True},
                {"descricao": "Quantidade (g)", "tipo": "numerico", "obrigatorio": True, "unidade": "g"},
            ]
        },
    },
    "COMPRESSOR": {
        "mecanica": {
            "nome": "Inspeção Mecânica Compressor",
            "perguntas": [
                {"descricao": "Pressão de trabalho (bar)", "tipo": "numerico", "obrigatorio": True, "unidade": "bar"},
                {"descricao": "Temperatura de descarga (°C)", "tipo": "numerico", "obrigatorio": True, "unidade": "°C"},
                {"descricao": "Nível de óleo", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar filtro de ar", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar dreno automático", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Verificar correias", "tipo": "boolean", "obrigatorio": True},
                {"descricao": "Horímetro (horas)", "tipo": "numerico", "obrigatorio": True, "unidade": "h"},
                {"descricao": "Observações", "tipo": "texto", "obrigatorio": False},
            ]
        },
    },
}

# OS de teste com diferentes estados/datas
OS_TEMPLATES = [
    {"titulo": "Troca de mandíbulas britador primário", "tipo": "corretiva", "disciplina": "mecanica", "prioridade": "alta", "area": "Britagem Primária", "tag_prefix": "BR", "status": "aberta", "data_offset": 0, "tempo_estimado": 480},
    {"titulo": "Preventiva 500h Redutor RD-01", "tipo": "preventiva", "disciplina": "mecanica", "prioridade": "media", "area": "Britagem Primária", "tag_prefix": "RD", "status": "planejada", "data_offset": 2, "tempo_estimado": 120},
    {"titulo": "Troca rolamentos motor MT-02", "tipo": "corretiva", "disciplina": "mecanica", "prioridade": "alta", "area": "Britagem Secundária", "tag_prefix": "MT", "status": "em_execucao", "data_offset": -1, "tempo_estimado": 240},
    {"titulo": "Revisão painel elétrico britagem", "tipo": "preventiva", "disciplina": "eletrica", "prioridade": "media", "area": "Britagem Secundária", "tag_prefix": "BR", "status": "planejada", "data_offset": 5, "tempo_estimado": 180},
    {"titulo": "Troca telas peneira PV-01", "tipo": "corretiva", "disciplina": "mecanica", "prioridade": "emergencia", "area": "Britagem Primária", "tag_prefix": "PV", "status": "aberta", "data_offset": 0, "tempo_estimado": 360},
    {"titulo": "Alinhamento correia TC-01", "tipo": "corretiva", "disciplina": "mecanica", "prioridade": "media", "area": "Britagem Primária", "tag_prefix": "TC", "status": "aberta", "data_offset": 1, "tempo_estimado": 60},
    {"titulo": "Manutenção compressor GA 90+", "tipo": "preventiva", "disciplina": "mecanica", "prioridade": "baixa", "area": "Britagem Secundária", "tag_prefix": "CP", "status": "planejada", "data_offset": 7, "tempo_estimado": 120},
    {"titulo": "Calibração balança rodoviária", "tipo": "preventiva", "disciplina": "instrumentacao", "prioridade": "alta", "area": "Expedição", "tag_prefix": "BL", "status": "aberta", "data_offset": 3, "tempo_estimado": 240},
    {"titulo": "Solicitação: ruído anormal bomba BB-01", "tipo": "corretiva", "disciplina": "mecanica", "prioridade": "media", "area": "Britagem Primária", "tag_prefix": "BB", "status": "aberta", "data_offset": 0, "tempo_estimado": 90},
    {"titulo": "Limpeza raspadores correia TC-05", "tipo": "corretiva", "disciplina": "producao", "prioridade": "baixa", "area": "Pátio de Estocagem", "tag_prefix": "TC", "status": "aberta", "data_offset": 0, "tempo_estimado": 30},
]

if __name__ == "__main__":
    print("Use via endpoint POST /api/seed/homologacao")
