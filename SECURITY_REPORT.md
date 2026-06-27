# MAINTRIX OMNI — RELATÓRIO DE SEGURANÇA E PRODUÇÃO (Bloco 5)
## Data: 21/06/2026

---

## 1. VALIDAÇÃO DE PERMISSÕES (RBAC)

### TÉCNICO
| Ação | Resultado | Status |
|------|-----------|--------|
| DELETE Ativo | 403 | ✅ |
| DELETE Estoque | 403 | ✅ |
| DELETE Sobressalente | 403 | ✅ |
| DELETE OS | 403 | ✅ |
| DELETE Inspeção | 403 | ✅ |

### PCM — NÃO PODE
| Ação | Resultado | Status |
|------|-----------|--------|
| Iniciar OS | 403 | ✅ |
| Concluir OS | 403 | ✅ |
| Pausar OS | 403 | ✅ |
| Executar Inspeção | 403 | ✅ |

### PCM — PODE
| Ação | Resultado | Status |
|------|-----------|--------|
| Editar OS | 200 | ✅ |
| Criar OS | 200 | ✅ |
| Exportar | 200 | ✅ |
| Planejar (Kanban) | 200 | ✅ |

### GERENTE/SUPERVISOR
| Ação | Resultado | Status |
|------|-----------|--------|
| Alterar Estoque | 403 | ✅ |
| Criar Estoque | 403 | ✅ |
| Alterar Sobressalente | 403 | ✅ |

---

## 2. VALIDAÇÃO DE SEGURANÇA API (Cross-Org)

| Teste | Resultado | Status |
|-------|-----------|--------|
| ASTEC GET ativo VALE | 404 | ✅ |
| ASTEC GET OS VALE | 404 | ✅ |
| ASTEC GET histórico VALE | 404 | ✅ |
| VALE PUT ativo ASTEC | 404 | ✅ |
| VALE GET histórico ASTEC | 404 | ✅ |
| Export ASTEC contém só dados ASTEC | 1 ativo | ✅ |

### Bugs encontrados e corrigidos:
- **PUT /api/ativos/{id}** não verificava org → Corrigido com `verify_org_access`
- **GET /api/ativos/{id}/historico** não verificava org → Corrigido
- **PUT/POST /api/estoque** permitia Supervisor → Corrigido (agora ['admin','pcm'])

---

## 3. BACKUP E RECUPERAÇÃO

### MongoDB (Motor/Local)
- **Backup:** `mongodump --db test_database --out /backup/$(date +%Y%m%d)`
- **Restore:** `mongorestore --db test_database /backup/YYYYMMDD/test_database`
- **Frequência recomendada:** Diário (noturno) + antes de cada deploy
- **Tempo estimado:** < 5 min para bases < 10GB

### Supabase (Auth)
- **Backup:** Supabase Dashboard → Database → Backups (automático diário)
- **Restore:** Via Dashboard ou CLI `supabase db restore`
- **Frequência:** Automática (Supabase gerencia)
- **RTO estimado:** < 30 min

---

## 4. PREPARAÇÃO DEPLOY

### GitHub
- Branch principal: `main` (97 commits)
- Tag recomendada: `v1.0.0-pilot`
- Estratégia: Merge via "Save to GitHub", tag após aprovação do piloto

### Variáveis de Ambiente

#### Backend (Railway/VPS)
```
MONGO_URL=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/<db>
DB_NAME=manutrix_production
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<service_role_key>
JWT_SECRET=<random-256-bit-key>
```

#### Frontend (Vercel)
```
REACT_APP_BACKEND_URL=https://api.manutrix.com.br
```

### Deploy Steps
1. **MongoDB Atlas:** Criar cluster, importar dados do piloto
2. **Railway:** Deploy backend via GitHub, configurar env vars
3. **Vercel:** Deploy frontend via GitHub, configurar REACT_APP_BACKEND_URL
4. **Domínio:** Configurar DNS A/CNAME para api.manutrix.com.br e app.manutrix.com.br
5. **SSL:** Automático via Railway/Vercel

---

## 5. CHECKLIST FINAL — PILOTO ASTEC

| Item | Status | Observação |
|------|--------|------------|
| **INFRAESTRUTURA** | | |
| Backend FastAPI | ✅ OK | Python 3.11, Motor async |
| Frontend React PWA | ✅ OK | Offline-first, Service Worker |
| MongoDB | ✅ OK | Todas as collections com índices |
| Supabase Auth | ✅ OK | Login + bcrypt fallback |
| **SEGURANÇA** | | |
| RBAC (4 perfis) | ✅ OK | Admin, PCM, Técnico, Gerente |
| Isolamento Multiempresa | ✅ OK | verify_org_access em todos endpoints |
| Proteção de APIs | ✅ OK | JWT obrigatório, 403/404 cross-org |
| Auditoria campo-a-campo | ✅ OK | Todas as entidades rastreadas |
| **BANCO** | | |
| Backup documentado | ✅ OK | mongodump + Supabase auto |
| Migração templates → planos | ✅ OK | POST /planos-inspecao/migrar |
| **PERMISSÕES** | | |
| Técnico bloqueado | ✅ OK | Só leitura + execução |
| PCM bloqueado execução | ✅ OK | Não inicia/conclui OS |
| Gerente bloqueado escrita | ✅ OK | Não altera estoque/sobressalentes |
| **MÓDULOS** | | |
| Áreas | ✅ OK | CRUD + isolamento |
| Ativos | ✅ OK | CRUD + QR + histórico |
| Ordens de Serviço | ✅ OK | Kanban + rastreabilidade |
| Inspeções | ✅ OK | Planos de inspeção 2 níveis |
| Anomalias | ✅ OK | Workflow completo |
| Estoque | ✅ OK | Movimentação + bloqueio negativo |
| Sobressalentes | ✅ OK | Condições + reformas + export |
| Paradas Programadas | ✅ OK | Indicadores + OS vinculadas |
| Materiais em OS | ✅ OK | Consumo + devolução + auditoria |
| **FUNCIONALIDADES** | | |
| Export Excel | ✅ OK | Todos os módulos |
| Export PDF | ✅ OK | Sobressalentes + auditoria |
| QR Code | ✅ OK | URL format + scanner |
| Histórico filtrado | ✅ OK | 5 filtros + 5 tipos de evento |
| Auditoria | ✅ OK | Login + CRUD + campo-a-campo |
| **DEPLOY** | | |
| GitHub | ✅ OK | Branch main, 97 commits |
| Supabase | ⏳ PENDENTE | Configurar projeto produção |
| Railway/VPS | ⏳ PENDENTE | Deploy backend |
| Vercel | ⏳ PENDENTE | Deploy frontend |
| Domínio | ⏳ PENDENTE | DNS configuração |
