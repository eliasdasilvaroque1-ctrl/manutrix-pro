# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
Enterprise-grade industrial maintenance management system (CMMS/EAM) with hierarchical asset management, work orders, inspections (with lubrication module), inventory/spare parts, photo attachments, AI assistant for PDF manuals, and executive dashboard.

## Architecture
- **Backend**: FastAPI + MongoDB (modularized)
  - `server.py` (~2291 lines) - Auth, inspections, estoque, sobressalentes, anomalias, AI, export, PowerBI, admin, seed
  - `deps.py` (~178 lines) - DB, auth, permissions, helpers
  - `models.py` (~400 lines) - All Pydantic models and enums
  - `routes/dashboard.py` (~290 lines) - KPIs, dashboard stats/trend, migration
  - `routes/assets.py` (~333 lines) - Plants, Sectors, Ativos CRUD
  - `routes/work_orders.py` (~291 lines) - OS CRUD, Kanban, Historico
- **Frontend**: React (`App.js` ~4860 lines) + Tailwind + Shadcn UI
  - `lib/api.js` - Shared API client and AuthContext
- **Auth**: Supabase Auth (primary) with MongoDB bcrypt fallback
- **AI**: Emergent LLM Key for PDF manual assistant
- **DB Hierarchy**: Organization -> Plant -> Sector -> Asset

## What's Been Implemented

### Core Features (DONE)
- Secure Auth (Supabase + MongoDB fallback, forgot password)
- Asset CRUD with QR codes, tags, photos, PDF manuals
- Work Orders CRUD (OS) with lifecycle management
- Inspections + Lubrication module with checklist system
- Inventory/Spare Parts management
- Anomalias with intelligent prioritization
- AI Assistant reading PDF manuals
- Executive Dashboard with drill-down, trend charts
- Power BI / Excel export endpoints
- Photo Registration System (OS, Anomalies, Inspections)
- Notifications system + Audit logging

### P0: Multi-Plant Hierarchy (DONE - June 2026)
- Plant/Sector CRUD endpoints
- Automatic migration: legacy plantas/areas -> plants/sectors
- Plant/Sector filtering on all major endpoints
- Frontend: Plantas/Setores management pages
- Dashboard global filter (All Plants / Specific Plant / Sector)
- Cascading Plant->Sector dropdowns in Asset creation
- Migration report endpoint
- **Testing**: 100% (iteration 13)

### P0.5: Architecture Hardening (DONE - June 2026)
- Backend split: server.py 3843->2291 lines (40% reduction)
- Extracted: deps.py, models.py, routes/dashboard.py, routes/assets.py, routes/work_orders.py
- Frontend: Extracted lib/api.js (shared API client)
- No business logic changes
- **Testing**: 100% regression (iteration 14)

### P1: Kanban Work Orders (DONE - June 2026)
- Drag-and-drop Kanban board with 5 columns
- PATCH /api/ordens-servico/{id}/status with role-based permission
- Audit trail: kanban_move logged to audit_logs collection
- GET /api/ordens-servico/{id}/historico — transition history endpoint
- OS detail page shows "Histórico de Transições" section
- Mobile responsive: quick-move buttons, snap scrolling
- Kanban/List view toggle
- **Testing**: 100% (iteration 14)

## Prioritized Backlog

### P1.5 - Enhanced Dashboard & Audit (NEXT)
- Dashboard Executivo Multi-Planta (enhanced metrics per plant)
- KPIs por Planta/Setor (comparative views)
- Árvore Hierárquica de Ativos (interactive tree: Plant -> Sector -> Assets)
- Histórico de movimentação de OS (complete timeline)
- Auditoria completa das transições do Kanban (admin view)

### P2 - PWA Offline-first
- Service worker, offline data sync, cache strategies

### P3 - Firebase Push Notifications
- In-app notifications + Firebase push

### P3+ - Digital Twin, IoT, ERP Integration
