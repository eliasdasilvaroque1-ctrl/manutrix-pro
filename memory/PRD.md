# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
Enterprise-grade industrial CMMS/EAM for field operations with offline capability, designed for technicians with unstable internet connections.

## Architecture
- **Backend**: FastAPI + MongoDB (modularized)
  - `server.py` - Auth, inspections, estoque, anomalias, AI, export, admin, seed, checklist templates
  - `deps.py` - DB, auth, permissions, helpers
  - `models.py` - All Pydantic models and enums
  - `routes/dashboard.py` - KPIs, stats, trend, OS por setor/disciplina, ativos mais falhas
  - `routes/assets.py` - Sectors (top-level), Ativos CRUD
  - `routes/work_orders.py` - OS CRUD with causa_falha/equipamento_parado/horas_parada, Kanban
- **Frontend**: React + Tailwind + Shadcn + PWA
  - `lib/api.js` - API client + AuthContext
  - `lib/offlineQueue.js` - IndexedDB offline queue + sync engine
  - `public/manifest.json` - PWA manifest
  - `public/service-worker.js` - SW with network-first API caching + static cache
- **Auth**: Supabase Auth + MongoDB bcrypt fallback
- **AI**: Emergent LLM Key for PDF manual assistant

## Hierarchy: Sector → Asset (no Plants)

## Enums
### OS Types: lubrificacao, limpeza_organizacao, preventiva, corretiva, preparacao_material, fabricacao_melhorias
### Discipline (mandatory): mecanica, eletrica, instrumentacao, civil, producao
### Inspection Types: mecanica, eletrica, lubrificacao
### Criticidade: baixa, media, alta, critica

## Implemented Features

### Core CMMS (DONE)
- Auth, Asset CRUD, Work Orders, Inspections, Inventory, Anomalias, AI Assistant, Dashboard, Kanban, Audit Trail

### Field Operations (DONE - June 2026)
- **PWA**: manifest.json, service worker, installable on Android/iOS/Tablet
- **Offline Cache**: SW caches static shell + API responses (network-first)
- **Offline Queue**: IndexedDB stores OS/Inspection creates/updates when offline
- **Auto Sync**: Syncs pending operations on reconnect with retry + conflict protection
- **Camera**: Native camera capture via getUserMedia (environment-facing)
- **Network Status**: Visual indicator bar (offline/syncing/pending)
- **OS New Fields**: causa_falha (required for corretiva), equipamento_parado (bool), horas_parada
- **Checklist Templates**: Default editable checklists for Mecânica (10 items), Elétrica (10 items), Lubrificação (9 items)
- **Inspection Types**: 3 tabs (Mecânica, Elétrica, Lubrificação) with checklist preview
- **Testing**: 100% (iteration 16)

## Backlog (After Production Validation)
1. Executive Multi-Plant Dashboard
2. OEE Foundation
3. Hierarchy Tree Visualization
4. Architecture Hardening Continuation
5. Firebase Push Notifications (NOT NOW)
