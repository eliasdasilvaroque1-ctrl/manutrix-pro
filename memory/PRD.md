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
- CRUD completo: Criar, Visualizar, Editar, Excluir (logico), Restaurar
- 11 tipos de documento, 6 status, pesquisa full-text, filtros combinados, paginacao
- Versionamento via `biblioteca_versoes` (edicao em publicado incrementa versao)
- Auditoria em `audit_log` (create, update, status_change, delete, restore)
- RBAC: Admin/PCM full, Tecnico read-only publicados
- Multi-tenant: org_id isolado em todas as queries
- Frontend: BibliotecaCorporativaPage com lista, filtros, form 7-step, viewer, versoes
- Formulario organizado em secoes: Identificacao, Classificacao, Aplicabilidade, Conteudo, Seguranca, Vigencia, Versionamento

### Endpoints Missao 1
- GET/POST `/api/documentos-corporativos` (list+create)
- GET/PUT/DELETE `/api/documentos-corporativos/{id}` (read+update+delete)
- PATCH `/api/documentos-corporativos/{id}/status` (change status)
- POST `/api/documentos-corporativos/{id}/restaurar` (undelete)
- GET `/api/documentos-corporativos/{id}/versoes` (history)
- POST `/api/documentos-corporativos/{id}/restaurar-versao/{v}` (restore version)
- GET `/api/documentos-corporativos/{id}/audit` (audit log)
- GET `/api/documentos-corporativos-stats` (KPIs)
- POST `/api/documentos-corporativos/{id}/duplicar` (clone doc)

---

## RC5.0 Missao 2 — Vinculo Automatico com OS + Upload Corporativo (CONCLUIDA 18/07/2026)

### Entregas
- Upload de arquivos corporativos (PDF, DOCX, XLSX, PNG, JPG) com validacao de extensao, MIME e tamanho (25MB max)
- Vinculo automatico de documentos com OS por Area, Ativo, Tipo OS, Disciplina, Categoria
- Scoring por relevancia (asset_id=20pt, tipo/asset_type=10pt, area=5pt, disciplina=5pt, universal=1pt)
- Confirmacao de leitura obrigatoria (requires_acknowledgement) com registro imutavel
- Snapshot imutavel de documentos vinculados na OS no momento da execucao
- Historico de arquivos substituidos em `documentos_file_history`
- Frontend: secao "Procedimentos Aplicaveis" na OSDetailPage com icones de seguranca, versao, botao "Li e estou ciente"
- RBAC: Upload restrito a Admin/PCM, Tecnico somente leitura
- Multi-tenant: Todas queries isoladas por org_id
- Auditoria completa: upload, vinculo_automatico, confirmacao_leitura, snapshot_documentos

### Endpoints Missao 2
- POST `/api/documentos-corporativos/{id}/upload` (upload file)
- GET `/api/documentos-corporativos/vinculo-automatico/{os_id}` (auto-link docs to OS)
- POST `/api/documentos-corporativos/confirmar-leitura/{os_id}` (read confirmation)
- GET `/api/documentos-corporativos/confirmacoes/{os_id}` (list confirmations)
- GET `/api/documentos-corporativos/pendentes-confirmacao/{os_id}` (check pending reads)
- POST `/api/documentos-corporativos/snapshot/{os_id}` (freeze docs in OS)

### Banco de dados impactado
- `documentos_corporativos`: campos file_url, file_name, file_type, file_size, file_hash adicionados
- `documentos_file_history`: nova collection para historico de uploads substituidos
- `confirmacoes_leitura`: nova collection para registro de leituras
- `ordens_servico`: campo `documentos_snapshot` e `documentos_snapshot_at` adicionados

### Arquitetura impactada
- `/app/backend/routes/documentos_corporativos.py` — endpoints de Upload, Vinculo, Confirmacao, Snapshot
- `/app/frontend/src/App.js` — OSDetailPage com secao "Procedimentos Aplicaveis"

### Validacao Missao 2
- Upload: PDF aceito, .exe rejeitado (400)
- RBAC: Tecnico 403 (create), 200 (read)
- Vinculo Automatico: 1 doc matched para OS corretiva/mecanica
- Confirmacao: 2 leituras registradas com idempotencia
- Snapshot: documentos congelados na OS
- Versionamento: v1 -> v2 apos publicacao e edicao
- Auditoria: 4+ registros (create, upload, status_change, update)
- Multiempresa: Isolamento por org_id verificado
- Frontend: Secao "Procedimentos Aplicaveis" renderizando com icones, badges, botoes

## RC5.0.1 — HOTFIX P0 (CONCLUIDA 18/07/2026)

### P0.1 — Build de Producao
- Corrigido: todos os imports `@/` convertidos para paths relativos em 50+ arquivos
- Corrigido: `eslintConfig` ausente no package.json (adicionado `DISABLE_ESLINT_PLUGIN=true` no .env)
- Corrigido: imports faltantes revelados pelo build (QRLabelModal, useRef, QRCodeSVG, axios, loadOS→fetchOS, AppLayout)
- Build prod: `CI=true react-scripts build` → Compiled successfully (389KB JS + 15KB CSS gzip)

### P0.2 — Auditoria Unificada
- Corrigido: `db.audit_log` → `db.audit_logs` em documentos_corporativos.py (2 ocorrencias)
- Novos registros de auditoria da Biblioteca Corporativa agora visiveis na tela de Auditoria geral

## RC5.0.2 — HARDENING P1 (CONCLUIDA 18/07/2026)

### P1.1 — Collection Estoque
- Corrigido: `db.estoque` → `db.itens_estoque` em work_orders.py L826 (dossie OS)

### P1.2 — IDOR em Assets
- Adicionado `verify_org_access()` em: delete_ativo, duplicate_ativo, add_ativo_material
- Isolamento multi-tenant completo em operacoes destrutivas e de escrita

### P1.3 — Sector Lookup
- Adicionado `organization_id` em sector lookups de create_ativo (L192) e duplicate_ativo (L263)
- Adicionado `organization_id` em tag uniqueness checks
- Previne referencia a areas de outra organizacao

### P1.4 — Require Sincrono
- Substituido `require('../lib/api')` por `import('../lib/api')` dinamico em DocConfigPage.js PreviewTab

---

## Backlog

### P1
- RC Construtor Visual de Documentos — Ondas 2 e 3 (DnD avancado)
- QR Code MVP (Fase 2 Piloto) — URLs publicas `/q/{ativo_id}`

### P2
- Integracoes ERP/SAP
- Dataset permanente de homologacao

### P3
- IA Assistente
