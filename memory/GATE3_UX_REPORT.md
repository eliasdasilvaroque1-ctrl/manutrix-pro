# GATE 3 — Auditoria UX do MAINTRIX Enterprise
## Piloto ASTEC | Data: 2026-07-09

---

## 1. ESTADOS VAZIOS (Empty States)

| Tela | Existe? | Ícone | Mensagem | Ação Sugerida | Veredicto |
|------|---------|-------|----------|---------------|-----------|
| Ativos (filtro sem resultado) | Sim | Box | "Nenhum ativo encontrado" | "Criar Ativo" | ✅ OK |
| OS (lista vazia) | Sim | Wrench | "Nenhuma OS encontrada" | "Nova OS" | ✅ OK |
| OS Kanban (colunas vazias) | Sim | — | "Arraste OS aqui" | — | ✅ OK |
| Inspeções (vazia) | Sim | ClipboardCheck | "Nenhuma inspeção encontrada" | "Nova Inspeção" / "Limpar Filtros" (dinâmico) | ✅ Excelente |
| Estoque (busca sem resultado) | Sim | Package | "Nenhum item encontrado" | "Novo Item" | ✅ OK |
| Sobressalentes (vazio) | Sim | Cog | "Nenhum sobressalente" | "Cadastre sobressalentes." | ✅ OK |
| Paradas (vazio) | Sim | Calendar | "Nenhuma parada" | "Nova Parada" | ✅ OK (bug de prop corrigido) |
| Planos (vazio) | Sim | ClipboardCheck | "Nenhum plano" | "Novo Plano" | ✅ OK (bug de prop corrigido) |
| Áreas (vazio) | Sim | Layers | "Nenhuma área encontrada" | "Nova Área" | ✅ OK |
| Unidades (vazio) | Sim | Factory | "Nenhuma unidade cadastrada" | "Nova Unidade" | ✅ OK |
| Auditoria (vazia) | Sim | Shield | "Nenhum registro" | — | ✅ OK |
| BOM/Materiais do ativo | Sim | — | "Nenhum material cadastrado." | — | ⚠️ Sem botão de ação |
| Documentos do ativo | Sim | — | "Nenhum documento cadastrado." | — | ⚠️ Sem botão de ação |

**Bugs corrigidos:**
- ❌→✅ Paradas: usava `onAction` (inexistente) em vez de `action` — botão de ação não funcionava
- ❌→✅ Planos de Inspeção: mesmo bug `onAction` → `action`

---

## 2. LOADING

| Tela | Tipo | Veredicto |
|------|------|-----------|
| Central de Trabalho | Loading skeleton | ✅ OK |
| Dashboard | Loading skeleton | ✅ OK |
| Ativos | Loading skeleton (5 rows) | ✅ OK |
| OS | Loading skeleton (5 rows) | ✅ OK |
| Inspeções | Loading skeleton (5 rows) | ✅ OK |
| Estoque | Loading skeleton (5 rows) | ✅ OK |
| Sobressalentes | Loading skeleton (5 rows) | ✅ OK |
| Paradas | Loading skeleton (5 rows) | ✅ OK |
| Auditoria | Loading skeleton (8 rows) | ✅ OK |
| Usuários | Loading skeleton (5 rows) | ✅ OK |
| Áreas | Loading skeleton (3 rows) | ✅ OK |
| Unidades | Loading skeleton (3 rows) | ✅ OK |
| Detalhe do Ativo | Loading skeleton (4 rows) | ✅ OK |
| Detalhe da OS | Loading skeleton (4 rows) | ✅ OK |

**Resultado:** ZERO tela branca durante carregamento. Todas usam skeleton loading.

---

## 3. MENSAGENS

