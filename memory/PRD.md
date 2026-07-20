# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Status: DOMÍNIO OFICIAL VALIDADO TECNICAMENTE — PENDENTE APENAS IDENTIFICAÇÃO JURÍDICA
## Branch: security/pre-pilot-access-hardening
## Versao piloto: pilot-astec-v1.0.0
## Domínio oficial: https://app.maintrix.com.br
## Último deploy validado: 2026-07-20

---

## Security Hardening
1. File downloads: JWT auth + file_registry + deny-by-default ✅
2. Master credential: env var only, zero hardcoded passwords ✅
3. Demo seed: ENABLE_DEMO_SEED flag, blocked in production ✅
4. force_password_change: backend enforcement ✅
5. CLI recovery: manage_master.py ✅
6. Branding: is_public only via admin config endpoints ✅
7. Backfill: startup scan of OS, ativos, org_config, estoque ✅

## Compliance Documents
- Política de Privacidade: v1.0, 4085 chars, 11 seções ✅
- Termos de Uso: v1.0, 3058 chars, 10 seções ✅ (CNPJ: [A definir])
- Arquivos: backend/compliance/ (co-localizados com backend)
- COMPLIANCE_DIR: resolve parent/compliance com fallback parent.parent/compliance

## QA Results
- R1-R3: 169/169 GREEN
- Compliance restore: 11/11 backend + frontend visual OK
- Smoke test produção: 10/10 PASS
- Console: Zero erros JS relacionados a compliance

---

## RESSALVAS PENDENTES
1. CNPJ: [A definir] nos Termos de Uso — aguardando proprietário
2. ENVIRONMENT=production não configurado no painel de deploy (P3 informativo)

## P2 BACKLOG
- preview_numeracao: 500 para ordens_servico (digitos=null)
- Org branding images 401 (fallback ativo)

## POST-PILOTO BACKLOG
1. RC6.1: Construtor de Secoes da OS
2. QR Code MVP (Fase 2)
3. Biblioteca Tecnica Inteligente
4. Templates por Equipamento
5. Otimizacao /api/central
6. Paginacao /api/ativos
7. Extracao OSDetailPage
8. ERP/SAP
9. IA Assistente
