"""
MAINTRIX ENTERPRISE — Organization Configuration Module
Central brain for each company: identity, theme, terminology, numbering, preferences.

Collection: org_config (one document per organization)
Collection: contadores (atomic numbering sequences)
"""
from datetime import datetime, timezone
from typing import Optional, Dict
from pydantic import BaseModel, Field
import uuid


# ============== DEFAULT TERMINOLOGY ==============

DEFAULT_TERMINOLOGY = {
    "empresa": "Empresa",
    "unidade": "Unidade",
    "area": "Área",
    "ativo": "Ativo",
    "subconjunto": "Subconjunto",
    "componente": "Componente",
    "os": "Ordem de Serviço",
    "os_abrev": "OS",
    "inspecao": "Inspeção",
    "lubrificacao": "Lubrificação",
    "anomalia": "Anomalia",
    "plano_preventivo": "Plano Preventivo",
    "parada_programada": "Parada Programada",
    "estoque": "Estoque",
    "sobressalente": "Sobressalente",
    "material": "Material",
    "tecnico": "Técnico",
    "supervisor": "Supervisor",
    "planejador": "Planejador",
    "administrador": "Administrador",
    "gerente": "Gerente",
    "inspetor": "Inspetor",
    "executante": "Executante",
    "solicitacao": "Solicitação",
    "dashboard": "Dashboard",
    "historico": "Histórico",
    "auditoria": "Auditoria",
    "relatorio": "Relatório",
    "equipamento": "Equipamento",
    "tag": "TAG",
    "prioridade": "Prioridade",
    "disciplina": "Disciplina",
    "corretiva": "Corretiva",
    "preventiva": "Preventiva",
    "melhoria": "Melhoria",
    "emergencial": "Emergencial",
    "calibracao": "Calibração",
    "fabricacao": "Fabricação",
    "instalacao": "Instalação",
    "reforma": "Reforma",
    "preparacao_material": "Preparação de Material",
    "ronda": "Ronda",
    "checklist": "Checklist",
    "hh": "Homem-Hora",
    "backlog": "Backlog",
    "ranking": "Ranking",
    "produtividade": "Produtividade",
    "desempenho": "Desempenho",
    "turno": "Turno",
}


# ============== DEFAULT THEME ==============

DEFAULT_THEME = {
    "cor_primaria": "#10b981",
    "cor_secundaria": "#3b82f6",
    "cor_fundo": "#020617",
    "cor_texto": "#e2e8f0",
    "cor_destaque": "#f59e0b",
    "cor_sucesso": "#22c55e",
    "cor_alerta": "#f59e0b",
    "cor_erro": "#ef4444",
}


# ============== DEFAULT NUMBERING ==============

DEFAULT_NUMERACAO = {
    "ordens_servico": {
        "prefixo": "{empresa}-{tipo_abrev}-{ano}-",
        "digitos": 6,
        "exemplo": "AST-CORR-2026-000001",
    },
    "inspecoes": {
        "prefixo": "{empresa}-INSP-{ano}-",
        "digitos": 6,
        "exemplo": "AST-INSP-2026-000001",
    },
    "anomalias": {
        "prefixo": "{empresa}-ANOM-{ano}-",
        "digitos": 6,
        "exemplo": "AST-ANOM-2026-000001",
    },
    "lubrificacoes": {
        "prefixo": "{empresa}-LUB-{ano}-",
        "digitos": 6,
        "exemplo": "AST-LUB-2026-000001",
    },
    "paradas_programadas": {
        "prefixo": "{empresa}-PAR-{ano}-",
        "digitos": 6,
        "exemplo": "AST-PAR-2026-000001",
    },
}

TIPO_ABREVIACOES = {
    "corretiva": "CORR",
    "preventiva": "PREV",
    "lubrificacao": "LUB",
    "inspecao": "INSP",
    "fabricacao": "FAB",
    "preparacao_material": "PREP",
    "melhoria": "MELH",
    "calibracao": "CAL",
    "instalacao": "INST",
    "reforma": "REF",
    "emergencial": "EMER",
    "limpeza_organizacao": "LIMP",
    "fabricacao_melhorias": "FAB",
}


# ============== DEFAULT PREFERENCES ==============

