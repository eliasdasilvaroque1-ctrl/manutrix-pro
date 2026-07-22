# MAINTRIX ENTERPRISE — PRD

## Status: HOTFIX P0 REACT ERROR #31 VALIDAÇÃO — APROVADO
## Versao: pilot-astec-v1.4.4-rc
## Domínio: https://app.maintrix.com.br

---

## HOTFIX P0 — REACT ERROR #31 EM ERROS DE VALIDAÇÃO (22/07/2026)

### Tela/Ação
Qualquer formulário que submete dados ao backend e recebe 422 (Pydantic validation).
Mais crítico: FieldOpsPage (criar OS), DocConfigPage, LayoutBuilderPage, BibliotecaCorporativaPage, DossierEditTab.

### Endpoint
Qualquer rota FastAPI com modelo Pydantic (ex: POST /api/ordens-servico).

### Campo que causou 422
Qualquer campo obrigatório ausente ou tipo inválido (ex: ativo_id, data_planejada).

### Causa Raiz
`toast.error(e.response?.data?.detail)` renderizava diretamente o array Pydantic `[{type, loc, msg, input, url}]` como React child → Error #31.

### Arquivos Alterados (8)
1. `frontend/src/lib/api.js` — safeErrorMsg() (novo)
2. `frontend/src/lib/constants.js` — normalizeError + formatApiDetail (melhorado)
3. `frontend/src/App.js` — payload sanitization (procedimento_id, causa_falha → null)
4. `frontend/src/pages/FieldOpsPage.js` — guard typeof string
5. `frontend/src/pages/BibliotecaCorporativaPage.js` — safeErrorMsg (5 calls)
6. `frontend/src/pages/DocConfigPage.js` — safeErrorMsg (5 calls)
7. `frontend/src/pages/LayoutBuilderPage.js` — safeErrorMsg (3 calls)
8. `frontend/src/pages/DossierEditTab.js` — safeErrorMsg (3 calls)
9. `frontend/src/components/widgets/ExportButtons.js` — safeErrorMsg (1 call)

### Testes: 11/11 backend + frontend PASS

---

## HOTFIX P0 — PROCEDIMENTO NO PDF (22/07/2026) ✅
## RC CORREÇÃO PDF OS (22/07/2026) ✅
## FIX preview_numeracao (22/07/2026) ✅
## RC CORREÇÃO PRÉ-PILOTO (22/07/2026) ✅

---

## POST-PILOTO BACKLOG
1. P2: Inserir CNPJ nos Termos de Uso (aguardando dados oficiais)
2. P2: Remover fallback Emergent Storage
3. P2: Adicionar mais chaves ao FIELD_LABEL_MAP (procedimento_id, causa_falha, data_planejada)
4. P2: Validador Pydantic para datetime em OSCreate.data_planejada
5. P1: RC6.1 — Construtor de Seções da OS
6. P3: Cadastro colaboradores, Turnos, Equipes, Indicadores
