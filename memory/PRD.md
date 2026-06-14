# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
MANUTRIX OMNI — CMMS/EAM field-ready for industrial maintenance. Flat Area→Asset hierarchy, Kanban Work Orders, Inspections, Spare Parts, QR Code, PWA offline-first.

## Architecture
- Backend: FastAPI + MongoDB + Supabase Auth
- Frontend: React PWA (Service Worker network-first v3)
- DB: sectors, ativos, ordens_servico, inspecoes, anomalias, anomalia_comentarios, anomalia_historico, itens_estoque, inspection_templates, ativo_materiais, spare_assets

## ALL MODULES VALIDATED — Production Ready (2026-06-14)

### Ativos ✅
- CRUD completo, busca por TAG/nome/área
- BOM (Lista Técnica) CRUD com busca
- Upload PDF manuais
- QR Code geração e impressão
- Área + TAG + Equipamento em todas as telas

### Ordens de Serviço ✅
- CRUD + Kanban (Aberta/Em Execução/Pausada/Concluída)
- Modal conclusão com "Serviço Executado" + "Tempo Gasto"
- Executantes múltiplos (equipe[])
- Histórico completo com audit trail

### Inspeções ✅
- Templates por tipo de equipamento (CRUD admin)
- Mecânica/Elétrica/Lubrificação padrão
- 7 tipos de campo (Boolean, Numérico, Temperatura, Vibração, Opção, Texto, Observação)
- Auto-conclusão via Ronda
- Geração automática de OS para não conformidades

### Anomalias ✅
- Workflow: Aberta→Em Análise→OS Gerada→Corrigida→Encerrada
- Edição, comentários, histórico
- Encerradas preservadas vinculadas ao ativo

### Estoque ✅
- CRUD com movimentações (entrada/saída)
- Label "Código" (não SKU)

### Sobressalentes ✅
- CRUD com busca
- Label "Código" (não TAG)

### Exportações ✅ (Validadas com conteúdo)
| Módulo | Excel | PDF |
|--------|-------|-----|
| Ativos | ✅ 15 registros | ✅ 2.8KB |
| OS | ✅ 31 registros | ✅ 4.4KB |
| Estoque | ✅ 18 registros | ✅ 3.1KB |
| Inspeções | ✅ 38 registros | ✅ 4.5KB |
| Sobressalentes | ✅ 6 registros | — |

### Auditoria Visual ✅
- Zero resquícios de: Planta, Criticidade, Status do Ativo, Centro de Custo, SKU
- PlantasPage removido (código morto)
- StatusBadge limpo (removidos operacional/parado/manutencao)
- Dashboard: "OS por Área" (não "Setor")
- Dados legados com prefixo "SKU-" migrados

## SUSPENSO
- Dashboard Executivo, OEE, Tree View, Push Notifications, novos KPIs
