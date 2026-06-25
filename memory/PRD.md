# MANUTRIX OMNI — Product Requirements Document

## Status: FASE 1 PILOTO ASTEC — BLOCO A COMPLETO
## Versão: 4.0.0

---

## BLOCO A — Infraestrutura + Operacional ✅ (25/06/2026, iteration_43)

### #1 Admin Master ✅
- Novo role `master` acima de `admin`
- Hierarquia: MASTER > ADMIN > GERENTE > PCM > SUPERVISOR > TÉCNICO > INSPETOR > VIEWER
- Master tem acesso total ao sistema
- Funções exclusivas do Master: cleanup, prepare-production, admin-actions

### #2 Limpeza do Ambiente ✅
- Painel exclusivo Master em /master/cleanup
- Limpeza seletiva (12 collections) e total ("Preparar para Produção")
- Confirmação dupla com digitação "PREPARAR PRODUCAO"
- Preserva: usuários, áreas, ativos, materiais, planos, configurações
- Todas as ações registradas em `admin_actions` collection

### #3 Kanban Visual ✅
- Cards redesenhados com: Planta (topo), Área, TAG + Nome do equipamento, OS # + Tipo (badge colorido), Título, Prioridade + Disciplina, Responsável, Data prevista, Badge ATRASADA
- 11 tipos de OS com cores distintas

### #4 Filtros Avançados ✅
- Busca por nº, título ou TAG
- Filtros por prioridade (botões rápidos)
- Painel expandível: Tipo de OS, Área, Responsável, Disciplina
- Botão "Limpar filtros"
- Contador de filtros ativos

### #5 Plantas (Hierarquia) ✅
- Nova entidade: Planta (Empresa > Planta > Área > Ativo)
- CRUD completo com auditoria
- Collection: `plantas_v2`
- Página frontend: /plantas

### #13 Auditoria de Exclusão Admin ✅
- Collection `admin_actions` imutável pelo cleanup
- Registra: quem, quando, o que, quantidade, resultado
- Acessível apenas pelo Master

### Novos Tipos de OS ✅
- corretiva, preventiva, lubrificação, inspeção, fabricação
- preparação material, melhoria, calibração, instalação, reforma, emergencial

---

## PRÓXIMOS BLOCOS

### BLOCO B — Gestão de Equipe + HH (A FAZER)
- #7 HH Automático (cronômetro + manual)
- #8 OS Compartilhadas (crédito individual)
- #5 Dashboard da Equipe (performance por técnico)
- #9 Produtividade (indicadores automáticos)

### BLOCO C — Dashboards Executivos + Export (A FAZER)
- #6 Ranking da Equipe
- #10 Dashboard Supervisor
- #11 Qualidade dos Serviços
- #12 Exportação Excel/PDF/CSV
- #14 Finalização

---

## Módulos Completos
Áreas, Ativos, OS, Inspeções, Anomalias, Estoque, Sobressalentes,
Paradas Programadas, Auditoria, Multiempresa, PWA/Offline,
Dashboard, Exportação, Object Storage, Plantas, Master Admin, Limpeza de Ambiente
