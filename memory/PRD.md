# MANUTRIX ENTERPRISE — Product Requirements Document

## Status: FASE DE CONSOLIDAÇÃO COMPLETA
## Versão: 4.2.0

---

## CONSOLIDAÇÃO ENTERPRISE ✅ (25/06/2026, iteration_45 — 21/21)

### org_config — Cérebro Central da Empresa ✅
- Collection `org_config` com documento único por organização
- **Identidade**: nome_sistema, subtitulo, logo_url, favicon_url, wallpaper_url, rodape, texto_institucional
- **Tema**: 8 cores CSS (primária, secundária, fundo, texto, destaque, sucesso, alerta, erro)
- **Terminologia**: 49 termos configuráveis (Área→Planta, OS→OM, Técnico→Mecânico, etc.)
- **Numeração**: Padrão por entidade com prefixo, tipo_abrev, ano, dígitos + preview ao vivo
- **Preferências**: horário trabalho, turnos, feriados, unidade_tempo, formato_data, fuso_horario, idioma, moeda, aprovação OS, fluxo assinatura, prefixo empresa

### Unidades ✅
- Collection `plantas_v2` renomeada para `unidades`
- Hierarquia: Empresa → Unidade → Área → Ativo
- Endpoints: GET/POST/PUT/DELETE /api/unidades
- Backward compat: /api/plantas continua funcionando

### Motor de Numeração ✅
- Collection `contadores` com operação atômica `findOneAndUpdate`
- Nunca reutiliza números
- Configurável por empresa: prefixo + tipo + ano + sequencial
- Preview em tempo real: GET /api/org/config/numeracao/preview

### White-Label ✅
- Upload de logo e favicon via Object Storage
- 8 cores personalizáveis com preview ao vivo
- Nome do sistema, subtítulo e rodapé configuráveis
- Preparado para temas prontos no futuro

### Tela de Configuração ✅
- 5 abas: Identidade, Tema, Terminologia, Numeração, Preferências
- Acessível por Admin e Master em /admin/config

---

## ARQUITETURA COMPLETA

### Collections Novas (Consolidação)
| Collection | Índice Único | Propósito |
|---|---|---|
| `org_config` | organization_id | Configuração central |
| `contadores` | org_id + chave | Numeração atômica |
| `unidades` | org (index) | Unidades da empresa |

### Collections Anteriores (Bloco A + Arquitetura)
| Collection | Propósito |
|---|---|
| `os_eventos` | Event log imutável |
| `hh_registros` | Apontamento HH |
| `os_executantes` | Equipe da OS |
| `metricas_diarias` | Métricas pré-agregadas/dia |
| `metricas_mensais` | Métricas pré-agregadas/mês |
| `admin_actions` | Log de ações admin |

### Total de Índices: 39+ em 16 collections

---

## PRÓXIMO: BLOCO B — Frontend de Gestão de Equipe
- Cronômetro visual na OS (usando /os/{id}/hh)
- Gestão de executantes na OS
- Dashboard da Equipe (usando /metricas/equipe)
- Indicadores de produtividade
- Ranking
- Dashboard Supervisor

## BLOCO C — Exportação + Qualidade (A FAZER)
