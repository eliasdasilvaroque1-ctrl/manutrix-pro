# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Status: APROVADO PARA MERGE E DEPLOY — Piloto ASTEC
## Branch aprovada: security/pre-pilot-access-hardening (edcc5de)
## Baseline producao anterior: main (ec78f1d)
## Versao piloto: pilot-astec-v1.0.0

---

## Security Hardening (esta branch)
1. File downloads: JWT auth + file_registry + deny-by-default
2. Master credential: env var only, zero hardcoded passwords
3. Demo seed: ENABLE_DEMO_SEED flag, blocked in production
4. force_password_change: backend enforcement
5. CLI recovery: manage_master.py
6. Branding: is_public only via admin config endpoints
7. Backfill: startup scan of OS, ativos, org_config, estoque

## Env Vars Required in Production
- ENVIRONMENT=production
- ENABLE_DEMO_SEED=false (or unset)
- MASTER_BOOTSTRAP_PASSWORD (only if no master exists, remove after)
- DEMO_SEED_PASSWORD (DO NOT set in production)
- JWT secret, MONGO_URL, DB_NAME, CORS origins (existing)

---

## QA Results
- R1: 43/43 PASSED
- R2: 78/78 PASSED
- R3: 48/48 PASSED
- Total: 169/169 GREEN
- Credential scan: 0 passwords in production code
- Cross-org isolation: verified 3x
- force_password_change: enforced at backend

---

## POST-PILOTO BACKLOG
1. RC6.1: Construtor de Secoes da OS
2. Biblioteca Tecnica Inteligente
3. Procedimentos Inteligentes
4. Templates por Equipamento
5. QR Code MVP
6. Otimizacao /api/central
7. Paginacao /api/ativos
8. Extracao OSDetailPage
9. ERP/SAP
10. IA Assistente
