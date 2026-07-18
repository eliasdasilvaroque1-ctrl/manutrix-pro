# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## RC5.0 Missao 1 — Biblioteca Corporativa (CONCLUIDA)
## RC5.0 Missao 2 — Vinculo Automatico + Upload (CONCLUIDA)
## RC5.0.1 — HOTFIX P0: Build + Auditoria (CONCLUIDA)
## RC5.0.2 — HARDENING P1: IDOR + Estoque + Sector (CONCLUIDA)

---

## RC5.1 — PERFORMANCE E ESTABILIZACAO (CONCLUIDA 18/07/2026)

### N+1 Queries Corrigidos
1. `/ordens-servico/estatisticas`: 13+ count_documents → 1 $facet + 2 counts (77% mais rapido)
2. `/dashboard/stats`: 15 count_documents → 3 $facet pipelines (ativos, OS, inspecoes)
3. `/dashboard/os-por-disciplina`: N loops count → 1 aggregation $group
4. `/dashboard/executivo`: N loops count por setor → 1 aggregation $group por sector_id
5. `/migration/report`: N find_one por sector → 1 aggregation $group

### Frontend Split
- App.js: 4124 → 3715 linhas (-409)
- Extraidos: MainLayout.js (243 linhas), AppProviders.js (107 linhas)
- Componentes extraidos: Sidebar, BottomNav, NetworkStatus, AppLayout, AuthProvider, BrandingLoader, ConsentGate, AppProviders

### Lazy Loading
- 19 chunks lazy criados via React.lazy + Suspense
- Bundle principal: 389KB → 189KB gzip (-51%)
- Paginas lazy: DashboardPage, EstoquePage, SobressalentesPage, ParadasPage, InspecoesPages, BibliotecaPage, EquipePage, WhiteLabelDesignerPage, DocConfigPage, LayoutBuilderPage, BibliotecaCorporativaPage, ConsultaPages, PortalPages, MasterCleanupPage, OrgConfigPage, FieldOpsPage, AssetDossierPage

### Metricas
| Endpoint | Antes | Depois | Ganho |
|----------|-------|--------|-------|
| Dashboard stats | 2.848s | 0.664s | -77% |
| OS list | 0.851s | 0.790s | -7% |
| Ativos | 0.577s | 0.534s | -7% |
| Inspecoes | 0.384s | 0.365s | -5% |
| Bundle JS | 389KB | 189KB | -51% |
| App.js | 4124 lin | 3715 lin | -10% |
| Chunks | 2 | 19 | +17 |

### Arquivos alterados
- backend/routes/dashboard.py (N+1 fixes)
- backend/routes/work_orders.py (estatisticas $facet)
- frontend/src/App.js (split + lazy imports)
- frontend/src/app/MainLayout.js (novo)
- frontend/src/app/AppProviders.js (novo)

---

## Backlog

### P1
- Construtor Visual Ondas 2-3
- QR Code MVP (Fase 2 Piloto)

### P2
- N+1 restantes (dossie OS, dossie ativo, ativo detail)
- Inline pages split (LoginPage, OSDetailPage, AtivosPage, etc.)
- Integracoes ERP/SAP
- Dataset permanente de homologacao

### P3
- IA Assistente
- Browserslist update
- Virtualizacao de listas grandes
