# FILE SECURITY DESIGN — MAINTRIX

**Data:** 2026-07-12  
**Versão:** 5.2.0-RC2  

---

## Problema

Tags HTML `<img src>`, `<a href>`, e `window.open()` fazem requests HTTP GET puros — sem header `Authorization`. Em apps com autenticação JWT Bearer, arquivos servidos precisam de uma estratégia diferente de proteção.

## Modelo de Segurança Adotado: UUID-Based Access

URLs de arquivos no MAINTRIX seguem o padrão:
```
/api/storage/maintrix/{categoria}/{owner_id}/{uuid}.{ext}
/api/uploads/{uuid}.{ext}
```

O UUID v4 possui 122 bits de entropia (5.3 × 10³⁶ combinações). A probabilidade de adivinhar uma URL válida é astronomicamente baixa — equivalente à segurança de um token de sessão.

### Comparação com serviços de referência

| Serviço | Modelo | Proteção |
|---------|--------|----------|
| AWS S3 (public bucket) | UUID/key-based URLs | Sem auth no GET, URL unguessable |
| Firebase Storage | Token em query string | Signed URLs temporários |
| Imgur | UUID-based URLs | Público, URL unguessable |
| **MAINTRIX** | **UUID-based URLs + rate limit** | **Público no GET, auth no POST** |

---

## Classificação de Recursos

### PÚBLICO (GET sem auth)
Recursos necessários para renderização do frontend via `<img>`, `<link>`, `window.open()`.

| Recurso | Padrão de URL | Consumidor | Justificativa |
|---------|--------------|-----------|---------------|
| Logos de organização | `/api/storage/.../org_assets/{org_id}/{uuid}.ext` | Sidebar, Portal Público, Login | Renderizado em todas as páginas, inclusive públicas |
| Fotos de ativos | `/api/storage/...` | Portal Público (sem auth) | Rota `/portal/equipamento/:id` é pública |
| Imagens de materiais | `/api/storage/...` ou `/api/uploads/{uuid}.ext` | MaterialThumbnail (`<img>`) | Exibido em listas de estoque/sobressalentes |
| Fotos de inspeção | `/api/storage/...` | InspecaoDetailPage (`<img>`) | Exibido no detalhe da inspeção |
| Anexos (imagens) | `/api/storage/...` ou `/api/uploads/{uuid}.ext` | OS Detail, Inspeção (`<img>`) | Exibido inline |
| Manuais (PDF) | `/api/uploads/manuals/{uuid}.pdf` | `window.open()` / download | Aberto em nova aba |

**Proteção:** UUID v4 (122 bits de entropia) + rate limiting (60 req/min por IP) + logging estruturado.

### PROTEGIDO (POST com auth)
Operações de escrita que alteram o estado do sistema.

| Operação | Endpoint | Auth | RBAC |
|----------|----------|------|------|
| Upload geral | `POST /api/upload` | ✅ JWT | Qualquer user autenticado |
| Upload manual PDF | `POST /api/ativos/{id}/manual` | ✅ JWT | Admin only |
| Upload imagem material | `POST /api/materiais/{tipo}/{id}/images` | ✅ JWT | Qualquer user autenticado |
| Upload anexo | `POST /api/attachments` | ✅ JWT | Qualquer user autenticado |
| Delete imagem | `DELETE /api/materiais/{tipo}/{id}/images` | ✅ JWT | Qualquer user autenticado |
| Delete manual | `DELETE /api/manuais/{id}` | ✅ JWT | Admin only |
| Delete anexo | `DELETE /api/attachments/{id}` | ✅ JWT | Qualquer user autenticado |

### ADMINISTRATIVO (GET/POST com auth + RBAC)
Endpoints que geram relatórios com dados sensíveis.

| Operação | Endpoint | Auth | RBAC |
|----------|----------|------|------|
| Export ativos (Excel) | `GET /api/export/ativos` | ✅ JWT | Admin/Supervisor |
| Export OS (Excel) | `GET /api/export/ordens-servico` | ✅ JWT | Admin/Supervisor |
| Export estoque (Excel) | `GET /api/export/estoque` | ✅ JWT | Admin/Supervisor |
| Export inspeções (Excel) | `GET /api/export/inspecoes` | ✅ JWT | Admin/Supervisor |
| Export sobressalentes | `GET /api/export/sobressalentes` | ✅ JWT | Admin/Supervisor |
| Export auditoria | `GET /api/export/audit` | ✅ JWT | Admin only |
| System status | `GET /api/system/status` | ✅ JWT | Admin/Master |

---

## Controles de Segurança para Endpoints Públicos

| Controle | Implementação |
|----------|--------------|
| **UUID v4** | 122 bits de entropia — inacessível sem URL exata |
| **Rate limiting** | 60 req/min por IP nos endpoints de servir arquivos |
| **Logging** | Cada acesso a arquivo logado (request_id, IP, path, status) |
| **Validação de upload** | Size limit (10MB), magic bytes, extension whitelist |
| **Path traversal** | Pathlib resolve previne `../` |
| **MIME type** | `FileResponse` infere content-type correto |

---

## Roadmap Futuro (Fase 3+)

| Melhoria | Benefício | Esforço |
|----------|----------|---------|
| Signed URLs com expiração | URLs temporárias (15min TTL) | Alto |
| Image proxy com auth cookie | Frontend faz fetch→blob URL | Médio |
| Watermark em imagens privadas | Rastreabilidade de vazamentos | Médio |
