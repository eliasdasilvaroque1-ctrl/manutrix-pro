# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
MANUTRIX OMNI — CMMS/EAM field-ready for industrial maintenance. Flat Area→Asset hierarchy, Kanban Work Orders, Inspections, Spare Parts, QR Code, PWA offline-first.

## Architecture
- Backend: FastAPI + MongoDB + Supabase Auth
- Frontend: React PWA (Service Worker network-first v3)
- DB: sectors, ativos, ordens_servico, inspecoes, anomalias, anomalia_comentarios, anomalia_historico, itens_estoque, inspection_templates, ativo_materiais

## IMPLEMENTED AND VALIDATED

### FASE 1 — Estabilização Operacional ✅
- [x] Área + TAG + Equipamento em todas as telas
- [x] Cadastro limpo (removidos criticidade, status, centro de custo, MTBF/MTTR manual)
- [x] Herdar ativo automaticamente (Nova OS/Inspeção com ativo travado)
- [x] Modal conclusão OS com "Serviço Executado" + "Tempo Gasto"
- [x] Histórico do Ativo (prontuário)
- [x] UNIQUE(area_id, tag)
- [x] Service Worker network-first (cache-v3)

### FASE 2 P0 — Operacional ✅
- [x] Bug Checklist CORRIGIDO (tipo numerico/opcao)
- [x] Templates de Inspeção por Equipamento (CRUD admin)
- [x] Lista Técnica (BOM) CRUD completo na ficha do ativo
- [x] Executantes na OS (multi-select equipe[])
- [x] SKU → Código em Estoque

### FASE 2 P1 — Workflow e Vinculação ✅ (2026-06-14)
- [x] **Templates vinculados ao fluxo de inspeção**: ao selecionar equipamento, templates específicos auto-carregam
- [x] **Anomalias workflow completo**: Aberta→Em Análise→OS Gerada→Corrigida→Encerrada
- [x] **Anomalias edição + comentários + histórico**: completo com audit trail
- [x] **Anomalias encerradas preservadas**: não são excluídas, permanecem vinculadas ao ativo
- [x] **SKU → Código em Sobressalentes**: renomeado
- [x] **Filtros de anomalias**: por status (Todas/Aberta/Em Análise/Corrigida/Encerrada)
- [x] **Anomalias no histórico do ativo**: aparecem na timeline com badge

## SUSPENSO
- Dashboard Executivo, OEE, Tree View, Push Notifications
