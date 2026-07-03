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

### Sprint 57 — Assistente Inteligente de Criação de Planos ✅ (2026-07-03)
**Backend:**
- `plan_parser.py`: Parser baseado em regras (sem IA) para extração de checklists de texto/PDF/Excel/Word/TXT
- Reconhece: listas numeradas (1. 2. 3.), bullets (- • ☐ □ ✓), checkboxes, tabelas, limites (°C, bar, RPM, %), frequências (diária, semanal, mensal), observações (OBS:, NOTA:)
- Detecta tipo de campo automaticamente (numerico, conforme_nao_conforme, foto, texto)
- Endpoints: POST `/api/planos-inspecao/parse-text`, POST `/api/planos-inspecao/parse-file`
- PCM pode criar/editar templates e planos (permissão atualizada de admin_only para pcm_or_admin)

**Frontend:**
- `PlanImportWizard`: Wizard 4 passos (Método → Configurar → Preview → Salvar)
- Método "Copiar e Colar" — textarea para texto do ChatGPT/manual
- Método "Arquivo" — upload PDF/Excel/Word/TXT com drag-and-drop
- Configuração: tipo plano, disciplina, equipamento, destino (Plano ou Modelo Mestre)
- Preview: resumo (X perguntas, Y obs, Z limites, frequência), lista editável, botão IA (futuro)
- Botão "Importar" na página de Planos de Inspeção

**Testing:** Backend 15/16 pytest ✅ | Frontend 88→100% após fix (schema template corrigido)

### Sprint 56 — Governança Operacional (Versão Leve) ✅ (2026-07-03)
**Backend:**
- OS tipos livres (enum removido) — valores vêm do `org_config.tipos_os` (configurável por empresa)
- OS origens livres — `org_config.origens_os` (operador, supervisor, pcm, inspecao, etc.)
- Novo campo `justificativa` na OS (para solicitações do operador)
- Objeto `aprovacao` embutido na OS ({necessaria, status, aprovador, data, observacao})
- Regras de workflow em `org_config.workflow` (tipos_que_precisam_aprovacao, aprovacao_gerente_acima)
- Novos status: solicitada → em_analise → aguardando_aprovacao → aguardando_material → programada → disponivel → em_execucao → pausada → concluida → encerrada → cancelada
- Endpoints aprovação: POST /api/ordens-servico/{id}/aprovar, POST /api/ordens-servico/{id}/enviar-aprovacao
- Dashboard estatísticas: por_origem, por_tipo, por_disciplina (aggregation), aguardando_aprovacao, aguardando_material
- Operador pode criar OS (origin=operador, status=solicitada)
- Kanban PATCH aceita todos os novos status
- Validação: aprovar só funciona se status=aguardando_aprovacao

**Frontend:**
- Nova tela "Solicitação de Serviço" (wizard 2 passos: selecionar ativo → descrever problema + justificativa + prioridade + equipamento parado)
- Sidebar Operador: "Solicitar Serviço" substitui "Anomalias"
- Sidebar Gerente: menu exclusivo (Central, Dashboard, OS, Ativos, Auditoria — apenas 5 itens)
- StatusBadge: 11 novos status com cores/ícones distintos + backward compat
- Kanban: 7 colunas novas (solicitada, em_analise, aguardando_aprovacao, programada, disponivel, em_execucao, pausada)
- OS Detail: seção "Justificativa da Solicitação" + painel "Aprovação Gerencial" com botões Aprovar/Rejeitar/Revisão (gerente only)
- Filtros OS: novos status disponíveis

**Testing:** Backend 13/13 pytest ✅ | Frontend 90% ✅

### Sprint de Homologação Operacional ✅ (2026-07-03)
- **RBAC por disciplina validado**: Mecânico vê só mecânica, Eletricista só elétrica+instrumentação, Operador só produção/civil
- **Bug fix: PCM criar/editar ativos**: `check_admin_only` → `check_pcm_or_admin` em POST/PUT `/api/ativos`
- **Bug fix: Sidebar Operador**: Removido link OS, adicionados Anomalias e Scanner
- **Bug fix: Sidebar PCM**: OS agora visível para todos exceto operacional
- **Usuários de teste configurados**: disciplina_principal, disciplinas_secundarias, area_ids corretos
- **Prontuário validado**: 6 tabs (Prontuário, Timeline, Planos, OS, Docs, BOM), QR Label
- **Portal Público validado**: Header branded, KPIs, 3 tabs, 404 handling
- **Portal Técnico validado**: 6 ações rápidas, navegação correta
- **Testing**: Backend 28/30 pytest, Frontend 85% → todos bugs corrigidos

