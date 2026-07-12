# MAINTRIX — Database Relationship Map

**Data:** 2026-07-12  
**Versao:** RC4.0  

---

## Core Entity Relationships

```
ORGANIZATION (1)
  │
  ├──► USERS (N)                    org_id
  ├──► UNIDADES (N)                 org_id
  │     └──► SECTORS (N)            unidade_id, org_id
  │           └──► ATIVOS (N)       sector_id, org_id    ← CENTRO
  ├──► ORG_CONFIG (1)               org_id
  └──► CONSENTS (N)                 org_id
```

## Asset-Centric Relationships

```
ATIVO (1)
  │
  ├──► ORDENS_SERVICO (N)           ativo_id
  │     ├──► HH_REGISTROS (N)       embedded in os.hh_registros[]
  │     ├──► MATERIAIS (N)          embedded in os.materiais[]
  │     └──► EXECUTANTES (N)        embedded in os.equipe[]
  │
  ├──► INSPECOES (N)                ativo_id
  │     ├──► CHECKLIST (N)          embedded in inspecao.checklist[]
  │     └──► FOTOS (N)             embedded in inspecao.fotos[]
  │
  ├──► PLANOS_INSPECAO (N)          ativo_id OR tipo_equipamento match
  │     └──► PERGUNTAS (N)         embedded in plano.perguntas[]
  │
  ├──► SOLICITACOES (N)             ativo_id
  │
  ├──► MANUAIS (N)                  ativo_id
  │
  ├──► ATTACHMENTS (N)              entity_id (entity_type=ativo)
  │
  ├──► AUDIT_LOGS (N)               entity_id (entity_type=ativo)
  │
  └──► ATIVO_MATERIAIS (N)          ativo_id (BOM)
```

## Cross-Entity References

```
INSPECAO.plano_id        ──► PLANO_INSPECAO.id
INSPECAO.responsavel_id  ──► USER.id
INSPECAO → anomalia      ──► SOLICITACAO (auto-generated)

SOLICITACAO.ativo_id          ──► ATIVO.id
SOLICITACAO.inspecao_origem_id ──► INSPECAO.id
SOLICITACAO → convertida       ──► ORDEM_SERVICO (auto-generated)

ORDEM_SERVICO.ativo_id        ──► ATIVO.id
ORDEM_SERVICO.responsavel_id  ──► USER.id
ORDEM_SERVICO.solicitacao_id  ──► SOLICITACAO.id

USER.organization_id ──► ORGANIZATION.id
USER.area_ids[]      ──► SECTOR.id[]
USER.unidade_ids[]   ──► UNIDADE.id[]
```

## Collections Summary

| # | Collection | Doc Count (ASTEC) | Primary Key | Foreign Keys |
|---|-----------|------------------|-------------|-------------|
| 1 | organizations | 2 | id | — |
| 2 | users | 26 | id | organization_id |
| 3 | unidades | 1 | id | organization_id |
| 4 | sectors | 4 | id | organization_id, unidade_id |
| 5 | ativos | 55 | id | organization_id, sector_id |
| 6 | ordens_servico | 28+ | id | organization_id, ativo_id |
| 7 | inspecoes | 0 | id | organization_id, ativo_id, plano_id |
| 8 | planos_inspecao | 0 | id | organization_id, ativo_id |
| 9 | solicitacoes | 0 | id | organization_id, ativo_id |
| 10 | itens_estoque | 1+ | id | organization_id |
| 11 | spare_assets | 0 | id | organization_id |
| 12 | manuais | 1+ | id | ativo_id |
| 13 | attachments | 0 | id | entity_type, entity_id |
| 14 | audit_logs | N | id | entity_type, entity_id, organization_id |
| 15 | knowledge_base | 0 | id | organization_id |
| 16 | consents | 2+ | id | user_id, organization_id |
| 17 | org_config | 1 | organization_id | — |
| 18 | notificacoes | 0 | id | user_id |
| 19 | rotas_inspecao | 0 | id | organization_id |
| 20 | paradas_programadas | 0 | id | organization_id |
