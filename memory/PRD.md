# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## RC — Biblioteca Corporativa — Sprint 3: Personalização Corporativa ✅

### Módulos Implementados (Fundação + Integração)
1. **Campos Personalizados**: 17 tipos, Pydantic validators, aplicação por módulo/tipo
2. **Cabeçalhos/Rodapés**: Configuráveis por empresa (razão social, CNPJ, endereço, etc.)
3. **Blocos de Assinatura**: Campos estruturados, captura digital (canvas touch)
4. **Layouts de Documento**: Blocos visíveis/ocultos/ordem, cabeçalho/rodapé com auto-snapshot

### Integrações Completas
- **PDF Personalizado**: Motor PDF usa layout congelado (cabecalho custom, rodapé custom, campos, assinaturas)
- **Auto-snapshot na OS**: Layout + campos + cabeçalho/rodapé congelados automaticamente na criação
- **Renderização Dinâmica**: DynamicFieldRenderer no formulário de criação de OS (17 tipos)
- **Assinatura Digital**: Canvas touch + captura base64 + POST /api/assinaturas/capturar
- **SignaturePad**: Integrado na modal "Finalizar Rapidamente" da OS
- **Snapshot Isolation**: Alterações futuras não afetam documentos já emitidos (verificado por pdfplumber)
- **Compatibilidade**: OS antigas sem layout geram PDF normalmente (fallback padrão)

### Endpoints
- `/api/doc-config/campos` (CRUD + versões + restaurar + `/por-modulo/{modulo}?tipo=`)
- `/api/doc-config/cabecalhos-rodapes` (CRUD + versões)
- `/api/doc-config/assinaturas` (CRUD + versões)
- `/api/doc-config/layouts` (CRUD + versões)
- `/api/assinaturas/capturar` (POST — captura digital com base64)

### Validação
- Sprint 3 foundation: 42/42 PASS
- Sprint 3 integration: 25/25 PASS
- Regressão rc41: 53/53 PASS
- Unicode PDF: 42/42 PASS
- **Total: ~210+ testes**

---

## Concluído
- Auth multi-tenant RBAC
- Dashboard executivo
- CRUD Ativos + Dossiê
- OS máquina de estados
- Inspeções + Checklists
- Estoque
- Exportações Excel/PDF
- PDF profissional Unicode
- Download autenticado Blob
- Performance otimizada
- MongoDB Atlas
- Sprint 1: Versionamento (Procedimentos + Segurança)
- Sprint 2: Checklists + Modelos Inspeção + Modelos OS
- Sprint 3: Campos Personalizados + Cabeçalhos/Rodapés + Assinaturas + Layouts + PDF Integration

---

## Backlog

### P1
- RC Construtor Visual (Drag-and-Drop)
- QR Code MVP (Fase 2 Piloto)

### P2
- ERP/SAP

### P3
- IA Assistente
