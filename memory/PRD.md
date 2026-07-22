# MAINTRIX ENTERPRISE — PRD

## Status: RC CORREÇÃO PDF OS HOMOLOGADA
## Versao: pilot-astec-v1.4.2-rc
## Domínio: https://app.maintrix.com.br

---

## CORREÇÃO PDF DA OS — MODO ECONÔMICO (22/07/2026)

### Causa Raiz 1 — CNPJ Fictício no Cabeçalho
O `layout_snapshot` da OS congelava o `cabecalho_snapshot` do Construtor Visual que continha dados de teste:
- `razao_social: "MAINTRIX INT LTDA"`
- `cnpj: "12.345.678/0001-99"`
- `endereco: "Rua Integracao 123 Sao Paulo SP"`
- `telefone: "(11) 5555-1234"`
O `_render_custom_header(cab)` no `pdf_engine.py` renderizava esses dados diretamente.
**Correção**: Pular aplicação do `layout_snapshot` no PDF da OS, usar header padrão com dados reais da organização.

### Causa Raiz 2 — QR Ainda Aparecendo
O `_render_custom_header` verificava `self.qr_path` e renderizava QR independentemente.
Com o header padrão e `qr_path=None`, QR não aparece mais.

### Causa Raiz 3 — Rodapé Incorreto
O `rodape_snapshot` tinha `texto_personalizado: "DOCUMENTO INT CONFIDENCIAL"` com flag `mostrar_identificacao_doc: true` mas sem `doc_code`, resultando em "DOCUMENTO INT CONFIDENCIAL | -".
**Correção**: Usar rodapé padrão: "Documento gerado pelo MAINTRIX Enterprise | data | emissor | Página X/Y".

### Arquivos Alterados (2)
1. `backend/server.py` — print_os_pdf: layout_snapshot ignorado, header institucional, layout compacto, campos vazios ocultos, procedimento condicional
2. `backend/pdf_engine.py` — header padrão melhorado (Unidade + OS nº), procedure_annex sem obs/assinaturas duplicadas

### Testes: 24/24 PASS
- OS sem procedimento: 1 página, ASTEC + Unidade, sem CNPJ fictício, sem QR ✅
- OS com procedimento: 2 páginas, título preservado, Procedimento Aplicável visível ✅
- OS campos vazios: fabricante/série ocultos, 1 página ✅
- QR de Ativos funcional ✅

---

## FIX preview_numeracao (22/07/2026) ✅
## RC CORREÇÃO PRÉ-PILOTO (22/07/2026) ✅
## RC Estabilização Fases 1-5 ✅
## RC Dossiê Digital v1.0 ✅
## HOTFIX QR Code URL Absoluta ✅

---

## POST-PILOTO BACKLOG
1. P2: Inserir CNPJ nos Termos de Uso (aguardando dados oficiais)
2. P2: Remover fallback Emergent Storage
3. P1: RC6.1 — Construtor de Seções da OS
4. P3: Cadastro de colaboradores, Turnos, Equipes, Indicadores
5. P3: Dossiê de Intervenção, QR Mobile, Relatórios, Power BI, IA
