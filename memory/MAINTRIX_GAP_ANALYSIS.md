# MAINTRIX — Gap Analysis V6

**Data:** 2026-07-12  
**Objetivo:** Comparar Arquitetura Atual × Arquitetura V6 Alvo  

---

## Legenda de Prioridade

| Tag | Significado | Critério |
|-----|------------|---------|
| **P0** | Crítico | Impede operação normal ou gera risco de dados |
| **P1** | Alto | Funcionalidade essencial ausente ou incompleta |
| **P2** | Médio | Melhoria significativa de usabilidade ou eficiência |
| **P3** | Baixo | Refinamento, otimização ou funcionalidade acessória |

---

## 1. WORKFLOW ENGINE

| # | Gap | Atual | V6 Alvo | P | Impacto | Risco | Esforço |
|---|-----|-------|---------|---|---------|-------|---------|
| W1 | Transições de estado não validadas no backend | Frontend faz transições livres; backend não verifica `old_status → new_status` | State machine com transições explícitas e validação | **P0** | Alto — estados inconsistentes em produção | Alto | Médio (2-3h) |
| W2 | Workflow de Solicitação incompleto | Solicitação existe mas fluxo `aberta → em_analise → aprovada → convertida` não está implementado como state machine | Fluxo completo com notificações | **P1** | Médio — PCM não recebe notificação de novas solicitações | Baixo | Médio (3-4h) |
| W3 | Ausência de notificações em transições | Mudanças de status não geram notificações push para responsáveis | Notificação automática em cada transição | **P1** | Médio — técnicos não sabem quando OS é atribuída | Baixo | Médio (2-3h) |
| W4 | Parada Programada sem workflow | Parada não tem estado formal `planejada → em_andamento → concluida` | State machine própria | **P2** | Baixo | Baixo | Baixo (1h) |

## 2. ASSET-CENTRIC MODEL

| # | Gap | Atual | V6 Alvo | P | Impacto | Risco | Esforço |
|---|-----|-------|---------|---|---------|-------|---------|
| A1 | Dossiê do Ativo fragmentado | Info do ativo espalhada por múltiplas queries — sem tela unificada de "tudo sobre este ativo" | Dossiê completo: info + docs + inspeções + OS + custos + indicadores | **P1** | Alto — PCM precisa abrir 5+ telas para entender o ativo | Baixo | Alto (6-8h) |
| A2 | Indicadores MTBF/MTTR não calculados | Dados existem (OS + tempos) mas cálculo não é feito | Cálculo automático por ativo/período | **P1** | Médio — gestores sem visibilidade de confiabilidade | Baixo | Médio (3h) |
| A3 | Custo por ativo não consolidado | Materiais e HH registrados, mas sem soma por ativo | Dashboard de custos por ativo, período, tipo | **P2** | Médio | Baixo | Médio (2-3h) |
| A4 | Timeline do ativo não visualizada | Audit logs existem mas sem visualização cronológica | Timeline visual com eventos, OS, inspeções | **P2** | Baixo | Baixo | Médio (3h) |

## 3. RBAC & SEGURANÇA

| # | Gap | Atual | V6 Alvo | P | Impacto | Risco | Esforço |
|---|-----|-------|---------|---|---------|-------|---------|
| S1 | Account lockout ausente | Apenas rate limit por IP | Lock após 5 falhas + desbloqueio automático | **P1** | Médio — brute force com IPs rotativos | Médio | Baixo (1h) |
| S2 | Password complexity ausente | Min 6 chars sem regras | Min 8 chars, 1 maiúscula, 1 número | **P1** | Médio | Baixo | Baixo (30min) |
| S3 | JWT sem refresh token | Token 24h, sem refresh | Access 15min + Refresh 7d | **P2** | Baixo — UX de re-login | Baixo | Médio (2h) |
| S4 | Rate limit não persistente | In-memory (perde no restart) | MongoDB-backed com TTL | **P2** | Baixo — janela de vulnerabilidade no restart | Baixo | Médio (1h) |
| S5 | CSP apenas em API responses | CSP no FastAPI, HTML servido sem CSP | CSP no HTML via meta tag ou Vercel headers | **P2** | Médio | Baixo | Baixo (30min) |

