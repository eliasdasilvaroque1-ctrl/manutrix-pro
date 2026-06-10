# MANUTRIX - Credenciais de Teste

## Contas de Usuário
| Role | Email | Senha | Supabase Synced |
|------|-------|-------|-----------------|
| Admin | admin@manutrix.com | admin123 | Yes |
| Supervisor | supervisor@manutrix.com | supervisor123 | Auto on login |
| Tecnico | tecnico@manutrix.com | tecnico123 | Auto on login |
| Tecnico 2 | pedro@manutrix.com | pedro123 | Auto on login |

## Supabase
- URL: https://qyzahffbzobetohxdkrp.supabase.co
- Auth: Email/password via Supabase Auth
- Fallback: MongoDB bcrypt auth if Supabase is down

## Auth Flow
1. Login tries Supabase first (sign_in_with_password)
2. If Supabase fails, falls back to MongoDB auth
3. On first MongoDB login, auto-creates Supabase user
4. Forgot password sends real email via Supabase

## Seed
- POST /api/seed - Creates demo data
