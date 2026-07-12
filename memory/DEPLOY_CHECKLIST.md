# DEPLOY CHECKLIST — MAINTRIX Enterprise
## Pipeline: Emergent → GitHub → Vercel (Frontend) + Railway (Backend) → Produção

---

## ESTADO ATUAL DO PIPELINE (2026-07-12)

| Componente | Status | Versão | Auto-Deploy |
|---|---|---|---|
| **Emergent** (workspace) | ✅ RC1.5 | v5.2.0-RC1 | N/A |
| **GitHub** (repositório) | ✅ Sincronizado | commit 6392c78 | N/A |
| **Vercel** (frontend) | ✅ DEPLOYADO | SW v4, build Jul 12 | ✅ Automático |
| **Railway** (backend) | ❌ DESATUALIZADO | v5.1.0 | ❌ NÃO disparou |

---

## PRÉ-DEPLOY: Checklist de Código

Antes de qualquer "Save to GitHub":

- [ ] `CI=true yarn build` no `/app/frontend` — zero warnings, zero errors
- [ ] Backend inicia sem erros — `sudo supervisorctl restart backend && tail /var/log/supervisor/backend.err.log`
- [ ] Versão correta em `server.py` — `grep 'v5.2.0' /app/backend/server.py`
- [ ] Service Worker versão correta — `head -1 /app/frontend/public/service-worker.js`
- [ ] Sem `console.log` de debug no frontend — `grep -c 'console.log' /app/frontend/src/App.js`

---

## DEPLOY: Passo a Passo

### 1. Save to GitHub (Emergent)
```
Ação: Clicar "Save to GitHub" na interface Emergent
Branch: main
Verificar: Abrir github.com → confirmar que commit existe
```

### 2. Vercel (Frontend) — Auto-Deploy
```
Esperar: 2-5 minutos após push
Verificar: https://www.maintrix.com.br
  → Novo ETag/Last-Modified
  → Service Worker versão correta
  → Rotas /termos, /sobre retornam 200
```

### 3. Railway (Backend) — REQUER AÇÃO MANUAL
```
⚠️ Railway NÃO está auto-deployando.

Opção A: Ativar auto-deploy no painel Railway
  → Railway Dashboard → Project → Settings → Deploys
  → Enable "Auto-deploy on push"
  → Verificar que o Source Branch é "main"
  → Verificar que Root Directory é "/backend" (ou "/")

Opção B: Trigger manual
  → Railway Dashboard → Project → Deployments
  → Clicar "Deploy" ou "Redeploy"

Opção C: Via Railway CLI
  → railway up --service backend
```

---

## PÓS-DEPLOY: Validação Automatizada

### Script de Validação
```bash
python3 /app/scripts/validate_deploy.py
```

### Checklist Manual (caso o script não esteja disponível)

#### Frontend (Vercel)
- [ ] `https://www.maintrix.com.br/` retorna HTTP 200
- [ ] `Last-Modified` header tem data recente (posterior ao deploy)
- [ ] Service Worker: `https://www.maintrix.com.br/service-worker.js` → `maintrix-v4`
- [ ] Rota `/login` carrega
- [ ] Rota `/termos` carrega (RC1.5 compliance)
- [ ] Rota `/sobre` carrega (RC1.5 compliance)
- [ ] Footer visível com "Termos de Uso | Privacidade | Sobre | v5.2.0-RC1"

#### Backend (Railway)
- [ ] `GET /api` retorna `{"message": "MAINTRIX API v5.2.0-RC1"}`
- [ ] `GET /api/compliance/about` retorna HTTP 200 com versão e contato
- [ ] `GET /api/compliance/terms` retorna HTTP 200 com conteúdo dos Termos
- [ ] `GET /api/public/organizations` retorna lista de organizações
- [ ] Security headers presentes: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy
- [ ] Rate limit funcional: 12+ POSTs em `/api/auth/login` → HTTP 429

#### Integração
- [ ] Login funciona end-to-end (frontend → backend via Vercel rewrite → Railway)
- [ ] Consent gate aparece para novos usuários
- [ ] PWA instalável (manifest.json válido)

---

## TROUBLESHOOTING

### Vercel não deployou
1. Verificar se o push chegou ao GitHub (abrir github.com)
2. Verificar no painel Vercel → Deployments se há build recente
3. Se build falhou: verificar Build Logs por erros ESLint
4. Solução: corrigir warnings (`CI=true yarn build` local) e re-push

### Railway não deployou
1. Railway NÃO tem auto-deploy configurado para este projeto
2. Após cada push, fazer redeploy manual no painel Railway
3. Ou: Ativar auto-deploy em Railway → Settings → Deploys → "Automatic"

### Frontend atualiza mas backend não
- Vercel e Railway são deployments INDEPENDENTES
- Vercel faz auto-deploy do frontend (root: `/frontend`)
- Railway precisa deploy separado do backend (root: `/backend` ou `/`)
- Ambos leem do MESMO repositório GitHub, mas com configurações separadas

### ConsentGate aparece mas API retorna 404
- Backend ainda está na versão antiga (v5.1.0)
- Frontend tem o código do ConsentGate mas os endpoints não existem no backend
- Solução: Deploy do backend no Railway

---

## CONFIGURAÇÃO DE REFERÊNCIA

### Vercel
```
Framework: Create React App
Root Directory: frontend
Build Command: craco build (ou CI=true craco build)
Output Directory: build
Install Command: yarn install
Node Version: 18.x ou superior
```

### Railway
```
Root Directory: backend (ou /)
Build Command: pip install -r requirements.txt
Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
```

### Variáveis de Ambiente

#### Vercel (Frontend)
```
REACT_APP_BACKEND_URL=  (vazio — usa rewrites do vercel.json)
```

#### Railway (Backend)
```
MONGO_URL=mongodb+srv://...  (MongoDB Atlas ou similar)
DB_NAME=maintrix
JWT_SECRET=...
PORT=8001
MAINTRIX_ENV=production
```

---

## PIPELINE ALVO (Quando Railway auto-deploy estiver ativo)

```
[Developer]
    ↓ code changes
[Emergent Workspace]
    ↓ "Save to GitHub"
[GitHub - branch main]
    ↓ webhook              ↓ webhook
[Vercel]               [Railway]
    ↓ auto-build            ↓ auto-build
[Frontend CDN]         [Backend API]
    ↓                       ↓
[www.maintrix.com.br]  [manutrix-pro-production.up.railway.app]
    ↓                       ↑
    └── /api/:path* ────────┘  (Vercel rewrite)
```

---

*Checklist v1.0 — Criado 2026-07-12*
*Executar após cada deploy para garantir integridade da cadeia de entrega*
