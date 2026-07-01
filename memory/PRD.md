# MAINTRIX ENTERPRISE — Product Requirements Document

## Versão: 5.3.1

---

## ADITIVO ARQUITETURAL Nº 002 ✅ (iteration_50 — 12/12 backend + 5/5 frontend)

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
| Supervisor | Todas disciplinas da empresa (mesmo acesso que PCM) |
| Gerente | Todos (somente leitura) |
| Técnico | Apenas disciplinas + áreas permitidas + atividades atribuídas |
| Inspetor | Mesmo que Técnico para inspeções |
| Operador | Apenas producao/civil. NUNCA vê mecanica/eletrica/instrumentacao |

### 3. Campos Denormalizados ✅
- OS: `disciplina` (obrigatório), `sector_id` (denormalizado do ativo)
- Inspeções: `disciplina` (derivado do tipo/plano), `sector_id` (denormalizado do ativo)
- Endpoint de migração: `POST /api/migrate/denormalize-sector`

### 4. Dashboard Scoped ✅
- Todos os endpoints usam `build_dashboard_visibility`

### 5. Bug Fix: Plano de Inspeção "Field required" ✅
- `ativo_id` agora é `Optional[str] = None` em `PlanoInspecaoCreate`
- `normalizeError` no frontend mostra nome do campo em português (ex: "Campo 'Nome' é obrigatório")
- Formulário atualizado com campos: Tipo do Plano, Disciplina, Vincular a Ativo
- Mapeamento `perguntas` ↔ `itens` corrigido no frontend
- PUT endpoint atualiza todos os campos (não apenas nome/perguntas)
- Testado com 10, 50 e 100 itens de checklist

### 6. Usuários de Teste ✅
- `POST /api/seed/test-users` cria 7 perfis com disciplinas e áreas

---

## ADITIVO ARQUITETURAL Nº 001 ✅ (iteration_48 — 22/22)
- Biblioteca de Modelos (Categorias, Fabricantes, Modelos Mestres)
- Classificação Técnica dos Ativos
- Deep Copy (Modelo → Ativo)
- Códigos Automáticos
- Preparação para Subconjuntos

---

## HISTÓRICO COMPLETO
- Bloco A: Admin Master, Kanban Visual, Filtros, Unidades, Auditoria ✅
- Arquitetura de Dados: Event-sourced, HH, Executantes, Métricas ✅
- Enterprise: org_config, Terminologia, Numeração, White-label ✅
- Bloco B: Cronômetro, Executantes, Equipe, Ranking ✅
- Planos Enterprise: Auto-load por ativo ✅
- Rebranding: MANUTRIX → MAINTRIX ✅
- Aditivo 001: Biblioteca, Classificação, Deep Copy ✅
- Aditivo 002: Visibilidade RBAC, Bug Plano Inspeção, Supervisor=PCM ✅

## PRÓXIMO: BLOCO C
- Dashboard Supervisor Executivo
- Indicadores de Qualidade (Retrabalho, OS reabertas, Tempo médio)
- Exportação Excel/PDF/CSV de relatórios de produtividade

## BACKLOG (P2)
- IA Features: Previsão de falhas, produtividade, consumo de peças
- Estrutura de Subconjuntos e Componentes (CRUD/UI)
- Integrações ERP/SAP (suspenso até pós-piloto)
