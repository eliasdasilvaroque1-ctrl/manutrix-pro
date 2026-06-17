# MANUTRIX OMNI — Product Requirements Document

## Problema Original
Sistema CMMS/EAM industrial simplificado para manutenção em campo.

## Arquitetura
- **Frontend:** React PWA — `/app/frontend/src/App.js`
- **Backend:** FastAPI — `/app/backend/server.py` + `/app/backend/routes/`
- **Banco:** MongoDB
- **Auth:** Supabase + MongoDB bcrypt fallback
- **Roles:** Admin, PCM, Técnico, Gerente (Supervisor)

## FASE 1 — Segurança, Auditoria e Perfis ✅

## FASE OPERACIONAL — Rastreabilidade e Execução (EM ANDAMENTO)

### Bloco 1: Poderes do PCM ✅ (2026-06-17)
PCM pode: criar/editar OS e inspeções, kanban, exportar.
PCM não pode: iniciar/concluir/pausar/excluir OS/inspeções.

### Bloco 2: Executantes + Rastreabilidade ✅ (2026-06-17)
**Campos de rastreabilidade na OS:**
- [x] Criado por + Data abertura
- [x] Planejado por + Data planejamento (set on kanban → planejada)
- [x] Executado por + Data execução (= iniciado_por + data_inicio)
- [x] Concluído por + Data conclusão
- [x] Executantes múltiplos (campo equipe com nomes enriquecidos)

**Campos de rastreabilidade na Inspeção:**
- [x] Criado por + Data criação
- [x] Iniciado por + Data início
- [x] Concluído por + Data conclusão
- [x] Executantes múltiplos (novo campo com nomes enriquecidos)

**Frontend:**
- [x] OS detail: seção Rastreabilidade com 8 campos + Executantes
- [x] Inspeção detail: seção Rastreabilidade com 6 campos + Executantes
- [x] Form de inspeção: seletor de executantes

**Testes:** iteration_30 — Backend 9/9, Frontend 15/15

### Bloco 3: Materiais Utilizados + Movimentação de Estoque (PRÓXIMO)
- [ ] Coleção os_materiais (código, descrição, quantidade, unidade, local_estoque)
- [ ] Adicionar/remover materiais durante execução da OS
- [ ] Ao concluir OS: dedução automática do estoque
- [ ] Tabela de movimentação de estoque
- [ ] Registrar: material, quantidade, usuário, data/hora, OS vinculada

### Bloco 4: Auditoria Detalhada
- [ ] Registrar alterações campo-a-campo (ex: "Prioridade: Média → Alta")

### Bloco 5: Histórico do Equipamento com Filtros
### Bloco 6: Detalhamento Completo da OS
### Bloco 7: Detalhamento Completo da Inspeção

## Regra de Ouro
> Parar após cada bloco. Entregar evidências. Aguardar aprovação.
