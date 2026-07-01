# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 6.1.0

---

## CENTRAL DE TRABALHO ✅ (iteration_52 — 11/12 backend + 12/12 frontend → bug fix applied)

### Conceito
"O que eu tenho para fazer hoje?" — O sistema ENTREGA o trabalho ao usuário.

### Implementação
- **Endpoint**: `GET /api/central` — retorna atividades agrupadas por urgência, adaptado ao perfil
- **Seções**: Vencidas, Em Execução, Para Hoje, Esta Semana, Sem Data
- **Role-specific**: resumo executivo (admin/master), planos pendentes (pcm/supervisor), OS críticas

### Roteamento por Perfil ✅
| Perfil | Tela Inicial | Título |
|--------|-------------|--------|
| Master | Central Executiva | Resumo + OS Críticas + Planos |
| Admin | Central Administrativa | Resumo + OS Críticas |
| PCM | Central PCM | Planos pendentes + Programações |
| Supervisor | Central Supervisor | Equipe + Aprovações + Críticas |
| Técnico | Minha Jornada | Inspeções + OS + Preventivas |
| Operador | Central Operacional | Rondas + Inspeções operacionais |

### Menu Lateral ✅
- PRINCIPAL: Central de Trabalho (ou "Minha Jornada" para operacionais) + Dashboard
- Dashboard (gráficos) movido para /dashboard como módulo de análise

### Migração Planos Legados ✅
- `POST /api/migrate/planos-legados` — converte "ativo" → "aprovado" com auditoria

---

## CORREÇÃO CRÍTICA: Fluxo Inspeções ✅ (iteration_51)
- Plano Permanente → Execução → Histórico
- Checklist genérico REMOVIDO
- Aprovação explícita obrigatória

## ADITIVO 002: RBAC ✅ (iteration_50)
## ADITIVO 001: Biblioteca ✅ (iteration_48)

## HISTÓRICO: Blocos A/B, Enterprise, Rebranding ✅

## PRÓXIMO: Sprint de Homologação
- Revisar fluxos completos
- Cadastrar equipamentos reais
- Executar inspeções reais
- Validar com usuários diferentes

## DEPOIS: BLOCO C
- Dashboard Supervisor Executivo, Indicadores, Exportação
