# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão: CMMS/EAM SaaS multi-tenant
## Stack: React PWA + FastAPI + MongoDB Atlas
## Piloto: ASTEC Engenharia

---

## RC — Documentos Profissionais Configuráveis — FASE 1 ✅

### Backend
- `backend/pdf_engine.py` — Motor PDF v2.0 (MaintrixPDF class, DejaVu Unicode fonts)
- `backend/routes/doc_config.py` — API CRUD: doc_config, procedimentos, segurança
- `backend/routes/exports.py` — Batch PDF OS/Inspeções com Unicode
- `backend/models.py` — OSCreate/OSUpdate com campos procedimento e segurança
- `backend/server.py` — OS PDF reescrito usando pdf_engine
- `backend/fonts/` — DejaVu Sans TTF (Regular, Bold, Oblique, BoldOblique)

### Frontend
- `frontend/src/pages/DocConfigPage.js` — Menu Documentos e Formulários (5 tabs)
- `frontend/src/App.js` — Rota /config/documentos + menu sidebar

### Collections MongoDB
- `doc_config` — Configuração de documentos por empresa
- `procedimentos_padrao` — Biblioteca de procedimentos por empresa
- `seguranca_padrao` — Biblioteca de segurança por empresa

### Endpoints
- GET/PUT `/api/doc-config` — Config documentos por org
- GET/POST/PUT/DELETE `/api/doc-config/procedimentos` — CRUD procedimentos
- GET/POST/PUT/DELETE `/api/doc-config/seguranca` — CRUD segurança
- GET `/api/ordens-servico/{id}/pdf?modo=digital|manual`
- GET `/api/inspecoes/{id}/pdf?modo=digital|manual`

### Validação (17 Jul 2026)
- Unicode PDF: 42/42 testes PASS (text extraction + content validation)
- Regressão: 53/53 testes PASS
- Total: 95 testes
- OS PDF Digital: 200 (73.6 KB)
- OS PDF Manual: 200 (77.2 KB)
- Fonte: DejaVu Sans v2.37 (Bitstream Vera License — livre para distribuição)

---

## Funcionalidades Concluídas
- Auth multi-tenant com RBAC (master/admin/pcm/tecnico)
- Dashboard executivo + indicadores
- CRUD Ativos com dossiê completo
- Ordens de Serviço com máquina de estados (8 estados, 12 transições)
- Planos de Inspeção + Checklist
- Gestão de Estoque
- Exportações Excel + PDF (OS, Ativos, Inspeções, Preventivas)
- PDF profissional multi-tenant com fotos reais, QR code, procedimentos, segurança
- Unicode/UTF-8 completo nos PDFs (µm, °C, Ω, Ø, ±, ≥, ≤, Δ, α, β, ², ³, →)
- Download autenticado de PDFs via Blob (sem popup 401)
- Performance: N+1 queries eliminados (35s → 1.6s)
- MongoDB Atlas migration completa

---

## Backlog Priorizado

### P1 — Próximas
- RC Documentos Fase 2: Construtor Visual Drag-and-Drop de PDFs
- QR Code MVP (Fase 2 Piloto): URLs públicas /q/{ativo_id}, viewer público

### P2
- Integrações ERP/SAP

### P3
- IA Assistente
- Impressão de etiquetas avançadas (Lote, A4, QR)
