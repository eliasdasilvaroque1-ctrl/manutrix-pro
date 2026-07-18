# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Concluido anteriormente
- RC Documentos Fase 1 (Unicode PDF com DejaVu Sans)
- Sprint 1-3 Biblioteca Corporativa (CRUD, Versionamento, Checklists, Personalizacao, Campos Dinamicos, Snapshot Isolation)
- RC Construtor Visual Onda 1 (Drag-and-Drop com @dnd-kit)
- HOTFIX P0: MasterCleanupPage e ExportButtons (Batch Print fix)

---

## RC5.0 Missao 1 — Biblioteca Corporativa de Documentos (CONCLUIDA)

### Entregas
- Collection `documentos_corporativos` com 30+ campos
- CRUD completo com 11 tipos, 6 status, full-text search, paginacao
- Versionamento, auditoria, RBAC, multi-tenant
- Frontend: BibliotecaCorporativaPage com lista, filtros, form 7-step, viewer

---

## RC5.0 Missao 2 — Vinculo Automatico com OS + Upload Corporativo (CONCLUIDA)

### Entregas
- Upload corporativo (PDF, DOCX, XLSX, PNG, JPG) com validacao
- Vinculo automatico por scoring multi-criterio
- Confirmacao de leitura obrigatoria, snapshot imutavel
- Frontend: secao "Procedimentos Aplicaveis" na OSDetailPage

---

## RC5.0.1 — HOTFIX P0 (CONCLUIDA 18/07/2026)

### P0.1 — Build de Producao
- Todos imports `@/` convertidos para paths relativos em 50+ arquivos
- `DISABLE_ESLINT_PLUGIN=true` no .env
- Imports faltantes corrigidos (QRLabelModal, useRef, QRCodeSVG, axios, loadOS, AppLayout)

### P0.2 — Auditoria Unificada
- `db.audit_log` → `db.audit_logs` em documentos_corporativos.py

---

## RC5.0.2 — HARDENING P1 (CONCLUIDA 18/07/2026)

### P1.1 — Collection Estoque
- `db.estoque` → `db.itens_estoque` em work_orders.py dossie

### P1.2 — IDOR em Assets
- `verify_org_access()` adicionado em delete_ativo, duplicate_ativo, add_ativo_material

### P1.3 — Sector Lookup
- `organization_id` adicionado em sector lookups (create_ativo, duplicate_ativo)
- `organization_id` adicionado em tag uniqueness checks

### P1.4 — Require Sincrono
- `require('../lib/api')` → `import('../lib/api')` dinamico em DocConfigPage.js

---

## Backlog

### P1
- Construtor Visual Ondas 2-3
- QR Code MVP (Fase 2 Piloto)

### P2
- N+1 queries (~25 locais)
- App.js split (4124 linhas)
- Lazy loading de paginas
- Integracoes ERP/SAP
- Dataset permanente de homologacao

### P3
- IA Assistente
- Browserslist update
