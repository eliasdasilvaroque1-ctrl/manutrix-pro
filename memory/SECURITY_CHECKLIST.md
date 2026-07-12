# SECURITY CHECKLIST — MAINTRIX v5.2.0-RC2

**Data:** 2026-07-12  

---

## Headers HTTP
- [x] X-Content-Type-Options: nosniff
- [x] X-Frame-Options: DENY
- [x] X-XSS-Protection: 1; mode=block
- [x] Referrer-Policy: strict-origin-when-cross-origin
- [x] Permissions-Policy configurado
- [x] Strict-Transport-Security (HSTS)
- [ ] HSTS preload directive
- [ ] Content-Security-Policy (CSP)

## Autenticação
- [x] bcrypt para hashing de senhas
- [x] JWT com expiração (24h)
- [x] JWT secret via env var (64 chars)
- [x] Rate limit no login (10/min)
- [x] Rate limit no forgot-password (3/min)
- [x] Reset token single-use + TTL
- [x] force_password_change no bootstrap
- [ ] Account lockout após N tentativas
- [ ] Password complexity validation
- [ ] JWT refresh token
- [ ] JWT blacklist/revogação

## Autorização (RBAC)
- [x] Matriz centralizada (30+ permissões)
- [x] 12 roles especializados
- [x] Organization isolation em todas as queries
- [x] verify_org_access() para acesso cross-tenant
- [x] Admin-only protegido com check_admin_only()
- [x] Seed endpoints protegidos com auth
- [x] Visibility scoping por área/disciplina

## CORS
- [ ] Origins restritos (atualmente wildcard `*`)
- [ ] Methods restritos (atualmente `["*"]`)
- [ ] Headers restritos (atualmente `["*"]`)
- [x] allow_credentials configurado
- [x] CORS_ORIGINS via env var

## Proteção contra Ataques
- [x] XSS: React auto-escaping + zero dangerouslySetInnerHTML
- [x] CSRF: JWT via Bearer header (imune)
- [x] Clickjacking: X-Frame-Options DENY
- [x] MIME sniffing: X-Content-Type-Options nosniff
- [ ] CSP: script-src, style-src, connect-src
- [x] NoSQL injection: Sem $where/eval
- [x] Path traversal: pathlib resolve

## File Upload
- [x] Upload requer autenticação
- [x] UUID para nome de arquivo local
- [ ] File size limit explícito
- [ ] Content-type validation (magic bytes)
- [ ] File access control (uploads públicos)
- [ ] Filename sanitization completa

## Rate Limiting
- [x] Auth endpoints protegidos
- [x] Upload endpoint protegido
- [x] Public endpoints protegidos
- [ ] Rate limit persistente (MongoDB-backed)
- [ ] Rate limit em endpoints de dados (GET)
- [x] Resposta 429 padronizada

## Secrets & Config
- [x] JWT_SECRET via env var
- [x] MONGO_URL via env var
- [x] .env no .gitignore
- [ ] Remover passwords hardcoded do seed
- [ ] Sanitizar error messages (IA endpoint)

## Logging & Monitoring
- [x] Logs JSON estruturados
- [x] Request ID por requisição
- [x] Tempo de resposta em cada request
- [x] Auth events (login/logout/denied)
- [x] Rate limit events
- [x] Exception logging com stack trace
- [x] Health check endpoint
- [x] System status endpoint (admin-only)

## Compliance (LGPD)
- [x] ConsentGate modal
- [x] Termos de uso documentados
- [x] Política de privacidade documentada
- [x] Consent tracking com versão/IP
- [x] Exportação de dados (Excel/PDF)
- [ ] Data purge/anonimização automática

## Dependências
- [x] Python deps atualizadas (FastAPI, bcrypt, PyJWT)
- [ ] Atualizar uvicorn (0.25 → 0.34+)
- [ ] NPM audit: 234 vulns (maioria dev-only)

---

**Resumo:** 37 de 52 itens conformes (71%)
