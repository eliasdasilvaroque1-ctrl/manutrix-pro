# MANUTRIX OMNI - PRD

## Correções aplicadas (2026-06-14 — Homologação em campo)

### 1. BUG ESTOQUE — CORRIGIDO
- **Causa raiz**: `CategoriaEstoque` era um Enum rígido com 10 valores. Frontend enviava `instrumentacao`, `eletrica`, `mecanica`, `outros` que NÃO existiam no Enum → Pydantic 422
- **Correção**: Removido Enum, campo `categoria` agora aceita qualquer string (backend: models.py). Frontend sincronizado com lista correta de categorias
- **Arquivos**: `/app/backend/models.py` (EstoqueCreate, EstoqueUpdate), `/app/frontend/src/App.js`

### 2. WORKFLOW ANOMALIAS — IMPLEMENTADO
- Fluxo: ABERTA → EM_ANALISE → OS_GERADA → AGUARDANDO_EXECUCAO → RESOLVIDA → ENCERRADA
- Reabrir: ENCERRADA → ABERTA (admin/supervisor apenas)
- Backend enforce de transições válidas + permissões
- **Arquivo**: `/app/backend/server.py` (change_anomalia_status)

### 3. ANOMALIAS CRUD COMPLETO
- Editar anomalia (PUT /api/anomalias/{id})
- Excluir anomalia (DELETE /api/anomalias/{id} — soft delete, admin/supervisor)
- Reabrir anomalia (POST /status {status: "aberta"} de encerrada)
- Comentários (POST /api/anomalias/{id}/comentarios)
- Histórico de alterações (7 entradas rastreadas)
- Data de encerramento + usuário que encerrou
- **Arquivos**: `/app/backend/server.py`, `/app/frontend/src/App.js` (AnomaliasPage)

## Status do Sistema
- Módulos homologados em campo: Ativos, OS, Inspeções, Ronda (NÃO ALTERADOS)
- Módulos corrigidos nesta sessão: Estoque, Anomalias
- SUSPENSO: Dashboard Executivo, OEE, Tree View, Push Notifications
