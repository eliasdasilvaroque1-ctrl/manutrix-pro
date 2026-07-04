# AUDITORIA RC-01 — MAINTRIX ENTERPRISE
**Data:** 04/07/2026  
**Escopo:** Auditoria funcional completa — RBAC, segurança, fluxos, UX, exportações, portais  
**Status:** Relatório entregue. Nenhuma correção aplicada.

---

## RESUMO EXECUTIVO

A auditoria identificou **6 bugs CRITICAL (P0)**, **7 bugs HIGH (P1)** e **5 bugs MEDIUM (P2)**, totalizando **18 issues**. O problema central é uma **desconexão entre os roles especializados** (`tec_mecanico`, `tec_eletrico`, `instrumentista`, `lubrificador`) e o sistema RBAC legado que ainda referencia apenas `tecnico`. Isso **bloqueia 100% das ações operacionais** para técnicos especializados — a persona principal do sistema.

---

## P0 — CRITICAL (Bloqueadores de Produção)

### P0-01: Técnicos Especializados Não Conseguem Criar/Iniciar/Concluir OS
- **Impacto:** BLOQUEADOR TOTAL. Nenhum tec_mecanico, tec_eletrico, instrumentista ou lubrificador consegue criar, iniciar, pausar ou concluir uma OS. Recebem HTTP 403.
- **Causa Raiz:** `check_write_permission(user, [..., 'tecnico'])` em 6+ endpoints. Os roles `tec_mecanico` etc. NÃO estão na lista.
- **Arquivos:**
  - `backend/routes/work_orders.py` — linhas 187, 198, 298, 309, 345, 402
- **Proposta:** Substituir `'tecnico'` por constante `ROLE_GROUPS['execucao']` (já definida em deps.py) em todos os `check_write_permission`.

### P0-02: Técnicos Especializados Não Conseguem Iniciar/Concluir Inspeções
- **Impacto:** BLOQUEADOR TOTAL. Mesma causa do P0-01 mas para inspeções.
- **Causa Raiz:** `check_write_permission(user, ['admin', 'supervisor', 'tecnico'])` — faltam roles especializados.
- **Arquivos:**
  - `backend/server.py` — linhas 1487, 1506
- **Proposta:** Adicionar `ROLE_GROUPS['execucao']` ao allowed_roles.

### P0-03: Motor de Visibilidade Não Reconhece Roles Especializados
- **Impacto:** Técnicos especializados veem ZERO itens na Central de Trabalho, Dashboard e listagens de OS/Inspeções. Caem no branch "viewer/unknown" que retorna apenas itens atribuídos diretamente.
- **Causa Raiz:** `build_visibility_query()` e `build_dashboard_visibility()` só checam `role in ('tecnico', 'inspetor')`.
- **Arquivos:**
  - `backend/deps.py` — linhas 337, 413
  - `backend/routes/dashboard.py` — linhas 33, 92, 154, 226
  - `backend/server.py` — linha 3382
- **Proposta:** Alterar para `role in ROLE_GROUPS['execucao']` ou `role in ('tecnico', 'tec_mecanico', 'tec_eletrico', 'instrumentista', 'lubrificador', 'inspetor')`.

### P0-04: Endpoint Diagnóstico Expõe Dados de Todos os Usuários Sem Autenticação
- **Impacto:** SEGURANÇA CRÍTICA. Qualquer pessoa na internet pode acessar `GET /api/diag/auth-audit?key=maintrix-diag-2026` e obter emails, roles, IDs e metadados de hash de senha de TODOS os 27+ usuários do sistema.
- **Causa Raiz:** `os.environ.get('DIAG_KEY', 'maintrix-diag-2026')` — chave padrão hardcoded + endpoint sem JWT.
- **Arquivos:**
  - `backend/server.py` — linhas 3527-3560
- **Proposta:** Remover endpoint completamente ou: (1) exigir env var sem fallback, (2) adicionar `Depends(get_current_user)` + `check_master_only`.

### P0-05: Token de Reset de Senha Vazado na Resposta da API
- **Impacto:** SEGURANÇA CRÍTICA. `POST /api/auth/forgot-password` retorna o token de reset no corpo JSON (`{"token": "snhQM..."}"`). Qualquer atacante pode solicitar reset de qualquer email e obter o token instantaneamente.
- **Causa Raiz:** `return {..., "token": token}` na branch local (non-Supabase).
- **Arquivos:**
  - `backend/server.py` — linha 207
- **Proposta:** Remover campo `token` da resposta. Manter apenas log server-side. Em produção, integrar envio por email.

