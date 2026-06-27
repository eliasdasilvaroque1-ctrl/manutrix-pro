# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 5.1.0

---

## REBRANDING MANUTRIX → MAINTRIX ✅ (27/06/2026)

### Arquivos Alterados
**Frontend:**
- `public/index.html` — title, meta tags, apple-mobile-web-app-title
- `public/manifest.json` — short_name, name
- `public/service-worker.js` — cache names
- `src/App.js` — UI strings (login, sidebar)
- `src/App.css` — comment
- `src/lib/api.js` — sessionStorage keys (maintrix_token, maintrix_user)
- `src/lib/offlineQueue.js` — IndexedDB name, comment

**Backend:**
- `server.py` — FastAPI title, export filenames, PDF titles, AI prompt
- `org_config.py` — default config strings
- `storage.py` — APP_NAME
- `models.py` — module docstring
- `data_architecture.py` — module docstring
- `migrate_storage.py` — print string

**Domínio preparado:** app.maintrix.com.br

### NÃO alterado
- Collections MongoDB (nomes internos mantidos)
- Endpoints da API (rotas mantidas)
- Emails de usuário (@manutrix.com — são dados, não branding)
- Event sourcing, auditoria, HH, estrutura de banco