### Sprint 63 — FASE 3: QR Code Enterprise ✅ (2026-07-03)
- **QR Label Modal**: Accessible from asset detail page (Prontuário) via "Etiqueta QR" button
- **4 Label Formats**: 50×30mm, 60×40mm, 80×50mm (compact), A4 (full prontuário)
- **Branded Labels**: Company logo/name + QR Code + TAG + Equipment name + "Powered by MAINTRIX"
- **QR URL**: Points to `/portal/equipamento/{ativo_id}` (public portal)
- **Print**: One-click print via browser print dialog

### Sprint 63 — FASE 4: Portal Público do Equipamento ✅ (2026-07-03)
- **Public Route**: `/portal/equipamento/{ativo_id}` — no authentication required
- **Mobile-first**: Optimized for QR code scanning on phones
- **Branded Header**: Dynamic company logo and name from org_config
- **Hero Card**: Asset photo/icon, TAG, name, type, status badge, area
- **KPI Cards**: Disponibilidade, Total OS, Total Inspeções
- **3 Tabs**: Informações (fabricante/modelo/série/área/tipo), Histórico (últimas 5 inspeções + OS), Manuais (PDFs downloadable)
- **Error Handling**: 404 page for invalid asset IDs
- **Backend**: Enriched endpoint with ultimas_inspecoes/os/manutencoes (limit 5), full branding payload

### Sprint 63 — FASE 5: Portal do Técnico ✅ (2026-07-03)
- **Auth Route**: `/portal/tecnico/{ativo_id}` — requires authentication
- **Quick Actions Grid**: 6 action buttons (Executar Inspeção, Abrir OS, Registrar Anomalia, Adicionar Fotos, Registrar HH, Ver Prontuário)
- **Scanner Integration**: QR scanner redirects authenticated users to Portal do Técnico (not public portal)
- **Asset Info**: TAG, name, area, type displayed in header

### Sprint 63 — FASE 2: Central White Label / Designer de Marca ✅ (2026-07-03)
- **WhiteLabelDesignerPage**: Full admin UI for MASTER to configure any organization's brand
- **Org Selector**: Visual selector showing all organizations with logos/initials
- **5 Configuration Tabs**: Identidade, Cores, Login, Domínios, Temas
- **Identity**: nome_empresa, nome_sistema, subtitulo, rodape, mostrar_powered_by, 4 asset uploaders (logo, logo_branca, favicon, wallpaper)
- **Colors**: 8 color pickers with hex input (primária, secundária, menu, header, login, fundo, texto, destaque)
- **Login Customization**: texto_login, texto_institucional, wallpaper upload, cor_login
- **Domains**: subdomínio + domínio customizado configuration
- **Preset Themes**: Industrial Dark, Midnight Steel, Corporativo Azul, Corporativo Verde — one-click apply
- **Live Preview**: Real-time preview of Login, Sidebar, and Asset Card — updates instantly without saving
- **New Org Creation**: Modal to create new organizations with auto-generated default config
- **Race condition protection**: Request versioning on org config loading (same pattern as branding.js)
- **Backend**: 5 new MASTER-only endpoints (list orgs, create org, get/put config, upload assets)
- **Testing**: Backend 10/10 pytest, Frontend ~95% (all tabs, save, create, preview, isolation verified)

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

### FASE 3-5 QR/Portals — COMPLETED
### P1 — Sprint 56: Wizard "Criar Planos ao Cadastrar Ativo" (Next)
- QR Code generator with company logo + QR + TAG + equipment name + "Powered by MAINTRIX"
- Label formats: 50x30, 60x40, 80x50, A4
- Uses organization's visual identity automatically

### FASE 3-5 — COMPLETED (see Completed Sprints above)

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