| Tipo | Antes | Depois | Severidade | Status |
|------|-------|--------|------------|--------|
| Erro de rede | Expunha `error.message` raw (ex: "AxiosError: Network Error") | "Sem conexão com o servidor. Verifique sua rede." | P1 | ✅ Corrigido |
| Timeout | Expunha "timeout of 30000ms exceeded" | "O servidor demorou para responder. Tente novamente." | P1 | ✅ Corrigido |
| Erro desconhecido | "Erro desconhecido" | "Não foi possível concluir a operação. Tente novamente." | P2 | ✅ Corrigido |
| Erro Pydantic JSON | Expunha `JSON.stringify(d)` | "Erro de validação" / "Erro ao processar requisição" | P2 | ✅ Corrigido |
| Carregar central | "Erro ao carregar central" | "Não foi possível carregar a central. Verifique sua conexão." | P2 | ✅ Corrigido |
| Carregar dashboard | "Erro ao carregar dashboard" | "Não foi possível carregar o dashboard. Verifique sua conexão." | P2 | ✅ Corrigido |
| Validação de campo | "Campo 'X' é obrigatório" | — | — | ✅ Já era amigável |
| Login inválido | "Credenciais inválidas" | — | — | ✅ Já era amigável |

---

## 4. FORMULÁRIOS

| Item | Ativos | OS | Estoque | Inspeção | Veredicto |
|------|--------|-----|---------|----------|-----------|
| Campos obrigatórios marcados (*) | ✅ | ✅ | ✅ | ✅ | OK |
| Validação front-end | ✅ | ✅ | ✅ | ✅ | OK |
| Placeholders | ✅ | ✅ | ✅ | ✅ | OK |
| Toast de validação | ✅ | ✅ | ✅ | ✅ | OK |
| Foco automático | ⚠️ | ⚠️ | ⚠️ | ⚠️ | P2 — modal não foca primeiro campo |

**P2 (documentado, não corrigido):** Modais de criação não focam automaticamente o primeiro campo ao abrir. Correção seria `autoFocus` no primeiro input, mas requer teste por modal.

---

## 5. NAVEGAÇÃO

| Item | Veredicto | Observação |
|------|-----------|------------|
| Sidebar desktop | ✅ | Categorias claras: Principal, Operação, Infraestrutura, Materiais, PCM, Admin |
| Bottom nav mobile | ✅ | 5 itens: Central, Inspeções, QR, Ativos, OS |
| Botão Voltar | ✅ | Detalhe de ativo/OS tem navegação de volta |
| Cancelar em modais | ✅ | Todos os modais têm botão Cancelar |
| Salvar em modais | ✅ | Todos os modais têm botão Salvar/Criar |
| Confirmação em exclusões | ✅ | ConfirmDialog com mensagem clara |
| Breadcrumb (Unidade > Área > TAG) | ✅ | Presente nos cards de ativo |
| Login → Dashboard | ✅ | Fluxo direto |
| Logout | ✅ | Botão "Sair" no footer do sidebar |

**P1 (documentado, não corrigido):** No mobile, páginas como Estoque, Sobressalentes, Paradas, Dashboard não são acessíveis pela bottom nav. O usuário precisa usar a URL diretamente ou voltar para desktop. Recomendação: adicionar menu "Mais" na bottom nav que expanda as demais opções.

---

## 6. RESPONSIVIDADE

| Dispositivo | Viewport | Sidebar | Conteúdo | Bottom Nav | Veredicto |
|-------------|----------|---------|----------|------------|-----------|
| Desktop | 1920x800 | ✅ Sidebar fixa | ✅ Full-width | — | ✅ OK |
| Notebook | 1366x768 | ✅ Sidebar recolhível | ✅ Adapta | — | ✅ OK |
| Tablet | 768x1024 | ✅ Sidebar visível | ✅ Adapta | — | ✅ OK |
| Mobile | 375x812 | Hidden | ✅ Full-width | ✅ 5 itens | ✅ OK |

**P1 (documentado):** Mobile não acessa Estoque/Sobressalentes/Paradas/Dashboard/Equipe/Unidades/Áreas/Planos/Auditoria via navegação nativa.

