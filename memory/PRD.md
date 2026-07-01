# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 7.1.0

---

## Sprint 55: PRONTUÁRIO DO ATIVO ✅ (iteration_55 — 9/9 backend + 27/27 frontend)

### Conceito
A principal tela de consulta do MAINTRIX. Toda a vida do equipamento em uma única tela.

### Seções Implementadas
1. **Identificação**: TAG, Nome, Área, Tipo, Fabricante, Modelo, Série, Criticidade, Status, QR Code
2. **KPIs**: Total OS, Falhas, Disponibilidade %, MTBF
3. **Saúde do Equipamento**: 8 cards (última/próxima inspeção, preventiva, lubrificação, OS, anomalia, MTTR)
4. **Planos Permanentes**: Grid de planos aprovados com disciplina, versão, perguntas
5. **OS em Aberto**: Lista com prioridade e status
6. **Últimos Eventos**: Preview da timeline com ícones e datas
7. **Tabs**: Prontuário, Timeline (com filtros e separadores de data), Planos, OS (por status), Docs, BOM

### Endpoint Backend
- `GET /api/ativos/{id}/saude` — resumo de saúde (última/próxima de cada tipo)

---

## Histórico Completo
- Sprint 54: Homologação ASTEC Cedro (61 ativos, 86 planos, 24 OS)
- Sprint 53: Usabilidade planos (hierarquia, duplicidade, painel)
- Sprint 52: Central de Trabalho adaptativa
- Sprint 51: Fluxo Inspeções (Plano Permanente → Execução)
- Sprint 50: RBAC por Disciplina/Área
- Sprint 48: Biblioteca de Modelos

## PRÓXIMO
- Sprint 56: Wizard "Criar Planos ao Cadastrar Ativo"
- Sprint 57: Padronização ciclo de vida
- Sprint 58: Revisão UX
- Sprint 59: Cliente Piloto
- Sprint 60: Dashboard Executivo (BLOCO C)
