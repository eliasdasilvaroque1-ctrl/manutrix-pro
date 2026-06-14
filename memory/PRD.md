# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
MANUTRIX OMNI is a field-ready CMMS/EAM system for industrial maintenance. Flat Area -> Asset hierarchy, Kanban Work Orders, customizable Inspections (Mechanical, Electrical, Lubrication), Spare Parts, QR Code scanning, offline-first PWA.

## Architecture
- **Backend**: FastAPI + MongoDB + Supabase Auth
- **Frontend**: React PWA
- **DB**: sectors (=Áreas), ativos, ordens_servico, inspecoes, anomalias, itens_estoque, spare_assets

## What's Implemented (Validated 2026-06-14, Phase 1)

### FASE 1 — Estabilização Operacional ✅
- [x] **Área + TAG + Equipamento** em todas as telas (lista, ficha, OS, inspeções, anomalias, ronda, histórico)
- [x] **Cadastro limpo**: removidos Criticidade, Status, Centro de Custo, MTBF/MTTR manual, financeiros
- [x] **Herdar ativo automaticamente**: "Nova OS" e "Nova Inspeção" da ficha do ativo → ativo travado
- [x] **Conclusão de OS com modal**: campo obrigatório "Serviço Executado" + tempo gasto
- [x] **Histórico do Ativo (Prontuário)**: aba com timeline de OS, Inspeções, Anomalias
- [x] **UNIQUE(area_id, tag)**: TAG repetida em áreas diferentes OK, bloqueada na mesma
- [x] **Export limpo**: Excel/PDF com "Área" como primeira coluna
- [x] **Terminologia**: "Áreas" consistente em toda a UI

### Módulos Anteriores (Validados Auditoria E2E 2026-06-13)
- [x] Auth: Login (admin/supervisor/tecnico), forgot password
- [x] Áreas: CRUD com cores e contagem de ativos
- [x] Ativos: CRUD com QR code, upload PDF
- [x] Inspeções: Mecânica/Elétrica/Lubrificação com checklists
- [x] Ronda: Fluxo completo Área→Equipamento→Tipo→Checklist→Salvar
- [x] OS: Kanban, criar/iniciar/concluir, audit trail
- [x] Estoque: CRUD com movimentações
- [x] Sobressalentes: CRUD
- [x] PWA: manifest, Service Worker, offline queue

## Backlog — FASE 2 (Próxima)
- [ ] **Anomalias completo**: workflow status (Aberta→Em análise→OS→Corrigida→Encerrada), edição, comentários
- [ ] **Templates de inspeção por tipo de equipamento**: CRUD vinculado a tipo de equipamento
- [ ] **Bug checklist obrigatório**: investigar "Preencha todos os itens" após preenchimento

## Backlog — FASE 3
- [ ] Exportações: validar Excel/PDF com download real e conteúdo
- [ ] Ronda: validação completa com evidências
- [ ] Varredura E2E final

## SUSPENSO (por solicitação do usuário)
- Dashboard Executivo
- OEE
- Tree View
- Push Notifications
