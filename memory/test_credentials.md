# MANUTRIX OMNI — Test Credentials

## Main Test Accounts (Organization: Indústria Demo)

| Role | Email | Password |
|------|-------|----------|
| Master | master@manutrix.com | master123 |
| Admin | admin@manutrix.com | admin123 |
| Supervisor | supervisor@manutrix.com | supervisor123 |
| Técnico | tecnico@manutrix.com | tecnico123 |
| PCM | pcm@manutrix.com | pcm123 |

## Multi-tenant Test Accounts

| Org | Email | Password | Role |
|-----|-------|----------|------|
| ASTEC | astec_admin@manutrix.com | astec123 | admin |
| VALE | vale_admin@manutrix.com | vale123 | admin |
| CSN | csn_admin@manutrix.com | csn123 | admin |

## API Endpoints

- POST /api/auth/login — Login
- POST /api/seed — Create demo data (admin/master only)

## Useful Commands

- Seed data: POST /api/seed (requires admin+ auth)
