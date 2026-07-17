# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Concluído

### RC Documentos Profissionais — Fase 1 ✅
- Motor PDF Unicode (DejaVu Sans), 95 testes

### RC Biblioteca Corporativa — Sprint 1: Governança ✅
- Versionamento completo Procedimentos + Segurança, histórico, restauração

### RC Biblioteca Corporativa — Sprint 2: Conteúdo Reutilizável ✅
- Checklists, Modelos Inspeção, Modelos OS — todos versionados com snapshot isolation

### RC Biblioteca Corporativa — Sprint 3: Personalização (em andamento)
**Fundação completa** — Backend + Frontend de gerenciamento:
- ✅ Campos Personalizados: 17 tipos, validação Pydantic, ident imutável, filtragem por módulo/tipo
- ✅ Cabeçalhos/Rodapés: razão social, CNPJ, endereço, paginação, data emissão
- ✅ Blocos de Assinatura: campos estruturados, captura digital flag, matrícula
- ✅ Layouts de Documento: blocos visíveis/ocultos, ordem, cabeçalho/rodapé com snapshot
- ✅ Versionamento completo nos 4 módulos
- ✅ Snapshot isolation verificado
- ✅ RBAC validado
- ✅ Frontend: 4 novas tabs com formulários completos

**Próximos passos da Sprint 3:**
- ⏳ Renderizador dinâmico de campos no frontend (OS/Inspeções/Ativos)
- ⏳ Integração com pdf_engine.py (custom headers/footers/fields/signatures)
- ⏳ Captura de assinatura digital por toque
- ⏳ Testes end-to-end completos

### Validação acumulada
- Sprint 3: 42/42 PASS
- Sprint 2: 29/29 PASS
- Sprint 1: 20/20 PASS
- Unicode PDF: 42/42 PASS
- Regressão rc41: 53/53 PASS
- **Total: ~186 testes**

---

## Backlog

### P1 (Sprint 3 restante)
- Renderizador dinâmico de campos
- Integração PDF com custom headers/footers/layouts
- Captura assinatura digital
- Testes completos Sprint 3

### P1 (Pós-Sprint 3)
- RC Construtor Visual (Drag-and-Drop)
- QR Code MVP (Fase 2 Piloto)

### P2
- Integrações ERP/SAP

### P3
- IA Assistente
