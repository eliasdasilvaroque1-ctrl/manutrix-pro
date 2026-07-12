# MAINTRIX — Test Credentials

## Organization
- ASTEC Cedro (org_id: 9a232bf2-fc01-4253-813f-8df356be31c1)

## Users by Role

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| master | master@maintrix.com | master123 | Acesso cross-tenant |
| admin | test.admin@maintrix.com | admin123 | Admin da org ASTEC |
| pcm | test.pcm@maintrix.com | pcm123 | Planejamento |
| supervisor (mec) | test.sup.mec@maintrix.com | sup123 | Turno A, mecânica |
| supervisor (ele) | test.sup.ele@maintrix.com | sup123 | Turno A, elétrica |
| técnico (mec) | test.mec@maintrix.com | tec123 | Turno A, mecânica |
| técnico (ele) | test.ele@maintrix.com | tec123 | Turno B, elétrica |
| operador | test.operador@maintrix.com | op123 | Turno A, force_password_change=True |

## Login Flow
1. Open app URL
2. Type email — org auto-detected for non-master users
3. Enter password
4. Click "Entrar"

## Login sem org_id (API)
- Non-master: `POST /api/auth/login {"email":"test.admin@maintrix.com","password":"admin123"}` → auto-resolve org
- Master: requires `organization_id` explicitly
