# MANUTRIX OMNI - Product Requirements Document

## Status: PRODUCTION READY ✅ (Simplified - June 2026)

## Architecture
- **Backend**: FastAPI + MongoDB (modularized)
- **Frontend**: React + Tailwind + Shadcn + PWA
- **Auth**: Supabase Auth + MongoDB bcrypt fallback
- **Hierarchy**: Área → Ativo (maximum simplicity)

## Data Model

### Área (collection: sectors)
- codigo, nome, descricao, cor, is_active

### Ativo (Required: Área, TAG, Nome, Tipo Equipamento)
- Optional: Fabricante, Modelo, Número de Série, Observações
- Attachments: Manual PDF, Fotos, Desenhos Técnicos
- Auto-calculated KPIs: MTBF, MTTR, Disponibilidade (from OS data)
- Materiais vinculados (bill of materials per asset)

### Ordem de Serviço
- Tipos: lubrificacao, limpeza_organizacao, preventiva, corretiva, preparacao_material, fabricacao_melhorias
- Disciplina (obrigatório): mecanica, eletrica, instrumentacao, civil
- Prioridade: baixa, media, alta, emergencia
- Fields: causa_falha, equipamento_parado, horas_parada

### Inspeção
- Tipos: mecanica, eletrica, lubrificacao
- Default editable checklists (10/10/9 items)

### Removidos (simplificação)
- ~~Criticidade~~, ~~Status do Ativo~~, ~~Centro de Custo~~
- ~~MTBF/MTTR manual~~, ~~Valor Aquisição~~, ~~Depreciação~~, ~~Garantia~~
- ~~Plantas~~, ~~Subsetores~~

## Backlog
1. Dashboard Executivo
2. OEE Foundation
3. Hierarchy Tree
4. Architecture Hardening (split App.js)
