# MANUTRIX OMNI — Product Requirements Document

## FASE FINAL PRÉ-PILOTO

### Bloco 1: Validação Multiempresa ✅ (2026-06-21)

**Mecanismo:** `organization_id` em todas as entidades (equivalente a tenant_id)

**Proteções implementadas:**
- [x] `verify_org_access()` em deps.py — verifica org do documento vs org do usuário
- [x] Aplicado em: GET ativos, GET OS, GET estoque, GET inspeção (retorna 404 se org diferente)
- [x] List queries filtram por `organization_id` em: sectors, ativos, OS, inspeções, estoque, sobressalentes

**Orgs de teste criadas:**
- ASTEC (admin@astec.com) — 1 área, 1 ativo, 1 OS, 1 estoque
- VALE (admin@vale.com) — 1 área, 1 ativo, 1 OS, 1 estoque
- CSN (admin@csn.com) — 1 área, 1 ativo, 1 OS, 1 estoque

**Testes de isolamento (29/29 PASS):**
- Listagem: cada org vê apenas seus dados ✅
- Acesso cruzado por ID: 404 em todas as combinações ✅
- Export: contém apenas dados da org autenticada ✅

**Testes:** iteration_38 — Backend 29/29

### Bloco 2: Auditoria Campo-a-Campo (PRÓXIMO)
### Bloco 3: Paradas Programadas
### Bloco 5: Segurança e Produção

## Regra de Ouro
> Parar após cada bloco. Entregar evidências. Aguardar aprovação.
