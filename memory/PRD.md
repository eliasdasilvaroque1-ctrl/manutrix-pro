# MAINTRIX ENTERPRISE — PRD

## Status: RC P0/P1 IMPLEMENTADO — PRONTO PARA DEPLOY
## Versao: pilot-astec-v1.1.0
## Domínio: https://app.maintrix.com.br

---

## RC P0/P1 — Alterações desta Release

### P0.0 — Storage/PDF fetch (DONE)
- `fetch_file` em `pdf_engine.py` corrigido para usar `storage.py` (StorageManager)
- Lookup no `file_registry` para path migrado Supabase
- Fallback Emergent para arquivos não migrados

### P0.1 — Procedimento completo no PDF (DONE)
- Novo método `procedure_annex()` no MaintrixPDF
- Procedimento vinculado renderizado como ANEXO completo após OS
- Inclui: título, código, revisão, descrição, objetivo, pré-requisitos, ferramentas, EPIs, riscos, etapas, status de execução, imagens, observações
- Cada procedimento inicia em nova página
- Procedimento ausente/inativo: PDF gera normalmente sem erro

### P0.2 — Imagens do Estoque (DONE)
- Upload de material registra no `file_registry` (privado, org_id, entity_type)
- Nenhum item tem imagem atualmente; upload funcional quando utilizado

### P0.3 — Identidade do Cliente no PDF (DONE)
- Cabeçalho: nome da empresa (org_config) + local de trabalho (unidade)
- Rodapé: "Documento gerado pelo MAINTRIX Enterprise" (discreto)
- Logo do cliente no cabeçalho

### P0.4 — Disciplina na OS (DONE)
- Campo já existia; opções expandidas: Mecânica, Elétrica, Instrumentação, Automação, Lubrificação, Civil, Operação, Produção, Multidisciplinar, Outra
- Obrigatório na criação; default "mecanica" para OS antigas

### P0.5 — Seletor de Ativos (DONE)
- Formato: "TAG — NOME | Área: X | Planta: Y | Modelo: Z"
- Busca por TAG, nome, área, modelo

### P1.1 — Campos de Texto Ampliados (DONE)
- textarea min-h 150px, resize-y, maxLength 5000
- PDF text_block renderiza até 5000 chars sem truncar

### P1.2 — RBAC Construtor Visual (DONE)
- Removido do menu PCM/Supervisor/Técnico/Operador
- Apenas Master e Admin veem no sidebar
- Rota frontend protegida: allow=['master','admin']
- API: `_require_layout_admin` → 403 para PCM em duplicar/publicar

---

## Arquivos Alterados (6)
- backend/pdf_engine.py (+293 linhas)
- backend/server.py (OS PDF + material upload registry)
- backend/routes/personalizacao.py (RBAC layout builder)
- frontend/src/App.js (disciplina options, textarea, route protection)
- frontend/src/app/MainLayout.js (sidebar RBAC)
- frontend/src/pages/InspecoesPages.js (asset selector format)

---

## Testes
- PDF com procedimento: 50.887 bytes, 3 páginas, ANEXO PROCEDIMENTO presente ✅
- PDF sem procedimento: 47.810 bytes, gera normalmente ✅
- PDF cabeçalho mostra "ASTEC Cedro" (cliente) ✅
- PDF rodapé discreto "MAINTRIX Enterprise" ✅
- RBAC: PCM duplicar layout → 403 ✅
- Branding, Health, CRUD, Compliance: OK ✅
- Regressão: 10/10 PASS ✅
