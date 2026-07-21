# MAINTRIX ENTERPRISE — PRD

## Status: HOTFIX P0 CONCLUÍDO — QR Code Público estável
## Versao: pilot-astec-v1.2.1-hotfix
## Domínio: https://app.maintrix.com.br

---

## HOTFIX P0 — Tela Branca QR Code Público (21/07/2026)

### Problema
Tela branca em dispositivos móveis ao escanear QR Code dos equipamentos. Causado por `React.lazy()` + `ChunkLoadError` após novos deploys (chunks JS com hashes desatualizados no cache do Service Worker).

### Solução Implementada
1. **Import estático** para `PublicEquipmentPage` (removido `React.lazy()`)
2. **PublicErrorBoundary** dedicado para rotas públicas com:
   - Detecção de `ChunkLoadError` (5 padrões)
   - Reload automático máximo 1x por sessão (`sessionStorage` flag)
   - Limpeza seletiva de caches MAINTRIX (sem afetar caches globais)
   - Fallback visual: Logo MAINTRIX + botão "Tentar novamente"
3. **Service Worker** atualizado: network-only para navegação em `/equipamento/*` e `/portal/*`
4. **Listener global** em `index.js` para ChunkLoadError não capturados

### Arquivos Modificados
- `frontend/src/App.js` — Import estático + PublicErrorBoundary wrapping
- `frontend/src/components/PublicErrorBoundary.js` — NOVO
- `frontend/src/pages/PublicEquipmentPage.js` — clearChunkReloadFlag no mount
- `frontend/src/index.js` — Listener global ChunkLoadError
- `frontend/public/service-worker.js` — Network-only para rotas públicas

### Testes: 13/13 PASS (9 backend + 4 frontend flows)
- Carregamento mobile (390x844): ~1.7s ✅
- Carregamento desktop: ~1.3s ✅
- Sem tela branca ✅
- Sem ChunkLoadError no console ✅
- Rota pública sem login ✅
- Slug/token inválido: mensagem amigável ✅
- Rotas autenticadas sem regressão ✅

---

## RC P1 — QR CODE PÚBLICO POR EQUIPAMENTO

### Modelo de Dados
- `public_slug`: URL-safe slug gerado de TAG+nome
- `public_qr_token`: 32 chars (secrets.token_urlsafe(24))
- `public_qr_url`: /equipamento/{slug}/{token}
- `public_qr_created_at`, `public_qr_updated_at`: timestamps
- `public_status`: enum (nao_informado default)
- Índices: (public_slug, public_qr_token), public_qr_token unique sparse
- qr_code (UUID) existente: PRESERVADO INTEGRALMENTE

### API Pública
- `GET /api/public/equipment/{slug}/{token}` — DTO pública (allowlist fixa)
- `GET /api/public/equipment/{slug}/{token}/image` — imagem controlada
- 404 genérico para token/slug inválido

### API Autenticada
- `GET /api/ativos/{id}/qrcode/png` — download PNG
- `GET /api/ativos/{id}/qrcode/svg` — download SVG
- `GET /api/ativos/{id}/qrcode/pdf?modelo=simples|etiqueta|placa` — PDF individual
- `POST /api/ativos/qrcode/batch-pdf` — PDF lote (6/8/12 por folha)
- `POST /api/ativos/{id}/qrcode/regenerate` — Master/Admin only

### Página Pública
- Rota: /equipamento/{slug}/{token}
- Mobile-first, sem login, sem sidebar
- Logo empresa, TAG, nome, fabricante, modelo, área, tipo, specs
- Rodapé: "Equipamento monitorado pelo MAINTRIX Enterprise"
- Link: "Conheça o MAINTRIX"

### Frontend
- Tab "QR Code" no detalhe do ativo
- Preview QR, URL, copiar link, download PNG/SVG, imprimir 3 modelos
- Regenerar (Master/Admin only com confirmação)
- Checkboxes na listagem + modal impressão em lote

### Segurança
- DTO pública: allowlist fixa (tag, nome, tipo, fabricante, modelo, etc.)
- ZERO exposição de: organization_id, _id, custos, estoque, OS, users, emails
- Token criptograficamente seguro (non-sequential, non-predictable)
- Regeneração invalida QR anterior
- Ativo inativo: "não possui informações públicas"
- Ativo excluído: 404

### Backfill
- 62/62 ativos com QR Code (100%)
- Idempotente: re-execução não sobrescreve tokens existentes

### Testes: 10/10 PASS
- Acesso público sem auth ✅
- Sem dados sensíveis ✅
- Token/slug inválido → 404 ✅
- PNG/SVG/PDF download ✅
- Batch PDF (6 ativos) ✅
- PCM cannot regenerate → 403 ✅
- Backfill completo (62/62) ✅
- Regressão: health+ativos+branding+compliance ✅

---

## Arquivos Alterados (8 nesta RC)
- backend/routes/assets.py (QR helper + auto-generation)
- backend/server.py (endpoints + backfill + include_router fix)
- backend/pdf_engine.py (QR PDF generation)
- frontend/src/App.js (route + QR tab + batch modal)
- frontend/src/pages/PublicEquipmentPage.js (NEW)
- frontend/src/app/MainLayout.js (sidebar RBAC)
- frontend/src/pages/InspecoesPages.js (asset selector)

## POST-PILOTO BACKLOG
1. P2: Inserir CNPJ nos Termos de Uso
2. P2: Remover fallback Emergent Storage
3. P2: Corrigir erro 500 intermitente `preview_numeracao` (digitos=null)
4. P1: RC6.1 — Construtor de Seções da OS (Ondas 2 e 3)
5. P3: Integrações ERP/SAP | IA Assistente