## 4. FRONTEND ARCHITECTURE

| # | Gap | Atual | V6 Alvo | P | Impacto | Risco | Esforço |
|---|-----|-------|---------|---|---------|-------|---------|
| F1 | App.js ainda monolítico (3.950 linhas) | Sidebar, Auth, Modals, alguns Pages ainda no App.js | App.js < 500 linhas (routing only) | **P2** | Baixo — maintainability | Baixo | Alto (8h+) |
| F2 | Zero lazy loading | 12+ páginas carregam estaticamente | React.lazy + Suspense em todas as páginas | **P2** | Médio — bundle 349KB gzip desnecessário | Baixo | Médio (2h) |
| F3 | Sidebar acoplado ao App.js | Sidebar é função dentro do App.js | Componente separado `components/layout/Sidebar.js` | **P3** | Baixo | Baixo | Baixo (1h) |
| F4 | Auth forms no App.js | Login, Register, ForgotPassword dentro do App.js | `pages/AuthPage.js` | **P3** | Baixo | Baixo | Baixo (1h) |

## 5. BACKEND ARCHITECTURE

| # | Gap | Atual | V6 Alvo | P | Impacto | Risco | Esforço |
|---|-----|-------|---------|---|---------|-------|---------|
| B1 | server.py monolítico (4150+ linhas) | Todos endpoints em um arquivo | Separar em routers: `routes/auth.py`, `routes/ativos.py`, `routes/os.py`, etc. | **P2** | Baixo — maintainability | Baixo | Alto (8h+) |
| B2 | Validação Pydantic inconsistente | Alguns endpoints validam via Pydantic, outros via dict manual | Pydantic models para todos os endpoints | **P2** | Médio — erros de tipo em runtime | Baixo | Alto (6h+) |
| B3 | Sem testes automatizados (pytest) | Zero test files | Suite mínima: auth, CRUD ativos, OS workflow, multi-tenant | **P1** | Alto — risco de regressão em cada deploy | Médio | Alto (8-12h) |

## 6. DATA & PERFORMANCE

| # | Gap | Atual | V6 Alvo | P | Impacto | Risco | Esforço |
|---|-----|-------|---------|---|---------|-------|---------|
| D1 | Sem backup automatizado | Nenhum backup | mongodump agendado + retenção 30 dias | **P0** | Crítico — perda de dados irrecuperável | Alto | Baixo (1h) |
| D2 | Sem paginação em endpoints de lista | Retorna todos os docs (filtrado por org) | Cursor-based pagination em GET /ativos, /os, /inspecoes | **P2** | Médio — lentidão com >1000 docs | Baixo | Médio (3h) |
| D3 | Sem cache de leitura | Toda query vai ao MongoDB | Cache Redis/in-memory para dados estáticos (org_config, planos) | **P3** | Baixo | Baixo | Médio (3h) |

## 7. FUNCIONALIDADES AUSENTES

| # | Gap | Descrição | P | Impacto | Risco | Esforço |
|---|-----|-----------|---|---------|-------|---------|
| N1 | Impressão de OS (PDF) | Técnicos precisam imprimir OS para levar a campo | **P1** | Alto — requisito operacional diário | Baixo | Médio (4h) |
| N2 | QR Code em ativos | Geração e impressão de etiquetas QR vinculadas ao ativo | **P1** | Médio — scanner existe, mas QR não é gerado | Baixo | Médio (3h) |
| N3 | Dashboard KPIs avançados | MTBF, MTTR, disponibilidade, custo/ativo, backlog aging | **P2** | Médio — gestores sem métricas avançadas | Baixo | Alto (6h) |
| N4 | Calendário de manutenção | Visualização de OS programadas em calendário | **P2** | Médio | Baixo | Médio (4h) |
| N5 | Integração ERP/SAP | Sincronização de materiais e custos | **P3** | Baixo (futuro) | Baixo | Muito Alto |

---

## Resumo Quantitativo

| Prioridade | Quantidade | Esforço Estimado |
|-----------|-----------|-----------------|
| **P0** | 2 | ~3-4h |
| **P1** | 8 | ~25-35h |
| **P2** | 11 | ~30-40h |
| **P3** | 4 | ~8-12h |
| **Total** | **25 gaps** | **~70-90h** |
