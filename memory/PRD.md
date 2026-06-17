# MANUTRIX OMNI — Product Requirements Document

## FASE OPERACIONAL — Rastreabilidade e Execução

### Bloco 1: Poderes do PCM ✅
### Bloco 2: Executantes + Rastreabilidade ✅

### Bloco 3: Materiais Utilizados + Movimentação de Estoque ✅ (2026-06-17)

**Pré-requisito (Última alteração por):**
- [x] `alterado_por` + `updated_at` em OS, Inspeções, Anomalias
- [x] Enriquecido com nome no GET de cada entidade

**Materiais na OS:**
- [x] POST /api/ordens-servico/{id}/materiais — Adiciona material, deduz estoque
- [x] GET /api/ordens-servico/{id}/materiais — Lista materiais consumidos
- [x] DELETE /api/ordens-servico/{id}/materiais/{mat_id} — Devolve ao estoque

**Movimentação de Estoque:**
- [x] GET /api/movimentacoes — Histórico global com filtros
- [x] Filtros: item_id, ativo_id, usuario_id, os_id, tipo
- [x] Campos: data, hora, usuario, codigo, descricao, quantidade, OS, equipamento, tipo

**Bloqueios:**
- [x] Estoque negativo → HTTP 400
- [x] Consumo sem item_estoque_id → HTTP 400
- [x] Consumo com quantidade ≤ 0 → HTTP 400

**Frontend:**
- [x] Seção "Materiais Utilizados" no detalhe da OS
- [x] Botão "Adicionar" com modal de seleção
- [x] Botão "Devolver" para admin/pcm/supervisor
- [x] Total de custo exibido
- [x] "Última alteração por" na rastreabilidade

**Testes:** iteration_31 — Backend 12/12, Frontend 6/6

### Bloco 4: Auditoria Detalhada (PRÓXIMO)
### Bloco 5: Histórico do Equipamento com Filtros
### Bloco 6: Detalhamento Completo da OS
### Bloco 7: Detalhamento Completo da Inspeção

## Regra de Ouro
> Parar após cada bloco. Entregar evidências. Aguardar aprovação.
