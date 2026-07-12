# MODULARIZAÇÃO — MAINTRIX Frontend
**Data:** 2026-07-12 | **Fase:** Início (RC2-prep)

---

## RESUMO

Primeira fase da modularização do `App.js` (11.040 → 10.855 linhas, -185 linhas). Extraídos **14 componentes UI puros** para `/components/shared/index.js` (190 linhas). Zero alteração de comportamento, layout ou rotas.

## COMPONENTES EXTRAÍDOS

| Componente | Linhas | Tipo | Uso |
|---|---|---|---|
| StatusBadge | 35 | memo | Badges de status em OS, Inspeções, Ativos |
| PriorityBadge | 8 | memo | Badges de prioridade em OS |
| Modal | 21 | pure | Modal genérico (15+ usos) |
| ConfirmDialog | 14 | pure | Diálogo de confirmação (8+ usos) |
| Loading | 10 | memo | Skeleton loader (20+ usos) |
| EmptyState | 11 | memo | Estado vazio (10+ usos) |
| DataTable | 16 | memo | Tabelas (estoque, sobressalentes, auditoria) |
| DataRow | 5 | memo | Linhas de tabela |
| PageContainer | 2 | pure | Wrapper de página |
| PageHeader | 9 | pure | Cabeçalho de página |
| PageToolbar | 2 | pure | Barra de ferramentas |
| FormInput | 7 | pure | Campo de formulário com label/erro |
| Select | 8 | pure | Select dropdown |
| SearchInput | 5 | pure | Campo de busca com ícone |

## ESTRUTURA CRIADA

```
frontend/src/
├── components/
│   ├── shared/
│   │   └── index.js          (190 linhas — 14 componentes)
│   └── ui/                   (shadcn — já existia)
├── App.js                    (10.855 linhas — reduzido de 11.040)
└── lib/
    ├── api.js
    ├── branding.js
    └── offlineQueue.js
```

## PRÓXIMAS FASES (RC2)

### Fase 2 — Modals e Forms (estimativa: -500 linhas)
- Extrair: ModalNovaOS, ModalNovoAtivo, ModalNovoEstoque, ModalNovaInspecao
- Para: `/components/modals/`

### Fase 3 — Widgets (estimativa: -400 linhas)
- Extrair: KanbanBoard, TrendChart, OSDistChart, MaterialThumbnail, PhotoUploader
- Para: `/components/widgets/`

### Fase 4 — Pages (estimativa: -6000 linhas)
- Extrair cada page component para arquivo próprio
- Para: `/pages/Dashboard.js`, `/pages/OS.js`, `/pages/Ativos.js`, etc.
- Requer: shared context para user, branding, navigation

### Meta Final
- App.js: ~500 linhas (router + providers + layout)
- Pages: 31 arquivos separados
- Components: ~40 arquivos organizados por categoria

---
*Modularização iniciada sem alterar comportamento, layout ou rotas*
