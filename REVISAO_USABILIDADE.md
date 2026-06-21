# MANUTRIX OMNI - REVISAO OPERACIONAL DE USABILIDADE
## Pre-Piloto ASTEC | Fevereiro 2026

> **Objetivo:** Identificar melhorias de usabilidade, campos faltantes e otimizacoes de produtividade para Tecnico, PCM e Gerencia. Nenhuma funcionalidade nova sera criada.

---

## LEGENDA DE PRIORIDADE
- **CRITICA** - Impacta diretamente a operacao em campo. Deve ser corrigido antes do piloto.
- **IMPORTANTE** - Melhora significativamente a produtividade. Implementar durante o piloto.
- **OPCIONAL** - Nice-to-have. Implementar apos validacao do piloto.

---

## 1. ATIVOS

### CRITICA
| # | Melhoria | Justificativa |
|---|----------|---------------|
| A1 | **Status do ativo visivel na listagem** | A lista de ativos nao mostra se o equipamento esta Operacional, Parado ou em Manutencao. O tecnico precisa saber imediatamente quais equipamentos estao indisponiveis. O modelo `AssetStatus` ja existe no backend (operacional, parado, manutencao, desativado) mas nao esta sendo usado no frontend. |
| A2 | **Contador de OS abertas por ativo na listagem** | Na lista de ativos, nao ha indicacao de quantas OS estao pendentes para cada equipamento. Um badge numerico ao lado do ativo ajuda o PCM a priorizar. |

### IMPORTANTE
| # | Melhoria | Justificativa |
|---|----------|---------------|
| A3 | **KPIs do ativo visiveis no card de lista (MTBF/MTTR mini)** | Os KPIs (MTBF, MTTR, disponibilidade) so sao visiveis na pagina de detalhe. Um indicador visual resumido (cor verde/amarelo/vermelho) na lista ajuda a Gerencia a identificar ativos criticos sem clicar em cada um. |
| A4 | **Campo "Localizacao" no cadastro do ativo** | O modelo Pydantic `AtivoCreate` nao possui campo de localizacao fisica (ex: "Galpao 2, Nivel 3"). Em plantas grandes, saber onde o equipamento esta fisicamente e essencial para o tecnico em campo. |
| A5 | **Indicador visual "Ultima Inspecao" na lista de ativos** | Nao ha como saber rapidamente quando foi a ultima inspecao de cada ativo. Um texto "Ha X dias" ou cor (verde < 7d, amarelo < 30d, vermelho > 30d) ajuda o PCM a identificar equipamentos negligenciados. |

### OPCIONAL
| # | Melhoria | Justificativa |
|---|----------|---------------|
| A6 | **Filtro por tipo de equipamento na listagem** | Atualmente so filtra por Area. Um filtro por tipo (Bomba, Motor, Compressor) facilita a gestao quando ha muitos ativos. |
| A7 | **Foto principal do ativo no card da lista** | Ativos com foto sao mais faceis de identificar em campo. Um thumbnail pequeno no card da listagem melhora a navegacao visual. |

---

## 2. ORDENS DE SERVICO (OS)

### CRITICA
| # | Melhoria | Justificativa |
|---|----------|---------------|
| OS1 | **Busca/filtro no Kanban** | O Kanban nao tem campo de busca. Com 50+ OS abertas, encontrar uma OS especifica por numero, titulo ou ativo e impossivel sem rolar todas as colunas. Um campo de busca no topo do Kanban e essencial. |
| OS2 | **Filtro por prioridade no Kanban/Lista** | Nao ha filtro por prioridade (Emergencia, Critica, Alta). O PCM precisa ver rapidamente todas as OS criticas independente do status. |

