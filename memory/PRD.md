# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão: CMMS/EAM SaaS multi-tenant
## Stack: React PWA + FastAPI + MongoDB Atlas
## Piloto: ASTEC Engenharia

---

## RC — Documentos Profissionais Configuráveis — FASE 1 ✅ (17 Jul 2026)

### Entregas
- `pdf_engine.py` — Motor PDF v2.0 com DejaVu Unicode (µm, °C, Ω, Ø, ±, ≥, ≤, Δ, α, β, ², ³, →)
- `routes/doc_config.py` — API CRUD: doc_config, procedimentos, segurança
- `routes/exports.py` — Batch PDF OS/Inspeções com Unicode
- `DocConfigPage.js` — Menu Documentos e Formulários (5 tabs)
- Validação: 95/95 testes (42 Unicode + 53 regressão)

---

## RC — Biblioteca Corporativa — Sprint 1: Governança ✅ (17 Jul 2026)

### Entregas
- **Versionamento completo** para Procedimentos e Segurança
  - Cada criação/atualização gera versão imutável em `biblioteca_versoes`
  - Histórico completo com snapshot, motivo, data, usuário
  - Restauração de qualquer versão anterior (cria nova versão incrementada)
  - Backfill automático para itens pré-existentes
- **Frontend**: Botão "Versões" em cada item, modal com histórico e botão "Restaurar"
- **Campo `motivo_alteracao`** opcional em atualizações
- **Diacríticos corrigidos** em todos os labels do frontend

### Endpoints novos
- `GET /api/doc-config/procedimentos/{id}/versoes` — Histórico de versões
- `POST /api/doc-config/procedimentos/{id}/restaurar/{versao}?motivo=` — Restaurar versão
- `GET /api/doc-config/seguranca/{id}/versoes`
- `POST /api/doc-config/seguranca/{id}/restaurar/{versao}?motivo=`

### Collections MongoDB
- `biblioteca_versoes` — Arquivo imutável de todas as versões de itens da biblioteca

### Validação
- Sprint 1 versioning: 20/20 testes PASS
- Regressão: 52/53 (1 flake de rate-limit pré-existente)
- Frontend: VersionHistoryModal, badges de versão, restore — todos OK

---

## Funcionalidades Concluídas
- Auth multi-tenant com RBAC (master/admin/pcm/tecnico)
- Dashboard executivo + indicadores
- CRUD Ativos com dossiê completo
- Ordens de Serviço com máquina de estados (8 estados, 12 transições)
- Planos de Inspeção + Checklist
- Gestão de Estoque
- Exportações Excel + PDF
- PDF profissional multi-tenant com fotos, QR code, procedimentos, segurança
- Unicode/UTF-8 completo nos PDFs
- Download autenticado de PDFs via Blob
- Performance: N+1 queries eliminados
- MongoDB Atlas migration completa
- **Versionamento completo de Procedimentos e Segurança**

---

## Backlog Priorizado

### P1 — Sprint 2: Conteúdo Reutilizável
- Biblioteca de Checklists
- Modelos de Inspeção
- Modelos de OS

### P1 — Sprint 3: Personalização
- Campos Personalizados (17 tipos)
- Cabeçalhos / Rodapés / Assinaturas configuráveis
- Layouts por empresa

### P1 — Após Sprints
- RC Construtor Visual (Drag-and-Drop) — consome base da Biblioteca
- QR Code MVP (Fase 2 Piloto)

### P2
- Integrações ERP/SAP
- Dataset de homologação para smoke tests

### P3
- IA Assistente
- Impressão de etiquetas avançadas
