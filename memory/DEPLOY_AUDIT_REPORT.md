# RELATÓRIO DE AUDITORIA DE DEPLOY — MAINTRIX
**Data:** 2026-07-11 | **Auditor:** Agente RC1.5

---

## RESUMO EXECUTIVO

**DIVERGÊNCIA CRÍTICA CONFIRMADA.** A versão em produção (maintrix.com.br) NÃO corresponde à RC1.5 certificada. Produção está executando código de **02 de Julho de 2026** — anterior a toda a missão de estabilização RC1. **88 commits estão faltando** em produção, incluindo todos os BLOCOs (A, B, C, D) e a RC1.5.

---

## 1. ESTADO DA PRODUÇÃO

### 1.1 Infraestrutura Identificada
| Componente | Plataforma | URL |
|---|---|---|
| Frontend | **Vercel** | www.maintrix.com.br |
| Backend | **Railway** | manutrix-pro-production.up.railway.app |
| Domínio | maintrix.com.br → 308 redirect → www.maintrix.com.br |
| DNS | Gerenciado via Vercel (CNAME) |

### 1.2 Versão em Produção
| Métrica | Valor | Evidência |
|---|---|---|
| API Version | **v5.1.0** | `GET /api` → `{"message": "MAINTRIX API v5.1.0"}` |
| Frontend Bundle | `main.8707c272.js` | HTML source |
| Last-Modified | **Thu, 02 Jul 2026 16:28:07 GMT** | HTTP header |
| Cache Age | ~793.733s (9,18 dias) | HTTP header `age` |
| Service Worker | **v3** | `/service-worker.js` → `CACHE_NAME = 'maintrix-v3'` |
| Organizações | **1** | `GET /api/public/organizations` |
| Security Headers | **AUSENTES** | Sem X-Content-Type-Options, X-Frame-Options, etc. |
| Compliance | **INEXISTENTE** | `GET /api/compliance/about` → 404 |

### 1.3 Versão RC1.5 Certificada (Local/Emergent)
| Métrica | Valor |
|---|---|
| API Version | **v5.2.0-RC1** |
| Frontend Bundle | Desenvolvimento (hot reload) |
| Service Worker | **v4** (15 rotas cacheadas) |
| Organizações | **5** (base de teste diferente) |
| Security Headers | **6 headers implementados** |
| Compliance | **Completo** (aceite, termos, privacidade) |

---

## 2. COMMITS EM FALTA

### 2.1 Quantidade
- **Commit em produção (estimado):** `1040c0d` (02 Jul 2026, 16:26 UTC)
- **Commit mais recente (local):** `e0dd19f` (11 Jul 2026, 13:27 UTC)
- **Total de commits faltantes:** **88 commits** (9 dias de trabalho)

### 2.2 Trabalho Não Publicado
| Período | Conteúdo | Impacto |
|---|---|---|
| 02-09 Jul | Trabalho pré-RC1 (sessão anterior) | Funcionalidades e correções |
| 11 Jul (manhã) | **BLOCO A** — Limpeza de código | -204 linhas, 10 React.memo |
| 11 Jul | **BLOCO B** — PWA/Offline | 11 operações offline, cache, fotos |
| 11 Jul | **BLOCO C** — Hardening | Rate limiting, Security Headers, 14 indexes, Timeouts |
| 11 Jul | **BLOCO D** — Certificação | Fix botão INICIAR, validação 58 testes |
| 11 Jul (tarde) | **RC1.5** — Compliance/LGPD | Termos, Privacidade, Aceite, Sobre, Footer |

---

## 3. ANÁLISE DETALHADA

### 3.1 DNS e Domínio
- `maintrix.com.br` → HTTP 308 → `www.maintrix.com.br` (Vercel redirect)
- HSTS: `max-age=63072000` (aplicado por Vercel)
- Certificado SSL: Válido (gerenciado por Vercel)
- **Status: OK** — DNS e domínio funcionam corretamente

### 3.2 Headers de Produção
```
server: Vercel
x-vercel-cache: HIT
x-vercel-id: sfo1::...
strict-transport-security: max-age=63072000
access-control-allow-origin: *
```
**AUSENTES (implementados em BLOCO C, mas não deployados):**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy
- Permissions-Policy
- X-XSS-Protection

### 3.3 Build Configuration
- **Build command:** `craco build` (via package.json)
- **vercel.json:** API rewrites para Railway (`/api/:path*` → `manutrix-pro-production.up.railway.app`)
- **Root directory:** `/frontend` (Vercel)
- **No `vercel.json` na raiz** — build settings vêm do painel Vercel

