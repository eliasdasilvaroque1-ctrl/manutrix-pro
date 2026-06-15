# MANUTRIX OMNI — Product Requirements Document

## Problema Original
Sistema CMMS/EAM industrial simplificado para manutenção em campo. Hierarquia Área -> Ativo, RBAC estrito, Ordens de Serviço em Kanban, Inspeções com templates, fluxo de Anomalias, e gestão de Materiais/Sobressalentes.

## Arquitetura
- **Frontend:** React PWA (offline-first) — `/app/frontend/src/App.js` (monolítico ~5900 linhas)
- **Backend:** FastAPI — `/app/backend/server.py` + rotas em `/app/backend/routes/`
- **Banco:** MongoDB via `MONGO_URL`
- **Auth:** Supabase (primário) + MongoDB bcrypt (fallback)
- **Roles:** Admin, PCM, Técnico, Gerente (Supervisor)

## FASE 1 — Segurança, Auditoria e Perfis (CONCLUÍDA)
- [x] Rastreabilidade (criado_por, concluido_por, data) em OS, Anomalias, Inspeções
- [x] RBAC backend: check_write_permission, check_admin_only, check_pcm_or_admin
- [x] RBAC frontend: botões ocultos por role
- [x] Sistema de Auditoria completo (login, logout, 403, CRUD) + página UI
- [x] Duplicar Ativo
- [x] Templates de Inspeção vinculados a Tipo de Equipamento
- [x] Workflow de Anomalias (Aberta -> Em análise -> OS -> Corrigida -> Encerrada)
- [x] BOM/Lista Técnica em Ativos
- [x] SKU renomeado para "Código"
- [x] **P0 FIX: Sobressalentes Edit/Delete botões visíveis e funcionais** (2026-06-15)
  - Causa raiz: classe CSS `group` ausente no card pai + `hidden group-hover:flex` nos botões
  - Permissão corrigida: `['admin','pcm']` no frontend (backend já estava correto)
  - Auditoria: PUT/DELETE registram logs corretamente
  - Validado: Admin/PCM veem botões, Técnico não vê

## FASE 2 — Experiência Visual (PENDENTE — Aguardando aprovação FASE 1)
- [ ] Bloco 3: Quick indicators em Ativos (TAG, Nome, Área, Tipo, OS abertas, Anomalias abertas, foto 60x60)
- [ ] Bloco 4: Quick indicators em Estoque (Código, Categoria, Qtd, Status: Normal/Atenção/Crítico, Filtros)
- [ ] Bloco 5: Quick indicators em Sobressalentes (Foto, Status formatado)

## FASE 3 — Estoque e Sobressalentes (FUTURA)
- [ ] Bloco 6-7: Export Excel/PDF + timeline histórica por sobressalente
- [ ] Bloco 8: Movimentação de Estoque (Fornecedor, NF, Data NF, bloqueio estoque negativo)
- [ ] Bloco 9: Controle de Sobressalentes (Garantia, NF, Empresa Reparadora, Anexos, Histórico Reformas)

## FASE 4 — Planejamento e Indicadores (FUTURA)
- [ ] Bloco 10: Paradas Programadas (Scheduling, OS linking, duração, resultados)
- [ ] Bloco 11: Indicadores Gerenciais (MTBF, MTTR, Disponibilidade, OS por Área)

## FASE 5 — Ficha Técnica e Polimento (FUTURA)
- [ ] Bloco 12: Ficha Técnica Completa (Timeline unificada de eventos do Ativo)
- [ ] Bloco 13: Polimento Visual (Padronizar cards, badges, cores)

## Regra de Ouro
> Ao concluir cada fase: Parar imediatamente. Entregar evidências. Aguardar aprovação. Somente após aprovação iniciar a próxima fase.
