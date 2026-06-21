# MANUTRIX OMNI — Product Requirements Document

## Status: PILOTO ASTEC — CONGELADO
## Versão: 3.2.1 (Final Pré-Piloto)
## Data congelamento: 21/06/2026

---

## REGRA DE OURO — MODO PILOTO ATIVO
> Sistema CONGELADO por 15 dias.
> Permitido: correção de bugs, falhas operacionais, usabilidade observada em campo.
> Proibido: funcionalidades novas, módulos novos, integrações, dashboards, IA, OEE, ERP.

---

## Fase Final Pré-Piloto ✅ APROVADA

| Bloco | Escopo | Status |
|-------|--------|--------|
| Bloco 1 | Validação Multiempresa | ✅ |
| Bloco 2 | Auditoria Campo-a-Campo | ✅ |
| Bloco 3 | Paradas Programadas | ✅ |
| Bloco 5 | Segurança e Produção | ✅ |

---

## 7 Itens Críticos de Usabilidade ✅ (iteration_41)
- A1: Status dinâmico do ativo, A2: Contador OS, OS1: Busca Kanban
- OS2: Filtro prioridade, I1: Filtro status inspeções, I2: Filtro área
- E1: Histórico movimentações expandível

## Migração Storage ✅ (iteration_42)
- 75 arquivos → Emergent Object Storage (451 MB)
- Novos uploads → cloud automático
- Risco Railway eliminado

## Revisão Final Segurança ✅ (21/06/2026)
- JWT_SECRET fixo configurado
- Endpoint /seed protegido com admin auth
- Restore testado: 1577 docs, 0 falhas, 11 collections OK
- Signed URLs: NÃO implementado (risco baixo, UUIDs = segurança por obscuridade)
- 0 riscos críticos, 0 vazamentos entre orgs

---

## Módulos Completos

Áreas, Ativos, OS, Inspeções, Anomalias, Estoque, Sobressalentes,
Paradas Programadas, Auditoria, Multiempresa, PWA/Offline,
Dashboard, Exportação, Object Storage

---

## Backlog Congelado (Pós-Piloto)
- 25 melhorias IMPORTANTES da revisão de usabilidade
- 11 melhorias OPCIONAIS
- Signed URLs para storage
- Rate limiting em endpoints de login
- Integrações ERP/SAP (suspenso)
- Dashboards novos, IA, OEE (suspenso)
