# GATE 3.5 — Auditoria de Consistência Visual e Conformidade com Design System
## MAINTRIX Enterprise — Piloto ASTEC | Data: 2026-07-09

---

## 1. Conformidade por Página

### Legenda
- **PC** = PageContainer | **PH** = PageHeader | **PT** = PageToolbar/SearchInput
- **Slate** = ocorrências de classes `text-slate-*`, `bg-slate-*`, `border-slate-*` (hardcoded)
- **Token** = ocorrências de `text-primary`, `text-secondary`, `bg-surface`, `border-surface` (tokenizado)

### Páginas CONFORMES (usam componentes DS)

| Página | PC | PH | PT | glass-card | Slate | Token | Status |
|--------|----|----|-----|-----------|-------|-------|--------|
| **EstoquePage** | ✅ | ✅ | ✅ | ✅ | 21 | 2 | ✅ Conforme |
| **SobressalentesPage** | ✅ | ✅ | ✅ | ✅ | 18 | 0 | ✅ Conforme |

### Páginas PARCIALMENTE CONFORMES (usam glass-card mas não componentes estruturais)

| Página | PC | PH | PT | glass-card | Slate | Token | Dívida Principal |
|--------|----|----|-----|-----------|-------|-------|------------------|
| **CentralTrabalhoPage** | ❌ | ❌ | ❌ | ✅ (5) | 21 | 3 | Falta PageContainer. Título manual. |
| **AtivosPage** | ❌ | ❌ | ❌ | ✅ (9) | 43 | 1 | Busca manual (não SearchInput). Título h1 manual. |
| **OSPage** | ❌ | ❌ | ❌ | ✅ (2) | 17 | 1 | Busca manual. Título h1 manual. |
| **InspecoesPage** | ❌ | ❌ | ❌ | ✅ (1) | 17 | 1 | Título h1 manual. FilterBar manual. |
| **SolicitacaoServicoPage** | ❌ | ❌ | ❌ | ✅ (3) | 22 | 1 | Título manual. |
| **ParadasPage** | ❌ | ❌ | ❌ | ✅ (8) | 32 | 2 | Título manual. Busca manual. |
| **AuditoriaPage** | ❌ | ❌ | ❌ | ✅ (4) | 20 | 2 | Título manual. |
| **AdminUsuariosPage** | ❌ | ❌ | ❌ | ✅ (3) | 17 | 2 | Título manual. |
| **SetoresPage** | ❌ | ❌ | ❌ | ✅ (2) | 13 | 2 | Título manual. |
| **UnidadesPage** | ❌ | ❌ | ❌ | ✅ (2) | 15 | 2 | Título manual. Busca manual. |
| **BibliotecaPage** | ❌ | ❌ | ❌ | ✅ (7) | 31 | 3 | Título manual. Busca manual. |
| **AdminTemplatesPage** | ❌ | ❌ | ❌ | ✅ (3) | 7 | 1 | Título manual. |
| **WhiteLabelDesignerPage** | ❌ | ❌ | ❌ | ✅ (6) | 19 | 1 | Título manual. |
| **PortalTecnicoPage** | ❌ | ❌ | ❌ | ✅ (5) | 21 | 1 | Título manual. |

### Páginas FORA DO PADRÃO (alta densidade de hardcoded)

| Página | PC | PH | PT | glass-card | Slate | Token | Dívida Principal |
|--------|----|----|-----|-----------|-------|-------|------------------|
| **DashboardPage** | ❌ | ❌ | ❌ | ❌ | 38 | 1 | Zero componentes DS. Gráficos com cores inline. |
| **AtivoDetailPage** | ❌ | ❌ | ❌ | ✅ (5) | 46 | 4 | Tabs, seções, tabelas — tudo manual. Maior dívida. |
| **OSDetailPage** | ❌ | ❌ | ❌ | ✅ (2) | 23 | 0 | Zero tokens. Materiais, HH, timeline — tudo hardcoded. |
| **InspecaoDetailPage** | ❌ | ❌ | ❌ | ✅ (5) | 43 | 0 | Zero tokens. Checklist items hardcoded. |
| **ConsultaEquipamentosPage** | ❌ | ❌ | ❌ | ✅ (11) | 39 | 2 | Portal público. Busca manual. |
| **DossiePesquisaPage** | ❌ | ❌ | ❌ | ✅ (10) | 39 | 3 | Dossiê. Muito conteúdo hardcoded. |
| **EquipePage** | ❌ | ❌ | ❌ | ✅ (6) | 37 | 2 | Gestão de equipe. |
| **RondaPage** | ❌ | ❌ | ❌ | ✅ (5) | 19 | 1 | Rondas de inspeção. |

---

## 2. Dívida Técnica Quantificada

### Classes Hardcoded (Slate) — Total: 1.164 ocorrências

