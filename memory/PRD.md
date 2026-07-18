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
- RC5.1: Performance e Estabilizacao — APROVADA E ENCERRADA (18/07/2026)

---

## RC5.1 — Detalhes (APROVADA E ENCERRADA)

### N+1 Eliminados (5)
1. work_orders.py os_estatisticas: 13+ count → 1 $facet + 2 count
2. dashboard.py dashboard_stats: 15 count → 3 $facet
3. dashboard.py os_por_disciplina: N count loop → 1 $group
4. dashboard.py executivo: N count loop setor → 1 $group
5. dashboard.py migration_report: N find_one loop → 1 $group

### Frontend
- App.js: 4124 → 3715 linhas (-10%)
- Extraidos: MainLayout.js (243 lin), AppProviders.js (107 lin)
- Lazy loading: 17 chunks, bundle 389KB → 189KB gzip (-51%)

### Metricas (media 3 exec)
- Dashboard stats: 2.848s → 0.703s (-75%)
- Bundle JS: 389KB → 189KB gzip (-51%)

---

## Backlog Formal

### P1
- Construtor Visual Ondas 2-3
- QR Code MVP (Fase 2 Piloto)

### P2
- N+1: Dossie OS, Dossie Ativo, Ativo detail
- Inline pages: OSDetailPage (~918 lin), LoginPage, AtivosPage
- Reducao adicional App.js (3715 lin)
- Testes de carga com dataset grande
- Integracoes ERP/SAP
- Dataset de homologacao

### P3
- IA Assistente
- Virtualizacao de listas
- Browserslist update
