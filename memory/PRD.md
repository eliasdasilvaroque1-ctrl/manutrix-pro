# MANUTRIX ENTERPRISE — Product Requirements Document

## Versão: 5.1.0

---

## REFATORAÇÃO PLANOS DE INSPEÇÃO ✅ (iteration_47 + fix)

### Arquitetura Nova
- Planos são SEMPRE vinculados a um ATIVO específico (não mais genéricos por disciplina)
- Tipos de plano: inspecao, preventiva, lubrificacao, limpeza, melhoria
- Perguntas com tipos ricos: boolean, numero, texto, lista, escala_4, faixa, foto, comentario
- Cada pergunta: texto, tipo_campo, obrigatoria, foto_obrigatoria, comentario_obrigatorio, unidade, valor_min, valor_max, opcoes, ordem

### Auto-Load de Planos
- Ao criar inspeção sem checklist: backend busca plano do ativo por tipo
- plano_id e plano_nome são registrados no documento da inspeção
- Fallback: equipment-type plan → minimal default (2 itens)
- Checklists genéricos hardcoded REMOVIDOS

### Bug Crítico Corrigido
- Duas chaves $or no dict Python → query ignorava filtro de tipo
- Corrigido com $and encapsulando os dois $or

### Endpoints
- GET /api/planos-inspecao/por-ativo/{ativo_id} — Planos por ativo
- GET /api/planos-inspecao/resolver?ativo_id=&tipo= — Resolve plano
- GET /api/planos-inspecao/categorias-disponiveis?ativo_id= — Tipos disponíveis

---

## MÓDULOS COMPLETOS
Bloco A (Admin Master, Kanban, Filtros, Unidades) ✅
Arquitetura de Dados (Event-sourced, HH, Executantes, Métricas) ✅
Consolidação Enterprise (org_config, Terminologia, Numeração, White-label) ✅
Bloco B (Cronômetro, Executantes, Equipe, Ranking) ✅
Planos de Inspeção Enterprise ✅

## PRÓXIMO: BLOCO C
- Dashboard Supervisor
- Qualidade dos Serviços
- Exportação Excel/PDF/CSV
- Finalização
