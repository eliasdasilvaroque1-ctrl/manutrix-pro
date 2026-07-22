# MAINTRIX ENTERPRISE — PRD

## Status: RC CORREÇÃO PRÉ-PILOTO HOMOLOGADA + FIX preview_numeracao
## Versao: pilot-astec-v1.4.1-rc
## Domínio: https://app.maintrix.com.br

---

## FIX: Erro 500 preview_numeracao (22/07/2026)

### Causa Raiz
`routes/org.py:218` — `pattern.get("digitos", 5)` trata chave ausente mas não trata `null`, `""`, `0` ou string inválida armazenados no banco. Linha 224 executa `"0" * digitos`, gerando `TypeError` quando `digitos` não é int positivo.

### Correção
Validação segura com try/except + fallback para 5 (padrão do sistema). Nenhuma alteração no banco.

### Testes
- null → digitos=5 ✅
- vazio → digitos=5 ✅
- zero → digitos=5 ✅
- string inválida → digitos=5 ✅
- valor válido (4) → digitos=4 ✅
- API retorna 200 com preview correto ✅

---

## RC CORREÇÃO PRÉ-PILOTO — MODO ECONÔMICO (22/07/2026)

### Correções Implementadas
- P0 Auditoria (React Error #31) ✅
- P0 Permissões PCM (Sidebar + API) ✅
- P0 QR da OS no PDF (oculto cabeçalho) ✅
- P1 Causa da Falha Opcional ✅
- P1 Formulário Nova OS Simplificado ✅
- P1 Título vs Procedimento Independente ✅

### Testes: 16/16 PASS (7 backend + 9 frontend)

---

## HISTÓRICO
- HOTFIX P0.2 — QR Code URL Absoluta ✅
- RC P1 — Dossiê Digital do Ativo v1.0 — Fases 1-3 ✅
- RC Estabilização Fases 1-5 ✅
- HOTFIX P0 — Tela Branca QR Code Público ✅

---

## POST-PILOTO BACKLOG
1. P2: Inserir CNPJ nos Termos de Uso (aguardando dados oficiais do cliente)
2. P2: Remover fallback Emergent Storage (ver análise abaixo)
3. P2: Remover AtivoDetailPage dead code
4. P1: RC6.1 — Construtor de Seções da OS
5. P3: Cadastro de colaboradores, Turnos, Equipes, Indicadores
6. P3: Dossiê de Intervenção, QR Mobile, Relatórios, Power BI, IA
