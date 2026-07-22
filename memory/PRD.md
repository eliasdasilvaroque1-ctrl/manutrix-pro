# MAINTRIX ENTERPRISE — PRD

## Status: HOTFIX P0 QR URLs CORRIGIDO — PRONTO PARA HOMOLOGAÇÃO
## Versao: pilot-astec-v1.2.2-hotfix
## Domínio: https://app.maintrix.com.br

---

## HOTFIX P0.2 — QR Code Redirecionando para Login e URL Inválida (22/07/2026)

### Problema
QR Codes codificavam URLs internas autenticadas (`/ativos/{id}`) e relativas, fazendo com que câmeras de celular abrissem a página de login ou interpretassem o QR como pesquisa.

### Causa Raiz
1. `public_qr_url` armazenado no banco como rota relativa (`/equipamento/{slug}/{token}`)
2. Frontend usava `window.location.origin` para montar URL (domínio errado em preview/admin)
3. Backend PNG/SVG/PDF usava `REACT_APP_BACKEND_URL` (URL da API, não do frontend)
4. `AssetDossierPage.js` usava `window.location.origin + /ativos/{id}` (rota interna)
5. `QRLabelModal` usava `/portal/equipamento/{id}` (rota interna com ID)

### Solução Implementada
1. **`build_public_equipment_url(asset)`** — Função centralizada única em `routes/assets.py`
2. **`PUBLIC_APP_URL=https://www.maintrix.com.br`** no backend `.env`
3. **Validação de URL** (`validate_public_qr_url`) antes de gerar QR
4. **Todos os consumidores corrigidos**: PNG, SVG, PDF (3 modelos), Batch PDF (6/8/12 por folha), header do ativo, tab QR Code, QRLabelModal
5. **Interceptor Axios** — `isPublicEndpoint()` skip 401 redirect para `/api/public/`
6. **Backfill idempotente** — 62 URLs corrigidas para absoluta (tokens preservados)
7. **Tab QR Code migrada** de código morto (App.js) para `AssetDossierPage.js`

### Arquivos Modificados
- `backend/.env` — Adicionado `PUBLIC_APP_URL`
- `backend/routes/assets.py` — `build_public_equipment_url()`, `validate_public_qr_url()`, `_generate_public_qr_fields()` com URL absoluta
- `backend/server.py` — QR endpoints usam `build_public_equipment_url()`, backfill com recálculo
- `backend/pdf_engine.py` — Usa `build_public_equipment_url()` (sem `REACT_APP_BACKEND_URL`)
- `frontend/src/pages/AssetDossierPage.js` — Header QR + Tab QR Code completa
- `frontend/src/pages/WhiteLabelDesignerPage.js` — QRLabelModal usa `public_qr_url`
- `frontend/src/App.js` — Tab QR usa `public_qr_url` direto
- `frontend/src/lib/api.js` — `isPublicEndpoint()` + interceptor skip

### Testes: 33/33 PASS (18 backend + 15 frontend)
- Header QR codifica `https://www.maintrix.com.br/equipamento/...` ✅
- Tab QR Code com todos os botões (copiar, abrir, download, imprimir) ✅
- PNG/SVG/PDF decodificados confirmam URL absoluta ✅
- Batch PDF (6 QRs) todos válidos ✅
- API pública sem Authorization → 200 ✅

---

## RC P1 — Dossiê Digital do Ativo v1.0 — FASE 1 CONCLUÍDA (22/07/2026)

### Modelo de Dados (`public_dossier` embedded no ativo)
```json
{
  "public_dossier": {
    "description": "", "curiosity": "", "warning": "", "safety": "", "best_practices": "",
    "image_url": "",
    "location": { "linha": "", "ponto_instalacao": "" },
    "technical_data": { "corrente": "", "frequencia": "" },
    "visibility": {
      "technical_data": "public", "history": "hidden", "inspections": "hidden",
      "maintenance": "hidden", "documents": "hidden",
      "curiosity": "public", "warning": "public", "safety": "public", "best_practices": "public"
    }
  }
}
```

### Endpoints Criados/Alterados
- `GET /api/ativos/{id}/dossier` — Retorna dossiê para edição (auth)
- `PUT /api/ativos/{id}/dossier` — Atualiza dossiê (RBAC: master/admin/pcm)
- `POST /api/ativos/{id}/dossier/photo` — Upload foto pública (Supabase)
- `DELETE /api/ativos/{id}/dossier/photo` — Remove foto pública
- `POST /api/ativos/{id}/dossier/documents` — Upload documento (FormData)
- `PUT /api/ativos/{id}/dossier/documents/{doc_id}/publish` — Toggle publicação
- `DELETE /api/ativos/{id}/dossier/documents/{doc_id}` — Soft-delete
- `GET /api/public/equipment/{slug}/{token}` — EVOLUÍDO: branding, location, technical_data, status com cor, history, inspeções (max 3), manutenções (max 3), documentos públicos
- `GET /api/public/equipment/{slug}/{token}/document/{doc_id}` — Download público controlado

