# MANUTRIX OMNI - Product Requirements Document

## Status: PRODUCTION READY ✅ (June 2026)

## Hierarchy: Área → Ativo (maximum simplicity)

## Architecture
- **Backend**: FastAPI + MongoDB (modularized)
- **Frontend**: React + Tailwind + Shadcn + PWA
- **Auth**: Supabase Auth + MongoDB bcrypt fallback
- **Scanner**: jsQR + BarcodeDetector (dual fallback)

## Ativo (Simplified)
- **Required**: Área, TAG, Nome, Tipo de Equipamento
- **Optional**: Fabricante, Modelo, Número de Série, Observações
- **Attachments**: Manual PDF, Fotos, Desenhos Técnicos
- **Materiais**: Bill of materials per equipment
- **KPIs**: Auto-calculated MTBF, MTTR, Disponibilidade

## QR Code System
- QR code auto-generated per ativo
- Scanner page with camera auto-start + jsQR fallback
- Manual TAG search fallback
- Print-friendly QR card with KPIs
- Central "Scan" button in mobile bottom nav

## Implemented
- Área CRUD + enable/disable
- Ativo CRUD simplified (no criticidade/status)
- Materiais por Equipamento (bill of materials)
- Work Orders: 6 types, 5 disciplines, causa_falha, equipamento_parado, horas_parada
- Inspections: 3 types with default editable checklists (10/10/9 items)
- Kanban board with audit trail
- Dashboard: KPIs auto-calc, OS por Área/Disciplina, Ativos mais Falhas
- PWA installable + offline queue + camera
- QR Scanner (camera + manual TAG search)
- Global error normalization

## Backlog
1. Executive Dashboard
2. OEE Foundation
3. Hierarchy Tree
4. Architecture Hardening (split App.js ~4838 lines)
