# MANUTRIX OMNI — Product Requirements Document

## Bloco A: Sobressalentes Avançado ✅
## Bloco B: Simplificação de Inspeções ✅ (2026-06-19)

### Nova Arquitetura — Planos de Inspeção

**Nível 1: Plano por Tipo de Equipamento**
- Coleção `planos_inspecao` com `tipo_equipamento` + `categoria` (mecanica/eletrica/lubrificacao)
- Ex: "ALIMENTADOR VIBRATORIO" + "mecanica" → 3 perguntas padrão

**Nível 2: Perguntas específicas por Ativo**
- Coleção `planos_inspecao` com `ativo_id` + `categoria`
- Ex: AV-01 + "mecanica" → 2 perguntas exclusivas

**Resolver**: GET /api/planos-inspecao/resolver?ativo_id=X&categoria=Y
- Merge Nível 1 + Nível 2 automaticamente
- Fallback para DEFAULT_CHECKLISTS se nenhum plano existir

**Atributos por pergunta:**
- [x] tipo (boolean, numerico, texto, lista, foto, observacao)
- [x] obrigatorio
- [x] periodicidade
- [x] foto_obrigatoria_nc
- [x] limites: limite_normal, limite_alerta, limite_critico
- [x] opcoes (para tipo lista)
- [x] ordem

**Fluxo do Técnico (simplificado):**
Equipamento → Nova Inspeção → Mecânica/Elétrica/Lubrificação → Perguntas carregadas automaticamente

**Remoções:**
- [x] Referências a "Template" removidas da UI do técnico
- [x] Sidebar: "Templates" → "Planos de Inspeção"
- [x] Página admin atualizada para usar nova API

**Migração:**
- [x] DEFAULT_CHECKLISTS migrados para planos_inspecao (3 planos universais)
- [x] Histórico preservado

**Endpoints:**
- CRUD: /api/planos-inspecao
- Resolver: /api/planos-inspecao/resolver
- Migração: /api/planos-inspecao/migrar
- Categorias: /api/planos-inspecao/categorias-disponiveis

**Testes:** iterations 37-38 — Backend 15/15, Frontend fix confirmed

## Regra de Ouro
> Parar após cada bloco. Entregar evidências. Aguardar aprovação.
