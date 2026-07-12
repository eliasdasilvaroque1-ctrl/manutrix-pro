# RC2.1 — Relatório de Correção de Regressões da Modularização

**Data:** 2026-07-12  
**Autorização:** RC2.1 — Correção de Regressões  
**Status:** CONCLUÍDO  

## Resumo

6 rotas do frontend quebraram durante a modularização (extração de páginas do `App.js` monolítico). Todas foram corrigidas sem alterar layout, lógica de negócio, APIs, rotas ou banco de dados.

## Erros Encontrados e Corrigidos

| # | Página | Erro Original | Causa Raiz | Correção |
|---|--------|---------------|------------|----------|
| 1 | EstoquePage | `useSearchParams is not defined` | Import não extraído junto com a página | Adicionado `import { useSearchParams } from "react-router-dom"` + movido `ModalNovoEstoque` do App.js |
| 2 | InspecoesPages | `useSearchParams is not defined` | Import não extraído | Adicionado `useSearchParams` ao import existente + `ConfirmDialog` + movido `ModalNovaInspecao` e `CameraCapture` do App.js |
| 3 | SobressalentesPage | `ORIGEM_OPTIONS is not defined` | Constantes ficaram em outro arquivo | Adicionados `ORIGEM_OPTIONS`, `CONDICAO_CONFIG` localmente + import de `MaterialThumbnail/ImageModal/ImageUploader` |
| 4 | ParadasPage | `PARADA_TIPOS is not defined` | Constantes não definidas no arquivo | Adicionados `PARADA_TIPOS`, `FIELD_TYPES` localmente + `Navigate` no import do react-router-dom |
| 5 | BibliotecaPage | `ConfirmDialog is not defined` | Import faltante do shared | Adicionado `ConfirmDialog` ao import de `@/components/shared` |
| 6 | EquipePage | `EmptyState is not defined` | Import faltante do shared | Adicionado `EmptyState` ao import de `@/components/shared` |

## Erro Adicional Encontrado e Corrigido

| Componente | Erro | Correção |
|------------|------|----------|
| ProtectedRoute (ParadasPage.js) | `Navigate is not defined` | Adicionado `Navigate` ao import de react-router-dom |

## Arquivos Modificados

| Arquivo | Ação | Linhas Antes | Linhas Depois | Delta |
|---------|------|-------------|---------------|-------|
| `src/pages/EstoquePage.js` | Adicionados imports + ModalNovoEstoque | 210 | 396 | +186 |
| `src/pages/InspecoesPages.js` | Adicionados imports + CameraCapture + ModalNovaInspecao, removidas constantes mortas | 1388 | 1657 | +269 |
| `src/pages/SobressalentesPage.js` | Adicionadas constantes + imports Material | 608 | 623 | +15 |
| `src/pages/ParadasPage.js` | Adicionadas constantes + Navigate | 1530 | 1546 | +16 |
| `src/pages/BibliotecaPage.js` | Adicionado ConfirmDialog ao import | 184 | 183 | -1 |
| `src/pages/EquipePage.js` | Adicionado EmptyState ao import | 147 | 146 | -1 |
| `src/App.js` | Removidos componentes migrados (ModalNovoEstoque, ModalNovaInspecao, CameraCapture) | 4541 | 3950 | -591 |

## App.js — Evolução

- **Original (pré-modularização):** 11.040 linhas
- **Após extração fase 1:** 4.541 linhas
- **Após RC2.1 (limpeza de código morto):** 3.950 linhas
- **Redução total:** 64.2%

## Validação

- [x] CI=true yarn build: **PASS** (zero warnings, zero errors)
- [x] Navegação todas as 6 rotas: **PASS**
- [x] Console logs: **zero PAGE ERROR**
- [x] Nenhuma alteração visual
- [x] Nenhuma alteração funcional
- [x] Nenhuma regressão introduzida
- [x] Nenhuma dependência nova instalada
