# MAINTRIX ENTERPRISE — PRD

## Status: RC IMPORTAÇÃO ESTOQUE EXCEL — APROVADO
## Versao: pilot-astec-v1.5.0-rc
## Domínio: https://app.maintrix.com.br

---

## RC — IMPORTAÇÃO INICIAL DE ESTOQUE POR EXCEL (23/07/2026)

### Fluxo Criado
1. Botão "Importar Planilha" na tela de Estoque (visível para Master/Admin/PCM)
2. Modal com instruções e download do modelo oficial .xlsx
3. Upload e validação server-side (códigos, tipos, duplicidades)
4. Pré-visualização com resumo (válidos/advertências/existentes/duplicados/inválidos)
5. Confirmação antes de importar
6. Importação em lote com `import_batch_id` para auditoria
7. Relatório final (importados, conferidos, não conferidos, ignorados)
8. Indicadores no topo: Valor Estimado, Cobertura do Inventário, Total de Itens

### Arquivos Alterados/Criados (3)
1. `backend/routes/estoque_import.py` (NOVO) — template, validate, confirm, indicadores
2. `backend/server.py` — import + include_router (2 linhas)
3. `frontend/src/pages/EstoquePage.js` — ImportExcelModal, indicadores, filtro conferido

### Campos Utilizados
- Reutiliza modelo existente `itens_estoque`: sku, nome, unidade, custo_unitario, quantidade
- Campos NOVOS (aditivos): `saldo_conferido`, `origem_cadastro`, `import_batch_id`
- Nenhum campo existente removido ou alterado

### Regras de Duplicidade
- Código existente no banco → marcado "Existente", ignorado
- Código duplicado na planilha → ambas linhas rejeitadas
- Importação repetida → detecta existentes, não duplica

### Regra de Saldo Conferido
- Quantidade vazia → saldo=0, saldo_conferido=false ("Não conferido")
- Quantidade zero explícito → saldo=0, saldo_conferido=true ("Conferido")
- Quantidade positiva → saldo=valor, saldo_conferido=true ("Conferido")

### Permissões
- Master, Admin, PCM: permitidos
- Técnico, Operador, etc.: bloqueados (403)
- Isolamento multiempresa via organization_id

### Validações
- Extensão .xlsx obrigatória
- Tamanho máx: 5MB, 5000 linhas
- Colunas obrigatórias: codigo, descricao, unidade, valor_unitario
- Valor aceita formatos: 1250, 1250.50, 1.250,50, R$ 1.250,50
- Valores negativos rejeitados

### Indicadores
- Valor Estimado: SUM(quantidade × custo_unitario) WHERE saldo_conferido=true
- Cobertura: itens_conferidos / total_itens × 100
- Total de Itens: contagem geral

### Testes: 15/15 backend + frontend PASS
- Template download ✅
- Validação com itens válidos/inválidos ✅
- Duplicidades detectadas ✅
- Importação em lote ✅
- Indicadores calculados ✅
- Permissões verificadas ✅
- Regressão CRUD estoque ✅
- Frontend: indicadores, botão, modal, filtro ✅

---

## HOTFIX P0 — REACT ERROR #31 VALIDAÇÃO (22/07/2026) ✅
## HOTFIX P0 — PROCEDIMENTO PDF (22/07/2026) ✅
## RC CORREÇÃO PDF OS (22/07/2026) ✅
## RC CORREÇÃO PRÉ-PILOTO (22/07/2026) ✅

---

## POST-PILOTO BACKLOG
1. P2: Inserir CNPJ nos Termos de Uso (aguardando dados oficiais)
2. P2: Remover fallback Emergent Storage
3. P2: Migrar saldo_conferido=false para itens legados
4. P1: RC6.1 — Construtor de Seções da OS
5. P3: Cadastro colaboradores, Turnos, Equipes, Indicadores
