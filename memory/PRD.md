# MAINTRIX ENTERPRISE — PRD

## Visao: CMMS/EAM SaaS multi-tenant | Stack: React PWA + FastAPI + MongoDB Atlas | Piloto: ASTEC

---

## Status: APROVADO PARA O PILOTO SEM RESSALVAS (18/07/2026)
## Fase: CONGELAMENTO FUNCIONAL — Piloto ASTEC Cedro em andamento

---

## Historico de RCs
- RC Documentos Fase 1 (Unicode PDF) — CONCLUIDA
- Sprint 1-3 Biblioteca Corporativa — CONCLUIDA
- RC Construtor Visual Onda 1 (@dnd-kit) — CONCLUIDA
- HOTFIX P0: MasterCleanupPage/ExportButtons — CONCLUIDA
- RC5.0 Missao 1: Biblioteca Corporativa — CONCLUIDA
- RC5.0 Missao 2: Vinculo Automatico + Upload — CONCLUIDA
- RC5.0.1: HOTFIX P0 Build + Auditoria — CONCLUIDA
- RC5.0.2: HARDENING P1 IDOR + Estoque + Sector — CONCLUIDA
- RC5.1: Performance e Estabilizacao — APROVADA E ENCERRADA
- RC5.1 Fase 3: JWT Fail-Fast + Isolamento Dossie + Indices MongoDB — APROVADA
- RC5.2: Procedimento Operacional integrado a OS — CONCLUIDA
- RC5.2.1: Hardening Final do Procedimento Operacional — CONCLUIDA
- RC5.9: Pilot Readiness Review (Auditoria Final) — CONCLUIDA
- RC5.9.1: Correcao P0 procedimento_id em OSCreate/OSUpdate — CONCLUIDA
- RC6.1: Construtor de Secoes da OS — PLANEJADA / BLOQUEADA

---

## Regra do Piloto

Permitido apenas:
- Bugs P0
- Bugs P1 com impacto operacional comprovado
- Correcoes de seguranca
- Correcoes de dados
- Ajustes indispensaveis ao uso da ASTEC

Novas funcionalidades aguardam feedback real do piloto.

---

## Backlog Tecnico

### RC6.1 — CONSTRUTOR DE SECOES DA ORDEM DE SERVICO
- **Status**: PLANEJADA / BLOQUEADA ATE ENCERRAMENTO DO PILOTO
- **Prioridade**: P1 (pos-piloto)

#### Objetivo
Permitir que cada organizacao personalize a estrutura da OS (secoes visiveis, ordem, titulos) sem alterar codigo.

#### Escopo
- Secoes do sistema (13): Cabecalho, Equipamento, Informacoes da OS, Descricao, Equipe, Datas e Tempos, Observacoes, Procedimento Operacional, Campos Personalizados, Materiais Consumidos, Evidencias, Assinaturas, Rodape. Protegidas (nao excluiveis). Podem ser ocultadas, reordenadas, renomeadas.
- Secoes personalizadas: CRUD completo + reordenar + ocultar + duplicar. Exemplos: Seguranca, Qualidade, Meio Ambiente, Checklist NR12/NR35.

#### Arquitetura Proposta
- **Collection**: `os_section_config` (por org). Schema: `{org_id, sections: [{id, key, title, type: system|custom, order, visible, locked, created_at}]}`
- **Endpoints**: `GET/PUT /api/os-model-config` (ler/salvar config completa), `POST /api/os-model-config/sections` (criar custom), `DELETE /api/os-model-config/sections/{id}` (excluir custom)
- **Auto-seed**: Na primeira consulta de uma org, gerar layout padrao com as 13 secoes do sistema
- **Frontend**: Nova pagina `OSModelConfigPage.js`, menu em Configuracoes > Modelo da OS. Lista com botoes up/down, show/hide, edit title, add, delete, duplicate
- **PDF**: Refatorar `print_os_pdf()` para ler config da org, renderizar apenas secoes visiveis na ordem configurada, fallback para layout padrao
- **RBAC**: Somente admin/PCM
- **Auditoria**: Registrar criacao, edicao, remocao, mudanca de ordem, mudanca de visibilidade
- **Multi-tenant**: Config independente por org
- **Sem drag-and-drop**: Apenas up/down. Arquitetura preparada para @dnd-kit futuro

#### Riscos
- Superficie de mudanca alta (collection, rota, pagina, PDF, ordenacao, visibilidade, auditoria, RBAC, compatibilidade)
- Alteracao no PDF pode impactar OSs existentes se fallback nao for robusto
- Secoes personalizadas sem conteudo estruturado (texto livre vs campos tipados) — decisao pendente

#### Dependencias
- Nenhuma dependencia tecnica bloqueante
- Depende de feedback do piloto para priorizar tipos de secoes personalizadas

#### Criterios de Aceite
1. Criar secao personalizada
2. Editar titulo de secao (sistema e personalizada)
3. Excluir secao personalizada
4. Ocultar secao do sistema
5. Mostrar secao do sistema novamente
6. Alterar ordem (up/down)
7. PDF respeita config (ordem e visibilidade)
8. Multiempresa isolado
9. Auditoria registrada
10. RBAC (admin/PCM apenas)
11. Compatibilidade (orgs existentes recebem layout padrao)

---

### P1 (Pos-piloto)
- RC6.1: Construtor de Secoes da OS (detalhado acima)
- Construtor Visual Ondas 2-3 (drag-and-drop avancado)
- QR Code MVP (Fase 2 do Piloto)
- Corrigir senha master ou atualizar test_credentials
- Otimizar /api/central (cache/aggregation, atual ~2.3s)

### P2
- Paginacao /api/ativos server-side
- RBAC ordering (Depends antes Pydantic)
- N+1: Dossie OS, Dossie Ativo
- server.py monolitico (4400+ linhas)
- Extracao OSDetailPage
- ERP/SAP

### P3
- IA Assistente
- Testes de carga
