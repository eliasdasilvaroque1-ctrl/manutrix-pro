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
- [x] Rastreabilidade completa
- [x] RBAC backend + frontend
- [x] Sistema de Auditoria
- [x] Duplicar Ativo, Templates, Anomalias, BOM, SKU→Código
- [x] FIX: Sobressalentes Edit/Delete
- [x] FIX: QR Code URL format

## FASE OPERACIONAL — Rastreabilidade e Execução (EM ANDAMENTO)

### Bloco 1: Poderes do PCM ✅ (2026-06-17)
**PCM PODE:**
- [x] Visualizar OS e Inspeções
- [x] Criar OS
- [x] Editar OS (prioridade, datas, responsável, equipe)
- [x] Editar Inspeções (observações, responsável, data planejada)
- [x] Mover OS no Kanban
- [x] Exportar relatórios

**PCM NÃO PODE:**
- [x] Iniciar OS → 403
- [x] Concluir OS → 403
- [x] Pausar OS → 403
- [x] Excluir OS → 403
- [x] Iniciar Inspeção → 403
- [x] Concluir Inspeção → 403
- [x] Excluir Inspeção → 403

**Arquivos alterados:** `routes/work_orders.py`, `server.py`, `App.js`
**Testes:** iteration_29 — Backend 14/14, Frontend 4/4

### Bloco 2: Executantes em OS e Inspeções (PRÓXIMO)
- [ ] Adicionar: Planejado por, Executado por, Concluído por em OS
- [ ] Executantes múltiplos em OS e Inspeções
- [ ] Registrar no histórico

### Bloco 3: Materiais Utilizados + Movimentação de Estoque
- [ ] Coleção os_materiais
- [ ] Dedução automática de estoque ao concluir OS
- [ ] Tabela de movimentação

### Bloco 4: Auditoria Detalhada
- [ ] Registrar alterações campo-a-campo (ex: "Prioridade: Média → Alta")

### Bloco 5: Histórico do Equipamento com Filtros
- [ ] Filtros: data, tipo, status, usuário

### Bloco 6: Detalhamento Completo da OS
- [ ] Todos os campos obrigatórios visíveis

### Bloco 7: Detalhamento Completo da Inspeção
- [ ] Todos os campos obrigatórios visíveis

## Fases Futuras
- FASE 2: Experiência Visual
- FASE 3: Estoque e Sobressalentes avançado
- FASE 4: Planejamento e Indicadores
- FASE 5: Ficha Técnica e Polimento

## Regra de Ouro
> Parar após cada bloco. Entregar evidências. Aguardar aprovação.
