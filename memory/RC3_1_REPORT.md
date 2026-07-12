# RC3.1 — Release 1: Business Critical Fixes

**Data:** 2026-07-12  
**Versão:** 5.2.0-RC3.1  
**Status:** CONCLUÍDO  

---

## 1. Multiempresa — Auto-detecção de Organização

### Implementado
- **`POST /api/auth/lookup-email`**: Novo endpoint que resolve a organização de um email. Retorna `organization_id`, `organization_name` e `is_master`.
- **Login auto-resolve**: Backend aceita login sem `organization_id` para usuários não-master — detecta automaticamente a organização do email.
- **Frontend `onBlur`**: Ao sair do campo de email, o sistema detecta automaticamente a organização do usuário. Usuários não-master veem a org travada (com ícone de cadeado). Master continua com seletor livre.
- **Botão "Trocar"**: Visível apenas para master ou seleção manual. Não aparece quando org é auto-detectada.

### Fluxo de Login por Perfil

| Perfil | Seletor de Org | Comportamento |
|--------|---------------|---------------|
| Master | ✅ Visível | Pode trocar de organização livremente |
| Admin/PCM/Supervisor | 🔒 Bloqueado | Org detectada automaticamente pelo email |
| Técnicos | 🔒 Bloqueado | Org detectada automaticamente pelo email |
| Operador | 🔒 Bloqueado | Org detectada automaticamente pelo email |

### Arquivos Alterados
- `backend/server.py`: +`lookup-email` endpoint, login auto-resolve
- `frontend/src/App.js`: `handleEmailBlur`, `isMasterUser`, `autoOrgLoading`, orgSource `'auto'`

---

## 2. Impressão de OS — PDF Profissional A4

### Implementado
- **`GET /api/ordens-servico/{id}/pdf`**: Gera PDF A4 profissional com:

| Seção | Conteúdo |
|-------|----------|
| Cabeçalho | Nome da empresa, slogan, QR Code da OS |
| Barra | Número da OS (centralizado, destaque) |
| Equipamento | TAG, Nome, Tipo, Local (setor) |
| Informações | Tipo, Prioridade, Disciplina, Status |
| Descrição | Texto completo da OS |
| Equipe | Responsável, Turno, Executantes |
| Datas | Abertura, Hora Inicial, Hora Final, Duração |
| Materiais | Tabela (nome, qtd, unidade) |
| Observações | Caixa em branco para anotações de campo |
| Assinaturas | Executor + Supervisor (com linhas e campos de data) |
| Rodapé | Empresa, número OS, data/hora de impressão |

- **QR Code**: Gerado via `qrcode` (python-qrcode), contém `OS:{id}`
- **Botão "Imprimir OS"**: Visível na tela de detalhe da OS para todos os usuários autenticados

### Dependências Adicionadas
- `fpdf2` — geração de PDF
- `qrcode[pil]` — geração de QR Code

### Arquivos Alterados
- `backend/server.py`: endpoint `ordens-servico/{id}/pdf`
- `backend/requirements.txt`: +fpdf2, +qrcode
- `frontend/src/App.js`: botão Imprimir OS + import Printer icon

---

## 3. Field Operations — Estrutura Stub

### Implementado
- **`FieldOpsPage.js`**: Página estrutural com:
  - Cards: Minhas OS, Minhas Inspeções, Solicitações, Ronda
  - Ações Rápidas: Nova OS, Nova Inspeção, Nova Solicitação
  - Placeholder visual (ícone + mensagem "módulo em preparação")
- **Sem lógica implementada**: Dados estáticos (count=0), sem fetch ao backend
- **Sem rota ativa**: Página criada em `src/pages/FieldOpsPage.js` mas não registrada no router (será ativada em release futura)

### Arquivos Criados
- `frontend/src/pages/FieldOpsPage.js`

---

## Validação

| Teste | Status |
|-------|--------|
| `CI=true yarn build` | ✅ PASS (zero warnings) |
| 17/17 rotas | ✅ PASS |
| PAGE ERROR | ✅ Zero |
| Lookup email (master) | ✅ `is_master: true` |
| Lookup email (non-master) | ✅ `is_master: false`, org auto-detect |
| Login sem org_id (non-master) | ✅ Auto-resolve |
| Login sem org_id (master) | ✅ Exige seleção de org |
| PDF geração | ✅ 3983 bytes, header `%PDF-` válido |
| PDF conteúdo | ✅ Cabeçalho, QR, seções completas |
| Botão Imprimir no frontend | ✅ Presente na tela de detalhe |
| FieldOpsPage criada | ✅ Componente stub sem erros |
| Sidebar logo | ✅ Carrega normalmente |
| Zero regressões | ✅ |

---

## Riscos
- Nenhum risco identificado. Todas as alterações são aditivas.
- Login existente (com org_id) continua funcionando normalmente.
- O PDF não altera dados — é somente leitura.
- FieldOpsPage não está registrada no router — sem impacto.

---

*RC3.1 concluída. Aguardando autorização do CTO.*
