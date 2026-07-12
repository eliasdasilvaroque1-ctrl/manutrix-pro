# MAINTRIX — Implementation Roadmap V6

**Data:** 2026-07-12  
**Princípio:** Cada release é independente, não quebra produção, possui rollback e testes.  

---

## Release 1 — Fundação de Confiabilidade
**Foco:** P0 + Testes  
**Esforço:** ~12h  
**Risco:** Baixo  
**Pré-requisito para todas as releases seguintes**

| Item | Ref | Descrição | Esforço |
|------|-----|-----------|---------|
| 1.1 | W1 | State machine para transições de OS no backend | 2-3h |
| 1.2 | D1 | Backup automatizado (mongodump + cron) | 1h |
| 1.3 | B3 | Suite mínima pytest (auth, CRUD ativos, OS, multi-tenant) | 6h |
| 1.4 | S1 | Account lockout (5 tentativas + desbloqueio 30min) | 1h |
| 1.5 | S2 | Password complexity (8 chars, 1 upper, 1 digit) | 30min |

**Rollback:** Reverter state machine = permitir transições livres (comportamento atual).  
**Teste:** `pytest` + teste manual de cada transição de OS + login lockout.  
**Resultado:** Base segura e testável para evoluções.

---

## Release 2 — Workflow Completo
**Foco:** P1 Workflows  
**Esforço:** ~8h  
**Risco:** Baixo  
**Depende de:** Release 1

| Item | Ref | Descrição | Esforço |
|------|-----|-----------|---------|
| 2.1 | W2 | Workflow de Solicitação (state machine completa) | 3h |
| 2.2 | W3 | Notificações automáticas em transições de estado | 3h |
| 2.3 | W4 | Workflow de Parada Programada | 1h |
| 2.4 | — | Testes do workflow (pytest + e2e) | 1h |

**Rollback:** Solicitações voltam ao fluxo manual.  
**Teste:** Criar solicitação → analisar → aprovar → verificar OS gerada.

---

## Release 3 — Dossiê do Ativo
**Foco:** P1 Asset-Centric  
**Esforço:** ~10h  
**Risco:** Baixo (aditivo — não altera telas existentes)  
**Depende de:** Release 1

| Item | Ref | Descrição | Esforço |
|------|-----|-----------|---------|
| 3.1 | A1 | Tela de Dossiê Completo do Ativo (agregando info de múltiplas collections) | 6h |
| 3.2 | A2 | Cálculo MTBF/MTTR por ativo | 2h |
| 3.3 | A3 | Custo consolidado por ativo | 2h |

**Rollback:** Remover rota `/ativos/:id/dossie`. Tela de detalhe atual permanece.  
**Teste:** Verificar dados agregados para ativo com histórico de OS/inspeções.

---

## Release 4 — Field Operations
**Foco:** P1 Funcionalidades de Campo  
**Esforço:** ~7h  
**Risco:** Baixo (aditivo)  
**Depende de:** Release 1

| Item | Ref | Descrição | Esforço |
|------|-----|-----------|---------|
| 4.1 | N1 | Geração PDF de OS (impressão) | 4h |
| 4.2 | N2 | Geração e impressão de QR Code para ativos | 3h |

**Rollback:** Remover botão "Imprimir" da tela de OS.  
**Teste:** Gerar PDF de OS completa (com materiais, HH). Gerar QR e escanear.

---

## Release 5 — Segurança Fase 2
**Foco:** P2 Segurança  
**Esforço:** ~4h  
**Risco:** Baixo  
**Depende de:** Release 1

| Item | Ref | Descrição | Esforço |
|------|-----|-----------|---------|
| 5.1 | S3 | JWT refresh token (access 15min + refresh 7d) | 2h |
| 5.2 | S4 | Rate limit persistente (MongoDB TTL) | 1h |
| 5.3 | S5 | CSP no HTML (meta tag ou Vercel headers) | 30min |

**Rollback:** Reverter JWT para token único 24h.  
**Teste:** Login → esperar 15min → verificar refresh automático.

---

## Release 6 — Performance & Frontend
**Foco:** P2 Performance  
**Esforço:** ~8h  
**Risco:** Baixo  
**Depende de:** Nenhuma (independente)

| Item | Ref | Descrição | Esforço |
|------|-----|-----------|---------|
| 6.1 | F2 | Lazy loading todas as páginas (React.lazy + Suspense) | 2h |
| 6.2 | D2 | Paginação cursor-based em endpoints de lista | 3h |
| 6.3 | A4 | Timeline visual do ativo | 3h |

**Rollback:** Reverter lazy loading = import estático.  
**Teste:** Medir bundle size antes/depois. Testar scroll infinito.

---

## Release 7 — Modularização Final
**Foco:** P2-P3 Arquitetura  
**Esforço:** ~16h  
**Risco:** Médio (muitos arquivos alterados)  
**Depende de:** Todas as releases anteriores

| Item | Ref | Descrição | Esforço |
|------|-----|-----------|---------|
| 7.1 | F1 | App.js → < 500 linhas (extrair Sidebar, Auth, Modals) | 6h |
| 7.2 | F3 | Sidebar como componente separado | 1h |
| 7.3 | F4 | Auth pages separadas | 1h |
| 7.4 | B1 | Backend: separar server.py em routers | 6h |
| 7.5 | B2 | Pydantic models para todos endpoints | 2h |

**Rollback:** Git revert do commit inteiro.  
**Teste:** `CI=true yarn build` + all routes + full regression.

---

## Release 8 — KPIs & Dashboard Avançado
**Foco:** P2 Funcionalidades  
**Esforço:** ~10h  
**Risco:** Baixo  
**Depende de:** Release 3

| Item | Ref | Descrição | Esforço |
|------|-----|-----------|---------|
| 8.1 | N3 | Dashboard KPIs avançados (MTBF, MTTR, disponibilidade) | 6h |
| 8.2 | N4 | Calendário de manutenção | 4h |

**Rollback:** Remover novos widgets do dashboard.

---

## Cronograma Visual

```
Semana 1:  Release 1 (Fundação)         ██████████████
Semana 2:  Release 2 (Workflows)        ████████████
           Release 5 (Segurança)         ██████
Semana 3:  Release 3 (Dossiê Ativo)     ████████████████
           Release 4 (Field Ops)         ██████████████
Semana 4:  Release 6 (Performance)       ████████████████
Semana 5:  Release 7 (Modularização)     ████████████████████████████████
Semana 6:  Release 8 (KPIs)             ████████████████████
```

**Tempo total estimado: 6 semanas (~75h de implementação)**

---

## Princípios de Cada Release

1. **Independência:** Cada release pode ser deployed isoladamente
2. **Rollback:** Plano de rollback definido antes da implementação
3. **Testes:** Mínimo: build + all routes + endpoints afetados
4. **Zero downtime:** Mudanças aditivas, nunca destrutivas
5. **Documentação:** Cada release atualiza CHANGELOG.md
