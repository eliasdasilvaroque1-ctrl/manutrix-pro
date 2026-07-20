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
| master | master@maintrix.com | (env: MASTER_BOOTSTRAP_PASSWORD) | REQUIRES organization_id in login. Password set via env var. |

## Login API
POST /api/auth/login
- Body: {"email":"...", "password":"..."}
- Master requires: {"email":"...", "password":"...", "organization_id":"9a232bf2-fc01-4253-813f-8df356be31c1"}
- Returns: {access_token, user}

## File Download Auth
- All private files require JWT token in Authorization header
- Branding files (logo_*, wallpaper_*) are public (for login page)
- Files registered in file_registry with org_id for cross-org protection

## Emergency Master Reset
MASTER_RESET_PASSWORD=<new_password> python backend/manage_master.py

## Other Orgs (for isolation testing)
- Org de Admin CSN: ae302c30-32d3-4cc0-b745-9c83e122fe91
