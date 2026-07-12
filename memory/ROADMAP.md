# ROADMAP — MAINTRIX Enterprise

## RC2 (Próxima Release)

### P0 — Bloqueadores
- [ ] CSP header (Content-Security-Policy) com teste dedicado para Design Tokens + Recharts
- [ ] CORS restritivo (substituir `*` por domínios: maintrix.com.br, *.vercel.app)
- [ ] Contrato de cliente template (`/commercial/contrato_cliente.md`)
- [ ] Política de retenção/exclusão de dados detalhada

### P1 — Modularização Frontend
- [ ] Fase 2: Extrair modals → `/components/modals/` (-500 linhas)
- [ ] Fase 3: Extrair widgets → `/components/widgets/` (-400 linhas)
- [ ] Fase 4: Extrair pages → `/pages/*.js` (-6000 linhas)
- [ ] Meta: App.js ~500 linhas (router + providers)

### P1 — Pipeline
- [ ] Railway auto-deploy na branch main
- [ ] GitHub Actions para CI (lint + test + build)
- [ ] Webhook de notificação de deploy (Slack/email)
- [ ] Checklist automatizado de release

### P1 — MAINTRIX Field Operations
- [ ] Geração de PDF de Ordens de Serviço (arquitetura em `/memory/FIELD_OPERATIONS_ARCH.md`)
- [ ] QR Codes para ativos (impressão em lote)
- [ ] Status badges visuais em documentos impressos

### P2 — Segurança
- [ ] Rate limiter Redis/slowapi (multi-pod)
- [ ] Header Retry-After na resposta 429
- [ ] Audit log de compliance (quem viu quais dados)
- [ ] Exportação de dados do titular (LGPD Art. 18)

### P2 — Funcionalidades
- [ ] Dashboard Executivo (gerencial)
- [ ] IA Assistente (emergentintegrations quando disponível)
- [ ] Mapeamento IDs temporários offline → reais
- [ ] Login offline (token renewal)
- [ ] Conflict detection multi-usuário offline

### P3 — Integrações
- [ ] ERP/SAP
- [ ] Notificações push (Firebase)
- [ ] Relatórios automatizados por email

---

## Métricas da RC1

| Métrica | Valor |
|---|---|
| Testes executados | 178+ |
| Regressões detectadas | 0 |
| Bugs corrigidos | 12 |
| Linhas removidas | ~400 |
| Componentes extraídos | 14 |
| MongoDB indexes | 69 |
| Security headers | 6 |
| Endpoints protegidos (rate limit) | 7 |
| Operações offline | 11 |
| Compliance docs | 6 |
