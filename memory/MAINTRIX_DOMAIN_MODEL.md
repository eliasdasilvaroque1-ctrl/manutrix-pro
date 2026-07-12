# MAINTRIX — Domain Model V6

**Data:** 2026-07-12  
**Status:** MODELAGEM — Nenhum código implementado  

---

## Diagrama de Entidades e Relacionamentos

```
┌──────────────┐
│ ORGANIZAÇÃO  │ ← Tenant raiz (isolamento total)
└──────┬───────┘
       │ 1:N
       ├────────────────┬──────────────────┬─────────────────┐
       ▼                ▼                  ▼                 ▼
┌──────────┐    ┌──────────┐      ┌──────────┐     ┌────────────┐
│ UNIDADE  │    │ USUÁRIO  │      │ ORG_CFG  │     │  CONSENT   │
└────┬─────┘    └────┬─────┘      └──────────┘     └────────────┘
     │ 1:N           │ N:M (áreas, unidades)
     ▼               │
┌──────────┐         │
│  SETOR   │◄────────┘ (area_ids)
└────┬─────┘
     │ 1:N
     ▼
┌──────────────────────────────────────────────────────────┐
│                        ATIVO                              │
│  (Entidade central — Asset-Centric Model)                │
└──┬────┬────┬────┬────┬────┬────┬────┬────┬──────────────┘
   │    │    │    │    │    │    │    │    │
   │    │    │    │    │    │    │    │    └─► AUDIT_LOG
   │    │    │    │    │    │    │    │
   │    │    │    │    │    │    │    └──────► ATTACHMENT
   │    │    │    │    │    │    │
   │    │    │    │    │    │    └───────────► MANUAL (PDF)
   │    │    │    │    │    │
   │    │    │    │    │    └────────────────► KNOWLEDGE_BASE
   │    │    │    │    │
   │    │    │    │    └─────────────────────► SOBRESSALENTE
   │    │    │    │                              │ 1:N
   │    │    │    │                              ▼
   │    │    │    │                          REFORMA
   │    │    │    │
   │    │    │    └──────────────────────────► ESTOQUE
   │    │    │                                  │ 1:N
   │    │    │                                  ▼
   │    │    │                           MOVIMENTAÇÃO
   │    │    │
   │    │    └───────────────────────────► PARADA_PROGRAMADA
   │    │
   │    └────────────────────────────────► PLANO_INSPECAO
   │                                         │ 1:N
   │                                         ▼
   │                                      INSPEÇÃO
   │                                         │
   │                                         │ (não conforme)
   │                                         ▼
   └─────────────────────────────────────► SOLICITAÇÃO
                                             │
                                             │ (convertida)
                                             ▼
                                          ORDEM_SERVICO
                                             │ N:M
                                             ├──► MATERIAIS (do estoque)
                                             ├──► HH_REGISTROS
                                             └──► EXECUTANTES (usuários)
```

---

## Cardinalidades

| Relação | Cardinalidade | Descrição |
|---------|--------------|-----------|
| Organização → Unidade | 1:N | Uma org tem várias unidades |
| Organização → Usuário | 1:N | Uma org tem vários usuários |
| Unidade → Setor | 1:N | Uma unidade tem várias áreas |
| Setor → Ativo | 1:N | Uma área tem vários ativos |
| Ativo → Plano Inspeção | 1:N | Um ativo pode ter vários planos |
| Ativo → Inspeção | 1:N | Um ativo pode ter várias inspeções |
| Ativo → OS | 1:N | Um ativo pode ter várias OS |
| Ativo → Solicitação | 1:N | Um ativo pode ter várias solicitações |
| Ativo → Manual | 1:N | Um ativo pode ter vários manuais |
| Ativo → Attachment | 1:N | Um ativo pode ter vários anexos |
| Plano → Inspeção | 1:N | Um plano gera várias execuções |
| Inspeção → Solicitação | 1:1 | Não conformidade gera uma solicitação |
| Solicitação → OS | 1:1 | Solicitação aprovada gera uma OS |
| OS → Materiais | N:M | Uma OS consome vários itens de estoque |
| OS → Executantes | N:M | Uma OS tem vários técnicos |
| Estoque → Movimentação | 1:N | Um item tem várias movimentações |
| Sobressalente → Reforma | 1:N | Uma peça pode ter várias reformas |
| Usuário → Inspeção | 1:N | Um técnico executa várias inspeções |
| Usuário → OS | 1:N | Um técnico é responsável por várias OS |

---

## Collections MongoDB (Atual)

| Collection | Entidade | Índices Chave |
|-----------|----------|--------------|
| `organizations` | Organização | `slug` (unique) |
| `users` | Usuário | `email` + `organization_id` (unique compound) |
| `unidades` | Unidade | `organization_id` |
| `sectors` | Setor | `organization_id`, `unidade_id` |
| `ativos` | Ativo | `organization_id`, `tag` + `org` (unique), `sector.id` |
| `planos_inspecao` | Plano Inspeção | `organization_id`, `ativo_id`, `tipo_equipamento` |
| `inspecoes` | Inspeção | `organization_id`, `ativo_id`, `plano_id`, `status` |
| `ordens_servico` | OS | `organization_id`, `ativo_id`, `status`, `numero` |
| `itens_estoque` | Estoque | `organization_id`, `sku` + `org` (unique) |
| `movimentacoes_estoque` | Movimentação | `organization_id`, `item_id` |
| `spare_assets` | Sobressalente | `organization_id` |
| `spare_movements` | Mov. Sobressalente | `organization_id`, `spare_id` |
| `spare_reformas` | Reforma | `spare_id` |
| `paradas_programadas` | Parada | `organization_id` |
| `manuais` | Manual | `ativo_id` |
| `attachments` | Anexo | `entity_type`, `entity_id` |
| `knowledge_base` | Biblioteca | `organization_id` |
| `audit_logs` | Histórico | `entity_type`, `entity_id`, `organization_id` |
| `consents` | Consentimento | `user_id` |
| `org_config` | Config Org | `organization_id` (unique) |
| `notificacoes` | Notificação | `user_id`, `lida` |
| `rotas_inspecao` | Rota Inspeção | `organization_id` |
| `checklist_templates` | Template | `organization_id`, `tipo` |
| `inspection_templates` | Template Inspeção | `organization_id` |

---

## Invariantes de Domínio

1. **Isolamento Tenant:** Toda query inclui `organization_id`. Nenhum dado cruza organizações.
2. **Soft Delete:** Entidades não são removidas fisicamente — `deleted_at` é preenchido.
3. **Audit Trail:** Toda operação CUD gera entry em `audit_logs`.
4. **Tag Única:** `ativo.tag` é único por `organization_id`.
5. **SKU Único:** `estoque.sku` é único por `organization_id`.
6. **Plano Aprovado:** Inspeções só podem ser criadas a partir de planos com `status: aprovado`.
7. **Transição de Estado:** OS segue fluxo definido — não pode pular estados.
