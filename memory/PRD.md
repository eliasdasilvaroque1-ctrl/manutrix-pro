# MAINTRIX ENTERPRISE — Product Requirements Document

## Visão do Produto
CMMS/EAM SaaS multi-tenant para gestão de manutenção industrial.

## Stack: React PWA + FastAPI + MongoDB Atlas + Supabase (Storage)

## v1.0 Release (Fev 2026) ✅
- Core: PWA Offline, RBAC 7 roles, Multi-tenant, Dossiê Ativo, Dashboard Executivo, State Machine OS, Auditoria
- Export: PDF/Excel (OS, Ativos, Inspeções, Preventivas), Batch Print, QR Code

## RC4.2 Production Hardening (Jul 2026) ✅
- N+1 eliminados: OS listing 35s→1.1s, Export 37s→1.6s
- Bugs: useCallback fix, RBAC técnico/preventiva, export N+1
- Migração MongoDB: localhost → Atlas Cluster0 (2468 docs, 49 collections)
- **Parecer: APTO PARA PILOTO ASTEC**

## Backlog
- P1: Railway/Vercel deploy config
- P2: Refresh Token, ERP/SAP integrations
- P3: IA Assistente, App.js refactor
