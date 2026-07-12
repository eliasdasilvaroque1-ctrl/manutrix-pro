# CHANGELOG — MAINTRIX Enterprise

## v5.2.0-RC2.4.2 (2026-07-12) — "Security & Observability"

### RC2.1 — Correção de Regressões da Modularização
- 7 regressões corrigidas em páginas extraídas (Estoque, Inspeções, Sobressalentes, Paradas, Biblioteca, Equipe, ProtectedRoute)
- Componentes movidos do App.js: `ModalNovoEstoque`, `ModalNovaInspecao`, `CameraCapture`
- Constantes relocadas: `ORIGEM_OPTIONS`, `CONDICAO_CONFIG`, `PARADA_TIPOS`, `FIELD_TYPES`
- App.js: 4.541 → 3.950 linhas (redução adicional de 591 linhas)
- Quality Gate: build PASS, 17/17 rotas, zero ReferenceError

### RC2.2 Bloco P0 — Confiabilidade & Observabilidade
- Logging JSON estruturado (timestamp, request_id, duration_ms, IP, status_code)
- Middleware de observabilidade: `X-Request-Id` e `X-Response-Time` em todas as respostas
- Global Exception Handler (backend → JSON padronizado, nunca mais crash sem resposta)
- Error Boundary (frontend → página amigável "Algo deu errado", elimina tela branca)
- `GET /api/health` — público, DB ping + latência, retorna 503 quando degradado
- `GET /api/system/status` — admin-only: version, uptime, git commit, memória, CPU, status de serviços
- Dependência: `psutil` 7.2.2
- API version: v5.2.0-RC1 → v5.2.0-RC2

### RC2.3 — Security Audit (somente leitura)
- Auditoria completa de 20 vetores de segurança
- Score baseline: 68/100
- 3 críticos, 5 altos, 6 médios, 3 baixos identificados
- Documentos: `SECURITY_AUDIT.md`, `SECURITY_CHECKLIST.md`, `SECURITY_ROADMAP.md`

### RC2.4 — Security Phase 1 (Críticos)
- **CSP**: Content-Security-Policy adicionado (default-src, script-src, style-src, connect-src, img-src, font-src, frame-ancestors, base-uri, form-action)
- **CORS**: Origins restritos para domínios oficiais (Vercel, Railway, localhost), methods e headers explícitos
- **Upload Hardening**: Limite 10MB, validação magic bytes, `_validate_file()` centralizado em 4 endpoints
- **Error Sanitization**: Removido `str(e)` do endpoint IA — stack trace apenas nos logs
- **HSTS**: Adicionado `preload` directive

### RC2.4.1 — Production Readiness Check (somente leitura)
- Identificado bloqueador: auth em endpoints GET de servir arquivos quebrava `<img src>` (15+ locais)
- CSP validado como seguro (aplicado apenas em respostas JSON API)
- Documento: `PRODUCTION_READINESS.md`

### RC2.4.2 — File Security Redesign
- **Modelo UUID-Based Access**: arquivos públicos com UUID v4 (122 bits entropia) + rate limit 60/min/IP
- Endpoints GET (servir arquivos): públicos com rate limit e logging
- Endpoints POST (upload): auth JWT + size limit 10MB + magic bytes
- Endpoints Export: auth JWT + RBAC admin/supervisor
- Logo sidebar, thumbnails e fotos carregam corretamente
- Score de segurança: 68 → 79/100
- Documentos: `FILE_SECURITY_DESIGN.md`, `FILE_SECURITY_MATRIX.md`

### Débitos Técnicos Atualizados
- ~~App.js monolítico (10.855 linhas)~~ → 3.950 linhas (redução 64%)
- Rate limiter in-memory (não distribuído) — planejado para Fase 3
- ~~CSP header não implementado~~ → implementado em respostas API
- ~~CORS aberto (allow_origins=*)~~ → restrito para domínios oficiais
- Fotos offline com entityId temporário
- Login offline não suportado (requer servidor)
- Account lockout ausente — planejado para Fase 2
- Password complexity ausente — planejado para Fase 2

---

## v5.2.0-RC1 (2026-07-12) — "ASTEC Pilot Release"