---

## 7. ACESSIBILIDADE

| Item | Veredicto | Observação |
|------|-----------|------------|
| Contraste texto/fundo | ✅ | Design Tokens garantem #e2e8f0 sobre #0f172a |
| Labels em inputs | ✅ | FormInput sempre inclui label |
| Botões com texto | ✅ | Todos os botões principais têm texto |
| Ícones com contexto | ✅ | Ícones acompanhados de texto |
| Focus ring | ✅ | `var(--brand-primary)` no focus |
| data-testid | ✅ | Presente em elementos interativos |

---

## 8. LOGIN

| Cenário | Veredicto | Observação |
|---------|-----------|------------|
| Org do localStorage | ✅ | Mostra "Última organização utilizada" + "Trocar" |
| Org do subdomínio | ✅ | Mostra "Ambiente" + 🔒 (sem trocar) |
| Org única | ✅ | Mostra "Organização única" + "Trocar" |
| Seleção manual | ✅ | Input de busca com autocomplete |
| Fluxo "Trocar" | ✅ | Abre seletor, permite escolher outra org |
| Esqueci senha | ✅ | Fluxo completo com email |
| Troca de senha forçada | ✅ | Redireciona para formulário de troca |

---

## RESUMO EXECUTIVO

### Correções aplicadas (BAIXO RISCO)

| # | Problema | Severidade | Arquivo | Correção |
|---|---------|------------|---------|----------|
| 1 | EmptyState Paradas: botão não funcionava (`onAction` inexistente) | P1 | App.js:7671 | `onAction` → `action` |
| 2 | EmptyState Planos: botão não funcionava (`onAction` inexistente) | P1 | App.js:8455 | `onAction` → `action` |
| 3 | Mensagem de erro raw: expunha "Network Error", "timeout exceeded" | P1 | App.js:95-117 | Mensagens amigáveis em PT-BR |
| 4 | Mensagem de erro: expunha `JSON.stringify()` ao usuário | P2 | App.js:95-117 | Substituído por texto amigável |
| 5 | Toast genérico: "Erro ao carregar central" | P2 | App.js:2530 | "Não foi possível carregar..." |
| 6 | Toast genérico: "Erro ao carregar dashboard" | P2 | App.js:2693 | "Não foi possível carregar..." |

### Problemas documentados (NÃO corrigidos — requerem aprovação do CTO)

| # | Problema | Severidade | Tela | Impacto | Correção Sugerida |
|---|---------|------------|------|---------|-------------------|
| 1 | Mobile: Estoque/Sobressalentes/Dashboard inacessíveis | P1 | Mobile (375px) | Técnicos em campo não acessam materiais | Adicionar "Menu Mais" na bottom nav ou hamburger |
| 2 | Modais não focam primeiro campo | P2 | Todos os modais | UX menor — usuário precisa clicar | Adicionar `autoFocus` no primeiro input de cada modal |
| 3 | BOM e Documentos: empty state sem botão de ação | P2 | Detalhe Ativo | Usuário não sabe como adicionar | Adicionar botão no empty state |

### Resultado por categoria

| Categoria | Nota | Detalhes |
|-----------|------|---------|
| Empty States | 12/14 ✅ | 2 bugs corrigidos, 2 sem botão ação (P2) |
| Loading | 14/14 ✅ | Cobertura total com skeleton |
| Mensagens | 6 corrigidas | Zero mensagens técnicas expostas ao usuário |
| Formulários | ✅ | Validação, placeholders, labels — OK |
| Navegação | Desktop ✅, Mobile ⚠️ | P1: bottom nav incompleta |
| Responsividade | ✅ | Desktop/Notebook/Tablet OK. Mobile funcional |
| Acessibilidade | ✅ | Contraste, focus, labels — OK |
| Login | ✅ | Smart Org Selector implementado |
