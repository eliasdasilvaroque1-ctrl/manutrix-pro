# MANUTRIX OMNI - Product Requirements Document

## Status: PRODUCTION READY ✅ (Validated June 2026)

## Architecture
- **Backend**: FastAPI + MongoDB (modularized)
- **Frontend**: React + Tailwind + Shadcn + PWA
- **Auth**: Supabase Auth + MongoDB bcrypt fallback
- **Hierarchy**: Sector → Asset (no Plants)

## Production Audit Results (Iteration 18)
- Backend: 44/44 tests PASSED (100%)
- Frontend: 8/8 critical flows PASSED (100%)
- All modules validated: Auth, Sectors, Ativos, Inventory, Spare Parts, Work Orders, Inspections, Dashboard, Users, Permissions

## Implemented Features
- Sector CRUD with enable/disable
- Asset CRUD with sector hierarchy, criticality, QR codes
- Work Orders: 6 types, 5 disciplines, causa_falha, equipamento_parado, horas_parada
- Inspections: 3 types (Mecânica, Elétrica, Lubrificação) with default checklists
- Kanban board with drag-and-drop + audit trail
- Inventory + Spare Parts management
- Dashboard: KPIs, trend charts, OS por Setor/Disciplina, Ativos mais Falhas
- PWA installable with offline cache + sync queue
- Global error normalization (normalizeError)
- Camera capture for field use

## Backlog (Post-Production Validation)
1. Executive Dashboard
2. OEE Foundation
3. Hierarchy Tree Visualization
4. Architecture Hardening (split App.js)
