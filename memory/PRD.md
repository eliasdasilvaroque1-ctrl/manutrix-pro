# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
Enterprise-grade industrial CMMS/EAM for mining/industrial operations with hierarchical asset management, work orders, inspections, inventory, AI assistant, and executive dashboard.

## Architecture
- **Backend**: FastAPI + MongoDB (modularized)
  - `server.py` (~2100 lines) - Auth, inspections, estoque, anomalias, AI, export, admin, seed
  - `deps.py` (~170 lines) - DB, auth, permissions, helpers
  - `models.py` (~400 lines) - All Pydantic models and enums
  - `routes/dashboard.py` (~250 lines) - KPIs, stats, trend, migration, new charts
  - `routes/assets.py` (~280 lines) - Sectors (top-level), Ativos CRUD
  - `routes/work_orders.py` (~280 lines) - OS CRUD, Kanban, Historico
- **Frontend**: React (`App.js` ~4850 lines) + Tailwind + Shadcn UI
  - `lib/api.js` - Shared API client and AuthContext
- **Auth**: Supabase Auth (primary) with MongoDB bcrypt fallback
- **AI**: Emergent LLM Key for PDF manual assistant

## Current Hierarchy
**Sector → Asset** (Plants removed June 2026)

## Enums (Current)
### OS Types: lubrificacao, limpeza_organizacao, preventiva, corretiva, preparacao_material, fabricacao_melhorias
### Discipline (mandatory): mecanica, eletrica, instrumentacao, civil, producao
### Inspection Types: mecanica, eletrica, lubrificacao
### Asset Criticality: baixa, media, alta, critica
### Asset Status: operacional, parado, manutencao, desativado

## What's Been Implemented

### Core CMMS (DONE)
- Secure Auth (Supabase + MongoDB fallback)
- Asset CRUD with QR codes, tags, photos, PDF manuals
- Work Orders with lifecycle, Kanban board, audit trail
- Inspections + Lubrication module with checklists
- Inventory/Spare Parts management
- Anomalias with intelligent prioritization
- AI Assistant reading PDF manuals
- Executive Dashboard with KPIs, trend charts, drill-down
- Photo Registration System
- Notifications + Audit logging

### Hierarchy Restructure (DONE - June 2026)
- Removed Plants entirely — Sectors are top-level
- Migration: removed plant_id from all sectors and ativos
- Sector CRUD with enable/disable toggle
- Dashboard: OS por Setor, OS por Disciplina, Ativos com Mais Falhas
- Asset form: Sector + Tag + Name + Equipment Type required
- OS form: 6 new types + mandatory Discipline field
- Backend backup collections preserved (_backup_*)

### Architecture Hardening (PARTIAL)
- Backend split: deps.py, models.py, routes/dashboard.py, routes/assets.py, routes/work_orders.py
- Frontend: lib/api.js extracted

## Prioritized Backlog

### P0 - Complete Sprint Phases (NEXT)
1. **PWA Field Operations**: Installable, offline cache, offline queue, camera, sync engine
2. **Executive Multi-Plant Dashboard**: Enhanced KPIs, plant comparison, asset ranking
3. **Hierarchy Visualization**: Interactive tree (Sector → Asset)
4. **OEE Foundation**: Availability calculation, performance/quality placeholders
5. **Architecture Hardening Continuation**: Split inspections, anomalias, inventory routes; extract frontend pages

### NOT Implementing
- Firebase Push Notifications
- ERP Integrations
- IoT / Digital Twin
