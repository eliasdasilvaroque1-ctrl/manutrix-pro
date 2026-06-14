# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
MANUTRIX OMNI — CMMS/EAM field-ready for industrial maintenance. Flat Area→Asset hierarchy, Kanban Work Orders, Inspections, Spare Parts, QR Code, PWA offline-first.

## Architecture
- Backend: FastAPI + MongoDB + Supabase Auth
- Frontend: React PWA (Service Worker network-first v3)
- DB: sectors, ativos, ordens_servico, inspecoes, anomalias, itens_estoque, inspection_templates, ativo_materiais

## FASE 1 — Estabilização Operacional (COMPLETA 2026-06-14)
- [x] Área + TAG + Equipamento em todas as telas
- [x] Cadastro limpo (removidos criticidade, status, centro de custo, MTBF/MTTR manual, financeiros)
- [x] Herdar ativo automaticamente (Nova OS/Inspeção com ativo travado)
- [x] Modal conclusão OS com "Serviço Executado" + "Tempo Gasto" obrigatórios
- [x] Histórico do Ativo (prontuário) com timeline OS/Inspeções/Anomalias
- [x] UNIQUE(area_id, tag) com índice MongoDB
- [x] Export limpo com "Área" como primeira coluna
- [x] Service Worker corrigido: network-first (cache-v3)

## FASE 2 — P0 Operacional (COMPLETA 2026-06-14)
- [x] **Bug Checklist CORRIGIDO**: tipo 'numerico' vs 'numero' normalizado + handler 'opcao' (Bom/Regular/Ruim/Crítico) adicionado
- [x] **Templates de Inspeção por Equipamento**: CRUD admin completo (criar/editar/excluir/duplicar), vinculado a tipo_equipamento, 7 tipos de campo
- [x] **Lista Técnica (BOM)**: CRUD completo na ficha do ativo com busca por código/descrição
- [x] **Executantes na OS**: Multi-select de executantes (equipe[]) com tags visuais
- [x] **SKU → Código**: Renomeado em Estoque

## Backlog P1 (PRÓXIMA FASE)
- [ ] Anomalias: workflow completo (Aberta→Em análise→OS→Corrigida→Encerrada), edição, comentários, encerramento
- [ ] Consulta histórica do ativo: filtros de anomalias (abertas/encerradas/todas)
- [ ] Vincular templates de inspeção ao fluxo de criação de inspeção (selecionar template por tipo de equipamento)
- [ ] SKU → Código: completar em Sobressalentes

## SUSPENSO
- Dashboard Executivo, OEE, Tree View, Push Notifications, novos KPIs