### Visibilidade (4 níveis)
- `public` — QR sem auth
- `authenticated` — Login MAINTRIX + org
- `restricted` — Master/Admin/PCM
- `hidden` — Não retornado

### Segurança
- Zero dados sensíveis no endpoint público (organization_id, _id, custos, emails, responsáveis)
- Projeção explícita — nunca retorna doc completo
- Documentos: slug/token + is_published + visibility + org match
- RBAC backend obrigatório (não só frontend)

### Testes: 34/34 PASS
- CRUD dossiê ✅ | RBAC ✅ | Validação status ✅ | Visibilidade ✅
- Endpoint público com/sem blocos ✅ | Sem dados sensíveis ✅
- Upload/publish/download/delete documentos ✅ | Token inválido 404 ✅

### Arquivos
- `backend/routes/dossier.py` — NOVO (265 linhas)
- `backend/server.py` — Endpoint público evoluído + document download + indexes

### Compatibilidade
- Nenhum campo obrigatório ✅ | Ativos antigos funcionam ✅ | QR Codes preservados ✅
- Nenhuma IA ✅ | Nenhum serviço pago ✅

---

## RC P1 — Dossiê Digital v1.0 — FASE 2 CONCLUÍDA (22/07/2026)

### Frontend Edição
- Tab "Dossiê Digital" no AssetDossierPage com formulário completo
- Preview em tempo real com seletor de modo (Público/Autenticado/Restrito)
- Upload foto pública (Supabase) com preview imediato
- Gestão de documentos (upload, publicar/despublicar, excluir)
- Status público com indicador colorido
- Localização extra (linha, ponto de instalação)
- Dados técnicos adicionais (corrente, frequência)
- 9 controles de visibilidade (4 níveis: public/authenticated/restricted/hidden)
- Botão "Visualizar Dossiê" → abre página pública real
- RBAC: Master/Admin/PCM editam, demais read-only
- Confirmação ao sair sem salvar (beforeunload)

### Arquivo Criado
- `frontend/src/pages/DossierEditTab.js` — NOVO (~400 linhas)
- `frontend/src/pages/AssetDossierPage.js` — Tab adicionada

### Testes: 16/16 PASS (Frontend E2E)
- Tab renderiza ✅ | Edição + Save ✅ | Preview real-time ✅
- Seletor de visão ✅ | Botão Visualizar Dossiê ✅ | Upload foto ✅
- Documentos ✅ | Visibilidade selects ✅ | Toast sucesso ✅
- Regressão tabs existentes ✅ | Console limpo ✅

---

## RC P1 — Dossiê Digital v1.0 — FASE 3 CONCLUÍDA (22/07/2026)

### Página Pública Evoluída
- PublicEquipmentPage reescrita completamente (~220 linhas)
- Mobile-first (360px), desktop com max-w-2xl
- 16 blocos condicionais — só renderiza se houver conteúdo público
- Branding da empresa (logo, nome, cor primária)
- Status com indicador visual colorido + texto
- Localização completa (área/unidade/linha/ponto)
- Blocos informativos com cores distintas (amber/orange/red/emerald)
- Dados técnicos em grid 2 colunas
- Últimas 3 inspeções e 3 manutenções (campos seguros)
- Histórico resumido, documentos públicos com download
- Estados de loading, erro, ativo indisponível
- Zero dados sensíveis | Zero tela branca

### Testes: 35/35 PASS (17 backend + 18 frontend)
- QR válido abre ativo ✅ | QR inválido = erro amigável ✅
- Status verde ✅ | Blocos com cores ✅ | Dados técnicos ✅
- Inspeções/manutenções ✅ | Histórico ✅ | Documentos ✅
- Mobile 360px ✅ | Desktop centralizado ✅ | Sem dados sensíveis ✅
- Refresh direto ✅ | Console limpo ✅ | Regressão OK ✅
- Campos vazios NÃO geram cartões ✅ | Ativo sem dossiê funciona ✅

- Rota frontend pública sem login ✅
- Nenhum QR contém blob:, localhost, rota interna ✅
- Interceptor Axios skip para /api/public/ ✅
- Rotas autenticadas sem regressão ✅

---

## HOTFIX P0.1 — Tela Branca QR Code Público (21/07/2026)

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
1. P0: RC Estabilização Fase 4 — Wallpaper Real White Label
2. P0: RC Estabilização Fase 5 — Diagnóstico e Otimização Performance
3. P2: Remover AtivoDetailPage dead code (App.js linhas 1746-2365)
4. P2: Inserir CNPJ nos Termos de Uso
5. P2: Remover fallback Emergent Storage
6. P2: Corrigir erro 500 intermitente `preview_numeracao` (digitos=null)
7. P1: RC6.1 — Construtor de Seções da OS (Ondas 2 e 3)
8. P3: Integrações ERP/SAP | IA Assistente
