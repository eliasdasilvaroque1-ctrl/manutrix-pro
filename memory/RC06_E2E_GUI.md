# RC-06 — RELATÓRIO E2E VIA INTERFACE GRÁFICA (Playwright)
**Data:** 06/07/2026

---

## RESULTADO POR PERFIL

### MASTER (master@maintrix.com)
**PASS** ✅ | Cliques: 8 | Tempo médio por tela: <1s
- Login via empresa autocomplete ✅
- Dashboard KPIs (Disponibilidade 99.7%, Backlog 30, OS Abertas 24) ✅
- Ativos (55 cards) ✅
- OS Kanban (Solicitadas 6, Em Análise 3, Aguardando Aprov. 1) ✅
- Usuários (24 listados) ✅
- Configurações ✅
- Auditoria (1166 registros) ✅
- White Label Designer ✅
- Logout (Sair) ✅

### GERENTE (test.gerente@maintrix.com)
**PASS** ✅ | Cliques: 9 | Sidebar: 5 itens (correto)
- Sidebar CORRETO: Central, Dashboard, OS, Ativos, Auditoria ✅
- "Solicitar Serviço" AUSENTE (correto) ✅
- /admin/config → "Acesso Restrito" ✅
- /master/white-label → "Acesso Restrito" ✅
- Dashboard, OS list, Prontuário do ativo ✅

### SUPERVISOR MECÂNICO (test.sup.mec@maintrix.com)
**PASS** ✅ | Cliques: 10
- Sidebar: Central, Dashboard, Equipe, Ativos, OS, Inspeções, Áreas, Estoque, Sobressalentes, Paradas, Auditoria ✅
- Modal "Nova OS": campos Ativo, Título, Tipo, Disciplina, Prioridade, Descrição ✅
- /admin/usuarios → "Acesso Restrito" ✅
- Dashboard, Equipe, Inspeções ✅

### PCM (test.pcm@maintrix.com)
**PASS** ✅ | Cliques: 9
- Sidebar completo com Biblioteca e Planos de Inspeção ✅
- Estoque: botão "Novo Item" visível ✅
- OS: botão "Nova OS" visível ✅
- Templates/Planos acessíveis ✅
- Exportação Excel disponível ✅

### TÉCNICO MECÂNICO (test.mec@maintrix.com)
**PASS** ✅ | Cliques: 8
- Sidebar: Minha Jornada, Ativos, Inspeções, Solicitar Serviço, Scanner, Ronda, Estoque ✅
- Minha Jornada: atividades visíveis, role=tec_mecanico ✅
- Solicitar Serviço: wizard 2 passos completo → OS #2026-00062 criada ✅
- Role label: "Técnico Mecânico" (não `tec_mecanico`) ✅
- /admin/config → "Acesso Restrito" ✅

### TÉCNICO ELÉTRICO (test.ele@maintrix.com)
**PASS** ✅ | Cliques: 6
- Sidebar idêntico ao Tec Mecânico ✅
- Role label: "Técnico Elétrico" ✅
- Solicitar Serviço: wizard abre ✅
- /admin/usuarios → "Acesso Restrito" ✅

### LUBRIFICADOR (test.lub@maintrix.com — criado/deletado)
**PASS** ✅ | Cliques: 5
- Sidebar padrão operacional ✅
- Role label: "Lubrificador" ✅
- Solicitar Serviço: wizard abre ✅
- /admin/config → "Acesso Restrito" ✅

### OPERADOR (test.operador@maintrix.com)
**PASS** ✅ | Cliques: 8
- Sidebar: Minha Jornada, Ativos, Inspeções, Solicitar Serviço, Scanner, Ronda, Estoque ✅
- Solicitar Serviço: wizard completo → OS #2026-00063 criada ✅
- Role label: "Operador" ✅
- /admin/config → "Acesso Restrito" ✅
- /master/cleanup → "Acesso Restrito" ✅

### VISUALIZADOR (rc06v2@maintrix.com — criado/deletado)
**PASS** ✅ (após fix) | Cliques: 5
- Sidebar CORRETO: apenas CONSULTA (Dashboard, Ativos, Ordens de Serviço, Inspeções) ✅
- Role label: "Visualizador" ✅
- "Nova OS" OCULTO na página de OS ✅ (FIX APLICADO)
- "Nova Inspeção" OCULTO na página de Inspeções ✅ (FIX APLICADO)
- /solicitar → "Acesso Restrito" ✅ (FIX APLICADO)
- /admin/config → "Acesso Restrito" ✅

---

## BUGS CORRIGIDOS DURANTE RC-06

| # | Severidade | Bug | Perfil | Arquivo | Correção |
|---|-----------|-----|--------|---------|----------|
| 1 | 🔴 HIGH | "Nova OS" visível para Visualizador | VIEWER | `App.js:3705` | Condição `user?.role !== 'visualizador' && !== 'gerente'` |
| 2 | 🔴 HIGH | "Nova Inspeção" visível para Visualizador | VIEWER | `App.js:4880` | Mesma condição |
| 3 | 🔴 HIGH | /solicitar acessível para Visualizador | VIEWER | `App.js:9980` | `allow` prop adicionado ao ProtectedRoute |
| 4 | 🟡 MED | `force_password_change` não editável via admin | ADMIN | `server.py:311` | Campo adicionado a `allowed_fields` |

---

## OBSERVAÇÕES UX (NÃO CORRIGIDOS — Não Impedem Fluxo)

| # | Prioridade | Observação | Perfil |
|---|-----------|-----------|--------|
| 1 | 🟡 | OS card e Ativo card abrem overlay/drawer sem atualizar URL → browser Back não funciona | Todos |
| 2 | 🟡 | Ícones de export (Excel/PDF) são icon-only sem tooltip/label | Todos |
| 3 | 🟢 | Casing inconsistente: "NOVO ATIVO" (maiúsculo) vs "Nova Parada" (título) | Todos |
| 4 | 🟢 | Autocomplete Empresa pode parecer vazio no primeiro keystroke enquanto API carrega | Login |
| 5 | 🟢 | Header "PCM" no sidebar aparece para Supervisor (pode confundir) | Supervisor |
| 6 | 🟢 | Estoque visível para roles operacionais (pode ser intencional) | Operacionais |

---

## TEMPOS DE CARREGAMENTO

| Tela | Tempo | Status |
|------|-------|--------|
| Login → Dashboard | <2s | ✅ |
| Dashboard KPIs | <1s | ✅ |
| Ativos (55 itens) | <1s | ✅ |
| OS Kanban | <1s | ✅ |
| Auditoria (1166 registros) | ~1.5s | ✅ |
| White Label Designer | <1s | ✅ |
| Minha Jornada (Central) | <1s | ✅ |

**Nenhuma tela demora >3s.** Performance satisfatória.

---

## RESULTADO FINAL

| Métrica | Valor |
|---------|-------|
| Perfis testados | 9 (Master, Gerente, Supervisor, PCM, Tec Mec, Tec Ele, Lubrificador, Operador, Visualizador) |
| Fluxos E2E | 76 steps |
| Taxa de sucesso | 100% (após fixes) |
| Bugs bloqueantes | 0 |
| Bugs corrigidos | 4 (3 HIGH + 1 MEDIUM) |
| Observações UX | 6 (nenhuma bloqueante) |
