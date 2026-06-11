# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
Enterprise-grade industrial maintenance management system (CMMS/EAM) with hierarchical asset management, work orders, inspections (with lubrication module), inventory/spare parts, photo attachments, AI assistant for PDF manuals, and executive dashboard.

## Architecture
- **Backend**: FastAPI + MongoDB (single server.py ~3800 lines)
- **Frontend**: React (single App.js ~4800 lines) + Tailwind + Shadcn UI
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
- Notifications system
- Audit logging

### Multi-Plant Hierarchy (DONE - June 2026)
- Plant CRUD endpoints (`/api/plants`)
- Sector CRUD endpoints (`/api/sectors`)
- Migration function: legacy `plantas`/`areas` -> `plants`/`sectors`
- All ativos migrated with `plant_id` and `sector_id`
- Migration report endpoint (`/api/migration/report`)
- Plant/Sector filtering on: KPIs, Dashboard Stats, Dashboard Trend, Work Orders, Inspections, Anomalias, Ativos
- Frontend: Plantas management page, Setores management page
- Frontend: Cascading Plant->Sector dropdowns in Asset creation modal
- Frontend: Dashboard global filter (All Plants / Specific Plant / Specific Sector)
- Frontend: Sidebar INFRAESTRUTURA section with Plants/Sectors links
- Frontend: Asset list with plant/sector filter dropdowns
- **Testing**: 100% pass rate (iteration 13) - backend 14/14, frontend all flows verified

## Prioritized Backlog

### P0.5 - Architecture Hardening (NEXT)
- Split `server.py` into: dashboard services, asset services, work order services
- Extract frontend components: Dashboard, Asset, Work Order into separate files
- Goal: Reduce risk and file size before Kanban implementation

### P1 - Kanban Work Orders
- Drag and drop between statuses using @dnd-kit (already installed)
- Status update persistence via PATCH /api/ordens-servico/{id}/status
- Permission validation (role-based)
- Mobile responsive
- Regression tests

### P2 - PWA Offline-first
- Service worker, offline data sync, cache strategies

### P3 - Firebase Push Notifications
- In-app notifications + Firebase push

### P3 - Digital Twin, IoT, ERP Integration
