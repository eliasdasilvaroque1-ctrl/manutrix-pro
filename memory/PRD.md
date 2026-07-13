# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão do Produto
CMMS/EAM SaaS multi-tenant para gestão de manutenção industrial. PWA com capacidade offline, RBAC estrito, dossiê de ativos e máquina de estados para ordens de serviço.

## Stack Tecnológico
- **Frontend:** React (PWA), TailwindCSS, Shadcn/UI, Lucide Icons, qrcode.react
- **Backend:** FastAPI (Python), Motor (MongoDB async), fpdf2, openpyxl, qrcode, reportlab
- **Database:** MongoDB
- **Build:** Craco (CRA override)
- **Testes:** Pytest (backend 41 tests), Playwright (frontend 19 E2E flows)

## v1.0 — Release Completa (Fev 2026)

### Core System ✅
- PWA Offline com queue de operações
- RBAC: Master, Admin, PCM, Supervisor, Técnico (Mec/Ele), Operador, Gerente
- Multi-tenant com auto-detect de organização
- Dossiê do Ativo (8 tabs, KPIs, QR Code)
- Dashboard Executivo (12 KPIs, trend 12m, charts)
- Máquina de Estados OS (validação + RBAC + auditoria)
- Auditoria automática em todas as transições

### Export & Print Package ✅
- PDF Individual: OS + Inspeção (layout padronizado com logo, cabeçalho, rodapé, QR, assinaturas)
- Impressão em Lote: OS + Inspeções (max 50 por lote, RBAC: master/admin/pcm)
- Export Excel: OS, Ativos, Inspeções, Preventivas
- Export PDF: OS, Ativos, Inspeções, Preventivas, Estoque, Auditoria

### QR Code ✅
- QR único por ativo (UUID permanente, independente de TAG/nome)
- QR na OS impressa (link direto para OS na PWA)
- QR no Dossiê do Ativo (renderizado via QRCodeSVG)
- Lookup: GET /api/ativos/qr/{qr_code}

## Releases Anteriores
- RC3.0: Architecture Freeze
- RC3.1: Business Critical Fixes (multiempresa, PDF OS, FieldOps)
- RC3.2: Operational Core (asset-centric, OS direta, KPIs)
- RC3.2.1: Full QA & Homologation
- RC4.0: Asset Dossier (8 tabs)
- RC4.1: Operação Enterprise (Dashboard, State Machine, Testes)
- v1.0: Export & Print Package + QR Code

## Arquitetura de Arquivos

```
/app/backend/
├── server.py (entry point, ~4400 lines)
├── models.py (Pydantic models)
├── deps.py (dependencies, RBAC, audit)
├── routes/
│   ├── dashboard.py
│   ├── work_orders.py
│   ├── assets.py
│   ├── exports.py (NOVO v1.0: batch PDF, inspeção PDF, preventivas export)
│   ├── events.py
│   ├── org.py
│   ├── biblioteca.py
│   └── central.py
└── tests/
    └── test_rc41.py (41 testes)

/app/frontend/src/
├── App.js (~4k lines — tech debt)
├── pages/
│   ├── DashboardPage.js
│   ├── AssetDossierPage.js (QR Code)
│   ├── InspecoesPages.js (batch checkboxes, print button)
│   ├── ParadasPage.js (preventivas export)
│   └── ...
├── components/
│   ├── shared/index.js
│   ├── ui/ (Shadcn)
│   └── widgets/
│       └── ExportButtons.js (ExportButtons, BatchPrintBar, BatchCheckbox)
└── lib/
    ├── api.js
    └── constants.js
```

## Endpoints Chave

### Auth & Core
- `POST /api/auth/login` — Login com auto-resolve org
- `GET /api/auth/me` — Dados do usuário

### Ordens de Serviço
- `POST /api/ordens-servico` — Criar OS
- `PATCH /api/ordens-servico/{id}/status` — Máquina de estados
- `GET /api/ordens-servico/{id}/transitions` — Transições válidas
- `POST /api/ordens-servico/{id}/concluir` — Conclusão com validações
- `GET /api/ordens-servico/{id}/pdf` — PDF individual com QR

### Export & Print (v1.0)
- `GET /api/inspecoes/{id}/pdf` — PDF individual inspeção
- `GET /api/ordens-servico/batch-pdf?ids=...` — Batch OS PDF
- `GET /api/inspecoes/batch-pdf?ids=...` — Batch inspeções PDF
- `GET /api/export/ordens-servico?format=excel|pdf`
- `GET /api/export/ativos?format=excel|pdf`
- `GET /api/export/inspecoes?format=excel|pdf`
- `GET /api/export/preventivas?format=excel|pdf`

### Dashboard & Dossiê
- `GET /api/dashboard/executivo` — Dashboard KPIs
- `GET /api/ativos/{id}/dossie` — Dossiê completo do ativo
- `GET /api/ativos/qr/{qr_code}` — Lookup ativo por QR

## Backlog (Próximas Releases)

### P1: Integrações ERP/SAP
### P2: IA Assistente

## Tech Debt
- App.js com ~4k linhas (target: < 2000)
- server.py com ~4400 linhas — extrair mais rotas para módulos
