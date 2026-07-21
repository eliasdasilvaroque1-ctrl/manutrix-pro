# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Status: STORAGE SUPABASE OPERACIONAL — PRONTO PARA PRODUÇÃO
## Versao: pilot-astec-v1.0.0
## Domínio: https://app.maintrix.com.br

---

## Storage Architecture
- Primary: Supabase Storage (bucket: maintrix-files, privado)
- Fallback: Emergent Object Storage (lazy-loaded, sob demanda)
- Abstração: StorageProvider → SupabaseStorageProvider / EmergentStorageProvider
- Config: STORAGE_PROVIDER=supabase, STORAGE_FALLBACK_PROVIDER=emergent
- Startup: APENAS Supabase inicializado. Emergent NÃO é tocado.
- Lazy loading: Emergent instanciado SOMENTE na primeira operação que requer fallback.

## Migração
- 33/34 objetos migrados (SHA-256 verificado)
- 1 falha: orgb_file.pdf (corrompido no Emergent, pré-existente)
- Fallback Emergent mantido para objetos não migrados

## Variáveis Railway Obrigatórias
- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- STORAGE_PROVIDER=supabase
- STORAGE_FALLBACK_PROVIDER=emergent
- EMERGENT_LLM_KEY (opcional, para fallback legado)

## Security
- Bucket privado, sem acesso público global ✅
- Branding: file_registry is_public=true + category=branding ✅
- Service key: backend only ✅
- Zero secrets no frontend/logs/bundle ✅

## Compliance
- Política de Privacidade: v1.0, 4085 chars ✅
- Termos de Uso: v1.0, 3058 chars ✅ (CNPJ: [A definir])

## QA
- 169/169 GREEN (pre-pilot)
- Migration: 33/34 SHA-256 verified
- Preview smoke: 10/10 PASS
- Startup sem EMERGENT_LLM_KEY: LIMPO (zero warnings)

## POST-PILOTO BACKLOG
1. Remover fallback Emergent após estabilização
2. RC6.1: Construtor de Seções da OS
3. QR Code MVP (Fase 2)
4. preview_numeracao fix (digitos=null)
5. ERP/SAP
6. IA Assistente
