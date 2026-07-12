# PRODUCTION READINESS — RC2.4.1

**Data:** 2026-07-12  
**Escopo:** Verificação de compatibilidade produção das mudanças de segurança RC2.4  
**Status:** 🔴 **BLOQUEADOR ENCONTRADO — NÃO APTO PARA PRODUÇÃO SEM CORREÇÃO**

---

## 1. CSP (Content-Security-Policy)

### Achado
O CSP é aplicado apenas nas respostas da API (FastAPI/backend). O documento HTML é servido por um servidor Express separado (porta 3000) que **não inclui CSP**.

| Resposta | CSP presente? |
|----------|--------------|
| `GET /` (HTML, servido pelo Express/Vercel) | ❌ Não |
| `GET /api/*` (JSON, servido pelo FastAPI) | ✅ Sim |

### Impacto em Produção
- **Vercel (frontend):** CSP precisa ser configurado via `vercel.json` headers — está FORA do controle do backend
- **Railway (backend):** CSP nas respostas JSON é cosmético — JSON não é renderizado como HTML pelo browser

### Risco de Indisponibilidade
**Nenhum.** O CSP em respostas JSON não bloqueia nenhum recurso do frontend.

### Risco de Ineficácia
**Alto.** O CSP atual não protege o documento HTML contra XSS. Para proteção real, precisa ser configurado no Vercel (headers) ou como `<meta http-equiv="Content-Security-Policy">` no `index.html`.

### ⚠️ Se o CSP FOSSE aplicado ao HTML (futuro)
Os seguintes recursos seriam bloqueados e precisariam de ajustes:

| Recurso | CSP Directive | Bloqueado? | Correção necessária |
|---------|--------------|-----------|-------------------|
| Inline `<script>` (index.html L17) | `script-src 'self'` | 🔴 Sim | Adicionar hash SHA-256 ou mover para arquivo externo |
| Google Fonts CSS | `style-src 'self' 'unsafe-inline'` | 🔴 Sim | Adicionar `https://fonts.googleapis.com` |
| Google Fonts arquivos | `font-src 'self' data:` | 🔴 Sim | Adicionar `https://fonts.gstatic.com` |
| CSS @import (index.css) | `style-src` | 🔴 Sim | Adicionar `https://fonts.googleapis.com` |
| Service Worker | `worker-src` (fallback `script-src 'self'`) | ✅ Não | Same-origin, OK |
| jsQR dynamic import | `script-src 'self'` | ✅ Não | Same-origin chunk, OK |
| Camera getUserMedia | N/A (Permissions-Policy) | ✅ Não | Já permitido `camera=(self)` |

**Conclusão CSP:** Seguro para deploy. Não causa indisponibilidade. Não oferece proteção efetiva no HTML (melhoria futura via Vercel headers).

---

## 2. CORS

### Configuração Atual
```
CORS_ORIGINS=https://procure-manutrix.preview.emergentagent.com,https://maintrix.vercel.app,http://localhost:3000
allow_methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"]
allow_headers=["Authorization","Content-Type","X-Request-Id","X-Requested-With"]
```

### Teste de Compatibilidade

| Ambiente | Origin | Status |
|----------|--------|--------|
| Emergent Preview | `https://procure-manutrix.preview.emergentagent.com` | ✅ Listado (mas proxy sobrescreve com `*`) |
| Vercel Produção | `https://maintrix.vercel.app` | ✅ Listado |
| Localhost Dev | `http://localhost:3000` | ✅ Listado |
| Railway (backend same-origin) | N/A | ✅ Same-origin não precisa CORS |

### Risco de Indisponibilidade
**Baixo.** Os 3 domínios oficiais estão listados. Se o cliente usar domínio customizado (ex: `app.cliente.com.br`), precisará ser adicionado ao `CORS_ORIGINS`.

### Nota sobre Preview
O proxy Kubernetes/Cloudflare do Emergent Preview sobrescreve CORS headers com wildcard. Em Railway e Vercel, o backend controla CORS diretamente.

---

## 3. HSTS

### Configuração
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

- Aplicado somente quando hostname ≠ localhost/127.0.0.1
- `preload` requer submissão manual em hstspreload.org (não automático)

### Risco de Indisponibilidade
**Nenhum.** HSTS é aplicado apenas em HTTPS. Todos os ambientes de produção usam HTTPS.

---

## 4. Upload Autenticado — 🔴 BLOQUEADOR

