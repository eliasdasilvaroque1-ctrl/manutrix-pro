# MAINTRIX v1.0 — RELATÓRIO COMPLETO DE AUDITORIA
## Principal Staff Engineer / CTO / DevOps

**Data:** 13/07/2026  
**Objetivo:** Identificar causa raiz de TODOS os erros de produção  
**Escopo:** GitHub → Vercel → Railway → MongoDB → Supabase → Frontend → Backend → Auth

---

# 1. GITHUB

| Item | Resultado |
|------|-----------|
| Branch | `main` (única) |
| Último commit | `2cbf9b29083ddf6e7be9d2f8a7e66f475410b7a4` |
| Data | 2026-07-13 17:40:50 UTC |
| Autor | emergent-agent-e1 |
| Remote | **NENHUM** — git remote está vazio. O push para GitHub é feito via plataforma Emergent ("Save to GitHub") |
| Arquivos tracked | 559 |
| Untracked | `frontend/yarn.lock`, `yarn.lock` |
| .gitignore | OK — ignora node_modules, .env*, build, coverage |

**Diagnóstico:** Sem remote configurado. Se o deploy no Vercel/Railway depende de push direto ao GitHub, é necessário usar "Save to GitHub" na plataforma Emergent. Não há como confirmar se o último commit no GitHub corresponde ao commit local sem acesso ao repo remoto.

---

# 2. VERCEL (Frontend)

| Item | Resultado |
|------|-----------|
| vercel.json | Presente |
| Build command | `cd frontend && yarn install && yarn build` |
| Output dir | `frontend/build` |
| Framework | create-react-app |
| Rewrites | `/api/(.*)` → `/api/$1` |
| REACT_APP_BACKEND_URL | `https://procure-manutrix.preview.emergentagent.com` |
| Build local | ✅ PASS (CI=true craco build — 0 warnings) |
| Homepage | NOT SET no package.json |

**⚠️ PROBLEMA CRÍTICO:** O `vercel.json` tem `rewrites` que redirecionam `/api/*` para `/api/$1` — mas NÃO especifica o destino (backend). Isso significa que o Vercel vai tentar servir `/api/*` como arquivo estático, resultando em **404 para todas as APIs**. A rewrite precisa apontar para a URL do Railway backend.

**⚠️ PROBLEMA:** `REACT_APP_BACKEND_URL` no `.env` local aponta para `preview.emergentagent.com`. No Vercel, esta variável precisa ser configurada no dashboard apontando para o backend em Railway.

---

# 3. RAILWAY (Backend)

| Item | Resultado |
|------|-----------|
| Entrypoint | `server.py` (ÚNICO — não existe main.py/app.py) |
| Procfile | **NÃO EXISTE** ❌ |
| runtime.txt | **NÃO EXISTE** ❌ |
| nixpacks.toml | **NÃO EXISTE** ❌ |
| railway.json | **NÃO EXISTE** ❌ |
| Python version | 3.11.15 (local) |
| Port | 8001 (hardcoded no supervisor) |
| Start command | `uvicorn server:app --host 0.0.0.0 --port 8001 --reload` |

### 🔴 P0 — `emergentintegrations==0.1.0` no requirements.txt (linha 24)
- Este pacote requer `--extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/`
- Railway executa `pip install -r requirements.txt` **SEM** o extra index
- **Resultado:** `No matching distribution found for emergentintegrations==0.1.0`
- **Build FALHA no Railway**
- O pacote está instalado no container Emergent (via pip com extra index), mas Railway não sabe como encontrá-lo

### 🔴 P0 — Sem Procfile
- Railway precisa saber como iniciar o app
- Sem Procfile, Railway tenta detectar automaticamente (pode falhar)
- **Necessário:** `web: cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`

### 🔴 P0 — MONGO_URL=mongodb://localhost:27017
- Em Railway, `localhost` é o container efêmero — NÃO tem MongoDB
- **O backend não consegue conectar ao banco em Railway**

---

# 4. BACKEND — Entrypoint

| Arquivo | Existe? |
|---------|---------|
| `/app/backend/server.py` | ✅ SIM (205KB, ~4434 linhas) |
| `/app/backend/main.py` | ❌ NÃO |
| `/app/backend/app.py` | ❌ NÃO |

**Entrypoint confirmado:** `server.py` com `app = FastAPI(title="MAINTRIX API", version="1.0.0")`

---

# 5. API — Teste de Todos os Endpoints

### Resultado: 63/64 endpoints ✅ (1 requer parâmetro obrigatório)

