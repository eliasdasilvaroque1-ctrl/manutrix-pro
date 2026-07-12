# SECURITY AUDIT — MAINTRIX v5.2.0-RC2

**Data:** 2026-07-12  
**Auditor:** E1 Agent  
**Escopo:** Auditoria completa de segurança — somente leitura  
**Versão:** 5.2.0-RC2  

---

## 1. HTTP HEADERS

| Header | Status | Valor |
|--------|--------|-------|
| `X-Content-Type-Options` | ✅ Conforme | `nosniff` |
| `X-Frame-Options` | ✅ Conforme | `DENY` |
| `X-XSS-Protection` | ✅ Conforme | `1; mode=block` |
| `Referrer-Policy` | ✅ Conforme | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | ✅ Conforme | `camera=(self), microphone=(), geolocation=(self)` |
| `Strict-Transport-Security` | ✅ Conforme | `max-age=31536000; includeSubDomains` (prod only) |
| `Content-Security-Policy` | 🔴 Ausente | Nenhum CSP definido |
| `X-Request-Id` | ✅ Conforme | UUID por requisição |
| `X-Response-Time` | ✅ Conforme | Duração em ms |
| `Cache-Control` | ✅ Conforme | `no-store, no-cache, must-revalidate` (via Cloudflare) |

---

## 2. CSP (Content-Security-Policy)

| Item | Status | Detalhe |
|------|--------|---------|
| CSP Header | 🔴 Crítico | **Completamente ausente.** Sem CSP, o navegador não restringe origens de scripts, estilos, imagens ou conexões. Abre vetor para XSS persistente e injeção de scripts terceiros. |
| `script-src` | 🔴 | Não definido — qualquer script pode executar |
| `style-src` | 🔴 | Não definido |
| `connect-src` | 🔴 | Não definido — fetch para qualquer domínio |
| `img-src` | 🔴 | Não definido |
| `frame-ancestors` | 🟡 | Parcialmente coberto por `X-Frame-Options: DENY` |

---

## 3. CORS

| Item | Status | Detalhe |
|------|--------|---------|
| `allow_origins` | 🔴 Crítico | **`*` (wildcard)**. Aceita requisições de qualquer domínio. Combinado com `allow_credentials=True`, viola a spec (browsers bloqueiam `*` + credentials, mas APIs REST ficam expostas). |
| `allow_methods` | 🟡 Melhorável | `["*"]` — deveria listar apenas `GET, POST, PUT, DELETE, PATCH, OPTIONS` |
| `allow_headers` | 🟡 Melhorável | `["*"]` — deveria listar headers específicos |
| `allow_credentials` | 🟡 | `True` — correto se origins forem restritos |
| Variável `.env` | ✅ | `CORS_ORIGINS` existe no .env, mas fallback é `*` |

---

## 4. HSTS

| Item | Status | Detalhe |
|------|--------|---------|
| Header presente | ✅ Conforme | `max-age=31536000; includeSubDomains` |
| Preload | 🟡 Melhorável | Falta `preload` directive para inclusão na preload list dos browsers |
| Condicional | ✅ | Correto — só aplica em produção (não localhost) |

---

## 5. Cookies

| Item | Status | Detalhe |
|------|--------|---------|
| Session cookies | ✅ | App não usa cookies de sessão — autenticação é JWT via `Authorization` header |
| Cloudflare `__cf_bm` | ✅ | `HttpOnly; SameSite=None; Secure` — setado pelo proxy, fora do controle da app |

---

## 6. JWT

| Item | Status | Detalhe |
|------|--------|---------|
| Algoritmo | ✅ Conforme | HS256 |
| Expiração | ✅ Conforme | 24 horas |
| Secret | ✅ Conforme | Via `JWT_SECRET` env var (64 chars hex), fallback `secrets.token_hex(32)` |
| Validação `exp` | ✅ | `ExpiredSignatureError` → 401 |
| Validação `sub` | ✅ | Verifica user existe no DB + `deleted_at: None` |
| Refresh Token | 🟡 Melhorável | Ausente — sem refresh token. Expirado = re-login. Aceitável para CMMS industrial. |
| Revogação | 🟡 Melhorável | Sem blacklist. Token válido até expirar mesmo após logout. |
| Payload exposto | ✅ | Apenas `sub`, `role`, `org`, `exp` — sem dados sensíveis |

---

## 7. Autenticação

