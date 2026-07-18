# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Historico de RCs
- RC Documentos Fase 1 (Unicode PDF) — CONCLUIDA
- Sprint 1-3 Biblioteca Corporativa — CONCLUIDA
- RC Construtor Visual Onda 1 (@dnd-kit) — CONCLUIDA
- HOTFIX P0: MasterCleanupPage/ExportButtons — CONCLUIDA
- RC5.0 Missao 1: Biblioteca Corporativa — CONCLUIDA
- RC5.0 Missao 2: Vinculo Automatico + Upload — CONCLUIDA
- RC5.0.1: HOTFIX P0 Build + Auditoria — CONCLUIDA
- RC5.0.2: HARDENING P1 IDOR + Estoque + Sector — CONCLUIDA

---

## RC5.1 — PERFORMANCE E ESTABILIZACAO (CONCLUIDA 18/07/2026)

### Objetivo
Otimizacao de performance, organizacao de codigo e reducao de divida tecnica.

### Diagnostico Inicial
- Dashboard stats: 2.848s (13+ count_documents sequenciais)
- Dashboard stats2: 15 count_documents sequenciais
- Dashboard OS por disciplina: N loops count
- Dashboard executivo: N loops por setor
- Migration report: N find_one por setor
- Bundle monolitico: 389KB gzip, 2 chunks
- App.js: 4124 linhas

### N+1 Corrigidos (5)
| # | Arquivo | Funcao | Antes | Depois |
|---|---------|--------|-------|--------|
| 1 | work_orders.py | os_estatisticas | 13+ count + 3 agg | 1 $facet + 2 count |
| 2 | dashboard.py | dashboard_stats | 15 count | 3 $facet |
| 3 | dashboard.py | os_por_disciplina | N count loop | 1 $group |
| 4 | dashboard.py | executivo | N count loop setor | 1 $group |
| 5 | dashboard.py | migration_report | N find_one loop | 1 $group |

### Frontend Split
- App.js: 4124 → 3715 linhas (-409, -10%)
- src/app/MainLayout.js: 243 linhas (Sidebar, BottomNav, NetworkStatus, AppLayout)
- src/app/AppProviders.js: 107 linhas (AuthProvider, BrandingLoader, ConsentGate, AppProviders)

### Lazy Loading
- 17 chunks lazy criados via React.lazy + Suspense
- Bundle principal: 389KB → 189KB gzip (-51%)
- Paginas: Dashboard, Estoque, Sobressalentes, Paradas, Inspecoes, Biblioteca, Equipe, WhiteLabel, DocConfig, LayoutBuilder, BibliotecaCorporativa, Consulta, Portal, MasterCleanup, OrgConfig, FieldOps, AssetDossier

### Metricas Validadas (3 execucoes, media)
| Endpoint | Antes | Depois | Ganho |
|----------|-------|--------|-------|
| Dashboard stats | 2.848s | 0.703s | -75% |
| OS list | 0.851s | 0.807s | -5% |
| Ativos list | 0.577s | 0.616s | ~0% |
| Bundle JS main | 389KB | 189KB | -51% |
| App.js linhas | 4124 | 3715 | -10% |
| Chunks | 2 | 17 | +15 |

### Validacoes
- Build frontend: Compiled successfully (CI=true)
- Backend: 6 arquivos compilam sem erros
- Smoke test: 25+ testes passaram
- RBAC: Admin OK, Tecnico 403
- Multiempresa: Cross-org bloqueado (404)
- Lazy loading: Dashboard + Estoque testados com refresh direto
- Logs: 0 erros novos, 0 ChunkLoadError, 0 circular imports

### Arquivos Alterados (7)
- backend/routes/dashboard.py (+108/-~60)
- backend/routes/work_orders.py (+54/-~54)
- frontend/src/App.js (-607 linhas net)
- frontend/src/app/AppProviders.js (+107, novo)
- frontend/src/app/MainLayout.js (+243, novo)
- memory/PRD.md
- .emergent/emergent.yml

---

## Backlog

### P1
- Construtor Visual Ondas 2-3
- QR Code MVP (Fase 2 Piloto)

### P2
- N+1 restantes: Dossie OS, Dossie Ativo, Ativo detail
- Inline pages split: LoginPage, OSDetailPage (~918 linhas), AtivosPage, etc.
- Integracoes ERP/SAP
- Dataset de homologacao
- Testes de carga

### P3
- IA Assistente
- Virtualizacao de listas
- Browserslist update
