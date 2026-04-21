# MANUTRIX - Credenciais de Teste

## Contas de Usuário
| Role | Email | Senha |
|------|-------|-------|
| Admin | admin@manutrix.com | admin123 |
| Supervisor | supervisor@manutrix.com | supervisor123 |
| Tecnico | tecnico@manutrix.com | tecnico123 |
| Tecnico 2 | pedro@manutrix.com | pedro123 |

## Auth Endpoints
- POST /api/auth/login
- POST /api/auth/register
- GET /api/auth/me
- POST /api/auth/forgot-password
- POST /api/auth/reset-password
- POST /api/auth/change-password
- POST /api/admin/users/{id}/reset-password
- PUT /api/admin/users/{id}
- GET /api/admin/users
- POST /api/admin/users
- DELETE /api/admin/users/{id}

## Password Security
- bcrypt hashing (auto-migrates from SHA-256)
- Token-based reset (1h expiry)
- Force password change after admin reset
- Min 6 characters for new passwords

## Seed
- POST /api/seed - Creates demo data
