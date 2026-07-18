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
- RC5.1.1: Polimento do PDF de Ordem de Servico — CONCLUIDA
- RC6.1: Construtor de Secoes da OS — PLANEJADA / BLOQUEADA

---

## RC5.1.1 — POLIMENTO DO PDF (CONCLUIDA 18/07/2026)

### Melhorias Aplicadas
1. Campos personalizados: filtro de valores vazios, oculta nomes tecnicos (TEST_C_*, FIELD_*, TMP_*), layout 2 colunas, secao oculta se vazia
2. Assinaturas: bloco redesenhado com espaco para assinatura/nome/data, nao divide entre paginas
3. Procedimento operacional: tabela com colunas alinhadas (#, Etapa, Status, Executado Por, Data), cores de status, descricao e obs indentados
4. Espacamento: section_title padronizado com 10mm, protecao contra titulo orfao (min 20mm apos titulo)
5. Paginacao: bloco de assinaturas move para nova pagina se nao couber, titulos nunca ficam sozinhos
6. Cabecalho: alinhamento preservado (logo, empresa, QR code)
7. Rodape: data/hora emissao UTC, nome do emissor, versao MAINTRIX, pagina X de Y, separador visual
8. Tipografia: tamanhos padronizados, contraste melhorado nos titulos de secao

### Arquivos Modificados
- backend/pdf_engine.py (section_title, signature_block, custom_fields_section, custom_signature_blocks, footer)
- backend/server.py (procedimento operacional section, MaintrixPDF constructor call)

### Testes: 10/10

---

## Regra do Piloto
Somente bugs P0/P1, seguranca, dados, ajustes ASTEC. Novas funcionalidades aguardam feedback.

---

## Backlog

### P1 (Pos-piloto)
- RC6.1: Construtor de Secoes da OS
- Construtor Visual Ondas 2-3
- QR Code MVP (Fase 2)
- Corrigir senha master
- Otimizar /api/central (~2.3s)

### P2
- Paginacao /api/ativos
- N+1: Dossie OS/Ativo
- server.py monolitico (4400+ linhas)
- Extracao OSDetailPage
- ERP/SAP

### P3
- IA Assistente
- Testes de carga
