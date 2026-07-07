# CRITÉRIOS PARA ACEITAR UMA NOVA FUNCIONALIDADE
## MAINTRIX ENTERPRISE — Piloto ASTEC
### Versão: v1.0.0-RC1 | Data: Fev/2026

---

## Protocolo de Avaliação

Toda solicitação de nova funcionalidade DEVE responder às 5 perguntas abaixo antes de ser considerada:

| # | Pergunta | Resposta Esperada |
|---|----------|-------------------|
| 1 | **Quem pediu?** | Nome, cargo e organização do solicitante |
| 2 | **Quantos usuários serão beneficiados?** | Estimativa de impacto (1 usuário, 1 equipe, toda organização, todos os tenants) |
| 3 | **Resolve um problema real?** | Descrição do problema concreto observado em campo |
| 4 | **Existe uma solução mais simples?** | Treinamento, ajuste de processo, configuração existente, ou workaround operacional |
| 5 | **Pode esperar para a próxima versão?** | Sim/Não — com justificativa de urgência |

---

## Regra de Decisão

- Se **menos de 3 respostas justificam o esforço** → vai para o **Backlog v2.0**
- Se **3 ou 4 respostas justificam** → avaliação do CTO antes de priorizar
- Se **todas as 5 justificam E impede operação** → aprovação imediata do CTO para correção

---

## Classificação de Severidade (para bugs do piloto)

| Nível | Descrição | SLA |
|-------|-----------|-----|
| **P0 — Bloqueante** | Impede operação. Usuário não consegue executar tarefa essencial | Correção imediata |
| **P1 — Crítico** | Funcionalidade degradada mas com workaround | Correção em 48h |
| **P2 — Importante** | UX ruim mas não impede uso | Próximo ciclo de manutenção |
| **P3 — Cosmético** | Visual, texto, ou melhoria menor | Backlog v2.0 |

---

## Protocolo de Alteração (Consultor de Implantação)

Antes de qualquer alteração no código, o consultor DEVE documentar:

1. **O problema impede a operação?** (Sim/Não)
2. **Qual o impacto?** (Usuários afetados, frequência, severidade)
3. **Existe uma solução mais simples?** (Treinamento, config, workaround)
4. **Essa alteração beneficia apenas um cliente ou todos?** (Escopo)

Toda correção aprovada DEVE:
- Preservar compatibilidade com v1.0.0-RC1
- Passar por teste de regressão
- Ser documentada com arquivos alterados
- Ser comunicada ao CTO

---

## Governança

- **CTO**: Aprovação final de qualquer alteração que não seja P0
- **Consultor (E1)**: Análise técnica, correção, regressão, documentação
- **Nenhuma Sprint nova** sem aprovação explícita do CTO
