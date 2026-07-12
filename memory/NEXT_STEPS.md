# NEXT STEPS — MAINTRIX Enterprise
**Data:** 2026-07-12 | **Versão:** v5.2.0-RC1.5

---

## AÇÕES MANUAIS PENDENTES (CTO)

### P0 — Railway Backend Deploy
- **O quê:** Backend de produção está em v5.1.0. Precisa v5.2.0-RC1.
- **Como:** Railway Dashboard → Projeto → Redeploy manual. Ou ativar auto-deploy.
- **Impacto:** Sem isso, compliance, rate limiting, security headers e 14 indexes NÃO estão ativos em produção.
- **Validação:** `curl https://www.maintrix.com.br/api` deve retornar v5.2.0-RC1

### P1 — Save to GitHub (após esta sessão)
- **O quê:** Enviar modularização + relatórios ao GitHub
- **Como:** "Save to GitHub" na plataforma Emergent
- **Impacto:** Vercel auto-deploya frontend. Railway precisa trigger manual.

---

## BACKLOG TÉCNICO (RC2)

### Modularização Frontend (P1)
- [ ] Fase 2: Extrair modals (ModalNovaOS, ModalNovoAtivo, etc.) — -500 linhas
- [ ] Fase 3: Extrair widgets (KanbanBoard, Charts, PhotoUploader) — -400 linhas
- [ ] Fase 4: Extrair pages para arquivos individuais — -6000 linhas
- [ ] Meta: App.js ~500 linhas (router + providers)

### Pipeline (P1)
- [ ] Ativar auto-deploy Railway (branch main, root /backend)
- [ ] Configurar webhook de notificação de deploy (Slack/email)
- [ ] Criar GitHub Action para CI (lint + test + build)
- [ ] Adicionar tag semântica no Git (v5.2.0-RC1.5)

### Segurança (P2)
- [ ] Implementar CSP header (Content-Security-Policy)
- [ ] Restringir CORS (substituir * por domínios específicos)
- [ ] Migrar rate limiter para Redis/slowapi (multi-pod)
- [ ] Adicionar header Retry-After na resposta 429

### Compliance (P2)
- [ ] Contrato de cliente (template) em /commercial/contrato_cliente.md
- [ ] Política de retenção/exclusão de dados detalhada
- [ ] Exportação de dados do titular (LGPD Art. 18)

### Funcionalidades (P2)
- [ ] MAINTRIX Field Operations (PDFs, QR Codes, batch print)
- [ ] Dashboard Executivo
- [ ] IA Assistente
- [ ] ERP/SAP Integrations

---

## RESUMO DA MISSÃO RC1 COMPLETA

| Bloco | Status | Linhas | Testes |
|---|---|---|---|
| A — Limpeza | ✅ | -204 | 33/33 |
| B — PWA | ✅ | +300 | 33/33 |
| C — Hardening | ✅ | +170 | 31/31 |
| D — Certificação | ✅ | - | 58/58 |
| RC1.5 — Compliance | ✅ | +200 | 23/23 |
| Modularização | ✅ | -185 | CI build green |
| **TOTAL** | **✅** | | **178/178 PASS** |

---
*O MAINTRIX está tecnicamente pronto para o piloto ASTEC.*
*Único bloqueio: Railway backend precisa de redeploy manual.*
