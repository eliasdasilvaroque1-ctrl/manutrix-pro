# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 5.2.0

---

## ADITIVO ARQUITETURAL Nº 001 ✅ (iteration_48 — 22/22)

### 1. Biblioteca de Modelos ✅
- `categorias_equipamento` — CRUD com auto-código CAT-000001
- `fabricantes` — CRUD com auto-código FAB-000001, vinculado a categoria
- `modelos_mestre` — CRUD com auto-código MM-000001, contém planos mestres com perguntas
- Página frontend com 3 abas (Categorias, Fabricantes, Modelos Mestres) + busca + paginação

### 2. Classificação Técnica dos Ativos ✅
- Novos campos: categoria_id, fabricante_id, modelo_id, familia, classe_equipamento, criticidade
- Formulário de Ativos atualizado com dropdowns dos catálogos corporativos

### 3. Deep Copy (Modelo → Ativo) ✅
- POST /api/biblioteca/modelos-mestre/{id}/aplicar/{ativo_id}
- Cria planos independentes com IDs novos para perguntas
- Rastreabilidade: modelo_origem_id, modelo_versao, plano_origem_id, motivo_criacao

### 4. Códigos Automáticos ✅
- CAT-000001, FAB-000001, MM-000001, PLA-000001
- Contadores atômicos via collection `contadores`

### 5. Preparação para Subconjuntos ✅
- Campos parent_ativo_id e nivel preparados no modelo (nullable)

---

## HISTÓRICO COMPLETO
- Bloco A: Admin Master, Kanban Visual, Filtros, Unidades, Auditoria ✅
- Arquitetura de Dados: Event-sourced, HH, Executantes, Métricas ✅
- Enterprise: org_config, Terminologia, Numeração, White-label ✅
- Bloco B: Cronômetro, Executantes, Equipe, Ranking ✅
- Planos Enterprise: Auto-load por ativo ✅
- Rebranding: MANUTRIX → MAINTRIX ✅
- Aditivo 001: Biblioteca, Classificação, Deep Copy ✅

## PRÓXIMO: BLOCO C
- Dashboard Supervisor
- Qualidade dos Serviços
- Exportação Excel/PDF/CSV
