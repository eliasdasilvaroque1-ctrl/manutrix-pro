# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
MANUTRIX OMNI is a field-ready CMMS/EAM system for industrial maintenance. Core features include a flat Area -> Asset hierarchy, Kanban-style Work Orders, customizable Inspections (Mechanical, Electrical, Lubrication), Spare Parts management, QR Code scanning, and offline-first PWA capabilities for field technicians.

## User Personas
- **Admin**: Full access, manages areas, assets, users, reports
- **Supervisor**: Manages work orders, inspections, views reports
- **Tecnico (Field Technician)**: Executes inspections via Ronda mode, creates work orders, uses QR scanner

## Core Requirements (Simplified)
- **Hierarchy**: Flat Area -> Asset (NO Plants, NO Subsetores, NO Criticidade)
- **Inspections**: Mecânica, Elétrica, Lubrificação with customizable checklists
- **Work Orders**: Kanban board (Aberta, Em Andamento, Concluída)
- **PWA**: Offline-first, Service Worker, IndexedDB queue
- **QR Code**: Generate, print, scan (native camera + jsQR fallback)
- **UNIQUE constraint**: UNIQUE(area_id, tag) - same tag allowed in different areas

## Architecture
- **Backend**: FastAPI + MongoDB + Supabase Auth
- **Frontend**: React (PWA) with Shadcn UI components
- **DB Collections**: sectors (=Áreas), ativos, ordens_servico, inspecoes, users
- **Key pattern**: sector_id links ativos to sectors; UI calls sectors "Áreas"

## What's Been Implemented
- [x] Multi-Plant → REVERTED to flat Area model
- [x] Architecture Hardening: Split server.py into models.py, deps.py, routes/
- [x] Kanban Work Orders with drag/drop, touch support, audit history
- [x] PWA: manifest.json, Service Worker, Offline Queue, Camera Integration
- [x] Fixed Pydantic 422 Array (normalizeError)
- [x] Production Audit fixes (InspecaoCreate, SpareAssetCreate)
- [x] DB Backup + Rollback Instructions
- [x] Radical Simplification (removed Criticidade, Status, Centro de Custo, MTBF manual, financial fields)
- [x] QR Code Scanner (jsQR fallback) + Printable Asset Detail Card
- [x] Ronda Module P0 Fix (2026-06-13):
  - UNIQUE(area_id, tag) constraint with MongoDB index
  - Auto-conclusion of inspections from Ronda (filled checklist = concluída)
  - Auto-OS generation for non-conformities
  - Fixed lubrificação checklist override
  - Cleaned asset form (removed duplicate fields, old payload)

## Prioritized Backlog
- **P1**: Executive Dashboard (Multi-Area KPIs, rankings)
- **P2**: OEE Foundation (Availability, placeholders for Performance/Quality)
- **P3**: Hierarchy Visualization (Interactive Tree View Area → Asset)
- **P4**: Architecture Hardening (Split App.js into components)

## Tech Stack
React (PWA), FastAPI, MongoDB, Supabase Auth, @dnd-kit (Kanban), jsQR, Pydantic
