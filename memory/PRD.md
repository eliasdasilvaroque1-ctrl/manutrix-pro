# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 6.0.0

---

## CORREÇÃO CRÍTICA: Fluxo de Execução de Inspeções ✅ (iteration_51 — 11/11 + 3/3)

### Problema Resolvido
O módulo de Inspeções NÃO utilizava os Planos criados pelo PCM. Criava inspeções genéricas com checklist padrão, tornando inútil todo o módulo de Planos.

### Novo Fluxo Implementado
```
PCM: Criar Plano → Vincular ao Ativo → Aprovar → Permanente
Técnico: Acessar Ativo → Ver Planos Aprovados → Executar → Execução vinculada
```

### Arquitetura Plano Permanente → Execuções Recorrentes ✅
| Entidade | Descrição |
|----------|-----------|
| Plano | Permanente, criado pelo PCM, status: rascunho → aprovado |
| Execução | Histórica, vinculada ao Plano (plano_id, plano_versao) |

### Mudanças Backend ✅
- `POST /api/inspecoes` EXIGE `plano_id` — 422 se ausente
- Plano deve ter status "aprovado" — 400 se rascunho/inativo
- Checklist genérico **REMOVIDO DEFINITIVAMENTE**
- `PATCH /api/planos-inspecao/{id}/aprovar` — aprovação explícita
- `GET /api/planos-inspecao/por-ativo/{id}` — somente planos aprovados
- Execução preserva: `plano_id`, `plano_nome`, `plano_versao`
- Novo plano inicia como "rascunho" (não mais "ativo")

### Mudanças Frontend ✅
- ModalNovaInspecao: mostra Planos Aprovados como cards selecionáveis
- RondaPage: mostra planos aprovados do ativo (não mais tipos hardcoded)
- AdminTemplatesPage: badge de status + botão "Aprovar"
- Tabs hardcoded Mecânica/Elétrica/Lubrificação **REMOVIDAS**

---

## ADITIVO ARQUITETURAL Nº 002 ✅ (iteration_50)

### Segurança de Visibilidade Backend (RBAC) ✅
| Perfil | Visibilidade |
|--------|-------------|
| MASTER | Todo o sistema |
| Admin/PCM/Supervisor | Todos da empresa |
| Técnico | Disciplinas + áreas + atividades atribuídas |
| Operador | Apenas producao/civil, NUNCA mecanica/eletrica |

### Bug Fix: Plano de Inspeção "Field required" ✅
- `normalizeError` mostra nome do campo em português
- Formulário com campos completos

---

## ADITIVO ARQUITETURAL Nº 001 ✅ (iteration_48)
- Biblioteca de Modelos, Classificação, Deep Copy, Códigos Automáticos

## HISTÓRICO
- Bloco A/B: Kanban, Filtros, Cronômetro, Equipe, Ranking ✅
- Enterprise: org_config, Terminologia, White-label ✅
- Rebranding: MANUTRIX → MAINTRIX ✅

## PRÓXIMO: BLOCO C
- Dashboard Supervisor Executivo
- Indicadores de Qualidade
- Exportação Excel/PDF/CSV

## BACKLOG (P2)
- IA Features, Subconjuntos, Integrações ERP/SAP
