# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Status: STORAGE MIGRADO PARA SUPABASE — AGUARDANDO DEPLOY PRODUÇÃO
## Branch: security/pre-pilot-access-hardening
## Versao: pilot-astec-v1.0.0
## Domínio: https://app.maintrix.com.br

---

## Storage Architecture (NOVA)
- Primary: Supabase Storage (bucket: maintrix-files, privado)
- Fallback: Emergent Object Storage (leitura apenas)
- Abstração: StorageProvider → SupabaseStorageProvider / EmergentStorageProvider
- Config: STORAGE_PROVIDER=supabase, STORAGE_FALLBACK_PROVIDER=emergent
- Migração: 33/34 objetos migrados com SHA-256 verificado (1 falha: orgb_file.pdf corrupto no Emergent)
- Branding: category=branding, is_public=true no file_registry

## Variáveis Obrigatórias Railway
- SUPABASE_URL (já configurado)
- SUPABASE_SERVICE_KEY (já configurado)
- STORAGE_PROVIDER=supabase (NOVO)
- STORAGE_FALLBACK_PROVIDER=emergent (NOVO, opcional)
- EMERGENT_LLM_KEY (para fallback, opcional)

## Security
1. File downloads: JWT auth + file_registry + deny-by-default ✅
2. Branding público: file_registry is_public=true + category=branding ✅
3. Bucket Supabase: privado (sem acesso público global) ✅
4. Service key: backend only ✅
5. Master credential: env var only ✅
6. force_password_change: backend enforcement ✅

## Compliance
- Política de Privacidade: v1.0, 4085 chars ✅
- Termos de Uso: v1.0, 3058 chars ✅ (CNPJ: [A definir])

## QA: 169/169 GREEN + Migration 33/34 + Preview 13/13

## POST-PILOTO BACKLOG
1. Remover fallback Emergent após estabilização
2. RC6.1: Construtor de Seções da OS
3. QR Code MVP (Fase 2)
4. preview_numeracao fix (digitos=null)
5. ERP/SAP
6. IA Assistente
