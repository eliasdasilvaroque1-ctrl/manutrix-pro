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
- RC5.9.1: Correcao P0 procedimento_id em OSCreate/OSUpdate — CONCLUIDA

---

## Status: APROVADO PARA O PILOTO SEM RESSALVAS (18/07/2026)

---

## Backlog

### P1
- Corrigir senha master ou atualizar test_credentials
- Otimizar /api/central (cache/aggregation, atual ~2.3s)
- Construtor Visual Ondas 2-3
- QR Code MVP (Fase 2)

### P2
- Paginacao /api/ativos server-side
- RBAC ordering (Depends antes Pydantic)
- N+1: Dossie OS, Dossie Ativo
- server.py monolitico (4400+ linhas)
- Extracao OSDetailPage
- ERP/SAP

### P3
- IA Assistente
- Testes de carga
