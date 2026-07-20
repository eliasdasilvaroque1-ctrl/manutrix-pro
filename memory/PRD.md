# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Status: DOMÍNIO OFICIAL VALIDADO TECNICAMENTE COM RESSALVA
## Branch aprovada: security/pre-pilot-access-hardening (edcc5de)
## Baseline producao anterior: main (ec78f1d)
## Versao piloto: pilot-astec-v1.0.0
## Domínio oficial: https://app.maintrix.com.br

---

## Security Hardening (esta branch)
1. File downloads: JWT auth + file_registry + deny-by-default ✅
2. Master credential: env var only, zero hardcoded passwords ✅
3. Demo seed: ENABLE_DEMO_SEED flag, blocked in production ✅
4. force_password_change: backend enforcement ✅
5. CLI recovery: manage_master.py ✅
6. Branding: is_public only via admin config endpoints ✅
7. Backfill: startup scan of OS, ativos, org_config, estoque ✅

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

## Smoke Test Domínio Oficial (2026-07-20)
- SSL: PASS (Let's Encrypt, válido até 2026-09-30)
- Auth (6 perfis): PASS
- Tenant isolation: PASS
- File deny-by-default: PASS
- CRUD (Ativos/OS/Procedimentos/Central): PASS
- Documentos Legais: FALHA (placeholder)
- preview_numeracao: FALHA (500, digitos=null)
- Relatório completo: /app/memory/RELATORIO_DOMINIO_OFICIAL.md

---

## PROBLEMAS ABERTOS

### P1 PRÉ-PILOTO (Bloqueante)
- Política de Privacidade e Termos de Uso retornando placeholder "Documento em preparação." (24 chars)
- Causa: arquivos compliance/ ausentes no deploy
- Ação: criar/restaurar politica_privacidade.md e termos_de_uso.md, deploy, validar

### P2
- preview_numeracao retorna 500 para entidade ordens_servico
- Causa: numeracao.ordens_servico.digitos = null no MongoDB
- Fix: `pattern.get("digitos") or 5` ou corrigir valor no DB
- Não afeta criação/execução de OS

### P3
- MAINTRIX_ENV=homologacao (deveria ser production) — apenas informativo

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
