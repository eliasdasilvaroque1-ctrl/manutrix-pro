# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## ✅ RC Construtor Visual de Documentos — Onda 1 (17 Jul 2026)

### Arquitetura
- **Camada visual sobre a Biblioteca Corporativa** — não duplica lógica
- **Schema JSON estruturado** (schema_version: 1) com blocos tipados e validados
- **@dnd-kit/core** + @dnd-kit/sortable para DnD (mouse + touch + teclado)
- **3-panel layout**: Paleta (esquerda) → Canvas (centro) → Propriedades (direita)
- **Workflow**: Rascunho → Publicado → Inativo (1 publicado por tipo_documento por org)

### Schema de Blocos
```json
{ "schema_version": 1, "blocks": [
  {"id": "uuid", "type": "header", "order": 0, "visible": true, "settings": {}, "library_ref_id": null}
]}
```
15 tipos de bloco: header, footer, equipment, info, description, team, dates, procedure, safety, checklist, signature, qr_code, photos, materials, indicators, history, custom_fields, free_text, separator, page_break, observations

### Validações Backend (Pydantic)
- Tipos de bloco: whitelist BLOCK_TYPES
- IDs duplicados → 422
- Max 1 header/footer → 422
- Referências cross-tenant → 400 na publicação
- HTML/scripts rejeitados

### Endpoints novos
- POST `/api/doc-config/layouts/{id}/publicar`
- POST `/api/doc-config/layouts/{id}/duplicar`
- GET `/api/doc-config/layouts/publicado/{tipo_documento}`
- GET `/api/doc-config/layouts/{id}/preview-data`

### Testes Wave 1: 24/24 PASS
### Regressão: 53/53 PASS
### Total acumulado: ~235+ testes

---

## Concluído
- Auth multi-tenant RBAC | Dashboard | CRUD Ativos | OS máquina de estados | Inspeções | Estoque
- Exportações Excel/PDF | PDF Unicode (DejaVu Sans) | Download Blob | Performance
- Sprint 1: Versionamento | Sprint 2: Checklists/Modelos | Sprint 3: Personalização completa
- **Construtor Visual Onda 1**: DnD, validação, publicação, snapshot isolation

---

## Backlog

### P1 (Onda 2/3 Construtor)
- Config por bloco (fontes, margens, cores)
- WYSIWYG preview em tempo real
- Texto livre avançado

### P1
- QR Code MVP (Fase 2 Piloto)

### P2
- ERP/SAP
- Dataset homologação

### P3
- IA Assistente