| Categoria | Classe | Ocorrências | Token Equivalente |
|-----------|--------|-------------|-------------------|
| Texto principal | `text-slate-100` | 36 | `text-primary` |
| Texto principal | `text-slate-200` | 129 | `text-primary` |
| Texto/labels | `text-slate-300` | 118 | `text-primary` ou `text-secondary` (contexto) |
| Labels/subtítulos | `text-slate-400` | 135 | `text-secondary` |
| Placeholders/muted | `text-slate-500` | 340 | `text-secondary` |
| Desabilitado | `text-slate-600` | 101 | `text-secondary` (opacity) |
| Background hover | `bg-slate-700` | 42 | `bg-surface-hover` |
| Background | `bg-slate-800` | 119 | `bg-surface` ou `bg-surface-hover` |
| Background dark | `bg-slate-900` | 26 | `bg-surface` |
| Border | `border-slate-700` | 60 | `border-surface` |
| Border | `border-slate-800` | 58 | `border-surface` |

### Classes Tokenizadas — Total: 92 ocorrências

| Token | Ocorrências |
|-------|-------------|
| `text-primary` | 32 |
| `text-secondary` | 39 |
| `bg-surface` | 5 |
| `bg-surface-hover` | 8 |
| `border-surface` | 8 |

### Cobertura Atual

**Token: 92 / (92 + 1.164) = 7.3%**

Somando as classes utilitárias do CSS (glass-card, btn-primary, input-industrial etc.) que **já usam tokens** e impactam todas as páginas:

**Cobertura visual estimada: ~35-40%**

O gap entre cobertura de código (7.3%) e cobertura visual (~35%) se explica porque `glass-card` aparece 145x e cada uso é tokenizado via CSS, sem contar nas ocorrências de App.js.

---

## 3. Componentes DS — Adoção

| Componente | Criado | Utilizado em | Adoção |
|------------|--------|-------------|--------|
| `PageContainer` | ✅ | EstoquePage, SobressalentesPage | 2/24 páginas (8%) |
| `PageHeader` | ✅ | EstoquePage, SobressalentesPage | 2/24 (8%) |
| `PageToolbar` | ✅ | EstoquePage, SobressalentesPage | 2/24 (8%) |
| `SearchInput` | ✅ | EstoquePage, SobressalentesPage | 2/24 (8%) |
| `FilterBar` | ✅ | Nenhuma página | 0/24 (0%) |
| `CardSection` | ✅ | Nenhuma página | 0/24 (0%) |
| `DataTable` | ✅ | BOM tab (AtivoDetail) | 1/24 (4%) |
| `DataRow` | ✅ | BOM tab (AtivoDetail) | 1/24 (4%) |
| `SectionDivider` | ✅ | Nenhuma página | 0/24 (0%) |

---

## 4. Recomendação de Migração por Prioridade

### Onda 1 — Máximo impacto, mínimo risco (8 páginas)
Substituir apenas **PageContainer + PageHeader + PageToolbar/SearchInput** nos headers. 
Não tocar no conteúdo interno. ~5 linhas por página.

| Página | Justificativa |
|--------|--------------|
| AtivosPage | Página mais usada da operação |
| OSPage | Página mais usada do PCM |
| InspecoesPage | Terceira mais usada |
| CentralTrabalhoPage | Primeira tela após login |
| ParadasPage | Padrão idêntico às demais |
| AuditoriaPage | Admin — mesmo padrão |
| AdminUsuariosPage | Admin — mesmo padrão |
| SetoresPage | Infraestrutura — mesmo padrão |

**Impacto estimado**: adoção de PageContainer/PageHeader sobe de 8% para 42% (10/24)

### Onda 2 — Páginas secundárias
UnidadesPage, BibliotecaPage, AdminTemplatesPage, EquipePage, SolicitacaoServicoPage, WhiteLabelDesignerPage, PortalTecnicoPage, RondaPage

### Onda 3 — Páginas complexas (alto risco)
DashboardPage, AtivoDetailPage, OSDetailPage, InspecaoDetailPage, ConsultaEquipamentosPage, DossiePesquisaPage

Estas têm layouts muito customizados (gráficos, tabs, timelines, checklists). Migrar tokens **internos** (text-slate → text-primary) sem alterar estrutura.

---

## 5. Veredito

| Métrica | Valor |
|---------|-------|
| Total de páginas | 24 |
| Conformes (DS completo) | 2 (8%) |
| Parcialmente conformes (glass-card sim, DS estrutural não) | 14 (58%) |
| Fora do padrão (alta dívida) | 8 (33%) |
| Componentes DS criados | 9 |
| Componentes DS em uso efetivo | 4 (PageContainer, PageHeader, PageToolbar, SearchInput) |
| Componentes DS nunca utilizados | 3 (FilterBar, CardSection, SectionDivider) |
| Cobertura de tokens no código | 7.3% |
| Cobertura visual estimada | 35-40% |
| Dívida técnica (classes slate) | 1.164 ocorrências |

### Conclusão

O Design System existe como **fundação** (tokens, CSS utilities, componentes) mas foi adotado em apenas **2 das 24 páginas**. A maioria das páginas utiliza `glass-card` (tokenizado via CSS) mas mantém headers, toolbars, buscas e textos com padrões antigos.

A boa notícia: 14 páginas seguem um padrão visual **muito similar** entre si (título h1 + busca + lista/cards). A migração para PageContainer/PageHeader/PageToolbar seria mecânica e de baixíssimo risco (~5 linhas por página).
