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
- PWA Offline, RBAC 7 roles, Multi-tenant, Dossiê Ativo, Dashboard Executivo, Máquina de Estados OS, Auditoria

### Export & Print Package ✅
- PDF Individual (OS + Inspeção), Impressão em Lote, Export Excel/PDF (OS, Ativos, Inspeções, Preventivas)

### QR Code ✅
- QR por ativo (UUID permanente), QR na OS impressa, QR no Dossiê

### Deploy Audit ✅ (Jul 2026)
- Corrigido: Middleware 500 errors, CSP hardcoded, vercel.json, versão 1.0.0, rate limiter
- 41/41 testes backend, 28/28 endpoints validados, Build PASS
- Relatório: /app/memory/DEPLOY_AUDIT_REPORT.md

## Backlog
- P1: Integrações ERP/SAP
- P2: IA Assistente
- Tech Debt: Refatorar App.js (~4k linhas) e server.py (~4.4k linhas)
