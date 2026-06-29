# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 5.3.0

---

## ADITIVO ARQUITETURAL Nº 002 ✅ (iteration_49 — 17/17 PASS)

### 1. Segurança de Visibilidade Backend (RBAC por Disciplina/Área) ✅
- **Motor de Visibilidade**: `build_visibility_query(user, entity_type)` e `build_dashboard_visibility(user)` em `deps.py`
- Toda filtragem de segurança ocorre **exclusivamente no Backend**
- Frontend aplica apenas filtros visuais (pesquisa, ordenação, paginação)

### 2. Regras de Visibilidade por Perfil ✅
| Perfil | Visibilidade |
|--------|-------------|
| MASTER | Todo o sistema |
| Admin | Todos os registros da empresa |
| PCM | Todas as disciplinas da empresa |
| Gerente | Todos (somente leitura) |
| Supervisor | Apenas disciplinas + áreas sob responsabilidade (AND) |
| Técnico | Apenas disciplinas + áreas permitidas + atividades atribuídas |
| Inspetor | Mesmo que Técnico para inspeções |
| Operador | Apenas producao/civil. NUNCA vê mecanica/eletrica/instrumentacao |

### 3. Campos Obrigatórios Denormalizados ✅
- OS: `disciplina` (obrigatório), `sector_id` (denormalizado do ativo)
- Inspeções: `disciplina` (derivado do tipo/plano), `sector_id` (denormalizado do ativo)
- Endpoint de migração: `POST /api/migrate/denormalize-sector`

### 4. Dashboard Scoped ✅
- Todos os endpoints de dashboard usam `build_dashboard_visibility`
- KPIs, stats, trend, os-por-setor, os-por-disciplina, ativos-mais-falhas
- Exportações (Excel/PDF) e Power BI também filtrados

### 5. Usuários de Teste ✅
- `POST /api/seed/test-users` cria 7 perfis com disciplinas e áreas
- Testados: master, admin, pcm, sup.mec, sup.ele, mecânico, eletricista, operador

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
- Aditivo 002: Visibilidade RBAC por Disciplina/Área ✅

## PRÓXIMO: BLOCO C
- Dashboard Supervisor Executivo
- Indicadores de Qualidade (Retrabalho, OS reabertas, Tempo médio)
- Exportação Excel/PDF/CSV de relatórios de produtividade

## BACKLOG (P2)
- IA Features: Previsão de falhas, produtividade, consumo de peças
- Estrutura de Subconjuntos e Componentes (CRUD/UI)
- Integrações ERP/SAP (suspenso até pós-piloto)