| Status | Count |
|--------|-------|
| 200 | 63 |
| 422 | 1 (`/planos-inspecao/categorias-disponiveis` — requer `?ativo_id=`) |
| 404 | 0 |
| 500 | 0 |

**PDF endpoint:** `GET /api/ordens-servico/{id}/pdf` → **200** (4642 bytes) ✅

**Se o PDF retorna 404 em produção (Railway):** A causa é que o Railway build falha no `emergentintegrations` e o backend nem inicia. Logo, TODOS os endpoints retornam 404/502.

---

# 6. FRONTEND — Auditoria

### 🔴 P0 — `useCallback is not defined`

| Item | Valor |
|------|-------|
| **Arquivo** | `/app/frontend/src/pages/WhiteLabelDesignerPage.js` |
| **Linha** | 161 |
| **Componente** | `WhiteLabelDesignerPage` (rota `/master/white-label`) |
| **Causa raiz** | Linha 1 importa `{ useState, useEffect, useRef }` mas **NÃO importa `useCallback`**. Linha 161 usa `const loadOrgs = useCallback(...)` |
| **Impacto** | `ReferenceError: useCallback is not defined` ao abrir White Label Designer |
| **Quem afeta** | Apenas role `master` (rota protegida) |

**Nota:** `carousel.jsx` também usa `React.useCallback` sem import direto, mas funciona porque usa `React.useCallback` (qualificado via namespace).

### Error Boundary
- Existe: `ErrorBoundary.js` — wraps toda a app (App.js:3971)
- Captura o erro do useCallback mas mostra tela de erro genérica

### Lazy Loading
- **Nenhum** lazy loading implementado (todas as páginas carregam no bundle inicial)
- Bundle: 348KB gzipped (aceitável mas poderia ser otimizado)

---

# 7. AUTENTICAÇÃO

| Item | Resultado |
|------|-----------|
| JWT Algorithm | HS256 |
| Expiração | 24 horas |
| Refresh Token | **NÃO EXISTE** |
| Storage | `sessionStorage` (não localStorage) |
| Key | `maintrix_token` / `maintrix_user` |

### Perguntas do CTO respondidas:

**"Técnico permanece logado após F5"**
- **ESPERADO.** `sessionStorage` persiste durante a sessão do tab. F5 NÃO limpa sessionStorage. O token só expira em 24h ou quando o tab é fechado.

**"Login aceita usuário sem empresa"**
- **CONFIRMADO.** O endpoint `POST /auth/login` faz auto-resolve de org_id (server.py:379-383). Se o email existe no banco e o role NÃO é `master`, o backend busca o org_id automaticamente. Apenas `master` precisa informar org_id. Isso é BY DESIGN, não é bug.

**"Técnico consegue criar preventiva"**
- **CONFIRMADO. BUG REAL.** 
  - `POST /api/ordens-servico` (work_orders.py:249) permite roles: `['admin', 'master', 'pcm', 'supervisor', 'operador'] + ROLE_GROUPS['execucao']`
  - `ROLE_GROUPS['execucao']` inclui `tec_mecanico`, `tec_eletrico`, `tec_instrumentacao`
  - O endpoint NÃO verifica o `tipo` da OS — técnico pode criar corretiva E preventiva
  - **Regra de negócio:** Técnico deveria poder criar apenas corretivas (execução direta), não preventivas

---

# 8. MONGODB — Investigação Especial

### Onde estão os dados?

| Item | Valor |
|------|-------|
| **MONGO_URL** | `mongodb://localhost:27017` |
| **DB_NAME** | `test_database` |
| **Tipo** | MongoDB LOCAL (dentro do container Emergent) |
| **Versão** | 7.0.37 |
| **NÃO é** | MongoDB Atlas, Railway Mongo, Docker externo |

### Dados atuais (container Emergent):

| Collection | Documentos |
|------------|-----------|
| users | 64 |
| ativos | 173 |
| ordens_servico | 182 |
| planos_inspecao | 188 |
| inspecoes | 2 |
| audit_logs | 1139 |
| org_config | 5 |
| organizations | 5 |
| **Total collections** | **49** |

### ⚠️ CONCLUSÃO CRÍTICA SOBRE MONGODB

**O CTO não encontra a conta MongoDB porque NÃO EXISTE conta externa.**

O sistema está usando `mongodb://localhost:27017` — o MongoDB **local do container Emergent**. Isso significa:
1. Os dados existem APENAS dentro do pod Kubernetes da Emergent
2. NÃO há backup externo
3. Se o container for recriado, os dados **podem ser perdidos**
4. Em Railway, `localhost:27017` NÃO existe — o backend não consegue conectar

