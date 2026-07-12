# FILE SECURITY MATRIX — MAINTRIX v5.2.0-RC2

**Data:** 2026-07-12  

---

## Endpoints de Servir Arquivos (GET)

| Endpoint | Classificação | Auth | Rate Limit | Proteção UUID | Justificativa |
|----------|--------------|------|-----------|---------------|---------------|
| `GET /api/uploads/{filename}` | **Público** | ❌ | 60/min/IP | ✅ UUID v4 | `<img src>` não envia auth header |
| `GET /api/uploads/manuals/{filename}` | **Público** | ❌ | 60/min/IP | ✅ UUID v4 | `window.open()` não envia auth header |
| `GET /api/storage/{path}` | **Público** | ❌ | 60/min/IP | ✅ UUID v4 | `<img src>` não envia auth header |

## Endpoints de Upload (POST/DELETE)

| Endpoint | Classificação | Auth | RBAC | Size Limit | Type Check |
|----------|--------------|------|------|-----------|-----------|
| `POST /api/upload` | **Privado** | ✅ JWT | Qualquer user | 10MB | ext + magic bytes |
| `POST /api/ativos/{id}/manual` | **Administrativo** | ✅ JWT | Admin | 10MB | .pdf only |
| `POST /api/materiais/{tipo}/{id}/images` | **Privado** | ✅ JWT | Qualquer user | 10MB | img + magic bytes |
| `POST /api/attachments` | **Privado** | ✅ JWT | Qualquer user | 10MB | ext + magic bytes |
| `DELETE /api/materiais/{tipo}/{id}/images` | **Privado** | ✅ JWT | Qualquer user | — | — |
| `DELETE /api/manuais/{id}` | **Administrativo** | ✅ JWT | Admin | — | — |
| `DELETE /api/attachments/{id}` | **Privado** | ✅ JWT | Qualquer user | — | — |

## Endpoints de Export (GET)

| Endpoint | Classificação | Auth | RBAC |
|----------|--------------|------|------|
| `GET /api/export/ativos` | **Administrativo** | ✅ JWT | Admin/Supervisor |
| `GET /api/export/ordens-servico` | **Administrativo** | ✅ JWT | Admin/Supervisor |
| `GET /api/export/estoque` | **Administrativo** | ✅ JWT | Admin/Supervisor |
| `GET /api/export/inspecoes` | **Administrativo** | ✅ JWT | Admin/Supervisor |
| `GET /api/export/sobressalentes` | **Administrativo** | ✅ JWT | Admin/Supervisor |
| `GET /api/export/audit` | **Administrativo** | ✅ JWT | Admin only |

## Endpoints de Compliance (GET)

| Endpoint | Classificação | Auth |
|----------|--------------|------|
| `GET /api/compliance/terms` | **Público** | ❌ |
| `GET /api/compliance/privacy` | **Público** | ❌ |
| `GET /api/compliance/about` | **Público** | ❌ |
| `GET /api/compliance/status` | **Privado** | ✅ JWT |
| `POST /api/compliance/accept` | **Privado** | ✅ JWT |
| `GET /api/compliance/history` | **Administrativo** | ✅ JWT + Admin |

## Endpoints de Diagnóstico

| Endpoint | Classificação | Auth |
|----------|--------------|------|
| `GET /api/health` | **Público** | ❌ |
| `GET /api/system/status` | **Administrativo** | ✅ JWT + Admin/Master |

---

## Resumo por Classificação

| Classificação | Qtd Endpoints | Controles |
|--------------|--------------|----------|
| **Público** | 8 | UUID + Rate Limit + Logging |
| **Privado** | 8 | JWT Auth + Upload Validation |
| **Administrativo** | 10 | JWT Auth + RBAC + Logging |