### BLOCO A — Auditoria e Limpeza (2026-07-11)
- Removidos 6 componentes mortos do App.js (AssetIdentity, KPICard, FilterBar, CardSection, SectionDivider, NotificationBell) — -204 linhas
- Removidos 10 ícones Lucide não utilizados, 3 React imports órfãos
- Removidos imports mortos no backend (hashlib, random, string, json de server.py; json de dashboard.py)
- Corrigidas 3 bare `except:` em events.py → `except Exception:`
- Aplicado `React.memo` em 10 componentes presentacionais
- Adicionados `memo`, `useCallback`, `useMemo` ao import React
- Regressão: 33/33 PASS

### BLOCO B — PWA/Offline (2026-07-11)
- Reescrito `offlineQueue.js` — 3 IndexedDB stores (pending_operations, cached_data, pending_photos)
- 8 novas operações offline: iniciar/pausar/concluir OS, status change Kanban, HH manual, finalizar rápido, iniciar/concluir inspeção
- Cache automático de dados via interceptor axios (10 rotas de campo)
- Armazenamento offline de fotos como ArrayBuffer no IndexedDB
- Sync engine com exponential backoff, ordenação por prioridade, dedup de status changes
- Service Worker v3 → v4 (15 rotas API cacheadas)
- Regressão: 33/33 PASS

### BLOCO C — Hardening Enterprise (2026-07-11)
- Rate Limiting middleware: login 10/min, forgot-password 3/min, upload 30/min, public 120/min
- Security Headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, X-XSS-Protection, HSTS
- 14 MongoDB indexes criados (total: 69 customizados)
- Request timeout global 120s
- Logging padronizado: AUTH_OK/AUTH_FAIL com IP, UPLOAD com tamanho, RATE_LIMIT, TIMEOUT
- API version: v5.1.0 → v5.2.0-RC1
- Regressão: 31/31 PASS

### BLOCO D — Certificação RC1 (2026-07-11)
- 58 testes de certificação executados: Auth(7), Multi-tenant(8), Ativos(4), OS(6), Inspeções(2), Dashboard(3), PWA(8), Performance(10), Segurança(4), Banco(4), UX(20/20 rotas)
- Fix: Botão "INICIAR OS" visível para status `programada` e `disponivel`
- Performance: todos endpoints < 320ms
- Parecer: GO — Apto para piloto ASTEC

### RC1.5 — Compliance, LGPD e Preparação Comercial (2026-07-11)
- Termos de Uso v1.0 (`/compliance/termos_de_uso.md`)
- Política de Privacidade v1.0 — LGPD compliant (`/compliance/politica_privacidade.md`)
- Modal de aceite obrigatório (ConsentGate) no primeiro acesso
- Registro versionado do aceite (user, org, IP, user-agent, versão) na coleção `consents`
- Mecanismo de reaceite automático quando versão mudar
- Página "Sobre o MAINTRIX" com versão, build, contato
- Footer permanente: Termos | Privacidade | Sobre | v5.2.0-RC1
- Documentação: `/compliance/` (4 docs) + `/commercial/` (2 docs)

### Modularização (2026-07-12)
- Extraídos 14 componentes UI para `/components/shared/index.js` (190 linhas)
- App.js: 11.040 → 10.855 linhas (-185)
- Componentes: StatusBadge, PriorityBadge, Modal, ConfirmDialog, Loading, EmptyState, DataTable, DataRow, PageContainer, PageHeader, PageToolbar, FormInput, Select, SearchInput

### Pipeline & Deploy (2026-07-12)
- requirements.txt limpo: 144 → 24 pacotes (apenas deps diretas)
- Removido `emergentintegrations` (private index — fallback graceful no código)
- `bcrypt>=4.3.0` para compatibilidade Python 3.13
- Fix: paths de compliance relativos ao projeto (funciona em Railway)
- Frontend deployado na Vercel (auto-deploy)
- Backend deployado no Railway (v5.2.0-RC1)
- Script de validação: `/app/scripts/validate_deploy.py`
- DEPLOY_CHECKLIST.md criado

---

## v5.1.0 (2026-07-02) — "Pre-RC1"
- Versão base antes da estabilização
- Design System Enterprise (CSS variables, PageContainer, PageToolbar)
- ORR (Operational Readiness Review) aprovado
- Gates 1-4.5 (Security, UX, Performance, Data Consistency) completados
