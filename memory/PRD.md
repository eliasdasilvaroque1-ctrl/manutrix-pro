# MANUTRIX OMNI — Product Requirements Document

## Status: PILOTO ASTEC — CONGELADO PARA PRODUÇÃO
## Versão: 3.2.0

---

## Fase Final Pré-Piloto ✅ APROVADA (21/06/2026)

### Bloco 1: Validação Multiempresa ✅
### Bloco 2: Auditoria Campo-a-Campo ✅
### Bloco 3: Paradas Programadas ✅
### Bloco 5: Segurança e Produção ✅

---

## 7 Itens Críticos de Usabilidade ✅ (21/06/2026, iteration_41)
- A1: Status dinâmico do ativo na listagem
- A2: Contador de OS abertas por ativo
- OS1: Busca no Kanban
- OS2: Filtro por prioridade
- I1: Filtro por status nas Inspeções
- I2: Filtro por área nas Inspeções
- E1: Histórico de movimentações expandível

---

## Migração Storage ✅ (21/06/2026, iteration_42)
- 75 arquivos migrados (35 attachments + 40 manuais = 451 MB)
- Destino: Emergent Object Storage (cloud)
- Novos uploads vão automaticamente para cloud
- Proxy endpoint: GET /api/storage/{path}
- Endpoints legados mantidos para compatibilidade
- Zero arquivos restantes em local no MongoDB
- Risco Railway eliminado

---

## Módulos Completos

| Módulo | Status |
|--------|--------|
| Áreas | ✅ |
| Ativos | ✅ |
| Ordens de Serviço | ✅ |
| Inspeções | ✅ |
| Anomalias | ✅ |
| Estoque | ✅ |
| Sobressalentes | ✅ |
| Paradas Programadas | ✅ |
| Auditoria | ✅ |
| Multiempresa | ✅ |
| PWA/Offline | ✅ |
| Dashboard | ✅ |
| Exportação | ✅ |
| Object Storage | ✅ |

---

## Regra de Ouro — PILOTO ASTEC
> Sistema CONGELADO. Nenhuma funcionalidade nova.
> Apenas correção de bugs e ajustes operacionais.

## Nota de Segurança (Documentada)
- GET /api/storage/{path} é público (URLs baseadas em UUID).
- Aceitável para piloto. Considerar signed URLs ou auth em produção futura.

## Backlog Congelado (Pós-Piloto)
- 25 melhorias IMPORTANTES da revisão de usabilidade
- 11 melhorias OPCIONAIS da revisão de usabilidade
- Integrações ERP/SAP (suspenso)
- Dashboards novos, IA, OEE (suspenso)
