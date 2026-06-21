# MANUTRIX OMNI — Product Requirements Document

## Status: PILOTO ASTEC — CONGELADO PARA PRODUÇÃO

---

## Fase Final Pré-Piloto ✅ APROVADA (21/06/2026)

### Bloco 1: Validação Multiempresa ✅ (iteration_38 — 29/29)
### Bloco 2: Auditoria Campo-a-Campo ✅ (iteration_39 — 10/10)
### Bloco 3: Paradas Programadas ✅ (iteration_40 — 13/13 + Frontend 100%)
### Bloco 5: Segurança e Produção ✅ (SECURITY_REPORT.md gerado)

---

## Relatórios de Produção ✅ (21/06/2026)
- `/app/RELATORIO_PRODUCAO.md` — Arquitetura, Deploy, Backup, Restore, Rollback, Atualização
- `/app/REVISAO_USABILIDADE.md` — Revisão de 8 módulos com 43 sugestões priorizadas

---

## 7 Itens Críticos de Usabilidade ✅ (21/06/2026, iteration_41 — 10/10)

| Cod | Módulo | Descrição | Status |
|-----|--------|-----------|--------|
| A1 | Ativos | Status dinâmico (Operacional/Em Manutenção/Parado) na listagem | ✅ |
| A2 | Ativos | Contador de OS abertas por ativo | ✅ |
| OS1 | OS | Busca no Kanban por nº, título ou TAG | ✅ |
| OS2 | OS | Filtro por prioridade (Emerg/Alta/Média/Baixa) | ✅ |
| I1 | Inspeções | Filtro por status com contadores | ✅ |
| I2 | Inspeções | Filtro por área | ✅ |
| E1 | Estoque | Histórico de movimentações expandível | ✅ |

**Alterações:** Apenas `/app/frontend/src/App.js`
**Backend:** ZERO alterações
**Banco de dados:** ZERO alterações
**RBAC/Auditoria:** ZERO alterações

---

## Módulos Completos

| Módulo | Status |
|--------|--------|
| Áreas (Sectors) | ✅ CRUD + Isolamento |
| Ativos | ✅ CRUD + QR + Histórico + KPIs + Duplicar |
| Ordens de Serviço | ✅ Kanban + Rastreabilidade + Materiais |
| Inspeções | ✅ Planos 2 Níveis + Execução + OS Auto |
| Anomalias | ✅ Workflow Completo + Comentários |
| Estoque | ✅ Movimentação + Bloqueio Negativo |
| Sobressalentes | ✅ Condições + Reformas + Export |
| Paradas Programadas | ✅ Indicadores + OS Vinculadas |
| Auditoria | ✅ Login + CRUD + Campo-a-Campo |
| Multiempresa | ✅ organization_id em todos os endpoints |
| PWA/Offline | ✅ Service Worker + Queue |
| Dashboard | ✅ KPIs + Drill-down + Gráficos |
| Exportação | ✅ Excel + PDF (ReportLab) |

---

## Regra de Ouro — PILOTO ASTEC
> Sistema CONGELADO. Nenhuma funcionalidade nova.
> Apenas correção de bugs e ajustes operacionais observados em campo.

## Backlog Congelado (Pós-Piloto)
- 25 itens IMPORTANTES da revisão de usabilidade
- 11 itens OPCIONAIS da revisão de usabilidade
- Exportação e Relatórios avançados
- Integrações ERP/SAP (suspenso)
- Dashboards novos, IA, OEE (suspenso)
