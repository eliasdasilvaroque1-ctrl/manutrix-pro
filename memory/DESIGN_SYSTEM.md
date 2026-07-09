# MAINTRIX — Design System Enterprise
## Referência Oficial v1.5 | Tema: Industrial Dark

---

## 1. Design Tokens

### Core Brand (definidos pelo White Label de cada organização)

| Token CSS | Origem | Exemplo ASTEC | Descrição |
|-----------|--------|---------------|-----------|
| `--brand-primary` | `cor_primaria` | `#0057B8` | Cor principal da marca |
| `--brand-secondary` | `cor_secundaria` | `#7C3AED` | Cor secundária |
| `--brand-bg` | `cor_fundo` | `#F4F6F8` | Fundo do body/página |
| `--brand-text` | `cor_texto` | `#1F2937` | Texto do body (sobre cor_fundo) |
| `--brand-accent` | `cor_destaque` | `#F59E0B` | Cor de destaque |
| `--brand-menu` | `cor_menu` | `#004A9E` | Cor do sidebar/menu |
| `--brand-login` | `cor_login` | `#020617` | Fundo da tela de login |
| `--brand-header` | `cor_header` | `#101B30` | Cor do header |

### Theme Engine (definidos pelo tema pré-selecionado, NÃO pela organização)

| Token CSS | Industrial Dark | Descrição |
|-----------|----------------|-----------|
| `--brand-surface` | `#0f172a` | Background de cards, modais, painéis |
| `--brand-surface-hover` | `#1e293b` | Hover state de surfaces |
| `--brand-border` | `#1e293b` | Bordas de cards, inputs, divisores |
| `--brand-text-primary` | `#e2e8f0` | Texto principal sobre surfaces |
| `--brand-text-secondary` | `#94a3b8` | Texto secundário, labels, placeholders |

### Semantic (fixos por tema, independem do White Label)

| Token CSS | Valor | Uso |
|-----------|-------|-----|
| `--brand-success` | `#10b981` | Conforme, operacional, positivo |
| `--brand-warning` | `#f59e0b` | Atenção, pendente, alerta |
| `--brand-danger` | `#ef4444` | Erro, crítico, destrutivo |
| `--brand-info` | `#3b82f6` | Informação, link, neutro |

---

## 2. Classes Utilitárias CSS

### Background
| Classe | Token | Uso |
|--------|-------|-----|
| `.bg-surface` | `--brand-surface` | Cards, modais, painéis |
| `.bg-surface-hover` | `--brand-surface-hover` | Hover, skeleton loading |
| `.bg-brand` | `--brand-primary` | Botões primários, destaques |
| `.bg-brand-10` | Primary 10% | Ícones, badges suaves |
| `.bg-brand-20` | Primary 20% | Tab ativo, filtro ativo |

### Texto
| Classe | Token | Uso |
|--------|-------|-----|
| `.text-primary` | `--brand-text-primary` | Títulos, nomes, valores |
| `.text-secondary` | `--brand-text-secondary` | Labels, descrições, subtítulos |
| `.text-brand` | `--brand-primary` | Tags, links, destaques de marca |
| `.text-success` | `--brand-success` | Status positivo |
| `.text-warning` | `--brand-warning` | Status alerta |
| `.text-danger` | `--brand-danger` | Status crítico, erros |
| `.text-info` | `--brand-info` | Informações, links |

### Bordas
| Classe | Token | Uso |
|--------|-------|-----|
| `.border-surface` | `--brand-border` | Bordas de cards, inputs, tabelas |
| `.border-brand` | `--brand-primary` | Borda ativa, selecionada |
| `.border-brand-30` | Primary 30% | Borda suave para tabs/filtros |

---

## 3. Componentes Reutilizáveis

### Estruturais (Prioridade 1)

#### `<PageContainer>`
Container principal de toda página. Aplica espaçamento e animação.
```jsx
<PageContainer>
  {/* conteúdo da página */}
</PageContainer>
```

#### `<PageHeader title="..." subtitle="...">`
Cabeçalho padronizado com título, subtítulo opcional e área de ações.
```jsx
<PageHeader title="Estoque" subtitle="Gestão de materiais">
  <button className="btn-primary">Novo Item</button>
</PageHeader>
```

#### `<PageToolbar>`
Barra horizontal para busca e filtros.
```jsx
<PageToolbar>
  <SearchInput value={search} onChange={...} placeholder="Buscar..." />
  <button>Filtro</button>
</PageToolbar>
```

#### `<SearchInput value onChange placeholder>`
Input de busca com ícone integrado.

#### `<FilterBar>`
Container para filtros inline.

#### `<SectionDivider label="opcional">`
Linha divisória com label opcional centralizado.

### Conteúdo (Prioridade 2)

#### `<CardSection title icon color actions>`
Seção dentro de um glass-card com título, ícone e área de ações.
```jsx
<CardSection title="Identificação" icon={Tag} color="text-brand">
  <FormInput label="Nome">...</FormInput>
</CardSection>
```