### IMPORTANTE
| # | Melhoria | Justificativa |
|---|----------|---------------|
| OS3 | **Data de criacao visivel no card do Kanban** | Os cards do Kanban mostram numero, titulo, ativo e prioridade, mas nao mostram ha quanto tempo a OS foi criada. Um "Ha X dias" ajuda a identificar OS esquecidas. |
| OS4 | **Indicador "ATRASADA" mais visivel** | O campo `atrasada` existe no card, mas so aparece como texto pequeno. Para OS atrasadas, o card inteiro deveria ter borda vermelha ou background diferenciado. |
| OS5 | **Filtro por disciplina (Mecanica/Eletrica) na lista** | Atualmente o filtro e so por status. Adicionar filtro por disciplina e por tipo (Corretiva/Preventiva) permite ao PCM focar na sua area de responsabilidade. |
| OS6 | **Campo "Descricao do Servico" obrigatorio na conclusao** | Ja e obrigatorio no frontend (validacao JS), mas reforcar no backend tambem. E critico para rastreabilidade. |
| OS7 | **Nome da Area visivel no card do Kanban** | O card mostra tag do ativo mas nao a area. Em plantas com muitas areas, saber a localizacao e essencial para despacho de tecnicos. |

### OPCIONAL
| # | Melhoria | Justificativa |
|---|----------|---------------|
| OS8 | **Filtro "Minhas OS" para o Tecnico** | O tecnico ve todas as OS. Um toggle "Minhas OS" que filtra por `responsavel_id` ou `equipe` do usuario logado melhora o foco. |
| OS9 | **Contador de materiais consumidos no card** | No card do Kanban ou lista, mostrar quantos materiais ja foram consumidos da OS ajuda o PCM a acompanhar custos. |

---

## 3. INSPECOES

### CRITICA
| # | Melhoria | Justificativa |
|---|----------|---------------|
| I1 | **Filtro por status na listagem de inspecoes** | A lista de inspecoes nao tem filtros. Com centenas de inspecoes, o tecnico precisa filtrar por Pendentes, Em Andamento, Concluidas para ver seu backlog. |
| I2 | **Filtro por ativo/area na listagem** | Nao ha como filtrar inspecoes por area ou equipamento especifico. Essencial para o PCM acompanhar a cobertura de inspecoes por area. |

### IMPORTANTE
| # | Melhoria | Justificativa |
|---|----------|---------------|
| I3 | **Indicador de progresso do checklist** | Na tela de execucao da inspecao, o tecnico nao ve quantos itens ja respondeu de forma rapida (ex: "8/15 respondidos"). O contador existe no topo mas e discreto. Uma barra de progresso visual tornaria mais claro. |
| I4 | **Botao "Proxima Inspecao" apos concluir** | Ao concluir uma inspecao, o tecnico e redirecionado para a lista. Um botao "Proxima inspecao pendente" agiliza o fluxo de ronda sem voltar a lista. |
| I5 | **Data da ultima inspecao por ativo na lista** | Ao ver a lista de inspecoes, nao fica claro quando foi a ultima inspecao de cada ativo. Mostrar isso ajuda a priorizar. |

### OPCIONAL
| # | Melhoria | Justificativa |
|---|----------|---------------|
| I6 | **Scroll automatico para o proximo item nao respondido** | Durante a execucao do checklist, ao responder um item, o scroll poderia ir automaticamente para o proximo item nao respondido, agilizando o preenchimento em campo. |

---

## 4. ANOMALIAS

### CRITICA
*Nenhuma melhoria critica identificada. O modulo esta funcional.*

### IMPORTANTE
| # | Melhoria | Justificativa |
|---|----------|---------------|
| AN1 | **Filtro por severidade na lista** | Alem do filtro por status (que ja existe), adicionar filtro por severidade (Critica, Alta) permite focar nas anomalias mais urgentes. |
| AN2 | **Contador de dias aberta** | Na lista de anomalias, mostrar "Ha X dias" desde a criacao. Anomalias abertas ha muito tempo indicam problemas de processo. |
| AN3 | **Notificacao ao responsavel quando status muda** | Quando o status de uma anomalia muda (ex: de "aberta" para "em_analise"), o responsavel do ativo deveria receber notificacao. |

### OPCIONAL
| # | Melhoria | Justificativa |
|---|----------|---------------|
| AN4 | **Campo "Acao Corretiva" visivel na lista** | Na lista, so aparece a descricao da anomalia. Mostrar se ja tem OS gerada ou acao corretiva planejada. |

---

## 5. ESTOQUE

