# BUG REPORT — RC3.2.1 QA

**Data:** 2026-07-12  

---

## Bugs Encontrados e Corrigidos

### BUG-001: `organization_id` obrigatório no Pydantic model impede login auto-resolve
- **Severidade:** P0
- **Arquivo:** `backend/models.py` (linha 155)
- **Causa:** `UserLogin.organization_id` era `str` (obrigatório). Pydantic rejeitava request sem o campo antes de chegar ao handler.
- **Correção:** Alterado para `Optional[str] = None`
- **Impacto:** Login auto-resolve para não-masters não funcionava.
- **Status:** ✅ Corrigido e testado

### BUG-002: OS Execução Direta não funcionava para master/admin/pcm
- **Severidade:** P1
- **Arquivo:** `backend/routes/work_orders.py` (linha 201)
- **Causa:** Condição `execucao_direta` verificava apenas `ROLE_GROUPS['execucao'] + ['supervisor']`. Master, admin e PCM não estavam incluídos.
- **Correção:** Adicionados `'admin', 'master', 'pcm'` à lista de roles permitidos.
- **Impacto:** OS criadas por master/admin com `execucao_direta=True` recebiam status `programada` em vez de `em_execucao`.
- **Status:** ✅ Corrigido e testado

---

## Bugs NÃO Encontrados (confirmados ausentes)

| Categoria | Verificação | Resultado |
|-----------|------------|-----------|
| PAGE ERROR | Console logs de 18 rotas | ✅ Zero |
| ReferenceError | Console logs | ✅ Zero |
| Build warnings | `CI=true yarn build` | ✅ Zero |
| Orphan imports | Scan de todos os page files | ✅ Zero |
| Memory leaks | N/A (não testável sem profiler) | — |
| Rotas órfãs | Todas as 18 rotas navegáveis | ✅ Zero |