### 3.4 Backend (Railway)
- Executa **v5.1.0** (pré-estabilização)
- Sem rate limiting
- Sem security headers (os headers BLOCO C são middleware do FastAPI)
- Sem endpoints de compliance
- Login com credenciais ASTEC falha (banco de dados diferente)

### 3.5 Service Worker
- Produção: **v3** (8 rotas API cacheadas)
- RC1.5: **v4** (15 rotas API cacheadas)
- Rotas faltantes em produção: `/api/planos-inspecao`, `/api/inspection-templates`, `/api/estoque`, `/api/central`, `/api/unidades`, `/api/rotas`, `/api/dashboard/`

---

## 4. CAUSA DA DIVERGÊNCIA

### Hipótese Principal (CONFIRMADA)
O código foi enviado ao GitHub pela última vez em/antes de **02 de Julho de 2026**. Desde então:
1. A Vercel auto-deployou a partir desse commit
2. Todo o trabalho subsequente (BLOCOs A-D + RC1.5) foi feito no **ambiente Emergent**, que mantém seu próprio histórico Git
3. O `git remote` está **vazio** no ambiente atual — não há remote GitHub configurado
4. A funcionalidade **"Save to GitHub"** da plataforma Emergent NÃO foi utilizada após 02/Jul

### Não é cache
- O `x-vercel-cache: HIT` com `age: 793733s` confirma que Vercel está servindo a versão correta do ÚLTIMO deploy (Jul 2). Não há cache impedindo um deploy mais recente — simplesmente não houve deploy mais recente.

### Não é branch incorreta
- O repositório local usa `main` branch. A Vercel provavelmente está conectada à mesma branch.

---

## 5. AÇÕES RECOMENDADAS

### Ação Imediata (Prioridade CRÍTICA)
1. **Usar "Save to GitHub"** na plataforma Emergent para enviar o código RC1.5 ao repositório GitHub
2. A Vercel deve auto-detectar o push e iniciar um novo build automaticamente
3. Verificar se o Railway também rebuilda automaticamente (ou trigger manual)

### Após o Deploy
1. Verificar `GET /api` retorna `v5.2.0-RC1`
2. Verificar `GET /api/compliance/about` retorna informações do sistema
3. Verificar security headers presentes
4. Verificar Service Worker v4 no browser
5. Testar fluxo de login + consent gate

### Variáveis de Ambiente
- **ATENÇÃO:** O `REACT_APP_BACKEND_URL` no `.env` do Emergent aponta para `preview.emergentagent.com`, mas o `vercel.json` no frontend faz rewrite para Railway. Verificar que as variáveis de ambiente da Vercel apontam corretamente para Railway ou estão vazias (para usar os rewrites).

### Banco de Dados
- Produção (Railway) usa um banco MongoDB **diferente** do ambiente Emergent
- As credenciais de teste ASTEC NÃO existem em produção (login falhou)
- Os 14 índices do BLOCO C precisarão ser criados no banco de produção (são criados no startup do backend)

---

## 6. INVENTÁRIO DE RISCOS DO DEPLOY

| Risco | Severidade | Mitigação |
|---|---|---|
| REACT_APP_BACKEND_URL incorreto no build Vercel | ALTA | Verificar env vars no painel Vercel — deve estar vazio ou apontar para Railway |
| Banco de produção sem índices BLOCO C | MÉDIA | Índices são criados automaticamente no startup do backend |
| Banco de produção sem coleção `consents` | BAIXA | Criada automaticamente no primeiro aceite |
| Service Worker v3 cacheado no browser dos usuários | MÉDIA | SW v4 com `skipWaiting()` + `clients.claim()` força atualização |
| CSS/JS bundle cacheado no CDN Vercel | BAIXA | Novo deploy gera novos hashes de bundle |

---

## 7. CONCLUSÃO

**A produção está 88 commits atrás da versão RC1.5 certificada.** A causa é a não-utilização do "Save to GitHub" após 02 de Julho. Toda a missão de estabilização (BLOCOs A-D + RC1.5) existe apenas no ambiente Emergent.

**Nenhuma alteração foi feita nesta auditoria.** Aguardando decisão do CTO para prosseguir com o deploy.

---
*Relatório gerado em 2026-07-11 — Auditoria exclusivamente diagnóstica*