### Achado Crítico
Os endpoints de servir arquivos agora exigem `Depends(get_current_user)`:
- `GET /api/uploads/{filename}` — requer auth
- `GET /api/uploads/manuals/{filename}` — requer auth
- `GET /api/storage/{path}` — requer auth

**Porém, o frontend carrega imagens via `<img src={url}>`.** Tags `<img>` fazem requests HTTP GET puros — **sem header `Authorization`**.

### Locais afetados (15+ ocorrências):

| Componente | Arquivo | Uso |
|-----------|---------|-----|
| Logo sidebar | `App.js` | Logo da organização |
| MaterialThumbnail | `MaterialComponents.js` (L32, L114, L172) | Thumbnails de materiais/sobressalentes |
| MaterialImageModal | `MaterialComponents.js` | Imagem fullscreen |
| Fotos de inspeção | `InspecoesPages.js` (L1309, L1312) | Fotos capturadas durante inspeção |
| Attachments OS | `App.js` (L1717, L1811) | Anexos de ordens de serviço |
| Portal Público | `PortalPages.js` (L62, L75, L272) | Logo e fotos de ativos |
| White Label | `WhiteLabelDesignerPage.js` (L53, L83, L110, L293, L551, L577) | Logos customizados |

### Evidência
Screenshot do preview mostra logo da organização quebrado no sidebar (retorna 401 para `<img>` sem auth header).

### Risco de Indisponibilidade
**🔴 CRÍTICO — TODAS as imagens e logos do sistema ficarão invisíveis em produção.**

### Solução Recomendada
Reverter a autenticação nos 3 endpoints de servir arquivos. As URLs já usam UUIDs aleatórios (v4), tornando-as efetivamente inacessíveis sem conhecer o caminho exato. Esta é a abordagem padrão para servir arquivos em apps com auth JWT:

| Endpoint | Recomendação |
|----------|-------------|
| `GET /api/uploads/{filename}` | Remover auth (UUID garante segurança) |
| `GET /api/uploads/manuals/{filename}` | Remover auth (UUID garante segurança) |
| `GET /api/storage/{path}` | Remover auth (path inclui UUID) |
| `POST /api/upload` | Manter auth ✅ |

**Alternativa futura (Fase 3):** Signed URLs com expiração (ex: `/api/storage/{path}?token={hmac}&expires={ts}`).

---

## 5. Login, Navegação & Rotas

| Teste | Status |
|-------|--------|
| Login completo (org + email + password) | ✅ OK |
| ConsentGate modal | ✅ OK |
| 17/17 rotas navegáveis | ✅ OK |
| PAGE ERROR no console | ✅ Zero |
| React component errors | ✅ Zero |
| Refresh de página | ✅ OK |

---

## 6. `CI=true yarn build`

| Critério | Status |
|----------|--------|
| Compilação | ✅ PASS |
| Warnings | ✅ Zero |
| Errors | ✅ Zero |

---

## 7. Compatibilidade com Browsers

| Browser | Compatibilidade |
|---------|----------------|
| Chrome 90+ | ✅ CSP, CORS, HSTS suportados |
| Firefox 90+ | ✅ Suportado |
| Safari 15+ | ✅ Suportado |
| Edge 90+ | ✅ Suportado |
| Mobile Chrome/Safari | ✅ Suportado |

---

## VEREDICTO

### 🔴 NÃO APTO para produção sem correção

**Bloqueador:** A autenticação nos endpoints de servir arquivos (`/uploads/`, `/manuals/`, `/storage/`) quebra TODAS as imagens do sistema (15+ locais no frontend usam `<img src>` que não envia auth headers).

### Ação Necessária Antes do Deploy

| # | Ação | Prioridade | Esforço |
|---|------|-----------|---------|
| 1 | Reverter auth nos endpoints GET de servir arquivos | 🔴 Obrigatório | 5 min |
| 2 | Manter auth no endpoint POST de upload | ✅ Já implementado | 0 |
| 3 | Validar imagens após revert | 🔴 Obrigatório | 5 min |

### O Que Está Seguro para Deploy (após correção do bloqueador)
- ✅ CSP no backend (seguro, sem impacto)
- ✅ CORS restritivo (domínios oficiais listados)
- ✅ HSTS com preload
- ✅ Upload hardening (size limit, magic bytes, type validation)
- ✅ Error detail sanitization
- ✅ File upload POST protegido com auth

### Próximo Passo
Aguardando autorização do CTO para reverter a auth nos endpoints GET de servir arquivos.

---

*Documento gerado como parte da verificação de produção RC2.4.1. Nenhum código alterado nesta fase.*
