# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 6.2.0

---

## Sprint de Homologação — Melhorias de Usabilidade ✅ (iteration_53 — 100%)

### Vinculação de Planos com Hierarquia Completa ✅
- Lista de planos mostra breadcrumb: **Área → TAG → Ativo → Plano**
- Cada card exibe: tipo, disciplina, versão, perguntas, status, data revisão, fabricante/modelo
- Seletor de ativo no formulário: `Área › TAG — Nome (Tipo) Fabricante`

### Validação de Duplicidade ✅
- Backend retorna **409** ao tentar criar plano com mesmo tipo+disciplina+ativo
- Mensagem clara: "Já existe plano 'X' (v1) do tipo 'inspecao' disciplina 'mecanica'"
- Opções: Abrir existente, Criar nova versão (force_override), Cancelar
- Planos genéricos (sem ativo) não sofrem validação de duplicidade

### Painel "Planos Vinculados" no Ativo ✅
- Nova tab "Planos" na página de detalhe do ativo
- Mostra todos planos aprovados vinculados com nome, tipo, disciplina, versão, perguntas, data revisão

### Bug Fix: Central sem_data (operador) ✅
- Query `sem_data` não vaza mais OS de disciplinas bloqueadas

---

## Central de Trabalho ✅ (iteration_52)
- Roteamento por perfil: Master→Central Executiva, Técnico→Minha Jornada etc
- Dashboard gráficos movido para /dashboard

## Fluxo Inspeções (Plano Permanente) ✅ (iteration_51)
## RBAC por Disciplina/Área ✅ (iteration_50)
## Biblioteca de Modelos ✅ (iteration_48)

## PRÓXIMO: Continuar Sprint de Homologação
- Cadastrar equipamentos reais
- Criar planos reais, aprovar e executar inspeções
- Testar preventivas, lubrificações, OS com HH
- Validar Central de Trabalho com dados reais
- Histórico no Ativo (última/próxima inspeção, preventiva, OS)

## DEPOIS: BLOCO C
- Dashboard Supervisor Executivo, Indicadores, Exportação