### CRITICA
| # | Melhoria | Justificativa |
|---|----------|---------------|
| E1 | **Historico de movimentacoes visivel na lista** | O usuario ve a quantidade atual mas nao tem acesso rapido ao historico de movimentacoes (entrada, saida, devolucao). Um link "Ver movimentacoes" ou expandir o card com as ultimas 5 movimentacoes e essencial para controle. |

### IMPORTANTE
| # | Melhoria | Justificativa |
|---|----------|---------------|
| E2 | **Filtro por categoria** | O backend ja suporta filtro por categoria (`?categoria=rolamento`), mas o frontend nao tem esse seletor. Adicionar dropdown de categoria na barra de filtros. |
| E3 | **Valor total em estoque visivel** | Na pagina de estoque, nao ha um resumo financeiro (total de itens, valor total em estoque). Uma linha de resumo no topo ajuda a Gerencia. |
| E4 | **Indicador visual de itens criticos mais destacado** | Itens criticos tem borda vermelha, mas em uma lista longa, um bloco fixo no topo "X itens criticos" com link direto seria mais efetivo. |

### OPCIONAL
| # | Melhoria | Justificativa |
|---|----------|---------------|
| E5 | **Botao de movimentacao rapida na lista** | Atualmente, para registrar entrada/saida, precisa ir ao detalhe do item. Um botao rapido "Entrada" / "Saida" direto na lista agiliza o processo do almoxarife. |
| E6 | **Filtro por almoxarifado** | Se houver multiplos almoxarifados, filtrar por local fisico. |

---

## 6. SOBRESSALENTES

### CRITICA
*Nenhuma melhoria critica identificada. O modulo esta funcional com condicoes, reformas e exportacao.*

### IMPORTANTE
| # | Melhoria | Justificativa |
|---|----------|---------------|
| S1 | **Filtro por condicao (Novo/Reformado/Em Reforma)** | A lista mostra as condicoes por item, mas nao ha filtro. O PCM precisa listar rapidamente "todos os sobressalentes em reforma" ou "todos os novos disponiveis". |
| S2 | **Vinculacao com ativo mais visivel** | O campo `ativo_vinculado` existe mas nao tem destaque. Mostrar claramente qual ativo o sobressalente atende ajuda na rastreabilidade. |
| S3 | **Alertas de reforma vencida** | Se um sobressalente esta em reforma ha mais de X dias (sem data de retorno), alertar o PCM. |

### OPCIONAL
| # | Melhoria | Justificativa |
|---|----------|---------------|
| S4 | **Campo "Numero de Serie" no sobressalente** | O modelo `SpareAssetCreate` ja tem `numero_serie`, mas nao esta sendo exibido no formulario de criacao. Adicionar ao form. |

---

## 7. HISTORICO DO EQUIPAMENTO

### CRITICA
*Nenhuma melhoria critica identificada. O historico unificado com 5 filtros e 5 tipos de evento esta completo.*

### IMPORTANTE
| # | Melhoria | Justificativa |
|---|----------|---------------|
| H1 | **Exportar historico do ativo em PDF** | O historico unificado (OS + Inspecoes + Anomalias + Materiais + Paradas) e valioso para auditorias externas. Um botao "Exportar Prontuario PDF" com todos os eventos filtrados seria muito util para o Gerente. |
| H2 | **Paginacao ou "carregar mais"** | Se um ativo tiver centenas de eventos, carregar tudo de uma vez pode ser lento. Implementar paginacao ou scroll infinito. |

### OPCIONAL
| # | Melhoria | Justificativa |
|---|----------|---------------|
| H3 | **Grafico de timeline visual** | Alem da lista textual, um grafico de timeline (eixo X = tempo, pontos = eventos coloridos por tipo) daria uma visao mais intuitiva do historico. |

---

## 8. PARADAS PROGRAMADAS

### CRITICA
*Nenhuma melhoria critica identificada. O modulo esta completo com indicadores.*

### IMPORTANTE
| # | Melhoria | Justificativa |
|---|----------|---------------|
| P1 | **Barra de progresso das OS na lista** | Na lista de paradas, mostrar uma barra de progresso visual (OS concluidas / OS total) ao inves de apenas numeros. Mais intuitivo para acompanhamento rapido. |
| P2 | **Status "Em Execucao" / "Concluida" na parada** | Atualmente a parada so tem status "planejada". Adicionar transicoes: planejada -> em_execucao -> concluida. Quando todas as OS vinculadas forem concluidas, sugerir conclusao automatica. |
| P3 | **Filtro por area e status** | O backend ja suporta filtros (`?area_id=&status=`), mas o frontend nao tem seletores. Adicionar. |