### P0-06: Criação de Usuário Descarta Campos Críticos de RBAC
- **Impacto:** BLOQUEADOR. Ao criar um novo usuário via Admin, os campos `disciplina_principal`, `disciplinas_secundarias`, `turno`, `area_ids` são SILENCIOSAMENTE ignorados. O backend retorna 200 mas os campos ficam null. Isso torna o motor de visibilidade (P0-03) inoperante mesmo após correção — usuários novos nunca terão escopo.
- **Causa Raiz:** `admin_create_user` constrói `user_doc` manualmente com apenas 7 campos, ignorando o restante do `UserCreate/UserBase`.
- **Arquivos:**
  - `backend/server.py` — linhas 3196-3230
- **Proposta:** Usar `data.dict(exclude={'password'})` ou adicionar todos os campos do model ao `user_doc`.

---

## P1 — HIGH (Falhas Significativas)

### P1-01: Frontend Sem Guarda de Role nas Rotas Protegidas
- **Impacto:** Qualquer usuário autenticado pode acessar `/admin/config`, `/admin/auditoria`, `/master/white-label` via URL direta. A UI renderiza completamente (formulários editáveis, botões de ação). Backend pode bloquear writes, mas a UI exposta gera confusão e risco.
- **Causa Raiz:** `ProtectedRoute` só verifica `if (!user)`, não verifica `user.role`.
- **Arquivos:**
  - `frontend/src/App.js` — linha 7982
- **Proposta:** Adicionar prop `allowedRoles` ao ProtectedRoute. Redirecionar para `/` com toast se role não autorizado. Aplicar em todas as rotas `/admin/*` e `/master/*`.

### P1-02: UX Inconsistente em Páginas Restritas
- **Impacto:** `/admin/usuarios` mostra "Acesso Restrito" (correto), mas `/admin/config` mostra a UI completa com campos editáveis para Operador (incorreto). Inconsistência confusa.
- **Causa Raiz:** Algumas páginas têm guard no componente, outras não.
- **Arquivos:**
  - `frontend/src/App.js` — componentes `OrgConfigPage`, `AuditoriaPage`, `WhiteLabelDesignerPage`
- **Proposta:** Adicionar guard uniforme em TODAS as páginas admin/master.

### P1-03: Master Não Consegue Exportar Auditoria
- **Impacto:** O Master (dono do sistema) recebe 403 ao tentar exportar auditoria em Excel/PDF.
- **Causa Raiz:** Whitelist `['admin', 'gerente', 'pcm']` exclui `master` e `supervisor`.
- **Arquivos:**
  - `backend/server.py` — linhas 3461, 3473
- **Proposta:** Adicionar `'master'` e `'supervisor'` à whitelist.

### P1-04: HH Manual Bloqueado para Técnicos Especializados
- **Impacto:** Técnicos não conseguem registrar horas de trabalho manual.
- **Causa Raiz:** Mesma issue de P0-01 — `'tecnico'` hardcoded sem roles especializados.
- **Arquivos:**
  - `backend/routes/events.py` — linha 184
- **Proposta:** Usar `ROLE_GROUPS['execucao']`.

### P1-05: Listagem de Ativos Sem Filtro de Visibilidade
- **Impacto:** `GET /api/ativos` retorna TODOS os ativos da organização para qualquer role. Operador e Técnico deveriam ver apenas ativos de suas áreas/disciplinas.
- **Arquivos:**
  - `backend/routes/assets.py` — linhas 97-123
- **Proposta:** Aplicar `build_visibility_query(user, "ativo")` ou filtrar por `area_ids` para roles operacionais.

### P1-06: Exportação de Auditoria Sem Filtro de Organização
- **Impacto:** `GET /api/export/audit` retorna logs de TODAS as organizações.
- **Causa Raiz:** Query `await db.audit_logs.find({}, ...)` sem filtro `organization_id`.
- **Arquivos:**
  - `backend/server.py` — linha 3475
- **Proposta:** Adicionar filtro `{"organization_id": user.get('organization_id')}`.

### P1-07: Endpoint GET /api/admin/users/{id} Inexistente
- **Impacto:** Retorna 405 Method Not Allowed. CRUD incompleto — impossível buscar detalhes de um único usuário.
- **Arquivos:**
  - `backend/server.py` — entre linhas 3188-3237
- **Proposta:** Criar endpoint `GET /api/admin/users/{user_id}`.

---

## P2 — MEDIUM (Melhorias e Riscos Menores)

### P2-01: PDF de Auditoria com Branding Hardcoded
- **Impacto:** PDF de exportação de auditoria usa título "MAINTRIX - Auditoria" ao invés do nome da empresa configurada no White Label.
- **Arquivos:**
  - `backend/server.py` — linha 3501
- **Proposta:** Buscar `org_config` e usar `nome_empresa` do White Label.

### P2-02: `is_operacional` no Backend Não Inclui Roles Especializados
- **Impacto:** Em `create_os`, a lógica `is_operacional = role in ('operador', 'inspetor', 'tecnico')` não reconhece técnicos especializados, afetando o status inicial da OS criada.
- **Arquivos:**
  - `backend/routes/work_orders.py` — linha 198
- **Proposta:** Usar `role in ROLE_GROUPS['operacional']`.

