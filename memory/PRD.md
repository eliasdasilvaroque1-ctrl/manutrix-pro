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
/app/frontend/src/App.js        — Monolithic React app (~10,800 lines)
/app/frontend/src/lib/branding.js — BrandingContext with race-condition protection
/app/frontend/src/lib/api.js    — Axios API client
/app/frontend/src/index.css     — Tailwind + brand utility CSS classes
/app/frontend/src/App.css       — Base CSS with :root variables
```

## Completed Sprints

### Sprint 59 — Consolidação de Permissões RBAC ✅ (2026-07-04)
- **Matriz centralizada**: `deps.py` — all permissions in a single `PERMISSION_MATRIX` dict
- **Roles especializados**: Replaced generic 'técnico' with `tec_mecanico`, `tec_eletrico`, `instrumentista`, `lubrificador`
- **Frontend RBAC**: Sidebar items, actions, buttons conditioned on `user.permissions[]`
- **Backend RBAC**: All endpoints check permissions via centralized matrix
- **ROLE_LABELS**: Consolidated top-level constant for human-readable role names (PT-BR)
- **Testing**: Backend 12/12 pytest ✅ | Frontend 6/6 Playwright ✅

### Sprint 60 — Eliminação Completa do Módulo de Anomalias ✅ (2026-07-04)
- **Frontend**: Removido `AnomaliasPage` (~300 linhas), rota `/anomalias`, item "Anomalias" do sidebar
- **Backend**: Removidos 7 endpoints `/api/anomalias/*`, model `AnomaliaCreate`, permissões RBAC, collections de cleanup/purge
- **Substituição**: Operadores usam "Solicitar Serviço" → cria OS diretamente (fluxo Sprint 56)
- **Limpeza**: Referências removidas de timeline, dashboard saúde, auditoria, exportação, numeração, org_config
- **Role labels cosméticos**: Sidebar mostra "Técnico Mecânico" ao invés de `tec_mecanico`
- **Testing**: Backend 12/12 pytest ✅ | Frontend 6/6 Playwright ✅

### AUDITORIA RC-01 ✅ (2026-07-04)
- **Relatório completo**: `/app/memory/AUDIT_RC01.md`
- **Resultado**: 6 P0 (CRITICAL) + 7 P1 (HIGH) + 4 P2 (MEDIUM) = 17 issues
- **Causa raiz principal**: Desconexão entre roles especializados (tec_mecanico, etc.) e RBAC legado que só referencia 'tecnico'
- **Maior risco**: 2 bugs de segurança (endpoint diagnóstico público + token reset vazado)
- **Testing**: 9 pytest + 8 Playwright confirmando os bugs

### Sprint RC-02 — Correção P0s da Auditoria ✅ (2026-07-04)
- **P0-04 FIXED**: Endpoint `/api/diag/auth-audit` removido completamente (expunha 27 usuários sem autenticação)
- **P0-05 FIXED**: `/api/auth/forgot-password` não retorna mais o token no corpo da resposta
- **P0-01 FIXED**: Técnicos especializados agora podem criar/iniciar/pausar/concluir OS (ROLE_GROUPS['execucao'])
- **P0-02 FIXED**: Técnicos especializados agora podem iniciar/concluir inspeções
- **P0-03 FIXED**: Motor de visibilidade (`build_visibility_query`, `build_dashboard_visibility`) reconhece roles especializados — tec_mecanico vê 21 itens vs 0 antes
- **P0-06 FIXED**: `admin_create_user` agora persiste disciplina_principal, disciplinas_secundarias, turno, area_ids, unidade_ids
- **P1-03 FIXED**: Master e Supervisor podem exportar auditoria (Excel/PDF)
- **P1-04 FIXED**: HH manual permitido para técnicos especializados
- **Testing**: Backend 14/14 pytest ✅ (100%)

### Sprint RC-03 — Correção P1s da Auditoria ✅ (2026-07-06)
- **P1-01/02 FIXED**: `ProtectedRoute` com prop `allow` — rotas admin/master bloqueadas para roles não autorizados. Operador em `/admin/config` vê "Acesso Restrito" ao invés do formulário editável
- **P1-05 FIXED**: `GET /api/ativos` filtra por `area_ids` para roles operacionais (técnicos, operadores)
- **P1-06 FIXED**: `GET /api/export/audit` filtra por `organization_id` — não mais vaza dados entre orgs
- **P1-07 FIXED**: `GET /api/admin/users/{id}` implementado com scoping multi-tenant
- **Testing**: Backend 10/10 pytest ✅ | Frontend 12/12 Playwright ✅

### RC-04 — Homologação Operacional ASTEC ✅ (2026-07-06)
- **Relatório completo**: `/app/memory/RC04_HOMOLOGACAO.md`
- **90 fluxos testados** por 8 perfis: Master, Gerente, Supervisor, PCM, Tec Mecânico, Tec Elétrico, Operador, Visualizador
- **2 bugs críticos encontrados e corrigidos**:
  - `check_write_permission` bloqueava gerente antes de verificar allowed_roles (impedia aprovação de OS)
  - Cálculo automático de tempo retornava 0 para execuções < 1min (impedia conclusão de OS)
- **Testing**: 14/14 pytest ✅ (100%)
- **Status piloto ASTEC: APROVADO**

### RC-05 — Teste de Casos Extremos (Edge Cases) ✅ (2026-07-06)
- **Relatório completo**: `/app/memory/RC05_EDGE_CASES.md`
- **38 edge cases testados**: autenticação, upload, concorrência, QR, multiempresa, workflow, banco, segurança
- **3 bugs encontrados e corrigidos**:
  - 🔴 OS concluída podia ser reiniciada (iniciar_os sem validação de status)
  - 🔴 Race condition: dois técnicos concluíam mesma OS (update atômico com filtro)
  - 🟡 Pausar OS fora de execução era aceito
- **Taxa final: 100%**

### RC-06 — Validação E2E via Interface Gráfica ✅ (2026-07-06)
- **Relatório completo**: `/app/memory/RC06_E2E_GUI.md`
- **9 perfis testados via Playwright**: Master, Gerente, Supervisor, PCM, Tec Mecânico, Tec Elétrico, Lubrificador, Operador, Visualizador
- **76 steps E2E** — login, navegação sidebar, RBAC, formulários, exportação, logout
- **4 bugs corrigidos**:
  - 🔴 "Nova OS" e "Nova Inspeção" visíveis para Visualizador (ocultados)
  - 🔴 /solicitar acessível para Visualizador (allow prop adicionado)
  - 🟡 `force_password_change` não editável via admin (campo adicionado)
- **6 observações UX** documentadas (nenhuma bloqueante)
- **Performance**: Todas as telas <2s, nenhuma >3s

### RC-07 — Consolidação do Perfil Visualizador ✅ (2026-07-06)
- **Conceito**: Visualizador acessa APENAS o Portal de Consulta de Equipamentos (busca por TAG + prontuário)
- **Sidebar**: Reduzido a único item "Portal de Equipamentos" → `/consulta`
- **ConsultaEquipamentosPage**: Busca por TAG/nome/tipo, cards com status, detalhe com KPIs/OS/Inspeções/Manuais
- **Bloqueios**: 9 rotas operacionais bloqueadas via `ROLES_EXCEPT_VIEWER` + ProtectedRoute allow
- **Backend**: 403 para POST OS, POST ativos, POST estoque, GET export (defesa em profundidade)
- **Redirect pós-login**: `/consulta` para Visualizador, `/` para demais
- **Testing**: Backend 7/7 pytest ✅ | Frontend 100% Playwright ✅ | Regressão Master/Operador OK

### RC-08 — Auditoria Multiempresa ✅ (2026-07-06)
- **P0-01 FIXED**: Login agora aceita e valida `organization_id` — org errada retorna 401
- **P0-02 FIXED**: Register público BLOQUEADO (403) — só admin pode criar usuários
- **P0-03 FIXED**: Forgot-password agora aceita `organization_id` e filtra por org (previne enumeração)
- **Frontend**: Envia `organization_id` no login e forgot-password
- **JWT**: Contém claim `org` com organization_id do usuário
- **Cross-org**: Ativos, OS, export todos scoped por organization_id
- **QR Code**: Portal público retorna branding da organização correta
- **Testing**: Backend 16/16 ✅ | Frontend 100% GUI ✅

### RC-09 — Congelamento da Arquitetura Multiempresa ✅ (2026-07-07) — v1.0.0-RC1
- **Login global ELIMINADO**: `organization_id` é campo OBRIGATÓRIO (Pydantic 422 se ausente)
- **Índice composto**: `(organization_id, email)` único — permite mesmo email em orgs diferentes
- **Forgot-password**: Exige `organization_id` obrigatoriamente
- **Register público**: BLOQUEADO (403) — só admin pode criar usuários
- **Admin create user**: Valida `organization_id` obrigatório, herda do admin se não informado
- **Frontend**: Envia `organization_id` em login e forgot-password
- **Testing**: Backend 11/11 ✅ | Frontend GUI ✅ | RBAC regressão ✅
- **STATUS: VERSÃO CONGELADA PARA PILOTO ASTEC**

### RC-11 — Identidade Operacional dos Ativos ✅ (2026-07-07)
- **Padrão aplicado**: Unidade › Área › TAG › Nome em 12 telas
- **Telas atualizadas**: Ativos list, OS Kanban, OS list, OS detail, Inspeções list/detail, Prontuário, Minha Jornada, Solicitações, Portal Público (QR), Portal Técnico, Consulta Visualizador
- **Backend**: `/api/public/ativo` agora retorna campo `unidade` (corrigido collection `db.unidades` vs stale `db.plantas`)
- **Helper**: `getAssetContext()` + `AssetIdentity` componente reutilizável
- **Bug corrigido**: Portal Público retornava "Planta Principal" (stale doc de collection errada) ao invés de "UNIDADE CEDRO"
- **Testing**: Backend 6/6 + Frontend 6/6 + Regressão 3/3 ✅

### RC-12 — Dossiê Permanente do Equipamento ✅ (2026-07-07) — ÚLTIMA SPRINT
- **Timeline completa**: Aba "Histórico Completo" no Prontuário — OS, Inspeções, Paradas, Materiais em uma única linha do tempo cronológica
- **Dossiê OS read-only**: Unidade/Área/TAG/Equipamento, número, tipo, origem, solicitante, PCM, supervisor, executantes com HH individual, materiais consumidos, fotos, causa da falha, solução, aprovação, auditoria completa — tudo em SOMENTE LEITURA
- **Dossiê Inspeção read-only**: Plano utilizado, todas as respostas do checklist, não conformidades destacadas, fotos, executor, tempo, observações
- **Pesquisa Global**: Página `/dossie` — pesquisa por número OS, TAG, tipo, área, equipamento. Resultados clicáveis para abrir dossiê completo
- **RBAC**: Dossiê acessível para Master, Admin, PCM, Supervisor, Gerente. Técnicos bloqueados (403)
- **Testing**: Backend 12/12 ✅ | Frontend 100% ✅ | Regressão Dashboard/OS/Inspeções ✅
- **STATUS: DESENVOLVIMENTO ENCERRADO — VERSÃO v1.0.0-RC1 CONGELADA**

### Sprint 58 — Exportação PDF/Excel Corrigida ✅ (2026-07-03)
- **10 endpoints corrigidos**: ativos, OS, inspeções, estoque, sobressalentes × excel + pdf
- **Branding dinâmico**: Títulos PDF usam nome da empresa (não mais "MAINTRIX"), cores dos headers usam cor_primaria da empresa
- **OS export enriquecido**: 15 colunas incluindo Origem, Disciplina, Justificativa, Aprovação
- **Inspeções export**: Coluna Disciplina adicionada
- **Excel formatação**: Headers negrito branco sobre cor primária, colunas auto-dimensionadas
- **Filenames**: Usam nome da empresa (ex: `os_ASTEC_Cedro.xlsx`)
- **Frontend**: Extrai filename do Content-Disposition header, Supervisor pode exportar

### Sprint 58 — Fluxo de Execução de OS ✅ (2026-07-03)
- **HH Manual**: Endpoint POST `/api/os/{id}/hh-manual` aceita {horas, data_inicio, data_fim, executante_id, descricao}. Calcula timestamps corretamente quando apenas horas é fornecido (data_fim=now, data_inicio=now-horas)
- **Seção HH compacta**: Timer inline (1 linha) + botão "Lançar HH" abre form com executante/horas/início/fim/descrição + resumo por executante
- **Finalizar Rapidamente (⚡)**: Modal único com: serviço executado, causa da falha, solução aplicada, HH, observações. Skip foto check na finalização rápida. Botão proeminente (primário) para em_execucao e pausada
- **modo_hh configurável**: `org_config.workflow.modo_hh` = "manual" | "cronometro" | "ambos"
- **Botões redesenhados**: ⚡Finalizar Rapidamente (primário) + Concluir/Pausar (secundários compactos)

### Sprint 58 — Estabilidade e Experiência de Login ✅ (2026-07-03)
- **Login redesenhado**: Formulário único com campo Empresa (autocomplete) + Email + Senha — sem tela separada de seleção
- **Autocomplete empresa**: Busca por nome, mostra logo/iniciais, carrega branding instantaneamente ao selecionar
- **localStorage**: Salva última empresa usada (`maintrix_last_org`) para preenchimento automático
- **Dashboard KPIs novos**: Solicitações, Aguardando Aprovação, Aguardando Material, OS por Origem (operador/pcm/manual)
- **Testing**: Backend 8/8 pytest ✅ | Frontend 100% ✅

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

## Fase Atual: PILOTO ASTEC — App CONGELADO (Fev/2026)

**Versão oficial**: v1.0.0 — CÓDIGO CONGELADO
**Status**: HOMOLOGAÇÃO ASTEC — Piloto 30 dias
**IPP**: 99%
**Função do agente**: Homologador do Piloto ASTEC (não desenvolvedor)
**Status**: GO LIVE APROVADO — Piloto em andamento
**Governança**: CTO aprova qualquer alteração que não seja P0 bloqueante

### RC-13 — Identificação Visual de Materiais ✅ (2026-07-08)
- **Backend**: Campo `images: []` em EstoqueCreate/Update e SpareAssetCreate/Update
- **Endpoints**: `POST/DELETE /api/materiais/{tipo}/{item_id}/images` (upload e remoção)
- **Frontend**: MaterialThumbnail (placeholder inteligente White Label), MaterialImageModal (zoom/fullscreen), MaterialImageUploader (drag&drop + câmera + compressão)
- **Integração**: Thumbnails em Estoque, Sobressalentes, OS Materiais, BOM, Dossiê
- **Testes**: Backend 15/15 ✅ | Frontend 95%+ ✅ (bug de estado LOW corrigido)

### RC-BUG-02 — White Label Wallpaper Freeze ✅ (2026-07-08)
- **Causa raiz**: `PreviewLogin` usava `absolute inset-0` sem `relative` no container pai → overlay cobria a página inteira
- **Arquivo**: `App.js`, componente `PreviewLogin` (~linha 9323)
- **Correção**: `relative` + `pointer-events-none` + `BACKEND_URL` prefix
- **NÃO é regressão da RC-13**

### Design System Onda 1 — Migração Completa ✅ (2026-07-09)
- **10 páginas migradas** para componentes DS
- **53 classes slate eliminadas**, cobertura tokens 7.3% → 11.3%
- **Adoção PageContainer/PageHeader**: 10/24 páginas (42%)

### QA Piloto ASTEC — GATE 3 UX ✅ (2026-07-09)
- **6 correções de baixo risco**: EmptyState Paradas/Planos (botão não funcionava), mensagens de erro amigáveis (Network Error, timeout, JSON), toasts genéricos humanizados

### ORR Final Fixes ✅ (2026-07-09)
- **4 correções aprovadas pelo CTO**:
  1. Audit log na criação de OS (P1)
  2. Filtro `entity_id` no endpoint de auditoria (P1)
  3. `data_planejamento` setado para status "programada" (P2)
  4. Conclusão de OS exige data/hora de início (P2)
- **0 alterações em**: frontend, RBAC, banco, arquitetura

### QA Piloto ASTEC — GATE 4.5 Consistência dos Dados ✅ (2026-07-09)
- **28/29 PASS** (96.5%) — cenários S1(lifecycle), S4(materiais), S6(RBAC), S7(multi-tenant), S9(soft-delete), S10(concorrência)
- **1 FAIL P0 encontrado e corrigido**: Cross-tenant write escalation em 7 endpoints de OS (PATCH status, iniciar, pausar, concluir, delete, add_material, remove_material) — `verify_org_access` adicionado em todos
- **Master bypass**: `verify_org_access` agora permite master cross-org explicitamente
- **Validação do fix**: 4/4 endpoints retornam 404 para cross-tenant write

### QA Piloto ASTEC — GATE 1 ✅ (2026-07-09)
- **Auditoria**: 14/14 loading states OK, 12/14 empty states OK, 0 mensagens técnicas expostas
- **Documentados P1**: Mobile bottom nav incompleta (Estoque inacessível)
- **Relatório**: `/app/memory/GATE3_UX_REPORT.md`
- **Validação**: 4/4 uploads testados (Logo, Logo Branca, Favicon, Wallpaper)

### Design System Enterprise — Fase 1 ✅ (2026-07-09)
- **9 Design Tokens**: `--brand-surface`, `--brand-surface-hover`, `--brand-border`, `--brand-text-primary`, `--brand-text-secondary`, `--brand-success`, `--brand-warning`, `--brand-danger`, `--brand-info`
- **15 Classes Utilitárias**: `bg-surface`, `bg-surface-hover`, `border-surface`, `text-primary`, `text-secondary`, `text-success`, `text-warning`, `text-danger`, `text-info`, `bg-success-10`, `bg-warning-10`, `bg-danger-10`, `bg-info-10`
- **7 Componentes Migrados**: Modal, ConfirmDialog, FormInput, Loading, EmptyState, KPICard + glass-card/btn-primary/btn-secondary/input-industrial/card-industrial (CSS)
- **Testes**: Backend 12/12 ✅ | Frontend 85%→100% (contraste corrigido)

### Design System Enterprise — Fase 1.5 ✅ (2026-07-09)
- **Theme Engine**: Arquitetura de temas pré-definidos em `branding.js` (Industrial Dark ativo, preparado para Light/Executive/Mining)
- **8 Componentes Reutilizáveis**: `PageContainer`, `PageHeader`, `PageToolbar`, `SearchInput`, `FilterBar`, `CardSection`, `DataTable`/`DataRow`, `SectionDivider`
- **Migrações globais**: Todos os page titles (20+), 17 section headers
- **Documentação**: `/app/memory/DESIGN_SYSTEM.md` — referência oficial do Design System

### UX Login Multiempresa ✅ (2026-07-09)
- **Smart Org Selector**: 3 modos visuais distintos — Subdomínio (🔒 fixo), Lembrado (localStorage), Manual (busca)
- **Clareza**: Cada modo mostra contexto ("Detectado pelo endereço", "Última organização utilizada", "Organização única", "Selecionada manualmente")
- **Trocar organização**: Botão "Trocar" permite alterar sem limpar browser
- **Terminologia**: "Empresa" → "Organização" em toda a tela de login
- **Auth (16/16)**: Login, logout, forgot-password, change-password, JWT claims — ZERO falhas
- **Multi-Tenant (7/7)**: Isolamento total entre orgs. Token adulterado rejeitado. IDs falsos → 404.
- **RBAC (17/19)**: Todas roles testadas. Operador pode criar OS com status=solicitada (decisão CTO: PASS condicional — OS solicitada é demanda, não operacional)
- **Fix P0**: Removido log de token de reset em texto plano

### QA Piloto ASTEC — GATE 2 ✅ (2026-07-09)
- **Fluxos (35/37)**: CRUD ativos/estoque/BOM, OS lifecycle completo, inspeções, uploads, exports, audit logs
- **KPIs**: OS `solicitada` excluída de TODOS os KPIs (backlog, atrasadas, MTBF, MTTR, por-setor, por-disciplina, ativos-mais-falhas)
- **Fixes**: Status default `operacional` para ativos (116 migrados), verify_org_access em inspeções e consumo de material (IDOR fix)

### Protocolo de Mudança
- Consultor (E1) atua como QA e Implantação — não como desenvolvedor
- Toda alteração requer análise de impacto documentada
- Critérios completos em: `/app/memory/CRITERIOS_NOVA_FUNCIONALIDADE.md`

### Permitido durante o piloto:
- Correção de bugs reais reportados por usuários
- Melhorias de UX quando usuário relatar dificuldade
- Investigação de problemas de desempenho
- Atualização de documentação e relatórios técnicos

### Backlog v2.0 (SUSPENSO — aguardando aprovação do CTO)

| Prioridade | Feature | Status |
|------------|---------|--------|
| P0 | Dashboard Supervisor Executivo (MTBF, MTTR, KPIs) | Backlog |
| P1 | IA Assistente (Melhorar Plano via LLM) | Backlog |
| P2 | Estrutura de Subconjuntos + Integrações ERP/SAP | Backlog |

## Data Models
- `users`: {id, nome, email, role, organization_id, disciplinas, turno, areas}
- `org_config`: {organization_id, identidade, tema, terminologia, numeracao, preferencias, dominio}
- `organizations`: {id, nome}
- `ativos`: {id, organization_id, nome, tag, tipo_equipamento, fabricante, ...}
- `ordens_servico`: {id, organization_id, numero, tipo, status, ativo_id, ...}
- `inspecoes`: {id, organization_id, ativo_id, status, resultado, ...}
- `itens_estoque`: {id, organization_id, sku, nome, categoria, quantidade, **images: []**, ...}
- `spare_assets`: {id, organization_id, tag, descricao, **images: []**, ...}
- `os_materiais`: {id, os_id, item_estoque_id, codigo, descricao, **image_url**, ...}

## Key API Endpoints
- `POST /api/auth/login` — JWT login
- `GET /api/public/organizations` — Public org list for login selector
- `GET /api/public/branding/{id}` — Public branding by org_id or subdomain
- `GET /api/org/config` — Authenticated org config
- `POST /api/materiais/{tipo}/{item_id}/images` — Upload material image (RC-13)
- `DELETE /api/materiais/{tipo}/{item_id}/images?image_url=...` — Remove material image (RC-13)
- `PUT /api/org/config/branding` — Update complete branding (admin)
- `PUT /api/org/config/tema` — Update theme colors (admin)
- `POST /api/org/config/logo` — Upload logo (admin)
- `POST /api/org/config/favicon` — Upload favicon (admin)


## MISSÃO RC1 — OPERAÇÃO ESTABILIZAÇÃO ENTERPRISE

### BLOCO A — Auditoria e Limpeza ✅ (2026-07-11)
- **Relatório completo:** `/app/memory/BLOCO_A_RELATORIO.md`
- **Resultado:** App.js 11.011 → 10.807 linhas (-204). 6 componentes mortos removidos. 10 React.memo aplicados. 13 imports órfãos removidos (frontend). 5 imports mortos removidos (backend). 3 bare except: corrigidos.
- **MongoDB:** 41 coleções auditadas. 5 coleções backup identificadas. 7 coleções com 0 docs. 14 índices faltantes mapeados.
- **Dependências:** 8 deps frontend possivelmente não utilizadas. Bundle total: 1 GB node_modules.
- **Regressão:** 22/22 pytest PASS, 11/11 rotas frontend PASS. **ZERO REGRESSÕES.**
- **Veredicto:** APROVADO para BLOCO B.

### BLOCO B — Fluxos Críticos PWA ✅ (2026-07-11)
- **Relatório completo:** `/app/memory/BLOCO_B_RELATORIO.md`
- **RC1.1 Fila Offline:** 8 novas operações protegidas (iniciar/pausar/concluir OS, status change, HH manual, iniciar/concluir inspeção). Total: 11 operações com fila offline.
- **RC1.2 Cache Local:** Interceptor automático em api.js cacheia 10 rotas de campo (ativos, setores, plantas, técnicos, templates, estoque). 5 caches confirmados em simulação.
- **RC1.3 Fotos Offline:** PhotoUploader armazena fotos como ArrayBuffer no IndexedDB (store `pending_photos`). Upload automático ao reconectar.
- **RC1.4 Sync Engine:** Exponential backoff (cap 300s), ordenação por prioridade, dedup de status changes, tolerância a conflitos 409/400.
- **Service Worker:** v3 → v4, 15 rotas API cacheadas (era 8).
- **Simulação Offline:** Kanban OS carrega completo offline, modal Nova OS funcional com dados cacheados.
- **Regressão:** 22/22 pytest PASS, 8/8 rotas + PWA checks PASS. **ZERO REGRESSÕES.**
- **Veredicto:** APROVADO para BLOCO C.

### BLOCO C — Hardening Enterprise ✅ (2026-07-11)
- **Relatório completo:** `/app/memory/BLOCO_C_RELATORIO.md`
- **Rate Limiting:** 7 endpoints protegidos (login 10/min, forgot-password 3/min, upload 30/min, public 60/min). HTTP 429 com logging.
- **Security Headers:** 6 headers implementados (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, X-XSS-Protection, HSTS).
- **MongoDB:** 14 índices criados (total: 69 customizados). background=True, zero impacto.
- **Timeouts:** 120s global com HTTP 504 + logging.
- **Logging:** Padronizado em auth (IP-aware), uploads, rate limit, timeouts.
- **Regressão:** 21/21 pytest PASS, 10/10 rotas frontend PASS. **ZERO REGRESSÕES.**
- **Veredicto:** APTO PARA CERTIFICAÇÃO RC1 (BLOCO D).

### RC1.5 — Compliance, LGPD e Preparação Comercial ✅ (2026-07-11)
- **Relatório completo:** `/app/memory/RC15_COMPLIANCE_RELATORIO.md`
- **Termos de Uso v1.0** + **Política de Privacidade v1.0** (LGPD-compliant)
- **Aceite obrigatório** com registro versionado (user, org, IP, user-agent, versão)
- **Reaceite automático** quando versão dos documentos mudar
- **Página "Sobre"** com versão, build, contato, links legais
- **Footer permanente:** Termos de Uso | Privacidade | Sobre | v5.2.0-RC1
- **Documentação comercial:** SLA, Onboarding
- **Regressão:** 12/12 backend PASS, 11/11 frontend PASS. **ZERO REGRESSÕES.**
- **Veredicto:** ✅ APROVADO — Preparado para piloto e demonstrações comerciais
- **Relatório completo:** `/app/memory/BLOCO_D_CERTIFICACAO.md`
- **58 testes executados, 58 PASS, 0 FAIL**
- **Etapas validadas:** Autenticação (7/7), Multi-tenant (8/8), Ativos (4/4), OS (6/6), Inspeções (2/2), Dashboard (3/3), PWA (8/8), Performance (10/10 < 320ms), Segurança (4/4), Banco (4/4), UX (20/20 rotas)
- **Fix aplicado:** Botão "INICIAR OS" agora visível para status `programada`/`disponivel`
- **Compliance (RC2):** LGPD, Termos de Uso, Aceite — lacunas identificadas, não bloqueiam piloto
- **PARECER: 🟢 GO — APTO PARA INICIAR O PILOTO ASTEC**

## Próximas Tarefas (v1.1 — NÃO IMPLEMENTAR EM RC1)
- MAINTRIX Field Operations (PDFs, QR, batch print) — Arquitetura em `/app/memory/FIELD_OPERATIONS_ARCH.md`
- Dashboard Executivo
- IA Assistente
- ERP/SAP Integrations

## Deploy & Modularização (2026-07-12)
- **Modularização Fase 1:** 14 componentes UI extraídos para `/components/shared/index.js`. App.js: 11.040 → 10.855 linhas.
- **Pipeline:** Frontend Vercel ✅ auto-deploy. Backend Railway ✅ v5.2.0-RC1.
- **Fix produção:** Paths compliance relativos (funciona em Railway e Emergent)
- **requirements.txt:** 144 → 24 pacotes. Removido emergentintegrations (private index).
- **Tag Git:** v5.2.0-RC1
- **Documentação:** CHANGELOG.md, ROADMAP.md, DEPLOY_CHECKLIST.md, PIPELINE_AUDIT.md, MODULARIZACAO.md, IMPORT_AUDIT.md, NEXT_STEPS.md

## Documentação Completa
- `/app/memory/PRD.md` — Requisitos do produto
- `/app/memory/CHANGELOG.md` — Histórico de mudanças
- `/app/memory/ROADMAP.md` — Plano RC2
- `/app/memory/DEPLOY_CHECKLIST.md` — Checklist de deploy
- `/app/memory/BLOCO_A_RELATORIO.md` — Relatório Auditoria
- `/app/memory/BLOCO_B_RELATORIO.md` — Relatório PWA
- `/app/memory/BLOCO_C_RELATORIO.md` — Relatório Hardening
- `/app/memory/BLOCO_D_CERTIFICACAO.md` — Certificação RC1
- `/app/memory/RC15_COMPLIANCE_RELATORIO.md` — Compliance LGPD
- `/app/memory/MODULARIZACAO.md` — Plano modularização
- `/app/memory/IMPORT_AUDIT.md` — Auditoria de imports
- `/app/memory/PIPELINE_AUDIT.md` — Auditoria de pipeline
- `/app/memory/NEXT_STEPS.md` — Próximos passos
- `/app/memory/FIELD_OPERATIONS_ARCH.md` — Arquitetura Field Ops
- `/app/compliance/` — Termos, Privacidade, LGPD, Changelog Jurídico
- `/app/commercial/` — SLA, Onboarding
- `/app/scripts/validate_deploy.py` — Validação pós-deploy


### RC2.1 — Correção de Regressões da Modularização ✅ (2026-07-12)
- **7 regressões corrigidas**: 6 páginas + ProtectedRoute com imports/constantes faltantes
- **Componentes movidos do App.js**: `ModalNovoEstoque` → EstoquePage, `ModalNovaInspecao` + `CameraCapture` → InspecoesPages
- **Constantes relocadas**: `ORIGEM_OPTIONS`, `CONDICAO_CONFIG` → SobressalentesPage; `PARADA_TIPOS`, `FIELD_TYPES` → ParadasPage
- **App.js**: 4.541 → 3.950 linhas (redução adicional de 591 linhas de código morto)
- **Build**: CI=true yarn build PASS (zero warnings/errors)
- **Relatórios**: `/app/memory/REGRESSION_REPORT.md`, `/app/memory/MODULARIZACAO.md` (atualizado)