### OPCIONAL
| # | Melhoria | Justificativa |
|---|----------|---------------|
| P4 | **Calendario visual das paradas** | Uma visao de calendario mostrando quando cada parada esta programada (em vez de lista). Util para planejamento de longo prazo. |

---

## RESUMO POR PRIORIDADE

### CRITICAS (Resolver antes do piloto)
| Cod | Modulo | Resumo |
|-----|--------|--------|
| A1 | Ativos | Status do ativo visivel na listagem |
| A2 | Ativos | Contador de OS abertas por ativo |
| OS1 | OS | Busca/filtro no Kanban |
| OS2 | OS | Filtro por prioridade |
| I1 | Inspecoes | Filtro por status |
| I2 | Inspecoes | Filtro por ativo/area |
| E1 | Estoque | Historico de movimentacoes acessivel |

**Total: 7 itens criticos**

### IMPORTANTES (Implementar durante o piloto)
| Cod | Modulo | Resumo |
|-----|--------|--------|
| A3 | Ativos | KPIs mini na lista |
| A4 | Ativos | Campo Localizacao |
| A5 | Ativos | Ultima inspecao na lista |
| OS3 | OS | Data de criacao no Kanban |
| OS4 | OS | Indicador ATRASADA mais visivel |
| OS5 | OS | Filtro por disciplina |
| OS6 | OS | Servico obrigatorio na conclusao (backend) |
| OS7 | OS | Nome da area no Kanban |
| I3 | Inspecoes | Barra de progresso do checklist |
| I4 | Inspecoes | Botao proxima inspecao |
| I5 | Inspecoes | Data ultima inspecao na lista |
| AN1 | Anomalias | Filtro por severidade |
| AN2 | Anomalias | Dias aberta na lista |
| AN3 | Anomalias | Notificacao de status |
| E2 | Estoque | Filtro por categoria |
| E3 | Estoque | Valor total em estoque |
| E4 | Estoque | Bloco fixo de criticos |
| S1 | Sobressalentes | Filtro por condicao |
| S2 | Sobressalentes | Vinculacao ativo mais visivel |
| S3 | Sobressalentes | Alerta reforma vencida |
| H1 | Historico | Export prontuario PDF |
| H2 | Historico | Paginacao |
| P1 | Paradas | Barra de progresso OS |
| P2 | Paradas | Status em_execucao/concluida |
| P3 | Paradas | Filtro por area/status |

**Total: 25 itens importantes**

### OPCIONAIS (Pos-piloto)
| Cod | Modulo | Resumo |
|-----|--------|--------|
| A6 | Ativos | Filtro por tipo equipamento |
| A7 | Ativos | Foto thumbnail na lista |
| OS8 | OS | Toggle "Minhas OS" |
| OS9 | OS | Materiais no card |
| I6 | Inspecoes | Auto-scroll checklist |
| AN4 | Anomalias | Acao corretiva na lista |
| E5 | Estoque | Movimentacao rapida |
| E6 | Estoque | Filtro por almoxarifado |
| S4 | Sobressalentes | Numero serie no form |
| H3 | Historico | Grafico timeline |
| P4 | Paradas | Calendario visual |

**Total: 11 itens opcionais**

---

## RECOMENDACAO DE IMPLEMENTACAO

### Antes do Piloto (1-2 dias)
Implementar os **7 itens criticos**. Sao todos filtros e campos visuais — nenhum requer alteracao de banco de dados ou logica de negocio complexa. Estimativa: 1 dia de desenvolvimento + 1 dia de teste.

### Durante o Piloto (15 dias)
Observar o uso real e priorizar os itens **importantes** conforme feedback da equipe ASTEC. Nao implementar todos de uma vez — esperar validacao em campo.

### Pos-Piloto
Avaliar itens opcionais com base nos dados reais de uso.

---

*Documento gerado automaticamente. Versao 1.0 - Fevereiro 2026*
