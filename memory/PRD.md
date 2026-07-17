# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão: CMMS/EAM SaaS multi-tenant
## Stack: React PWA + FastAPI + MongoDB Atlas
## Piloto: ASTEC Engenharia

---

## RC — Documentos Profissionais — Fase 1 ✅ (17 Jul 2026)
- Motor PDF Unicode (DejaVu Sans), 95 testes

## RC — Biblioteca Corporativa — Sprint 1: Governança ✅ (17 Jul 2026)
- Versionamento completo para Procedimentos e Segurança
- Histórico + Restauração + Backfill automático

## RC — Biblioteca Corporativa — Sprint 2: Conteúdo Reutilizável ✅ (17 Jul 2026)

### Entregas
- **Biblioteca de Checklists**: CRUD + versionamento + itens com tipo/tolerância/unidade/ordem
- **Modelos de Inspeção**: CRUD + versionamento + associação (checklist, procedimento, segurança)
- **Modelos de OS**: CRUD + versionamento + associação + prioridade padrão
- **Auto-snapshot**: ao referenciar item da biblioteca via *_id, snapshot é criado automaticamente
- **Snapshot isolation**: alterações na biblioteca NÃO afetam snapshots já capturados
- **Frontend**: 3 novas tabs (Checklists, Modelos Inspeção, Modelos OS) com formulários completos

### Endpoints novos
- `/api/doc-config/checklists` (CRUD + versões + restaurar)
- `/api/doc-config/modelos-inspecao` (CRUD + versões + restaurar)
- `/api/doc-config/modelos-os` (CRUD + versões + restaurar)

### Collections MongoDB novas
- `checklists_padrao`, `modelos_inspecao`, `modelos_os`

### Validação
- Sprint 2: 29/29 testes PASS
- Sprint 1: 20/20 testes PASS
- Regressão rc41: 52/53 (1 flake pré-existente de rate-limit)
- Unicode PDF: 42/42
- **Total: ~143 testes**

---

## Funcionalidades Concluídas
- Auth multi-tenant com RBAC
- Dashboard executivo + indicadores
- CRUD Ativos com dossiê completo
- OS com máquina de estados (8 estados, 12 transições)
- Planos de Inspeção + Checklist
- Gestão de Estoque
- Exportações Excel + PDF
- PDF profissional multi-tenant com Unicode
- Download autenticado de PDFs
- Performance otimizada (N+1 eliminados)
- MongoDB Atlas
- Versionamento completo (Procedimentos, Segurança)
- **Biblioteca de Checklists (versionada)**
- **Modelos de Inspeção (versionados, com snapshot)**
- **Modelos de OS (versionados, com snapshot)**

---

## Backlog Priorizado

### P1 — Sprint 3: Personalização
- Campos Personalizados (17 tipos)
- Cabeçalhos / Rodapés / Assinaturas configuráveis
- Layouts por empresa

### P1 — Após Sprints
- RC Construtor Visual (Drag-and-Drop)
- QR Code MVP (Fase 2 Piloto)

### P2
- Integrações ERP/SAP
- Dataset de homologação para smoke tests

### P3
- IA Assistente
- Impressão de etiquetas avançadas
