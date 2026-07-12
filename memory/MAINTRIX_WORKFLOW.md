# MAINTRIX — Workflow Engine V6

**Data:** 2026-07-12  
**Status:** DOCUMENTAÇÃO — Nenhum código implementado  

---

## 1. Workflow Universal de Manutenção

O MAINTRIX segue o ciclo PDCA (Plan-Do-Check-Act) adaptado para manutenção industrial:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUXO UNIVERSAL DA OS                        │
│                                                                  │
│  IDENTIFICAÇÃO → PLANEJAMENTO → PROGRAMAÇÃO → EXECUÇÃO → FECHAMENTO │
└─────────────────────────────────────────────────────────────────┘
```

### Estados Oficiais

```
ABERTA ──► PLANEJADA ──► PROGRAMADA ──► DISPONÍVEL ──► EM_EXECUÇÃO ──► CONCLUÍDA ──► ENCERRADA
                                                           ▲    │
                                                           │    ▼
                                                           └─ PAUSADA

Qualquer estado ──► CANCELADA (admin/master)
```

---

## 2. Transições Permitidas

| Estado Atual | Estados Seguintes | Quem Pode | Ação |
|-------------|-------------------|-----------|------|
| `aberta` | `planejada`, `cancelada` | PCM, Admin | PCM define escopo |
| `planejada` | `programada`, `cancelada` | PCM, Admin | PCM agenda data e recursos |
| `programada` | `disponivel`, `cancelada` | PCM, Admin | Libera para execução |
| `disponivel` | `em_execucao`, `cancelada` | Técnicos, Supervisor | Técnico inicia trabalho |
| `em_execucao` | `pausada`, `concluida`, `cancelada` | Técnicos, Supervisor | Execução em andamento |
| `pausada` | `em_execucao`, `cancelada` | Técnicos, Supervisor | Retoma execução |
| `concluida` | `encerrada`, `cancelada` | Gerente, Admin | Aprovação final |
| `encerrada` | — | — | Estado terminal |
| `cancelada` | — | — | Estado terminal |

---

## 3. Entidades que Utilizam Workflows

### 3.1 Ordem de Serviço
**Workflow completo** (9 estados)

| Fase | Estados | Responsável |
|------|---------|------------|
| Identificação | `aberta` | Solicitante / Sistema |
| Planejamento | `planejada` | PCM |
| Programação | `programada`, `disponivel` | PCM |
| Execução | `em_execucao`, `pausada` | Técnicos |
| Fechamento | `concluida`, `encerrada` | Técnicos + Gerente |
| Exceção | `cancelada` | Admin |

### 3.2 Inspeção
**Workflow simplificado** (4 estados)

```
PENDENTE ──► EM_ANDAMENTO ──► CONCLUÍDA
                                  └──► COM_PENDÊNCIAS
```

| Estado | Responsável | Evento |
|--------|------------|--------|
| `pendente` | Sistema | Inspeção criada |
| `em_andamento` | Técnico | Técnico inicia |
| `concluida` | Sistema | Checklist completo, conforme |
| `com_pendencias` | Sistema | Checklist com não conformidade |

### 3.3 Plano de Inspeção
**Workflow de aprovação** (2 estados)

```
RASCUNHO ──► APROVADO
```

| Estado | Responsável | Evento |
|--------|------------|--------|
| `rascunho` | PCM | Plano criado/editado |
| `aprovado` | Admin/PCM | Plano revisado e aprovado |

### 3.4 Solicitação
**Workflow de triagem** (5 estados)

```
ABERTA ──► EM_ANÁLISE ──► APROVADA ──► CONVERTIDA (→ OS)
                      └──► REJEITADA
```

| Estado | Responsável | Evento |
|--------|------------|--------|
| `aberta` | Qualquer | Solicitação criada |
| `em_analise` | PCM | PCM recebe e avalia |
| `aprovada` | PCM | Justificada e aceita |
| `rejeitada` | PCM | Não justificada |
| `convertida` | PCM | Gera OS automaticamente |

---

## 4. Eventos de Workflow

Cada transição de estado gera:

| Evento | Destino | Dados |
|--------|---------|-------|
| `status_change` | audit_logs | entity, old_status, new_status, user, timestamp |
| `notificacao` | notificacoes | user_id destino, mensagem, link |
| `historico_ativo` | audit_logs | ativo_id, ação, detalhes |

---

## 5. Regras de Negócio por Transição

### OS: aberta → em_execucao (atalho para corretivas urgentes)
- OS criadas como "corretiva" + "crítica" podem ir direto de `aberta` → `em_execucao`
- Registrado no audit como "execução emergencial"

### OS: em_execucao → concluida
- Sistema calcula `tempo_execucao_minutos` automaticamente
- Materiais consumidos são baixados do estoque
- HH são consolidadas

### Inspeção: em_andamento → com_pendencias
- Itens não conformes geram solicitação automática
- Solicitação vinculada ao ativo e à inspeção de origem

### Parada Programada
- Não segue o workflow de OS
- Estados próprios: `planejada`, `em_andamento`, `concluida`
- Vincula N ordens de serviço à parada
