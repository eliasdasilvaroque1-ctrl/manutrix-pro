# PIPELINE AUDIT — GitHub → Vercel → Railway
**Data:** 2026-07-12

---

## ESTADO ATUAL

| Elo | Status | Detalhes |
|---|---|---|
| Emergent → GitHub | ✅ | "Save to GitHub" funcional (último push: Jul 12) |
| GitHub → Vercel | ✅ | Auto-deploy ativo, build passando |
| GitHub → Railway | ❌ | **NÃO auto-deploya**. Requer trigger manual |

## FRONTEND (Vercel) — ✅ SINCRONIZADO

- Last-Modified: Sun, 12 Jul 2026
- Service Worker: v4
- Bundle: main.bdb23ab2.js
- Rotas /termos, /sobre: HTTP 200
- Build: CI=true yarn build → Compiled successfully

## BACKEND (Railway) — ❌ DESATUALIZADO

- API Version: **v5.1.0** (deveria ser v5.2.0-RC1)
- Compliance endpoints: **404** (não existem)
- Security Headers: **AUSENTES** (middleware BLOCO C não deployed)
- Rate Limiting: **INATIVO**
- 14 MongoDB indexes do BLOCO C: **NÃO CRIADOS** (criados no startup)

## AÇÃO MANUAL NECESSÁRIA (Railway)

O CTO precisa executar no painel Railway:

1. **Railway Dashboard** → Projeto MAINTRIX → Settings → Deploys
2. Verificar: "Auto-deploy" está **OFF** ou apontando para branch/diretório errado
3. Ativar auto-deploy na branch `main` com Root Directory = `backend` (ou `/`)
4. OU: Fazer redeploy manual → Deployments → "Deploy"

## BUILD COMMAND (Railway)

```
Build: pip install -r requirements.txt
Start: uvicorn server:app --host 0.0.0.0 --port $PORT
Root: /backend
```

## VARIÁVEIS DE AMBIENTE (Railway)

```
MONGO_URL=mongodb+srv://...
DB_NAME=maintrix
JWT_SECRET=...
PORT=8001
MAINTRIX_ENV=production
```

## VALIDAÇÃO PÓS-DEPLOY

Executar `/app/scripts/validate_deploy.py` ou verificar manualmente:
- `GET /api` → `v5.2.0-RC1`
- `GET /api/compliance/about` → HTTP 200
- Response headers incluem X-Content-Type-Options, X-Frame-Options

---
*Railway é o único ponto que requer intervenção manual*
