# MAINTRIX — Asset Dossier Architecture

**Data:** 2026-07-12  
**Versao:** RC4.0  

---

## Modelo Asset-Centric Implementado

```
ATIVO (AV-01 — ALIMENTADOR)
│
├── 📋 VISAO GERAL        → Tab 1: Cards de status + resumo operacional
│
├── 🔧 ORDENS DE SERVICO  → Tab 2: Lista filtrada por status
│   └── by ativo_id in ordens_servico collection
│
├── 🔍 PLANOS INSPECAO    → Tab 3: Planos aprovados (diretos + genericos)
│   └── by ativo_id OR tipo_equipamento in planos_inspecao
│
├── ✅ EXECUCOES          → Tab 4: Historico de inspecoes com fotos
│   └── by ativo_id in inspecoes collection
│
├── 📨 SOLICITACOES       → Tab 5: Backlog de solicitacoes
│   └── by ativo_id in solicitacoes collection (quando existir)
│
├── 📄 DOCUMENTOS         → Tab 6: Manuais PDF + Anexos
│   └── by ativo_id in manuais + attachments collections
│
├── 📜 HISTORICO          → Tab 7: Timeline unificada
│   └── by entity_id in audit_logs (via /ativos/{id}/historico)
│
└── 📊 INDICADORES        → Tab 8: KPIs calculados
    ├── MTBF = 720h / falhas_corretivas
    ├── MTTR = media(tempo_reparo) / 60
    ├── Disponibilidade = MTBF / (MTBF + MTTR) * 100
    ├── Custos = materiais + HH
    └── Contadores por tipo/status
```

## Database Relationships

```
ativos.id ──────────┬──► ordens_servico.ativo_id
                    ├──► inspecoes.ativo_id
                    ├──► planos_inspecao.ativo_id (OR tipo_equipamento match)
                    ├──► solicitacoes.ativo_id
                    ├──► manuais.ativo_id
                    ├──► attachments.entity_id (entity_type="ativo")
                    ├──► audit_logs.entity_id (entity_type="ativo")
                    └──► ativo_materiais.ativo_id (BOM)

ativos.sector_id ──► sectors.id (nome do setor/area)
ordens_servico.responsavel_id ──► users.id (nome do responsavel)
inspecoes.responsavel_id ──► users.id (nome do responsavel)
inspecoes.plano_id ──► planos_inspecao.id (nome do plano)
```

## Indices Utilizados

| Collection | Indice | Uso |
|-----------|--------|-----|
| `ordens_servico` | `{ativo_id: 1, created_at: -1}` | OS por ativo |
| `inspecoes` | `{ativo_id: 1, created_at: -1}` | Inspecoes por ativo |
| `planos_inspecao` | `{ativo_id: 1, status: 1}` | Planos por ativo |
| `manuais` | `{ativo_id: 1}` | Manuais |
| `attachments` | `{entity_type: 1, entity_id: 1}` | Anexos |
| `audit_logs` | `{entity_id: 1, entity_type: 1}` | Historico |
