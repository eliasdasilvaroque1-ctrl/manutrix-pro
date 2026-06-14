# MANUTRIX OMNI - Product Requirements Document

## Original Problem Statement
MANUTRIX OMNI — CMMS/EAM field-ready for industrial maintenance. Flat Area→Asset hierarchy, Kanban Work Orders, Inspections, Spare Parts, QR Code, PWA offline-first.

## Architecture
- Backend: FastAPI + MongoDB + Supabase Auth
- Frontend: React PWA (Service Worker network-first)
- DB: sectors, ativos, ordens_servico, inspecoes, anomalias, itens_estoque

## FASE 1 — Estabilização Operacional (COMPLETA 2026-06-14)

### Implementado e Validado com Evidência Visual:
- [x] Área + TAG + Equipamento em TODAS as telas
- [x] Cadastro limpo (removidos criticidade, status, centro de custo, MTBF/MTTR manual, financeiros)
- [x] Herdar ativo automaticamente (Nova OS/Inspeção com ativo travado)
- [x] Modal conclusão OS com "Serviço Executado" + "Tempo Gasto" obrigatórios
- [x] Histórico do Ativo (prontuário) com timeline OS/Inspeções/Anomalias
- [x] UNIQUE(area_id, tag) com índice MongoDB
- [x] Export Excel com "Área" como primeira coluna
- [x] Service Worker corrigido: network-first (cache-v3) para evitar versão antiga

### Bug Corrigido: OS "Erro na ação"
- **Causa raiz**: Service Worker usava cache-first para JS/CSS → navegador servia bundle antigo
- **Correção**: Bump cache para v3 + estratégia network-first + auto-update do SW
- **Evidência**: Fluxo completo OS Criar→Iniciar→Pausar→Retomar→Concluir via modal com screenshots

## FASE 2 — Anomalias e Templates (PRÓXIMA)
- [ ] Anomalias: workflow completo (Aberta→Em análise→OS→Corrigida→Encerrada)
- [ ] Templates de inspeção por tipo de equipamento (CRUD admin)
- [ ] Bug checklist "Preencha todos os itens"
- [ ] Consulta histórica filtrada (anomalias abertas/encerradas)
- [ ] Auditoria visual final

## SUSPENSO
- Dashboard Executivo, OEE, Tree View, Push Notifications
