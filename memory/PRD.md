# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## PILOT FREEZE — Ativo desde 19/07/2026

### Baseline do Piloto
- Commit Base: 2d67eb0
- Branch: main
- Versao: v5.2.0
- Deployment: READY (Production, Vercel)
- Data: 19/07/2026
- Ambiente: Production (Vercel + Railway)

### Regras do Congelamento
PERMITIDO: P0, P1, seguranca, perda de dados, bloqueio operacional
PROIBIDO: funcionalidades, refatoracoes, visuais, arquitetura, banco, APIs sem aprovacao

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
- RC5.1: Performance e Estabilizacao — CONCLUIDA
- RC5.1 Fase 3: JWT Fail-Fast + Isolamento Dossie + Indices MongoDB — CONCLUIDA
- RC5.1.1: Polimento do PDF de Ordem de Servico — CONCLUIDA
- RC5.2: Procedimento Operacional integrado a OS — CONCLUIDA
- RC5.2.1: Hardening Final do Procedimento Operacional — CONCLUIDA
- RC5.9: Pilot Readiness Review (Auditoria Final) — CONCLUIDA
- RC5.9.1: Correcao P0 procedimento_id em OSCreate/OSUpdate — CONCLUIDA
- HOTFIX P1: Deploy Vercel bloqueado por ESLint — CONCLUIDA

---

## POST-PILOTO BACKLOG

### P1 — Evolucoes Aprovadas
1. RC6.1: Construtor de Secoes da Ordem de Servico
2. Biblioteca Tecnica Inteligente
3. Procedimentos Inteligentes
4. Templates por Equipamento
5. QR Code MVP (Fase 2 do Piloto)
6. Otimizacao do Central (/api/central ~2.3s)
7. Correcao senha master

### P2 — Divida Tecnica
8. Paginacao /api/ativos server-side
9. RBAC ordering (Depends antes Pydantic)
10. N+1: Dossie OS, Dossie Ativo
11. server.py monolitico (4400+ linhas)
12. Extracao OSDetailPage do App.js
13. Integracoes ERP/SAP

### P3 — Futuro
14. IA Assistente
15. Testes de carga
16. Construtor Visual Ondas 2-3 (drag-and-drop avancado)
