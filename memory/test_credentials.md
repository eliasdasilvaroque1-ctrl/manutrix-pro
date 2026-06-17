# MANUTRIX - Credenciais de Teste

## Contas de Usuário
| Role | Email | Senha |
|------|-------|-------|
| Admin | admin@manutrix.com | admin123 |
| PCM | pcm@manutrix.com | pcm123 |
| Supervisor | supervisor@manutrix.com | supervisor123 |
| Tecnico | tecnico@manutrix.com | tecnico123 |
| Tecnico 2 | pedro@manutrix.com | pedro123 |

## Auth Flow
1. Login tries Supabase first
2. Falls back to MongoDB bcrypt if Supabase fails
3. Forgot password via Supabase email

## Seed
- POST /api/seed - Creates demo data (sectors, ativos, OS, inspections)
