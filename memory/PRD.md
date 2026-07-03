# MAINTRIX ENTERPRISE — Product Requirements Document

## Vision
A highly robust, field-ready CMMS/EAM SaaS platform for industrial maintenance. Each organization experiences a fully white-labeled system as if it were developed exclusively for them.

## Core Architecture
- **Stack**: React PWA (frontend) + FastAPI (backend) + MongoDB
- **Multi-tenant**: `organization_id` isolation across all collections
- **Event-Sourced**: Work Orders use event sourcing for full audit trail
- **White Label**: Dynamic theming via `BrandingContext` + CSS variables per org
- **Auth**: JWT + bcrypt, MongoDB as single source of truth (Supabase bypassed)
- **Storage**: Emergent Object Storage for files/documents

## Key Files
```
/app/backend/server.py          — Main entry, auth routes, middleware
/app/backend/routes/org.py      — Org config, White Label endpoints
/app/backend/org_config.py      — Default config builder, numbering engine
/app/backend/deps.py            — Auth, DB, RBAC logic
/app/frontend/src/App.js        — Monolithic React app (~8600 lines)
/app/frontend/src/lib/branding.js — BrandingContext with race-condition protection
/app/frontend/src/lib/api.js    — Axios API client
/app/frontend/src/index.css     — Tailwind + brand utility CSS classes
/app/frontend/src/App.css       — Base CSS with :root variables
```

## Completed Sprints

### Sprint 63 — FASE 1: White Label Enterprise ✅ (2026-07-03)
- **BrandingProvider** wraps entire app, provides `useBranding()` hook
- **BrandingLoader** loads org branding after auth automatically
- **CSS Variables**: `--brand-primary`, `--brand-secondary`, `--brand-bg`, `--brand-text`, `--brand-accent`, `--brand-menu`, `--brand-login`, `--brand-header` set on `:root`
- **CSS Utility Classes**: `.text-brand`, `.bg-brand-10`, `.bg-brand-20`, `.border-brand`, `.border-brand-30`, `.accent-brand`, `.section-title`, `.tag-brand`, `.tab-active`
- **Race condition fix**: Request versioning (`requestVersion` ref), hostname filtering (`isCustomerSubdomain()`), sessionStorage fallback for authenticated users on hard reload
- **Sidebar**: Dynamic company name, logo, subtitle, active menu color from branding
- **BottomNav**: Dynamic brand color for scan button and active items
- **LoginPage**: Org selector, dynamic branding, company logo display
- **All pages**: KPI cards, section headers, tags, filters, buttons, tabs — all consume brand CSS variables
- **Backend**: Public endpoints (`/api/public/organizations`, `/api/public/branding/{id}`), tema whitelist expanded with `cor_menu`/`cor_login`/`cor_header`
- **Zero hardcoded MAINTRIX** in UI (only "Powered by MAINTRIX" when `mostrar_powered_by=true`)
- **Testing**: Backend 7/7, Frontend 100% pass (hard reload, SPA nav, all pages)

### Earlier Sprints (Completed)
- Sprint 55: Prontuário do Ativo (centralized asset dashboard)
- Sprint 52: Central de Trabalho & Migration
- Aditivo 002: Visibility RBAC
- Sprint de Homologação: ASTEC Cedro seed data, UI filters
- Production Sprints 001-002: Vercel routing, branding cleanup
- Auth Audit: MongoDB-only auth, bypass Supabase
- Bug fixes: Circular structure on Save Plan, HTTP 422 on change-password

## Pending / Backlog (Prioritized)

### FASE 2: Central White Label para MASTER (P0 - Next)
- Admin screen for MASTER to configure White Label per org
- Fields: nome_empresa, nome_exibicao, logo, logo_branca, favicon, cor_primaria, cor_secundaria, cor_menu, cor_login, imagem_fundo, texto_boas_vindas, rodape, mostrar_powered_by, dominio, subdominio, tema
- Upload logo/favicon/wallpaper via Emergent Object Storage
- Live preview of changes
- Changes reflect immediately in the application

### FASE 3: QR Code Enterprise (P0)
- QR Code generator with company logo + QR + TAG + equipment name + "Powered by MAINTRIX"
- Label formats: 50x30, 60x40, 80x50, A4
- Uses organization's visual identity automatically

### FASE 4: Portal Público do Equipamento (P0)
- Read-only public page accessible via QR code scan (no auth)
- Shows: Foto, TAG, Nome, Área, Fabricante, Modelo, Manual, Últimas inspeções, Últimas manutenções, Últimas OS, Disponibilidade

### FASE 5: Portal do Técnico (P0)
- Authenticated portal via QR scan
- Opens equipment directly, execute inspection, open OS, register anomaly, add photos, register HH

### P1 — Sprint 56: Wizard "Criar Planos ao Cadastrar Ativo"
### P1 — Sprint 57: Padronização do ciclo de vida
### P2 — Sprint 58: Revisão UX
### P2 — Sprint 59: Cliente Piloto
### P2 — Sprint 60/Bloco C: Dashboard Supervisor Executivo, Indicadores, Exportação
### P3 — IA Features, Subconjuntos, Integrações ERP/SAP

## Data Models
- `users`: {id, nome, email, role, organization_id, disciplinas, turno, areas}
- `org_config`: {organization_id, identidade, tema, terminologia, numeracao, preferencias, dominio}
- `organizations`: {id, nome}
- `ativos`: {id, organization_id, nome, tag, tipo_equipamento, fabricante, ...}
- `ordens_servico`: {id, organization_id, numero, tipo, status, ativo_id, ...}
- `inspecoes`: {id, organization_id, ativo_id, status, resultado, ...}

## Key API Endpoints
- `POST /api/auth/login` — JWT login
- `GET /api/public/organizations` — Public org list for login selector
- `GET /api/public/branding/{id}` — Public branding by org_id or subdomain
- `GET /api/org/config` — Authenticated org config
- `PUT /api/org/config/branding` — Update complete branding (admin)
- `PUT /api/org/config/tema` — Update theme colors (admin)
- `POST /api/org/config/logo` — Upload logo (admin)
- `POST /api/org/config/favicon` — Upload favicon (admin)
