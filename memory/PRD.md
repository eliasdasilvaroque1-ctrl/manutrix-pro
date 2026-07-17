# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão: CMMS/EAM SaaS multi-tenant
## Stack: React PWA + FastAPI + MongoDB Atlas + Supabase

## RC — Documentos Profissionais Configuráveis — FASE 1 ✅

### Backend (3 novos arquivos + alterações)
- `backend/pdf_engine.py` — Motor PDF v2.0 (MaintrixPDF class)
- `backend/routes/doc_config.py` — API CRUD: doc_config, procedimentos, segurança
- `backend/models.py` — OSCreate/OSUpdate com campos procedimento e segurança
- `backend/server.py` — OS PDF reescrito usando pdf_engine

### Frontend (1 novo arquivo + alterações)
- `frontend/src/pages/DocConfigPage.js` — Menu Documentos e Formulários (5 tabs)
- `frontend/src/App.js` — Rota /config/documentos + menu sidebar

### Collections MongoDB novas
- `doc_config` — Configuração de documentos por empresa
- `procedimentos_padrao` — Biblioteca de procedimentos por empresa
- `seguranca_padrao` — Biblioteca de segurança por empresa

### Endpoints novos
- GET/PUT `/api/doc-config` — Config documentos por org
- GET/POST/PUT/DELETE `/api/doc-config/procedimentos` — CRUD procedimentos
- GET/POST/PUT/DELETE `/api/doc-config/seguranca` — CRUD segurança
- GET `/api/ordens-servico/{id}/pdf?modo=manual` — Modo formulário manual

### Validação
- Build: PASS
- Backend: 41/41 testes PASS
- OS PDF Digital: 200 (44KB)
- OS PDF Manual: 200 (44.5KB)
- Doc Config APIs: 200
