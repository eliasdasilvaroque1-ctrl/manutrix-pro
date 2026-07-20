# Test Credentials — MAINTRIX Enterprise

## Organização: ASTEC Cedro
- ID: 9a232bf2-fc01-4253-813f-8df356be31c1

## Accounts
| Role | Email | Password | Notes |
|------|-------|----------|-------|
| admin | test.admin@maintrix.com | admin123 | Org auto-detected |
| pcm | test.pcm@maintrix.com | pcm123 | |
| supervisor | test.sup.mec@maintrix.com | sup123 | |
| tec_mecanico | test.mec@maintrix.com | tec123 | |
| operador | test.operador@maintrix.com | op123 | |
| master | master@maintrix.com | master123 | REQUIRES organization_id in login body |

## Login API
POST /api/auth/login with {email, password} returns {access_token, user}
Master: add organization_id to body

## Security
- All private file downloads require JWT Authorization header
- Branding files (logo_*, wallpaper_*) with is_public=true in file_registry are public
- Unregistered files: DENIED (404) by default
- Demo seed: requires ENABLE_DEMO_SEED=true (blocked in production)
- force_password_change: enforced at backend level (blocks all except /auth/*)

## Emergency Master Reset
MASTER_RESET_PASSWORD=<new_password> python backend/manage_master.py
