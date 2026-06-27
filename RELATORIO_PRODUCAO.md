# MAINTRIX - RELATORIO FINAL DE PRODUCAO
## Versao 3.1.0 | Piloto ASTEC | Fevereiro 2026

---

## 1. ARQUITETURA ATUAL DO SISTEMA

### 1.1 Frontend
| Item | Detalhe |
|------|---------|
| Framework | React 19 (CRA + CRACO) |
| UI | Shadcn/UI + Tailwind CSS 3.4 |
| Estado | Context API (AuthContext) + useState local |
| Roteamento | React Router DOM 7.5 |
| PWA | Service Worker registrado, offline queue (localforage) |
| Graficos | Recharts 3.8 |
| QR Code | qrcode.react (gerar) + jsQR + BarcodeDetector (ler) |
| Exportacao | Blob download via Axios (responseType: blob) |
| Drag & Drop | HTML5 nativo (Kanban) |
| Build | craco build -> static files |
| Arquivo principal | `/app/frontend/src/App.js` (~6600 linhas, monolitico) |

### 1.2 Backend
| Item | Detalhe |
|------|---------|
| Framework | FastAPI 0.110 + Uvicorn 0.25 |
| Banco de dados | MongoDB via Motor 3.3 (async) |
| Autenticacao | Supabase Auth (primario) + bcrypt/MongoDB (fallback) |
| Autorizacao | RBAC customizado (deps.py) - 4 perfis ativos |
| PDF | ReportLab 4.4 |
| Excel | OpenPyXL 3.1 |
| Modelos | Pydantic v2 |
| JWT | PyJWT (HS256, 24h expiracao) |
| Arquivos | server.py (3091 linhas) + deps.py (277) + models.py (489) + routes/ (3 arquivos) |

### 1.3 Banco de Dados
| Item | Detalhe |
|------|---------|
| Engine | MongoDB (Motor async driver) |
| DB Name | Configuravel via `DB_NAME` env var |
| Collections | users, sectors, ativos, ordens_servico, inspecoes, anomalias, itens_estoque, movimentacoes_estoque, sobressalentes, paradas_programadas, planos_inspecao, audit_logs, notificacoes, attachments, manuais, ativo_materiais, os_materiais, password_reset_tokens, organizations |
| Multi-tenant | Campo `organization_id` em todas as collections principais |
| Soft delete | `deleted_at` (ISO timestamp) em todas as entidades |

### 1.4 Storage
| Item | Detalhe |
|------|---------|
| Uploads | Disco local `/app/backend/uploads/` |
| Manuais PDF | `/app/backend/uploads/manuals/` |
| Limite | .jpg, .jpeg, .png, .gif, .webp, .pdf |
| **ATENCAO** | Em producao, configurar volume persistente ou migrar para object storage (S3/Supabase Storage) |

### 1.5 Diagrama de Arquitetura
```
[Browser/PWA]
     |
     | HTTPS
     v
[Vercel CDN] --> React SPA (build estatico)
     |
     | API calls (/api/*)
     v
[Railway/VPS] --> FastAPI (uvicorn, porta 8001)
     |
     | Motor async
     v
[MongoDB Atlas] --> Collections com organization_id
     |
[Supabase] --> Auth (login, signup, password reset)
```

---

## 2. CHECKLIST DE DEPLOY DETALHADO

### Passo 1: GitHub
- [ ] Fazer commit final via "Save to GitHub" na plataforma Emergent
- [ ] Criar tag de release: `git tag v1.0.0-pilot -m "Piloto ASTEC"`
- [ ] Push da tag: `git push origin v1.0.0-pilot`
- [ ] Verificar branch `main` atualizada com todos os commits
- [ ] Proteger branch `main` (Settings > Branches > Branch protection rules)