**Para produção:** É necessário criar um MongoDB Atlas cluster e configurar `MONGO_URL` com a connection string do Atlas (ou adicionar um MongoDB service no Railway).

### Onde o CTO deve acessar os dados:
- **Agora (preview):** Os dados estão no MongoDB dentro do container Emergent. Não há dashboard externo.
- **Para produção:** Criar conta MongoDB Atlas → cluster → configurar MONGO_URL

---

# 9. SUPABASE

| Item | Valor |
|------|-------|
| URL | `https://qyzahffbzobetohxdkrp.supabase.co` |
| Project Ref | `qyzahffbzobetohxdkrp` |
| Dashboard | `https://supabase.com/dashboard/project/qyzahffbzobetohxdkrp` |
| Uso | Object Storage (imagens, manuais PDF) |
| Uso secundário | Password sync (supabase_id em users) |
| Anon Key | Configurada ✅ |
| Service Key | Configurada ✅ |

**Supabase NÃO é usado como banco principal.** É usado apenas para:
1. Upload/armazenamento de arquivos (imagens, PDFs)
2. Sincronização de senhas (quando usuário tem supabase_id)

---

# 10. INTEGRAÇÃO — Mapa de Sincronização

```
GitHub (branch: main)
  │
  ├── "Save to GitHub" (Emergent) → Push manual
  │
  ├──→ Vercel (Frontend)
  │     ├── Build: craco build
  │     ├── REACT_APP_BACKEND_URL → deve apontar para Railway
  │     └── ⚠️ rewrites /api/* sem destino backend
  │
  └──→ Railway (Backend)
        ├── ❌ Sem Procfile
        ├── ❌ emergentintegrations falha no pip install
        ├── ❌ MONGO_URL=localhost (não funciona)
        └── Conecta a:
              ├── MongoDB (precisa Atlas/Railway Mongo)
              └── Supabase (Object Storage)
```

---

# 11. ERROS DE PRODUÇÃO — Causa Raiz

### "Minha Área não carrega"
- **Causa:** Se em Railway, backend não inicia (emergentintegrations falha)
- **Preview Emergent:** Funciona (HTTP 200, dados retornados)

### "White Label quebra"
- **Causa raiz encontrada:** `WhiteLabelDesignerPage.js` linha 1 NÃO importa `useCallback`, mas linha 161 usa `useCallback`. Resulta em `ReferenceError: useCallback is not defined`
- **Arquivo:** `/app/frontend/src/pages/WhiteLabelDesignerPage.js`
- **Linha:** 161

### "Cleanup quebra"
- **Causa provável:** Se o backend não está rodando em Railway, todas as chamadas API falham
- **MasterCleanupPage.js:** Imports OK, sem hook issues

### "PDF retorna 404"
- **Causa:** Em Railway, o backend não inicia → todos endpoints retornam 404/502
- **Preview Emergent:** PDF funciona (HTTP 200, 4642 bytes)

### "Erro ao carregar dados"
- **Causa:** Backend não conecta ao MongoDB em Railway (`localhost:27017` não existe)

### "Cadastro abre cortado"
- **Causa provável:** O modal `ModalNovoAtivo` (App.js:147) pode ter overflow issue no mobile ou em telas pequenas. Sem acesso a screenshots específicos, não é possível determinar a causa exata.

### "useCallback is not defined"
- **Arquivo:** `/app/frontend/src/pages/WhiteLabelDesignerPage.js`
- **Linha 1:** `import { useState, useEffect, useRef } from "react";` ← FALTA `useCallback`
- **Linha 161:** `const loadOrgs = useCallback(async () => {` ← USA sem importar

---

# CLASSIFICAÇÃO DE ISSUES

## 🔴 P0 — CRÍTICO (Bloqueia produção)

| # | Issue | Arquivo | Linha | Impacto | Tempo fix |
|---|-------|---------|-------|---------|-----------|
| 1 | `emergentintegrations==0.1.0` no requirements.txt sem extra-index-url | `requirements.txt:24` | 24 | Railway build FALHA | 5 min |
| 2 | `MONGO_URL=mongodb://localhost:27017` — inválido em Railway | `backend/.env` | 1 | Backend não conecta ao banco | 10 min (precisa Atlas) |
| 3 | Sem Procfile para Railway | Raiz do projeto | — | Railway não sabe iniciar o backend | 2 min |
| 4 | vercel.json rewrites sem destino backend | `vercel.json` | 6 | APIs retornam 404 no Vercel | 5 min |

## 🟡 P1 — ALTO (Funcionalidade quebrada)

