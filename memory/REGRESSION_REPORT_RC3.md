# REGRESSION REPORT — RC3.2.1

**Data:** 2026-07-12  

---

## Resultado: ZERO REGRESSÕES

Nenhuma regressão introduzida pelas releases RC3.1 e RC3.2.

### Verificações Realizadas

| # | Teste | Status |
|---|-------|--------|
| 1 | Build `CI=true yarn build` | ✅ PASS (zero warnings) |
| 2 | 18/18 rotas navegáveis (17 originais + /minha-area) | ✅ PASS |
| 3 | Login master (com org_id) | ✅ PASS |
| 4 | Login admin (com org_id) | ✅ PASS |
| 5 | Login PCM (com org_id) | ✅ PASS |
| 6 | Login supervisor (com org_id) | ✅ PASS |
| 7 | Login operador (com org_id) | ✅ PASS |
| 8 | Login técnico (com org_id) | ✅ PASS |
| 9 | Login auto-resolve (admin sem org_id) | ✅ PASS |
| 10 | Login master sem org_id (rejeita) | ✅ PASS |
| 11 | Criar OS (execução direta) | ✅ PASS |
| 12 | Concluir OS (com hora inicio/final) | ✅ PASS |
| 13 | Imprimir OS (PDF) | ✅ PASS (3949+ bytes, PDF válido) |
| 14 | Endpoint /minha-area | ✅ 200 (55 equipamentos) |
| 15 | Endpoint /indicadores (4 períodos) | ✅ 200 |
| 16 | Endpoint /health | ✅ 200 (healthy) |
| 17 | Zero PAGE ERROR | ✅ |
| 18 | Zero ReferenceError | ✅ |
| 19 | Zero orphan imports | ✅ |
| 20 | Logo sidebar carregando | ✅ |

### Dead Code (Pré-existente — não introduzido)

| Arquivo | Item |
|---------|------|
| `SobressalentesPage.js` | `FIELD_TYPES`, `PARADA_TIPOS` (duplicados, não usados neste arquivo) |
| `WhiteLabelDesignerPage.js` | `QRLabelModal` (referência única) |
