# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
MANUTRIX OMNI is a field-ready CMMS/EAM system for industrial maintenance. Core features include a flat Area -> Asset hierarchy, Kanban-style Work Orders, customizable Inspections (Mechanical, Electrical, Lubrication), Spare Parts management, QR Code scanning, and offline-first PWA capabilities for field technicians.

## User Personas
- **Admin**: Full access, manages areas, assets, users, reports
- **Supervisor**: Manages work orders, inspections, views reports
- **Tecnico (Field Technician)**: Executes inspections via Ronda mode, creates work orders, uses QR scanner

## Core Architecture
- **Backend**: FastAPI + MongoDB + Supabase Auth (hybrid)
- **Frontend**: React (PWA) with custom components
- **DB Collections**: sectors (=Áreas), ativos, ordens_servico, inspecoes, users, itens_estoque, spare_assets
- **Key pattern**: sector_id links ativos to sectors; UI calls sectors "Áreas"

## What's Been Implemented (All PASS per Audit 2026-06-13)
- [x] Auth: Login (admin/supervisor/tecnico), forgot password via Supabase
- [x] Áreas (Sectors): CRUD with color coding and asset counts
- [x] Ativos: CRUD with UNIQUE(area_id, tag), QR code generation, PDF manual upload
- [x] Inspeções: Mecânica/Elétrica/Lubrificação with customizable checklists
- [x] Ronda: Full flow Área→Equipamento→Tipo→Checklist→Salvar with auto-conclusion
- [x] Ordens de Serviço: Kanban board, create/iniciar/concluir, audit trail
- [x] Estoque: CRUD with movimentações (entrada/saída), alertas de mínimo
- [x] Sobressalentes: CRUD with auto-tag generation
- [x] PWA: manifest.json, Service Worker, Offline Queue via IndexedDB
- [x] QR Code Scanner (jsQR fallback) + Printable Asset Detail Card
- [x] Anomalias: Registro com geração automática de OS
- [x] Assistente IA: Chat com histórico
- [x] Admin: Gestão de usuários e audit logs
- [x] Export: CSV/Excel para todos os módulos
- [x] Permissões: Role-based (admin/supervisor/tecnico)

## Production Readiness Status
- **Audit Result**: ALL MODULES PASS (2026-06-13)
- **Bugs Found**: 3 (all fixed)
- **Risk Level**: LOW
- **Full Report**: /app/AUDIT_REPORT.md

## Prioritized Backlog (FROZEN per user request)
- **P1**: Dashboard Executivo (KPIs multi-área, rankings) — SUSPENDED
- **P2**: OEE Foundation (Availability, Performance, Quality) — SUSPENDED
- **P3**: Hierarchy Visualization (Tree View) — SUSPENDED
- **P4**: Architecture Hardening (Split App.js) — SUSPENDED

## Tech Stack
React (PWA), FastAPI, MongoDB, Supabase Auth, @dnd-kit (Kanban), jsQR, Pydantic
