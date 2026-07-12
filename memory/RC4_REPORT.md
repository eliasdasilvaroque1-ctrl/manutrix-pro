# RC4.0 — Asset Dossier Report

**Data:** 2026-07-12  
**Versao:** 5.2.0-RC4  
**Status:** CONCLUIDO  

---

## Implementacao

### Backend: `GET /api/ativos/{id}/dossie`

Endpoint unico que agrega todos os dados do ativo em uma unica chamada:

| Dado | Fonte | Campos |
|------|-------|--------|
| Ativo | `ativos` | tag, nome, fabricante, modelo, serie, criticidade, status, sector |
| OS | `ordens_servico` | todas por ativo_id (numero, titulo, tipo, status, responsavel, datas, materiais) |
| Inspecoes | `inspecoes` | todas por ativo_id (tipo, status, resultado, checklist, fotos, responsavel) |
| Planos | `planos_inspecao` | diretos (ativo_id) + genericos (tipo_equipamento) |
| Solicitacoes | `solicitacoes` | todas por ativo_id |
| Documentos | `manuais` + `attachments` | manuais PDF + anexos |
| KPIs | calculados | MTBF, MTTR, Disponibilidade, custos, contadores |
| Nomes | `users` | responsaveis e solicitantes enriched |
| Plano nomes | `planos_inspecao` | nome do plano nas inspecoes |

### KPIs Calculados

| Indicador | Formula | Exemplo |
|-----------|---------|---------|
| MTBF | 720h / total_falhas_corretivas | 180h |
| MTTR | media(tempo_reparo_corretivas) / 60 | 2h |
| Disponibilidade | MTBF / (MTBF + MTTR) * 100 | 98.9% |
| Custo Materiais | soma(material.custo * material.qtd) | R$ 0,00 |
| Custo HH | soma(tempo_min/60 * R$80) | R$ 700,00 |
| Custo Total | materiais + HH | R$ 700,00 |

### Frontend: `AssetDossierPage.js` (rota `/ativos/:id`)

**8 abas implementadas:**

| Aba | Conteudo | Filtros |
|-----|----------|---------|
| Visao Geral | Cards (OS abertas, atrasadas, insp pendentes, solicitacoes, total OS, total inspecoes), ultima inspecao, proxima preventiva, custos acumulados | — |
| OS | Lista completa com numero, titulo, tipo, status, prioridade, responsavel, data | Por status (todas, aberta, em_execucao, concluida, programada) |
| Planos | Lista de planos aprovados com tipo, disciplina, frequencia, quantidade de perguntas, versao, status | — |
| Inspecoes | Historico com resultado, tipo, responsavel, duracao, fotos thumbnail | Por status (todas, concluida, pendente, em_andamento, com_pendencias) |
| Solicitacoes | Timeline com descricao, tipo, status, solicitante, data | — |
| Documentos | Manuais (PDF com download) + Anexos (com visualizacao) | — |
| Historico | Timeline visual com icones coloridos por tipo (OS, inspecao, anomalia, material, parada), filtro por tipo | Por tipo (todos, os, inspecao, anomalia, material, parada) |
| Indicadores | Disponibilidade, MTBF, MTTR, HH Total, OS por tipo, custos, inspecoes/pendentes/falhas | — |

### Componentes

| Componente | Responsabilidade |
|-----------|-----------------|
| `DossierHeader` | Cabecalho com tag, nome, area, fabricante, modelo, serie, criticidade, status + KPIs inline |
| `TabVisaoGeral` | 6 cards + ultima inspecao + proxima preventiva + custos |
| `TabOS` | Lista filtrada + navegacao para detalhe |
| `TabPlanos` | Lista de planos com metadata |
| `TabInspecoes` | Lista filtrada + fotos thumbnail |
| `TabSolicitacoes` | Lista com status e solicitante |
| `TabDocumentos` | Manuais PDF + anexos com download/visualizacao |
| `TabHistorico` | Timeline visual com lazy loading |
| `TabIndicadores` | KPIs + OS por tipo + custos + inspecoes |

---

## Validacao

| Criterio | Resultado |
|----------|-----------|
| `CI=true yarn build` | PASS (zero warnings) |
| 19/19 rotas (18 + /ativos/:id dossie) | PASS |
| PAGE ERROR | Zero |
| Dossie endpoint | 200 (dados completos) |
| Header KPIs | 98.9% Disp, 180h MTBF, 2h MTTR |
| 8 abas renderizam | Confirmado via screenshot |
| Zero regressoes | Confirmado |
| Banco inalterado | Nenhuma collection nova |

## Arquivos

| Arquivo | Acao |
|---------|------|
| `frontend/src/pages/AssetDossierPage.js` | NOVO — pagina completa do dossie |
| `frontend/src/App.js` | Import + rota /ativos/:id → AssetDossierPage |
| `backend/routes/assets.py` | +endpoint `/ativos/{id}/dossie` |

---

*RC4.0 concluida. Aguardando autorizacao do CTO.*