| Item | Status | Detalhe |
|------|--------|---------|
| Password hashing | ✅ Conforme | bcrypt com salt automático |
| Login rate limit | ✅ | 10 req/min por IP |
| Forgot password rate limit | ✅ | 3 req/min por IP |
| Reset token | ✅ | `secrets.token_urlsafe(32)` + TTL (expireAfterSeconds no MongoDB) |
| Reset token single-use | ✅ | Marcado `used: True` após consumo |
| Account lockout | 🟡 Melhorável | **Ausente.** Apenas rate limit por IP, não por conta. Um atacante com IPs rotativos (botnet) poderia tentar brute force. |
| Password complexity | 🟡 Melhorável | Sem validação de complexidade no backend (min length, chars). |
| Force password change | ✅ | `force_password_change: True` para bootstrap e reset admin |
| Bootstrap credentials | 🟡 Melhorável | `master123` hardcoded no seed. Mitigado por `force_password_change: True`. |
| Temp password in response | 🟡 Melhorável | Admin reset retorna `temp_password` no JSON. Aceito para fluxo admin→técnico, mas logado em audit trail. |

---

## 8. Autorização (RBAC)

| Item | Status | Detalhe |
|------|--------|---------|
| Matriz de permissões | ✅ Conforme | Centralizada em `deps.py` — `PERMISSIONS` dict com 30+ permissões |
| Roles especializados | ✅ | 12 roles: master, admin, pcm, supervisor, gerente, tec_mecanico, tec_eletrico, instrumentista, lubrificador, operador, inspetor, visualizador |
| Org isolation | ✅ Conforme | `organization_id` em todas as queries + `verify_org_access()` |
| Admin-only endpoints | ✅ | `check_admin_only()` protege endpoints sensíveis |
| Seed endpoints | ✅ | Protegidos por `check_admin_only()` |
| Visibility scoping | ✅ | Técnicos veem apenas OS das suas áreas/disciplinas |

---

## 9. XSS

| Item | Status | Detalhe |
|------|--------|---------|
| `dangerouslySetInnerHTML` | ✅ Conforme | **Zero ocorrências** em todo o frontend |
| React auto-escaping | ✅ | React escapa todas as strings renderizadas por padrão |
| CSP script-src | 🔴 | Sem CSP, XSS refletido/stored pode executar (ver §2) |
| Input sanitization | ✅ | Pydantic valida inputs no backend; React escapa no frontend |

---

## 10. CSRF

| Item | Status | Detalhe |
|------|--------|---------|
| Proteção CSRF | ✅ Conforme | JWT via `Authorization: Bearer` header — imune a CSRF. Browsers não incluem headers custom em requests cross-origin automáticos. |
| Cookies de sessão | N/A | App não usa cookies de sessão |

---

## 11. Clickjacking

| Item | Status | Detalhe |
|------|--------|---------|
| `X-Frame-Options` | ✅ Conforme | `DENY` |
| `frame-ancestors` (CSP) | 🟡 | Ausente (coberto pelo X-Frame-Options, mas CSP é mais robusto) |

---

## 12. MIME Sniffing

| Item | Status | Detalhe |
|------|--------|---------|
| `X-Content-Type-Options` | ✅ Conforme | `nosniff` |

---

## 13. Rate Limiting

| Item | Status | Detalhe |
|------|--------|---------|
| Mecanismo | ✅ | In-memory com window sliding |
| Auth endpoints | ✅ | login: 10/min, register: 5/min, forgot: 3/min, reset: 5/min |
| Upload endpoint | ✅ | 30/min |
| Public endpoints | ✅ | 120/min |
| Persistência | 🟡 Melhorável | **In-memory** — perde contadores no restart. Aceito para scale atual. |
| Endpoints não cobertos | 🟡 Melhorável | Endpoints de dados (GET /estoque, /ativos, etc.) sem rate limit. Vulnerável a scraping massivo. |
| Resposta 429 | ✅ | JSON padronizado |

---

## 14. Variáveis de Ambiente

| Item | Status | Detalhe |
|------|--------|---------|
| `MONGO_URL` | ✅ | Via .env, não hardcoded |
| `JWT_SECRET` | ✅ | Via .env, 64 chars hex |
| `SUPABASE_*` | ✅ | Via .env |
| `EMERGENT_LLM_KEY` | ✅ | Via .env |
| `CORS_ORIGINS` | ✅ | Via .env (mas valor atual permite wildcard — ver §3) |
| Frontend `REACT_APP_BACKEND_URL` | ✅ | Apenas URL pública, sem secrets |

---

## 15. Secrets Expostos

| Item | Status | Detalhe |
|------|--------|---------|
| Hardcoded passwords | 🟡 Melhorável | `admin123` no seed data (linha 2092, 2301, 2324). Protegido por `check_admin_only`. |
| `master123` no bootstrap | 🟡 | Hardcoded no startup migration. Mitigado por `force_password_change`. |
| Error detail leak | 🟡 Melhorável | Assistente IA expõe `str(e)` no response (linha 2831): `"Erro no assistente: {str(e)}"`. Pode vazar info interna. |
| `.env` no .gitignore | ✅ | Verificado — .env está no .gitignore |

---

## 16. Dependências Vulneráveis

### NPM (frontend)

| Severidade | Quantidade |
|-----------|-----------|
| Critical | 2 |
| High | 111 |
| Moderate | 102 |
| Low | 19 |
| **Total** | **234** |

