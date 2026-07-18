# MAINTRIX ENTERPRISE — PRD

## Visão: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## ✅ RC5.0 Missão 1 — Biblioteca Corporativa de Documentos (18 Jul 2026)

### Entregas
- Collection `documentos_corporativos` com 30+ campos
- CRUD completo: Criar, Visualizar, Editar, Excluir (lógico), Restaurar
- 11 tipos de documento, 6 status, pesquisa full-text, filtros combinados, paginação
- Versionamento via `biblioteca_versoes` (edição em publicado incrementa versão)
- Auditoria em `audit_log` (create, update, status_change, delete, restore)
- RBAC: Admin/PCM full, Técnico read-only publicados
- Multi-tenant: org_id isolado em todas as queries
- Frontend: BibliotecaCorporativaPage com lista, filtros, form 7-step, viewer, versões
- Formulário organizado em seções: Identificação, Classificação, Aplicabilidade, Conteúdo, Segurança, Vigência, Versionamento

### Endpoints
- GET/POST `/api/documentos-corporativos` (list+create)
- GET/PUT/DELETE `/api/documentos-corporativos/{id}` (read+update+delete)
- PATCH `/api/documentos-corporativos/{id}/status` (change status)
- POST `/api/documentos-corporativos/{id}/restaurar` (undelete)
- GET `/api/documentos-corporativos/{id}/versoes` (history)
- POST `/api/documentos-corporativos/{id}/restaurar-versao/{v}` (restore version)
- GET `/api/documentos-corporativos/{id}/audit` (audit log)

### Validação
- CRUD: ✅ Create, Read, Update, Delete, Restore
- Search/Filters: ✅ Texto, tipo, disciplina, status, segurança
- Versioning: ✅ 3 versões registradas em fluxo create→update→publish
- Audit: ✅ 3 entries (create, update, status_change)
- RBAC: ✅ Técnico→403 (create), 200 (read)
- Duplicate code: ✅ HTTP 409
- Backward compat: ✅ Todos endpoints existentes retornando 200
- Regressão: Limitada por rate-limiter (endpoints verificados individualmente)

---

## Concluído anteriormente
- RC Documentos Fase 1 (Unicode PDF)
- Sprint 1-3 Biblioteca Corporativa (Versionamento, Checklists, Personalização)
- RC Construtor Visual Onda 1

## Backlog
### P1
- RC5.0 Missão 2: Vínculo automático com OS
- Upload de arquivos para documentos
- Snapshot de documentos na OS

### P1
- QR Code MVP
- Construtor Visual Ondas 2-3

### P2
- ERP/SAP
