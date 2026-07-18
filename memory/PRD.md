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
- RC5.1 Fase 3: JWT Fail-Fast + Isolamento Dossie + Indices MongoDB — APROVADA
- RC5.2: Procedimento Operacional integrado a OS — CONCLUIDA
- RC5.2.1: Hardening Final do Procedimento Operacional — CONCLUIDA
- RC5.9: Pilot Readiness Review (Auditoria Final) — CONCLUIDA

---

## RC5.9 — PILOT READINESS REVIEW (CONCLUIDA 18/07/2026)

### Achados
- P0: procedimento_id nao salvo via formulario OS (OSCreate/OSUpdate model)
- P1: Master login com senha desatualizada
- P1: /api/central ~2.3s latencia
- P2: Ativos sem paginacao server-side
- P2: Validacao Pydantic antes de RBAC check

### Validacao
- Build: OK
- Multi-tenant: OK
- RBAC: OK (exceto P2 ordering)
- PDF: OK
- Seguranca: OK
- 0 regressoes

---

## Backlog

### P0 (Blocker para piloto)
- procedimento_id em OSCreate/OSUpdate (15-30min)

### P1
- Corrigir senha master ou atualizar test_credentials
- Otimizar /api/central (cache/aggregation)
- Construtor Visual Ondas 2-3
- QR Code MVP (Fase 2)

### P2
- Paginacao /api/ativos
- RBAC ordering (Depends antes Pydantic)
- N+1: Dossie OS, Dossie Ativo
- server.py monolitico (4400+ linhas)
- Extracao OSDetailPage
- ERP/SAP

### P3
- IA Assistente
- Testes de carga
