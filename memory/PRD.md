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
- RC5.2 P0: JWT Fail-Fast + Isolamento Dossie + Indices MongoDB — APROVADA

---

## RC5.2 — PROCEDIMENTO OPERACIONAL NA OS (EM HOMOLOGACAO 18/07/2026)

### Objetivo
Permitir que OS possua procedimento operacional com etapas executaveis pelo tecnico.

### Entregas
- CRUD de Procedimentos (codigo, nome, descricao, revisao, versao, status, etapas)
- Etapas com ordem, titulo, descricao, obrigatoriedade
- Vinculacao procedimento <-> OS (opcional, campo procedimento_id)
- Execucao na OS: checkbox por etapa, observacao, executor, timestamp
- PDF atualizado com secao "Procedimento Executado"
- Menu "Procedimentos" no sidebar (Admin/PCM)
- Select de procedimentos aprovados no formulario da OS
- Auditoria completa (create, update, delete, vincular, etapa_concluida)
- RBAC: Admin/PCM criam, Supervisor visualiza, Tecnico executa etapas
- Multi-tenant: organization_id em todas as queries

### Endpoints
- GET/POST /api/procedimentos
- GET/PUT/DELETE /api/procedimentos/{id}
- GET /api/procedimentos-select (aprovados, light)
- PATCH /api/ordens-servico/{id}/procedimento (vincular/desvincular)
- GET /api/ordens-servico/{id}/procedimento-execucao
- POST /api/ordens-servico/{id}/procedimento-execucao/etapa

### Collections
- procedimentos: {id, org_id, codigo, nome, descricao, revisao, versao, status, etapas[], ...}
- procedimento_execucoes: {id, os_id, proc_id, org_id, etapas_executadas: {etapa_id: {concluida, obs, por, em}}}
- ordens_servico: +campo procedimento_id (opcional)

### Arquivos
- backend/routes/procedimentos.py (novo)
- backend/server.py (import + include_router + PDF)
- frontend/src/pages/ProcedimentosPage.js (novo)
- frontend/src/App.js (rota + lazy import + OS form + OS detail section)
- frontend/src/app/MainLayout.js (menu item)

### Testes: 13/13
- Criar, Editar, Listar, Select, Vincular, Execucao, Estado, PDF, Auditoria, RBAC, Multi-empresa, Compatibilidade

---

## Backlog

### P1
- Construtor Visual Ondas 2-3
- QR Code MVP

### P2
- N+1: Dossie OS, Dossie Ativo
- server.py monolitico (4400+ linhas)
- Inline pages split
- /api/ativos sem paginacao
- ERP/SAP

### P3
- IA Assistente
- Testes de carga
