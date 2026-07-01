# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 7.0.0

---

## SPRINT DE HOMOLOGAÇÃO ✅ (iteration_54 — 12/12 backend + 6/6 frontend)

### Planta ASTEC Cedro — Operacional
| Item | Quantidade |
|------|-----------|
| Áreas | 4 (Britagem Primária, Britagem Secundária, Pátio de Estocagem, Expedição) |
| Ativos | 61 (Britadores, Alimentadores, Correias, Peneiras, Motores, Redutores, Bombas, Compressores, Balança) |
| Planos Aprovados | 86 (Mecânica, Elétrica, Lubrificação, Operacional) |
| Ordens de Serviço | 24 (variados status/prioridades/datas) |
| Inspeções Pendentes | 45 (distribuídas na semana) |

### Resultados da Homologação
- **0 bugs funcionais** encontrados
- **Visibilidade RBAC** validada end-to-end (master/admin/pcm/supervisor/técnico/operador)
- **Central de Trabalho** adaptativa por perfil: confirmada
- **Planos → Execuções** fluxo completo: confirmado
- **OS com sector_id denormalizado**: confirmado

### Melhorias implementadas
- Filtro de busca na página de Planos (pesquisa + disciplina + status)
- Seletor de ativo com hierarquia completa
- Validação de duplicidade de planos

---

## Versões Anteriores
- 6.2: Usabilidade planos (hierarquia, duplicidade, painel planos no ativo)
- 6.1: Central de Trabalho adaptativa por perfil
- 6.0: Fluxo Inspeções (Plano Permanente → Execução)
- 5.3: RBAC por Disciplina/Área, Bug Plano "Field required"
- 5.0: Biblioteca de Modelos, Classificação Técnica
- 4.0: Enterprise org_config, White Label, Terminologia
- 3.0: Event Sourcing, Cronômetro, Equipe
- 2.0: Admin Master, Kanban, Filtros
- 1.0: MVP inicial

## PRÓXIMO
- Wizard "Criar Planos ao Cadastrar Ativo" (deseja criar planos agora? Sim/Depois)
- Histórico resumido no Ativo (última inspeção/preventiva/OS/lubrificação)
- Ciclo de vida: Programada → Disponível → Em Execução → Pausada → Concluída → Reprogramada

## DEPOIS: BLOCO C
- Dashboard Supervisor Executivo, Indicadores, Exportação
