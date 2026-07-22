# MAINTRIX ENTERPRISE — PRD

## Status: RC CORREÇÃO PRÉ-PILOTO HOMOLOGADA
## Versao: pilot-astec-v1.4.0-rc
## Domínio: https://app.maintrix.com.br

---

## RC CORREÇÃO PRÉ-PILOTO — MODO ECONÔMICO (22/07/2026)

### Objetivo
Resolver pontualmente problemas críticos confirmados antes do piloto em campo.
Modo econômico: mínimo de alterações, sem refatoração, sem nova arquitetura.

### Correções Implementadas

#### P0 — Auditoria (React Error #31)
- **Arquivo**: `frontend/src/pages/ParadasPage.js` linha 1083
- **Problema**: `{log.details}` renderizava objetos diretamente no JSX, causando crash
- **Solução**: Formatter seguro com typeof/JSON.stringify
- **Teste**: Auditoria abre sem erro, 41 logs renderizados ✅

#### P0 — Permissões PCM (Bloqueio Admin)
- **Arquivos**: `frontend/src/app/MainLayout.js` (sidebar), `backend/server.py` (API)
- **Problema**: PCM via acesso a Auditoria, White Label, Construtor Visual, Configurações
- **Solução Frontend**: Menu Auditoria filtrado por `isAdmin || isSupervisor` no sidebar ADMIN
- **Solução Backend**: Removido 'pcm' das rotas `/admin/audit-logs`, `/admin/audit-logs/stats`, `/export/audit`
- **Teste**: PCM sem acesso sidebar ✅, PCM recebe 403 na API ✅, Admin/Master inalterados ✅

#### P0 — QR Code da OS no PDF
- **Arquivo**: `backend/server.py` linha 3286-3288
- **Problema**: QR aparecia no cabeçalho do PDF da OS
- **Solução**: `qr_path = None` no construtor MaintrixPDF para OS PDF
- **Preservado**: QR de Ativos, QR do Dossiê, endpoints QR — tudo intacto
- **Teste**: PDF gerado HTTP 200, cabeçalho sem QR ✅, QR Ativos funcional ✅

#### P1 — Causa da Falha Opcional
- **Arquivo**: `frontend/src/App.js` (ModalNovaOS)
- **Backend**: Já era `Optional[str] = None` em `models.py`
- **Problema**: Frontend marcava como `required` para corretivas
- **Solução**: Removido `required={form.tipo === 'corretiva'}` do input
- **Teste**: OS corretiva criada sem causa_falha ✅

#### P1 — Formulário Nova OS Simplificado
- **Arquivo**: `frontend/src/App.js` (ModalNovaOS)
- **Ocultos**: Seção "Estimativa de Custo" (Custo Peças, Custo MO, Custo Total)
- **Filtrados**: Campos personalizados com prefixos TEST_, DEV_, DEBUG_, TMP_
- **Visíveis**: Ativo, Título, Tipo, Disciplina, Prioridade, Descrição, Procedimento, Causa da Falha, Equipamento Parado, Responsável, Executantes, Data Planejada
- **Teste**: Modal verificado sem custos ✅, campos filtrados ✅

#### P1 — Título da OS Independente do Procedimento
- **Frontend**: Seleção de procedimento NÃO altera form.titulo (já era independente)
- **PDF**: Seção renomeada para "Título da Intervenção" + seção separada "Procedimento Aplicável"
- **Teste**: Título permanece inalterado após seleção de procedimento ✅

### Arquivos Alterados (4 arquivos)
1. `frontend/src/pages/ParadasPage.js` — formatAuditValue (React Error #31)
2. `frontend/src/app/MainLayout.js` — sidebar RBAC para PCM
3. `frontend/src/App.js` — ModalNovaOS simplificado
4. `backend/server.py` — QR oculto no PDF OS, bloqueio PCM auditoria API, título intervenção

### Testes: 16/16 PASS (7 backend + 9 frontend)
- Auditoria renderiza sem crash ✅
- PCM bloqueado no sidebar E na API ✅
- Admin/Master com acesso normal ✅
- OS criada sem causa_falha ✅
- OS criada sem procedimento ✅
- Título independente do procedimento ✅
- PDF gerado sem QR no cabeçalho ✅
- QR de Ativos funcional ✅
- Campos TEST_ filtrados ✅

---

## HISTÓRICO DE RCs ANTERIORES

### HOTFIX P0.2 — QR Code URL Absoluta (22/07/2026) ✅
### RC P1 — Dossiê Digital do Ativo v1.0 — Fases 1-3 ✅
### RC Estabilização Fases 1-4 ✅
### RC Estabilização Fase 5 — Performance Pré-Piloto ✅
### HOTFIX P0 — Tela Branca QR Code Público ✅

---

## POST-PILOTO BACKLOG
1. P2: Inserir CNPJ nos Termos de Uso
2. P2: Remover fallback Emergent Storage após estabilização
3. P2: Corrigir erro 500 intermitente `preview_numeracao` (digitos=null em org.py)
4. P2: Remover AtivoDetailPage dead code (App.js)
5. P1: RC6.1 — Construtor de Seções da OS (Ondas 2 e 3)
6. P3: Cadastro de colaboradores sem login
7. P3: Turnos e letras
8. P3: Equipe planejada versus equipe real
9. P3: Indicadores por colaborador/equipe
10. P3: Dossiê de Intervenção completo
11. P3: QR de consulta mobile
12. P3: Central de Relatórios
13. P3: Power BI
14. P3: IA Assistente
15. P3: Integrações ERP/SAP