### P2-03: Role "Almoxarife" Não Existe no Sistema
- **Impacto:** O usuário mencionou este perfil na auditoria, mas ele não existe em `SYSTEM_ROLES`, `UserRole` enum, ou na `PERMISSIONS` matrix. Se for necessário, precisa ser criado.
- **Arquivos:**
  - `backend/deps.py`, `backend/models.py`
- **Proposta:** Avaliar com o usuário se é necessário criar este role com permissões específicas para estoque/sobressalentes.

### P2-04: Constantes de Roles Repetidas em Múltiplos Endpoints
- **Impacto:** `['admin', 'supervisor', 'tecnico']` aparece 6+ vezes hardcoded em work_orders.py e server.py. Cada novo role exige alteração em N lugares, gerando bugs como P0-01.
- **Arquivos:**
  - Todos os arquivos de routes
- **Proposta:** Extrair constantes `OS_EXECUTE_ROLES`, `OS_MANAGE_ROLES`, `INSP_EXECUTE_ROLES` no deps.py e referenciar em todos os endpoints.

### P2-05: ~~Portal Técnico Referencia "Registrar Anomalia"~~ — FALSO POSITIVO
- **Status:** Verificado — já foi corrigido. Portal usa "Registrar Problema" → `/solicitar`.

---

## MATRIZ DE IMPACTO

| ID | Severidade | Tipo | Personas Afetadas | Estimativa Fix |
|---|---|---|---|---|
| P0-01 | CRITICAL | RBAC | Todos os Técnicos Especializados | 15 min |
| P0-02 | CRITICAL | RBAC | Todos os Técnicos Especializados | 5 min |
| P0-03 | CRITICAL | RBAC | Todos os Técnicos Especializados | 15 min |
| P0-04 | CRITICAL | Segurança | Todos (exposição pública) | 5 min |
| P0-05 | CRITICAL | Segurança | Todos (reset de senha) | 5 min |
| P0-06 | CRITICAL | Dados | Admins + novos usuários | 15 min |
| P1-01 | HIGH | Frontend | Todos (bypass de UI) | 20 min |
| P1-02 | HIGH | UX | Todos | 10 min |
| P1-03 | HIGH | RBAC | Master, Supervisor | 5 min |
| P1-04 | HIGH | RBAC | Técnicos Especializados | 5 min |
| P1-05 | HIGH | Visibilidade | Operador, Técnicos | 15 min |
| P1-06 | HIGH | Segurança | Multi-tenant | 5 min |
| P1-07 | HIGH | API | Admin | 10 min |
| P2-01 | MEDIUM | UX | Todos (exportação) | 10 min |
| P2-02 | MEDIUM | RBAC | Técnicos Especializados | 5 min |
| P2-03 | MEDIUM | Feature | Almoxarife | A definir |
| P2-04 | MEDIUM | Dívida Técnica | Desenvolvedores | 15 min |
| P2-05 | MEDIUM | Cosmético | Técnicos (Portal) | 5 min |

---

## CAUSA RAIZ PRINCIPAL

Dois padrões sistêmicos:

**A) Desconexão Role-Taxonomy:** O Sprint 59 criou roles especializados (`tec_mecanico`, `tec_eletrico`, etc.) no RBAC centralizado (deps.py PERMISSIONS matrix) e no frontend, MAS os endpoints e o motor de visibilidade legados ainda referenciam apenas `'tecnico'`. O resultado é que a PERMISSIONS matrix diz "tec_mecanico pode executar OS", mas o endpoint chama `check_write_permission(user, [..., 'tecnico'])` e rejeita.

**B) Desconexão Model-Endpoint:** `UserCreate` declara `disciplina_principal`, `area_ids`, `turno`, mas `admin_create_user` não os persiste. Mesmo que (A) seja corrigido, usuários novos não teriam escopo de visibilidade porque seus campos de disciplina/área são null.

---

## ORDEM DE CORREÇÃO RECOMENDADA

1. **P0-04 + P0-05** (Segurança) — 10 min total
2. **P0-01 + P0-02 + P0-03 + P1-04 + P2-02** (RBAC Técnicos) — 30 min total (uma única refatoração)
3. **P0-06** (Persistência de campos) — 15 min
4. **P1-03 + P1-06** (Export audit) — 10 min
5. **P1-01 + P1-02** (Frontend route guards) — 30 min
6. **P1-05 + P1-07** (API ativos/users) — 25 min
7. **P2-**** (Restantes) — 35 min

**Tempo total estimado: ~2.5 horas**

---

## TESTE DE VALIDAÇÃO

Suítes de teste criadas durante a auditoria:
- `/app/backend/tests/test_rbac_audit_rc01.py` — 9 testes confirmando os bugs
- `/app/test_reports/iteration_75.json` — Relatório completo do testing agent

Após correções, re-executar os testes e inverter as asserções de confirmação de bug.