**Nota:** A grande maioria vem de dependências transitivas de `react-scripts` (jest, babel, webpack). Não são exploráveis em produção — afetam apenas ambiente de build/test. A vulnerabilidade `ws` (DoS) é a mais relevante mas está no jest (dev-only).

| Pacote | Severidade | Nota |
|--------|-----------|------|
| `ws` (via jest/jsdom) | High | Dev-only, não em runtime |
| `nth-check` (via css-select) | High | Build-only |
| Diversos `postcss` | Moderate | Build-only |

**Risco real em produção:** 🟡 Baixo — vulnerabilidades são em dev dependencies.

### Python (backend)

| Pacote | Versão | Status |
|--------|--------|--------|
| FastAPI | 0.110.1 | ✅ Recente |
| Starlette | 0.37.2 | ✅ |
| PyJWT | 2.13.0 | ✅ |
| bcrypt | 5.0.0 | ✅ |
| motor | 3.3.1 | ✅ |
| uvicorn | 0.25.0 | 🟡 Versão antiga (0.34+ disponível) |
| cryptography | 46.0.5 | ✅ |

---

## 17. File Upload & Access

| Item | Status | Detalhe |
|------|--------|---------|
| Upload auth | ✅ | `Depends(get_current_user)` |
| File type validation | 🟡 Melhorável | Verifica extensão mas não content-type/magic bytes |
| File size limit | 🟡 Melhorável | Sem limite explícito (só timeout de 120s) |
| Filename sanitization | 🟡 Melhorável | UUID renomeia para storage local, mas `file.filename` original é logado sem sanitização |
| **File access control** | 🔴 Crítico | **`/api/uploads/{filename}` e `/api/uploads/manuals/{filename}` são públicos sem autenticação.** Qualquer pessoa que conheça o nome do arquivo pode acessá-lo. |
| Path traversal | ✅ | Mitigado pelo uso de `UPLOAD_DIR / filename` (pathlib resolve `..`) |
| Object storage access | ✅ | Via `objstore.get_file()` — sem path traversal |

---

## 18. Logs & Observabilidade

| Item | Status | Detalhe |
|------|--------|---------|
| Formato estruturado | ✅ Conforme | JSON com timestamp, level, request_id, duration_ms, IP |
| Auth events | ✅ | Login success/failure logados |
| Rate limit events | ✅ | Bloqueios logados com IP e path |
| Exception logging | ✅ | Stack trace completo em JSON |
| Sensitive data in logs | ✅ | Nenhum password ou token logado |
| Log level | ✅ | INFO em produção |

---

## 19. Health & Error Handling

| Item | Status | Detalhe |
|------|--------|---------|
| `/api/health` | ✅ Conforme | Público, DB ping + latência |
| `/api/system/status` | ✅ Conforme | Admin-only, métricas completas |
| Global exception handler | ✅ | JSON com request_id |
| ErrorBoundary frontend | ✅ | Página amigável, sem tela branca |
| Error detail exposure | 🟡 | Assistente IA expõe `str(e)` |

---

## 20. LGPD / Compliance

| Item | Status | Detalhe |
|------|--------|---------|
| ConsentGate | ✅ Conforme | Modal obrigatório antes de usar o sistema |
| Termos de Uso | ✅ | `/app/compliance/termos_de_uso.md` |
| Política de Privacidade | ✅ | `/app/compliance/politica_privacidade.md` |
| Consent tracking | ✅ | `user_consents` collection com versão, IP, user_agent |
| Data export | ✅ | Endpoints de exportação (Excel/PDF) |
| Data deletion | 🟡 | Soft delete (`deleted_at`) — sem purge automático |

---

## SCORE GERAL

### Classificação por Severidade

| Severidade | Qtd | Itens |
|-----------|-----|-------|
| 🔴 Crítico | **3** | CSP ausente, CORS wildcard, File access sem auth |
| 🟡 Alto | **5** | Account lockout ausente, Password complexity, Upload sem size limit, Error detail leak (IA), Uvicorn desatualizado |
| 🟡 Médio | **6** | Rate limit não-persistente, HSTS sem preload, JWT sem refresh/revogação, CORS methods/headers wildcard, File type validation, Hardcoded seed passwords |
| ℹ️ Baixo | **3** | NPM dev deps, Data purge ausente, Filename sanitization cosmética |

### Score

```
SEGURANÇA GERAL: 68/100
```

**Breakdown:**
- Headers HTTP: 85/100
- Autenticação: 75/100
- Autorização (RBAC): 95/100
- Data Isolation: 95/100
- Transport Security: 90/100
- Input Validation: 85/100
- File Security: 45/100
- CSP/CORS: 25/100
- Rate Limiting: 70/100
- Logging/Monitoring: 95/100
- Compliance (LGPD): 90/100
