# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Status: HOMOLOGAÇÃO E2E CONCLUÍDA — 169/169 testes
## Fase: PILOT FREEZE + QA Completo
## Branch QA: fix/pre-pilot-privacy-branding (commit 833423f)
## Baseline Piloto: commit 2d67eb0 (main)

---

## Historico de RCs
- RC5.0-5.2.1: Todas CONCLUÍDAS
- RC5.9/5.9.1: Auditoria + P0 fix — CONCLUÍDAS
- RC5.1.1: PDF Polimento — CONCLUÍDA
- HOTFIX P1: ESLint/Vercel — CONCLUÍDA (deploy READY)
- QA R1 (iter110): 43/43 PASSED
- QA R2 (iter111): 78/78 PASSED
- QA R3 (iter112): 48/48 PASSED
- Fixes: P1 LegalDocPage, P2 Logo fallback, P1 Master password, P2 RBAC ordering, P2 Asset refs cleanup

---

## Bugs Corrigidos nesta Branch
1. P1: LegalDocPage catch silencioso → estados loading/error/retry (App.js)
2. P2: Logo 404 → SidebarLogo fallback com Cog icon (MainLayout.js)
3. P1: Master password hash corrompido → reset bcrypt (DB)
4. P2: RBAC antes de Pydantic em POST /ativos (assets.py)
5. P2: Logo/wallpaper refs 404 limpas do org_config (DB)

## Bugs Abertos (Nenhum P0/P1)
- P3: POST /ativos/{id}/documentos e /ordens-servico/{id}/anexos não existem (usa /upload genérico)
- P3: GET /planos-inspecao/{id} retorna 405 (não usado pelo frontend)

---

## POST-PILOTO BACKLOG
1. RC6.1: Construtor de Secoes da OS
2. Biblioteca Tecnica Inteligente
3. Procedimentos Inteligentes
4. Templates por Equipamento
5. QR Code MVP
6. Otimizacao /api/central
7. Paginacao /api/ativos
8. Extracao OSDetailPage
9. ERP/SAP
10. IA Assistente