DEFAULT_PREFERENCES = {
    "horario_trabalho": {"inicio": "07:00", "fim": "17:00"},
    "turnos": [
        {"nome": "Administrativo", "inicio": "07:00", "fim": "17:00"},
        {"nome": "1º Turno", "inicio": "06:00", "fim": "14:00"},
        {"nome": "2º Turno", "inicio": "14:00", "fim": "22:00"},
        {"nome": "3º Turno", "inicio": "22:00", "fim": "06:00"},
    ],
    "feriados": [],
    "unidade_tempo": "minutos",
    "formato_data": "DD/MM/YYYY",
    "fuso_horario": "America/Sao_Paulo",
    "idioma": "pt-BR",
    "moeda": "BRL",
    "aprovacao_os": {"requer_aprovacao": False, "niveis": []},
    "fluxo_assinatura": {"habilitado": False, "etapas": []},
    "prefixo_empresa": "",
}


# ============== DEFAULT CONFIG BUILDER ==============

def build_default_org_config(org_id: str, org_nome: str = "") -> dict:
    """Build a complete default org_config document."""
    prefixo = "".join(c for c in org_nome[:3].upper() if c.isalpha()) or "MNT"
    prefs = {**DEFAULT_PREFERENCES, "prefixo_empresa": prefixo}
    return {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "identidade": {
            "nome_sistema": f"Portal de Manutenção {org_nome}".strip(),
            "subtitulo": "Powered by MAINTRIX",
            "logo_url": None,
            "favicon_url": None,
            "wallpaper_url": None,
            "rodape": f"© {datetime.now().year} {org_nome} — Powered by MAINTRIX",
            "texto_institucional": "",
        },
        "tema": {**DEFAULT_THEME},
        "terminologia": {**DEFAULT_TERMINOLOGY},
        "numeracao": {**DEFAULT_NUMERACAO},
        "preferencias": prefs,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ============== NUMBERING ENGINE ==============

async def gerar_numero(db, org_id: str, entidade: str, tipo: str = "", config: dict = None):
    """
    Generate next sequential number using atomic increment.
    Uses org_config.numeracao pattern if available, otherwise falls back to simple format.
    """
    ano = datetime.now().year
    
    # Get config if not provided
    if not config:
        cfg_doc = await db.org_config.find_one({"organization_id": org_id}, {"_id": 0, "numeracao": 1, "preferencias": 1})
        config = cfg_doc or {}
    
    numeracao = config.get("numeracao", DEFAULT_NUMERACAO)
    prefs = config.get("preferencias", DEFAULT_PREFERENCES)
    prefixo_empresa = prefs.get("prefixo_empresa", "")
    
    # Determine counter key
    if entidade == "ordens_servico" and tipo:
        counter_key = f"{entidade}_{tipo}_{ano}"
    else:
        counter_key = f"{entidade}_{ano}"
    
    # Atomic increment
    result = await db.contadores.find_one_and_update(
        {"organization_id": org_id, "chave": counter_key},
        {
            "$inc": {"sequencial": 1},
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "organization_id": org_id,
                "chave": counter_key,
                "entidade": entidade,
                "tipo": tipo,
                "ano": ano,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
        upsert=True,
        return_document=True,
    )
    
    seq = result.get("sequencial", 1)
    
    # Build number from pattern
    pattern_config = numeracao.get(entidade, {})
    digitos = pattern_config.get("digitos", 5)
    padrao = pattern_config.get("prefixo", "")
    
    if padrao and prefixo_empresa:
        tipo_abrev = TIPO_ABREVIACOES.get(tipo, tipo[:4].upper()) if tipo else ""
        try:
            numero = padrao.format(
                empresa=prefixo_empresa,
                tipo_abrev=tipo_abrev,
                ano=ano,
                unidade="",
                area="",
            ) + str(seq).zfill(digitos)
        except (KeyError, IndexError):
            # Malformed pattern fallback
            numero = f"{prefixo_empresa}-{tipo_abrev}-{ano}-{str(seq).zfill(digitos)}"
    else:
        # Fallback to simple format
        numero = f"{ano}-{str(seq).zfill(5)}"
    
    return numero


# ============== INDEXES FOR NEW COLLECTIONS ==============

CONFIG_INDEXES = {
    "org_config": [
        {"keys": [("organization_id", 1)], "name": "org", "unique": True},
    ],
    "contadores": [
        {"keys": [("organization_id", 1), ("chave", 1)], "name": "org_chave", "unique": True},
    ],
    "unidades": [
        {"keys": [("organization_id", 1)], "name": "org"},
    ],
}