### Passo 2: MongoDB Atlas
- [ ] Criar conta em [cloud.mongodb.com](https://cloud.mongodb.com)
- [ ] Criar cluster (M0 Free ou M10+ para producao)
- [ ] Criar database: `maintrix_production`
- [ ] Criar usuario de banco com permissao readWrite
- [ ] Configurar Network Access (IP do Railway/VPS ou 0.0.0.0/0 temporario)
- [ ] Copiar connection string: `mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/maintrix_production`
- [ ] Testar conexao com `mongosh`

### Passo 3: Supabase (Producao)
- [ ] Criar projeto em [supabase.com](https://supabase.com)
- [ ] Anotar: `SUPABASE_URL` (Settings > API > Project URL)
- [ ] Anotar: `SUPABASE_ANON_KEY` (Settings > API > anon/public)
- [ ] Anotar: `SUPABASE_SERVICE_KEY` (Settings > API > service_role - **secreto**)
- [ ] Configurar Auth > Settings:
  - Site URL: `https://app.maintrix.com.br`
  - Redirect URLs: `https://app.maintrix.com.br/**`
- [ ] Habilitar Email Auth (desabilitar "Confirm email" se desnecessario)

### Passo 4: Railway (Backend)
- [ ] Criar conta em [railway.app](https://railway.app)
- [ ] New Project > Deploy from GitHub repo
- [ ] Root Directory: `/backend`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
- [ ] Configurar variaveis de ambiente (ver Secao 3)
- [ ] Gerar dominio: `api-maintrix.up.railway.app` (ou custom domain)
- [ ] Verificar logs de deploy

### Passo 5: Vercel (Frontend)
- [ ] Criar conta em [vercel.com](https://vercel.com)
- [ ] Import GitHub repo
- [ ] Root Directory: `/frontend`
- [ ] Framework Preset: Create React App
- [ ] Build Command: `yarn build` (ou `craco build`)
- [ ] Output Directory: `build`
- [ ] Configurar variavel de ambiente:
  - `REACT_APP_BACKEND_URL` = URL do Railway (ex: `https://api-maintrix.up.railway.app`)
- [ ] Deploy

### Passo 6: Dominio
- [ ] Registrar dominio (ex: maintrix.com.br)
- [ ] DNS para Frontend: CNAME `app.maintrix.com.br` -> `cname.vercel-dns.com`
- [ ] DNS para Backend: CNAME `api.maintrix.com.br` -> `<railway-domain>`
- [ ] Configurar dominio customizado no Vercel (Settings > Domains)
- [ ] Configurar dominio customizado no Railway (Settings > Networking)
- [ ] SSL: Automatico em ambos (Let's Encrypt)
- [ ] Atualizar `REACT_APP_BACKEND_URL` no Vercel para `https://api.maintrix.com.br`
- [ ] Atualizar `Site URL` no Supabase para `https://app.maintrix.com.br`

### Passo 7: Dados Iniciais
- [ ] Fazer login com conta admin na aplicacao
- [ ] Criar organizacao ASTEC (via registro ou seed)
- [ ] POST `/api/seed` para dados de demonstracao (opcional)
- [ ] Criar usuarios reais da equipe ASTEC
- [ ] Criar areas, ativos e planos de inspecao reais

---

## 3. VARIAVEIS DE AMBIENTE

### 3.1 Backend (Railway / .env)
```
MONGO_URL=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>?retryWrites=true&w=majority
DB_NAME=maintrix_production
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
CORS_ORIGINS=https://app.maintrix.com.br
```

**Opcionais:**
```
JWT_SECRET=<gerar-com-openssl-rand-hex-32>
EMERGENT_LLM_KEY=<se-usar-assistente-ia>
```

> **IMPORTANTE:** Se `JWT_SECRET` nao for definido, sera gerado automaticamente a cada restart. Para sessoes persistentes entre deploys, defina manualmente com `openssl rand -hex 32`.

### 3.2 Frontend (Vercel / .env)
```
REACT_APP_BACKEND_URL=https://api.maintrix.com.br
```

> Nenhuma outra variavel e necessaria no frontend. Todas as chaves sensiveis ficam exclusivamente no backend.

---

## 4. PROCEDIMENTO DE BACKUP

### 4.1 MongoDB Atlas (Recomendado)
- **Backup automatico:** MongoDB Atlas faz snapshots diarios automaticos (retencao de 7 dias no plano gratuito, configuravel em planos pagos)
- **Backup manual:**
```bash
# Instalar mongodump (MongoDB Database Tools)
mongodump --uri="mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/maintrix_production" \
  --out=/backup/$(date +%Y%m%d_%H%M%S)
```
- **Frequencia recomendada:** Diario (noturno) + antes de cada deploy
- **Armazenamento:** S3 bucket ou disco externo

### 4.2 MongoDB Local (Desenvolvimento)
```bash
mongodump --db maintrix_production --out /backup/$(date +%Y%m%d)
```

### 4.3 Supabase Auth
- Backup automatico diario pelo Supabase (Dashboard > Database > Backups)
- Para backup manual: `supabase db dump` via CLI

### 4.4 Uploads/Attachments
```bash
# Se usando disco local no Railway
tar -czf uploads_$(date +%Y%m%d).tar.gz /app/backend/uploads/
# Transferir para storage externo (S3, etc)
```

---

## 5. PROCEDIMENTO DE RESTORE

### 5.1 MongoDB
```bash
# Restore completo
mongorestore --uri="mongodb+srv://<user>:<pass>@<cluster>.mongodb.net" \
  --db maintrix_production \
  /backup/YYYYMMDD/maintrix_production

# Restore de collection especifica
mongorestore --uri="<connection-string>" \
  --db maintrix_production \
  --collection ordens_servico \
  /backup/YYYYMMDD/maintrix_production/ordens_servico.bson
```

### 5.2 Supabase Auth
- Via Dashboard: Database > Backups > Restore
- Via CLI: `supabase db restore <backup-file>`

### 5.3 Uploads
```bash
tar -xzf uploads_YYYYMMDD.tar.gz -C /app/backend/
```

### 5.4 Tempo Estimado de Restore
| Cenario | Tempo |
|---------|-------|
| DB < 1GB | < 5 min |
| DB 1-10GB | 5-30 min |
| Supabase Auth | < 30 min |
| Uploads (100MB) | < 2 min |

---

## 6. PROCEDIMENTO DE ROLLBACK

### 6.1 Rollback de Codigo (Frontend - Vercel)
1. Acessar Vercel Dashboard > Deployments
2. Encontrar o deploy anterior funcionando
3. Clicar nos 3 pontos > "Promote to Production"
4. Deploy anterior sera restaurado em < 1 minuto

### 6.2 Rollback de Codigo (Backend - Railway)
1. Acessar Railway Dashboard > Deployments
2. Clicar no deploy anterior
3. "Redeploy" para restaurar a versao anterior
4. Backend sera reiniciado em < 2 minutos

### 6.3 Rollback de Codigo (Git)
```bash
# Ver historico de commits
git log --oneline -20

# Reverter para commit especifico (cria novo commit)
git revert <commit-hash>
git push origin main

# OU criar branch de hotfix
git checkout -b hotfix/rollback <commit-hash>
git push origin hotfix/rollback
# Fazer deploy da branch hotfix
```

### 6.4 Rollback de Dados (MongoDB)
```bash
# 1. Parar o backend (Railway > Pause service)
# 2. Restore do backup
mongorestore --drop --uri="<connection-string>" \
  --db maintrix_production \
  /backup/YYYYMMDD/maintrix_production
# 3. Reiniciar o backend
```

### 6.5 Rollback na Plataforma Emergent
- Usar o botao "Rollback" no chat Emergent (gratuito)
- Selecionar o checkpoint desejado
- O ambiente sera restaurado automaticamente

---

## 7. PROCEDIMENTO DE ATUALIZACAO SEM PERDA DE DADOS

### 7.1 Pre-Atualizacao
```bash
# 1. Backup completo do banco
mongodump --uri="<connection-string>" --out=/backup/pre_update_$(date +%Y%m%d)

# 2. Backup dos uploads
tar -czf uploads_pre_update.tar.gz /app/backend/uploads/

# 3. Anotar versao atual
git describe --tags
```

### 7.2 Atualizacao do Backend
```bash
# 1. Testar localmente
cd backend
pip install -r requirements.txt
python -c "from server import app; print('OK')"

# 2. Push para GitHub
git add .
git commit -m "v1.0.x - descricao da atualizacao"
git push origin main

# 3. Railway fara deploy automatico (se configurado com auto-deploy)
# Ou fazer deploy manual no Railway Dashboard
```

### 7.3 Atualizacao do Frontend
```bash
# 1. Testar build localmente
cd frontend
yarn install
yarn build

# 2. Push para GitHub (Vercel fara deploy automatico)
```

### 7.4 Migracoes de Banco (Se Necessario)
```python
# Exemplo: adicionar campo novo a todos os documentos
# Criar script migration_001.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate():
    client = AsyncIOMotorClient("mongodb+srv://...")
    db = client["maintrix_production"]
    
    # Adicionar campo com valor padrao
    result = await db.ativos.update_many(
        {"novo_campo": {"$exists": False}},
        {"$set": {"novo_campo": "valor_padrao"}}
    )
    print(f"Atualizados: {result.modified_count}")

asyncio.run(migrate())
```

### 7.5 Checklist Pos-Atualizacao
- [ ] Verificar logs do backend (Railway > Logs)
- [ ] Testar login
- [ ] Verificar dashboard carrega
- [ ] Testar criacao de OS
- [ ] Verificar export funciona
- [ ] Monitorar por 30 minutos

### 7.6 Rollback de Emergencia
Se algo der errado:
1. Rollback do codigo (Secao 6.1/6.2)
2. Se necessario, restore do banco (Secao 5.1)
3. Comunicar equipe ASTEC

---

## RESUMO DE CONTATOS E ACESSOS

| Servico | URL | Funcao |
|---------|-----|--------|
| GitHub | github.com/<repo> | Codigo fonte |
| MongoDB Atlas | cloud.mongodb.com | Banco de dados |
| Supabase | supabase.com/dashboard | Autenticacao |
| Railway | railway.app | Backend hosting |
| Vercel | vercel.com | Frontend hosting |
| DNS | Registrador de dominio | Dominios |

---

*Documento gerado automaticamente. Versao 1.0 - Fevereiro 2026*
