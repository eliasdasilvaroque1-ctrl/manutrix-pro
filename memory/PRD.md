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
- RC5.1: Performance e Estabilizacao — APROVADA E ENCERRADA

---

## RC5.2 — HOTFIX P0 (EM HOMOLOGACAO 18/07/2026)

### FASE 1 — P0.2 JWT_SECRET Fail-Fast
- Removido fallback `secrets.token_hex(32)` de deps.py
- Backend falha com RuntimeError se JWT_SECRET ausente
- Testes: 8/8 (login, RBAC, token invalido, sessao, logs limpos)

### FASE 2 — P0.3 Isolamento Multiempresa Dossie
- Adicionado organization_id em 10 queries de ordens_servico e attachments
- Adicionado verify_org_access em list_ativo_materiais (endpoint desprotegido)
- Testes: 22/22 (6 positivos, 6 cross-tenant, 10 regressao)

### FASE 3 — P0.1 Indices MongoDB
- Corrigido expires_at_1: normal → TTL (expireAfterSeconds: 0)
- Corrigido os_user: unique sem partial → unique com partialFilterExpression
- Corrigido org_ident: sem unique → unique: true
- Alinhado data_architecture.py org_ident com unique: true
- Alinhado server.py expires_at com background: true
- Script: backend/scripts/fix_indexes.py (--dry-run, --apply, --rollback)
- Validado: TTL funcional, unique rejeita dups, partial permite soft-delete
- 2 restarts sem warnings

### Arquivos alterados
- backend/deps.py (JWT fail-fast)
- backend/routes/assets.py (org_id em queries + verify_org_access)
- backend/data_architecture.py (org_ident unique: true)
- backend/server.py (expires_at background: true)
- backend/scripts/fix_indexes.py (novo — migration script)
- memory/PRD.md

---

## Backlog Formal

### P1
- Construtor Visual Ondas 2-3
- QR Code MVP (Fase 2 Piloto)

### P2
- N+1: Dossie OS, Dossie Ativo, Ativo detail
- server.py monolitico (4425 linhas, 134 endpoints)
- Inline pages: OSDetailPage (~918 lin), LoginPage, AtivosPage
- /api/ativos sem paginacao
- Refs Supabase obsoletas
- Testes legados (96 arquivos)
- Integracoes ERP/SAP

### P3
- IA Assistente
- Virtualizacao de listas
- Testes de carga
