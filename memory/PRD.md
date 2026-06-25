# MANUTRIX OMNI — Product Requirements Document

## Status: FASE 1 PILOTO ASTEC — ARQUITETURA DE DADOS COMPLETA
## Versão: 4.1.0

---

## BLOCO A — Infraestrutura + Operacional ✅ (iteration_43)
- Admin Master, Limpeza Ambiente, Kanban Visual, Filtros, Plantas, Auditoria Admin, 11 Tipos OS

## ARQUITETURA DE DADOS — Event-Sourced ✅ (iteration_44)

### Novas Collections
| Collection | Propósito | Índices |
|---|---|---|
| `os_eventos` | Log imutável de eventos por OS | 3 |
| `hh_registros` | Apontamento de mão de obra (INICIAR/PAUSAR/RETORNAR/FINALIZAR/TRANSFERIR) | 4 |
| `os_executantes` | Equipe da OS com funções (Executor/Apoio/Supervisor/Inspetor/Líder) | 3 |
| `metricas_diarias` | Indicadores pré-agregados por usuário/dia | 2 |
| `metricas_mensais` | Indicadores pré-agregados por usuário/mês | 2 |

### Índices Criados: 36 total em 13 collections
- `ordens_servico`: 8 (org+status, org+tipo+status, org+data_conclusao, ativo+status, responsavel+status, equipe, org+resp+conclusao, org+created)
- `inspecoes`: 3 | `anomalias`: 3 | `audit_logs`: 2 | `movimentacoes_estoque`: 3
- `hh_registros`: 4 | `os_eventos`: 3 | `os_executantes`: 3 (partial unique)
- `metricas_diarias`: 2 (unique org+user+data) | `metricas_mensais`: 2 (unique org+user+ano+mes)

### API Endpoints Novos
- `POST/GET /api/os/{id}/hh` — Cronômetro HH
- `GET /api/hh/resumo/{os_id}` — Resumo HH bruta/líquida/parado
- `POST/GET /api/os/{id}/executantes` — Equipe da OS
- `GET /api/os/{id}/eventos` — Timeline de eventos
- `GET /api/metricas/usuario/{id}?periodo=` — Métricas por técnico
- `GET /api/metricas/equipe?periodo=` — Ranking da equipe
- `POST /api/metricas/rebuild` — Reconstruir métricas (admin)

### Campos padrão em todas as collections novas
organization_id, created_at, updated_at, created_by, updated_by, deleted_at (soft delete)

### Escalabilidade
- Projetado para 500 empresas, milhões de OS, dezenas de milhões de HH
- Toda query inicia por organization_id
- Métricas pré-agregadas para dashboards rápidos
- Preparado para IA futura (event-sourcing permite reconstrução completa)

---

## PRÓXIMOS: BLOCO B — Frontend + Integração
- Dashboard da Equipe (frontend usando /metricas/equipe)
- Cronômetro visual na OS (frontend usando /os/{id}/hh)
- Gestão de executantes na OS (frontend usando /os/{id}/executantes)
- Timeline de eventos na OS (frontend usando /os/{id}/eventos)
- Indicadores de produtividade (frontend usando metricas)

## BLOCO C — Dashboards Executivos + Export (A FAZER)
- Ranking, Dashboard Supervisor, Qualidade, Exportação
