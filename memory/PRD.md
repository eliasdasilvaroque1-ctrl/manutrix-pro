# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão do Produto
CMMS/EAM SaaS multi-tenant para gestão de manutenção industrial. PWA com capacidade offline, RBAC estrito, dossiê de ativos e máquina de estados para ordens de serviço.

## Stack Tecnológico
- **Frontend:** React (PWA), TailwindCSS, Shadcn/UI, Lucide Icons
- **Backend:** FastAPI (Python), Motor (MongoDB async)
- **Database:** MongoDB
- **Build:** Craco (CRA override)
- **Testes:** Pytest (backend), Playwright (frontend E2E)

## Releases Concluídas

### RC3.0 — Architecture Freeze ✅
- Documentação da arquitetura

### RC3.1 — Business Critical Fixes ✅
- Multiempresa auto-detect
- OS PDF print
- FieldOps stub

### RC3.2 — Operational Core ✅
- Fundação asset-centric
- OS direta
- KPIs

### RC3.2.1 — Full QA & Homologation ✅
- Bugs org_id
- Password hashes
- Master OS direta states

### RC4.0 — Asset Dossier ✅
- AssetDossierPage com 8 tabs agregados

### RC4.1 — Operação Enterprise ✅ (Feb 2026)
**Sprint 1: Dashboard Executivo** ✅
- GET /dashboard/executivo com KPIs, trend_12m, top_falhas
- 12 KPIs no frontend com charts

**Sprint 2: Máquina de Estados OS** ✅
- OS_TRANSITIONS com validação de estado + perfil
- PATCH /ordens-servico/{id}/status
- GET /ordens-servico/{id}/transitions
- POST /ordens-servico/{id}/concluir com validações (foto, descrição, tempo)
- Auditoria automática em todas as transições

**Sprint 3: Testes Automatizados** ✅
- 31 testes backend (pytest): Auth, StateMachine, Dashboard, Dossier, Performance, RBAC
- 12 fluxos frontend E2E (Playwright): Login, Dashboard, Ativos, OS, Inspeções, Preventivas
- Quality Gate: **GO** — Build PASS, 100% testes, zero erros

## Backlog (Próximas Releases)

### RC5.0 — Field Operations (P1)
- Geração de PDF de ordens de serviço
- Impressão em lote
- Integração QR Code

### RC6.0 — Integrações ERP/SAP (P2)

### RC7.0 — IA Assistente (P3)

## Arquitetura de Arquivos

```
/app/backend/
├── server.py (entry point)
├── models.py (Pydantic models)
├── deps.py (dependencies, RBAC, audit)
├── routes/
│   ├── dashboard.py
│   ├── work_orders.py
│   └── assets.py
└── tests/
    └── test_rc41.py (31 testes)

/app/frontend/src/
├── App.js (~4k lines — tech debt)
├── pages/
│   ├── DashboardPage.js
│   ├── AssetDossierPage.js
│   ├── InspecoesPages.js
│   └── ...
├── components/
│   ├── shared/index.js
│   ├── ui/ (Shadcn)
│   └── modals/
└── lib/
    ├── api.js
    └── constants.js
```

## Endpoints Chave
- `POST /api/auth/login` — Login com auto-resolve org
- `PATCH /api/ordens-servico/{id}/status` — Máquina de estados
- `GET /api/ordens-servico/{id}/transitions` — Transições válidas
- `POST /api/ordens-servico/{id}/concluir` — Conclusão com validações
- `GET /api/dashboard/executivo` — Dashboard KPIs
- `GET /api/ativos/{id}/dossie` — Dossiê completo do ativo

## Tech Debt Identificado
- App.js com ~4k linhas (target: < 2000) — extrair ConsentGate, SobrePage, LegalDocPage, modais
- Kanban pode precisar de virtual scroll para muitas colunas