| # | Issue | Arquivo | Linha | Impacto | Tempo fix |
|---|-------|---------|-------|---------|-----------|
| 5 | `useCallback` não importado em WhiteLabelDesignerPage | `WhiteLabelDesignerPage.js` | 1, 161 | White Label crasheia para master | 1 min |
| 6 | Técnico pode criar OS preventiva (regra de negócio violada) | `routes/work_orders.py` | 249 | RBAC incompleto para tipo de OS | 10 min |
| 7 | REACT_APP_BACKEND_URL aponta para preview, não produção | `frontend/.env` | 1 | Frontend não conecta ao backend real | 1 min (env var) |

## 🟠 P2 — MÉDIO

| # | Issue | Arquivo | Linha | Impacto | Tempo fix |
|---|-------|---------|-------|---------|-----------|
| 8 | Sem runtime.txt (Python version) para Railway | Raiz do projeto | — | Railway pode usar Python errado | 1 min |
| 9 | JWT sem refresh token — sessão expira em 24h sem renovação | `deps.py` | 33 | Usuário precisa re-logar diariamente | 2h |
| 10 | sessionStorage perde token ao fechar tab | `lib/api.js` | 35 | UX: "deslogou sozinho" | 30 min |
| 11 | `yarn.lock` não tracked no git | `.gitignore` / root | — | Builds não determinísticos | 5 min |

## 🟢 P3 — BAIXO

| # | Issue | Arquivo | Linha | Impacto | Tempo fix |
|---|-------|---------|-------|---------|-----------|
| 12 | Sem lazy loading no React | `App.js` | — | Bundle 348KB (OK mas otimizável) | 2h |
| 13 | server.py com ~4434 linhas | `server.py` | — | Manutenibilidade (tech debt) | 8h |
| 14 | App.js com ~4025 linhas | `App.js` | — | Manutenibilidade (tech debt) | 8h |
| 15 | git remote vazio | `.git/config` | — | Push manual necessário | 5 min |

---

# PLANO DE CORREÇÃO (Ordem de Prioridade)

### Fase 1 — Desbloquear Railway (30 min)
1. Criar `Procfile`: `web: cd backend && pip install -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ && uvicorn server:app --host 0.0.0.0 --port $PORT`
2. Criar `backend/runtime.txt`: `python-3.11.15`
3. Criar MongoDB Atlas cluster e obter connection string
4. Configurar env vars no Railway: `MONGO_URL`, `DB_NAME`, `JWT_SECRET`, `CORS_ORIGINS`, `SUPABASE_*`

### Fase 2 — Desbloquear Vercel (15 min)
5. Corrigir `vercel.json` rewrites para apontar para URL do Railway
6. Configurar `REACT_APP_BACKEND_URL` no Vercel dashboard

### Fase 3 — Bugs P1 (15 min)
7. Adicionar `useCallback` ao import do `WhiteLabelDesignerPage.js` linha 1
8. Adicionar validação de `tipo` no `create_os` para técnicos

### Fase 4 — Melhorias P2 (3h)
9. Criar `runtime.txt`
10. Avaliar localStorage vs sessionStorage
11. Planejar refresh token

---

# MAPA DE ARQUITETURA DE DADOS

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│  React PWA (Vercel)                                  │
│  REACT_APP_BACKEND_URL → Railway backend             │
│  Auth: sessionStorage (maintrix_token)               │
└───────────────────┬─────────────────────────────────┘
                    │ HTTPS
                    ▼
┌─────────────────────────────────────────────────────┐
│                    BACKEND                           │
│  FastAPI (Railway)                                   │
│  server.py (entrypoint)                              │
│  Port: $PORT (Railway dynamic)                       │
│  JWT: HS256, 24h                                     │
└───────┬───────────────────────┬─────────────────────┘
        │                       │
        ▼                       ▼
┌───────────────────┐   ┌─────────────────────────────┐
│     MongoDB        │   │       Supabase               │
│  ⚠️ ATUALMENTE:    │   │  qyzahffbzobetohxdkrp       │
│  localhost:27017   │   │                               │
│  (container local) │   │  ├── Object Storage           │
│  test_database     │   │  │   (imagens, PDFs, manuais) │
│  49 collections    │   │  └── Password Sync            │
│  173 ativos        │   │      (supabase_id → users)    │
│  182 OS            │   │                               │
│  64 users          │   │  Dashboard:                   │
│                    │   │  supabase.com/dashboard/      │
│  ⚠️ PRODUÇÃO:      │   │  project/qyzahffbzobetohxdkrp│
│  Precisa Atlas ou  │   └─────────────────────────────┘
│  Railway Mongo     │
└───────────────────┘
```