#### `<DataTable headers>`
Tabela padronizada com headers tokenizados.
```jsx
<DataTable headers={[
  { label: 'Código' },
  { label: 'Descrição' },
  { label: 'Qtd', align: 'right' },
]}>
  <DataRow>
    <td>ROL-001</td>
    <td>Rolamento 6205</td>
    <td className="text-right">10</td>
  </DataRow>
</DataTable>
```

#### `<DataRow onClick className>`
Linha de tabela com hover e borda tokenizados.

### Base (Fase 1)

| Componente | Tokenizado | Descrição |
|------------|-----------|-----------|
| `<Modal>` | Sim | Painel modal com overlay e animação |
| `<ConfirmDialog>` | Sim | Dialog de confirmação/cancelamento |
| `<FormInput>` | Sim | Label + input com estado de erro |
| `<Loading>` | Sim | Skeleton loading animado |
| `<EmptyState>` | Sim | Estado vazio com ícone e ação |
| `<KPICard>` | Sim | Card de indicador com tendência |

### CSS Components

| Classe | Tokenizado | Descrição |
|--------|-----------|-----------|
| `.glass-card` | Sim | Card principal (surface + border) |
| `.btn-primary` | Sim | Botão principal (primary color) |
| `.btn-secondary` | Sim | Botão secundário (surface + border) |
| `.btn-destructive` | Sim | Botão destrutivo (vermelho) |
| `.input-industrial` | Sim | Input padrão 48px |
| `.card-industrial` | Sim | Card alternativo |
| `.section-title` | Sim | Título de seção (primary color) |

---

## 4. Hierarquia Visual

```
Page Background (--brand-bg)
  └── Sidebar (--brand-menu)
  └── Content Area
        └── PageContainer (spacing + animation)
              └── PageHeader (text-primary + text-secondary)
              └── PageToolbar (SearchInput + FilterBar)
              └── glass-card (--brand-surface + --brand-border)
                    └── CardSection (section-title)
                    └── DataTable (border-surface + text-secondary headers)
                          └── DataRow (hover: surface-hover)
              └── Modal (--brand-surface + text-primary)
                    └── FormInput (text-secondary labels)
                    └── btn-primary / btn-secondary
```

---

## 5. Regras de Uso

### FAZER
- Usar `text-primary` para qualquer texto principal sobre surfaces
- Usar `text-secondary` para labels, descrições, subtítulos
- Usar `text-brand` para tags, SKUs, códigos, links de destaque
- Usar `bg-surface` para backgrounds de painéis e containers
- Usar `border-surface` para bordas de cards e divisores
- Usar `glass-card` como container principal de conteúdo
- Usar `PageHeader` + `PageToolbar` em toda página nova
- Usar `DataTable` + `DataRow` para tabelas de dados

### NÃO FAZER
- NÃO usar `bg-slate-900`, `bg-slate-800` diretamente — usar `bg-surface`, `bg-surface-hover`
- NÃO usar `text-slate-100`, `text-slate-200` — usar `text-primary`
- NÃO usar `text-slate-400`, `text-slate-500` — usar `text-secondary`
- NÃO usar `border-slate-800`, `border-slate-700` — usar `border-surface`
- NÃO hardcodar cores de status — usar `text-success`, `text-warning`, `text-danger`, `text-info`
- NÃO criar novos padrões de header/toolbar — usar `PageHeader`, `PageToolbar`

### Cores de Status (FIXAS por tema, não usar Tailwind direto)
| Contexto | Classe | Exemplo |
|----------|--------|---------|
| Sucesso | `text-success` | Conforme, concluída |
| Alerta | `text-warning` | Pendente, pausada |
| Erro | `text-danger` | Cancelada, não conforme |
| Info | `text-info` | Em análise, aberta |

---

## 6. Theme Engine (preparação para futuro)

### Tema atual: `industrial_dark`
```javascript
{
  surface: '#0f172a',
  surfaceHover: '#1e293b',
  border: '#1e293b',
  textPrimary: '#e2e8f0',
  textSecondary: '#94a3b8',
}
```

### Temas futuros (exemplo de como serão adicionados):
```javascript
industrial_light: {
  surface: '#ffffff',
  surfaceHover: '#f1f5f9',
  border: '#e2e8f0',
  textPrimary: '#111827',
  textSecondary: '#6b7280',
}
```

### Regra de ouro
> O **tema** define as cores de interface (surface, border, text).
> O **White Label** define a identidade da marca (primary, logo, wallpaper).
> Nunca misturar os dois.

---

## 7. Cobertura Atual

| Categoria | Migrado | Pendente (Fase 2+) |
|-----------|---------|---------------------|
| Componentes base | Modal, Dialog, Form, Loading, Empty, KPI | — |
| Estruturais | PageContainer, PageHeader, PageToolbar, SearchInput, FilterBar, CardSection, DataTable, DataRow, SectionDivider | — |
| Page Titles | Todos (replace global text-primary) | — |
| Section Titles | 17 seções migradas (text-secondary) | Restantes inline |
| CSS Components | glass-card, btn-*, input, card, nav | — |
| StatusBadge | — | Fase 2 |
| PriorityBadge | — | Fase 2 |
| Kanban | — | Fase 2 |
| Gráficos Recharts | — | Fase 2 |
| Textos inline (text-slate-*) | ~30% migrado | ~70% pendente |
