# MAINTRIX FIELD OPERATIONS
## Arquitetura Completa — Documentos de Campo
### Versão: v1.1 | Status: PROJETO | Data: 2026-07-09

---

## 1. Visão do Módulo

```
MAINTRIX FIELD OPERATIONS
  ├── 📱 Operação Digital
  │     └── Fluxo atual v1.0 (tablet, celular, desktop)
  └── 📄 Documentos de Campo
        ├── OS Individual (PDF A4)
        ├── OS em Lote (PDF multi-OS)
        ├── Roteiro de Inspeção (PDF)
        ├── Lista de Materiais (PDF)
        ├── Plano Diário de Trabalho (PDF)
        └── Pasta Completa da Parada (PDF compilado)
```

**Posicionamento**: Plataforma que permite operação híbrida (papel + digital) no ritmo de cada empresa.

---

## 2. Catálogo de Documentos

| # | Documento | Tipo | Páginas Est. | Descrição |
|---|-----------|------|-------------|-----------|
| D1 | **OS Individual** | PDF A4 | 2-4 | Documento oficial completo da OS |
| D2 | **OS em Lote** | PDF A4 | N × 2-4 | Múltiplas OS em um único PDF |
| D3 | **Roteiro de Inspeção** | PDF A4 | 1-3 | Checklist imprimível com campos de medição |
| D4 | **Lista de Materiais** | PDF A4 | 1 | BOM/materiais para separação no almoxarifado |
| D5 | **Plano Diário de Trabalho** | PDF A4 | 1-2 | Resumo do turno com todas as atividades |
| D6 | **Pasta da Parada** | PDF A4 | 10-50+ | Compilação completa de uma parada programada |

---

## 3. Layout do Documento — OS Individual (D1)

### Página 1: Cabeçalho + Descrição + Materiais

```
┌──────────────────────────────────────────────────────────────────┐
│ [LOGO EMPRESA]              ORDEM DE SERVIÇO              [QR]  │
│  White Label                                              CODE  │
│                                                                  │
│                    ┌──────────────────────┐                      │
│                    │   OS-2026-000145     │  🟡 PROGRAMADA       │
│                    │   (48pt, bold)       │  (status badge)      │
│                    └──────────────────────┘                      │
├──────────────────────────────────────────────────────────────────┤
│ ÁREA         │ EQUIPAMENTO        │ TAG          │ DISCIPLINA    │
│ Britagem     │ Alimentador Vibr.  │ AV-01        │ Mecânica      │
├──────────────┼────────────────────┼──────────────┼───────────────┤
│ TIPO         │ PRIORIDADE         │ DATA PROG.   │ PRAZO         │
│ Corretiva    │ ■■■ ALTA           │ 09/07/2026   │ 12/07/2026    │
├──────────────┼────────────────────┼──────────────┼───────────────┤
│ SOLICITANTE  │ PLANEJADOR         │ EXECUTANTE                   │
│ José Operador│ Maria PCM          │ João Técnico                 │
├──────────────────────────────────────────────────────────────────┤
│ DESCRIÇÃO DO SERVIÇO                                             │
│                                                                  │
│ Vibração excessiva detectada no alimentador vibrató rio AV-01.   │
│ Verificar rolamentos, alinhamento e fixação da base.             │
│ Substituir rolamento lado acoplamento se necessário.             │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ SEGURANÇA                                                        │
│                                                                  │
│ APR: ☐ Sim  ☐ N/A    LOTO: ☐ Sim  ☐ N/A    PT: ☐ Sim  ☐ N/A  │
│                                                                  │
│ EPI Obrigatório: ☐ Capacete ☐ Óculos ☐ Luvas ☐ Protetor Aud.  │
│                  ☐ Bota     ☐ Cinto  ☐ _____________           │
│                                                                  │
│ Observações de Segurança:                                        │
│ ____________________________________________________________     │
│ ____________________________________________________________     │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ MATERIAIS                                                        │
│                                                                  │
│  Código      │ Descrição                    │ Qtd  │ Un │ ☐ OK  │
│ ─────────────┼──────────────────────────────┼──────┼────┼─────  │
│  ROL-6205    │ Rolamento 6205-2RS           │  2   │ UN │ ☐     │
│  GRX-SKF    │ Graxa SKF LGMT3              │  1   │ KG │ ☐     │
│  VED-R50    │ Vedação radial 50mm          │  2   │ UN │ ☐     │
│              │                              │      │    │       │
│  Conferido por almoxarifado: _____________  Data: ___/___/___   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                                      Página 1 de 2
```

### Página 2: Execução + Checklist + Assinaturas + Apontamento

```
┌──────────────────────────────────────────────────────────────────┐
│ OS-2026-000145 │ AV-01 — Alimentador Vibrató rio │ 🟡 PROGRAMADA│
├──────────────────────────────────────────────────────────────────┤
│ EXECUÇÃO                                                         │
│                                                                  │
│ Data de Início:  ___/___/______    Hora de Início:  ___:___     │
│ Data de Término: ___/___/______    Hora de Término: ___:___     │
│ Tempo Total: ________ minutos                                    │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ CHECKLIST DE EXECUÇÃO                                            │
│                                                                  │
│ ☐ Equipamento desenergizado e bloqueado (LOTO)                  │
│ ☐ Rolamento lado acoplamento inspecionado                       │
│ ☐ Rolamento lado livre inspecionado                             │
│ ☐ Alinhamento verificado com relógio comparador                 │
│ ☐ Torque de fixação da base verificado                          │
│ ☐ Teste de vibração pós-manutenção realizado                   │
│ ☐ Equipamento liberado para operação                            │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ OBSERVAÇÕES DO EXECUTANTE                                        │
│                                                                  │
│ ____________________________________________________________     │
│ ____________________________________________________________     │
│ ____________________________________________________________     │
│ ____________________________________________________________     │
│ ____________________________________________________________     │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ ASSINATURAS                                                      │
│                                                                  │
│ Executante:  ______________________  Data: ___/___/___          │
│ Supervisor:  ______________________  Data: ___/___/___          │
│ PCM:         ______________________  Data: ___/___/___          │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ APONTAMENTO PARA DIGITAÇÃO                                       │
│ (Uso exclusivo do escritório — não preencher em campo)           │
│                                                                  │
│ Data da Digitação: ___/___/______  Hora: ___:___                │
│ Digitado por:    ______________________________________________  │
│ Conferido por:   ______________________________________________  │
│ Revisado por:    ______________________________________________  │
│                                                                  │
│ Observações do Digitador:                                        │
│ ____________________________________________________________     │
│                                                                  │
│ Assinatura do Digitador: _____________________________________   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ [QR CODE]  Escaneie para acessar esta OS no MAINTRIX            │
│            https://astec.maintrix.com.br/os/OS-2026-000145      │
└──────────────────────────────────────────────────────────────────┘
                                                      Página 2 de 2
```

---

## 4. Layout — Roteiro de Inspeção (D3)

```
┌──────────────────────────────────────────────────────────────────┐
│ [LOGO]           ROTEIRO DE INSPEÇÃO                      [QR]  │
│                                                                  │
│              INSP-2026-000089                                    │
│              (36pt, bold)                                        │
├──────────────────────────────────────────────────────────────────┤
│ EQUIPAMENTO  │ TAG    │ ÁREA       │ TIPO        │ DATA PROG.   │
│ Britador BR  │ BR-01  │ Britagem   │ Preventiva  │ 09/07/2026   │
├──────────────────────────────────────────────────────────────────┤
│ CHECKLIST                                                        │
│                                                                  │
│  #  │ Item                              │ C  │ NC │ N/A │ OBS  │
│ ────┼───────────────────────────────────┼────┼────┼─────┼───── │
│  1  │ Nível de óleo do redutor          │ ☐  │ ☐  │ ☐   │ ____ │
│  2  │ Temperatura do mancal LA          │ ☐  │ ☐  │ ☐   │ ____ │
│  3  │ Vibração axial                    │ ☐  │ ☐  │ ☐   │ ____ │
│  4  │ Estado das correias               │ ☐  │ ☐  │ ☐   │ ____ │
│  5  │ Vazamentos hidráulicos            │ ☐  │ ☐  │ ☐   │ ____ │
│  6  │ Ruídos anormais                   │ ☐  │ ☐  │ ☐   │ ____ │
│  7  │ Estado geral das proteções        │ ☐  │ ☐  │ ☐   │ ____ │
│                                                                  │
│ MEDIÇÕES                                                         │
│ Temp. Mancal LA: ______°C    Temp. Mancal LF: ______°C         │
│ Vibração Axial:  ____mm/s    Vibração Radial:  ____mm/s         │
│                                                                  │
│ RESULTADO: ☐ Conforme  ☐ Não Conforme  ☐ Com Pendências        │
│                                                                  │
│ Observações: ________________________________________________    │
│ _____________________________________________________________    │
│                                                                  │
│ Inspetor: ______________________ Data: ___/___/___ Hora: ___:___│
│ Supervisor: ____________________ Data: ___/___/___              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Layout — Plano Diário de Trabalho (D5)

```
┌──────────────────────────────────────────────────────────────────┐
│ [LOGO]      PLANO DIÁRIO DE TRABALHO                     [QR]  │
│                                                                  │
│ Data: 09/07/2026    Turno: A (07:00-19:00)    Área: Britagem   │
│ Supervisor: Carlos Souza                                         │
├──────────────────────────────────────────────────────────────────┤
│  #  │ OS/INSP        │ Equip.  │ Tipo  │ Prioridade │ Executante│
│ ────┼────────────────┼─────────┼───────┼────────────┼────────── │
│  1  │ OS-2026-000145 │ AV-01   │ CORR  │ ■■■ ALTA   │ João     │
│  2  │ OS-2026-000146 │ BR-01   │ PREV  │ ■■  MÉDIA  │ Pedro    │
│  3  │ OS-2026-000147 │ TC-01   │ LUBR  │ ■   BAIXA  │ João     │
│  4  │ INSP-2026-0089 │ BR-01   │ INSP  │ ■■  MÉDIA  │ Maria    │
│  5  │ INSP-2026-0090 │ PP-02   │ INSP  │ ■   BAIXA  │ Maria    │
├──────────────────────────────────────────────────────────────────┤
│ MATERIAIS SEPARADOS                                              │
│  ☐ ROL-6205 (2 un) — OS-000145                                 │
│  ☐ GRX-SKF (1 kg) — OS-000145                                  │
│  ☐ FLT-HID (1 un) — OS-000146                                  │
├──────────────────────────────────────────────────────────────────┤
│ OBSERVAÇÕES DO TURNO                                             │
│ ____________________________________________________________     │
│                                                                  │
│ Supervisor: ______________________  Hora: ___:___               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Estrutura dos PDFs (Técnica)

### Biblioteca: ReportLab (já instalada no backend)
- Vetorial (não bitmap)
- Suporte a A4 (210×297mm)
- Frente e verso compatível
- Paginação automática
- Fontes embeddadas

### Arquitetura do Gerador

```python
# /app/backend/routes/field_operations.py (v1.1)

class DocumentGenerator:
    """Base class for all field documents."""
    
    def __init__(self, org_config, white_label):
        self.logo = white_label.logo_url
        self.empresa = white_label.nome_empresa
        self.colors = white_label.tema
    
    def header(self, canvas, doc_number, status, equipment_tag):
        """Standard header: Logo | Doc Number (48pt) | Status Badge | QR"""
        pass
    
    def footer(self, canvas, page_num, total_pages):
        """Page X of Y | Generated by MAINTRIX | Timestamp"""
        pass


class OSDocument(DocumentGenerator):
    """OS Individual — 2-4 pages."""
    pages = [
        'header_info',      # Cabeçalho + dados da OS
        'descricao',        # Descrição do serviço
        'seguranca',        # APR, LOTO, EPI
        'materiais',        # Lista de materiais
        'execucao',         # Campos de apontamento manual
        'checklist',        # Itens do checklist (se houver)
        'observacoes',      # Campo amplo
        'assinaturas',      # 6 campos de assinatura
        'apontamento',      # Seção para digitação
        'qr_footer',        # QR Code + link
    ]


class InspectionDocument(DocumentGenerator):
    """Roteiro de Inspeção — 1-3 pages."""
    pass


class DailyPlanDocument(DocumentGenerator):
    """Plano Diário de Trabalho — 1-2 pages."""
    pass


class ShutdownFolder(DocumentGenerator):
    """Pasta da Parada — compilação completa."""
    sections = [
        'capa',             # Capa com dados da parada
        'resumo',           # Estatísticas e cronograma
        'cronograma',       # Timeline visual
        'os_list',          # Todas as OS (D1 × N)
        'insp_list',        # Todos os roteiros (D3 × N)
        'materiais',        # Lista consolidada de materiais
        'assinaturas',      # Folha de assinaturas geral
    ]
```

### Status Badge (visual para mesa de operação)

```
Cores dos badges no PDF:
  SOLICITADA   → ⚪ Cinza (#94a3b8)
  PROGRAMADA   → 🟡 Amarelo (#f59e0b)
  EM EXECUÇÃO  → 🔵 Azul (#3b82f6)
  CONCLUÍDA    → 🟢 Verde (#10b981)
  CANCELADA    → 🔴 Vermelho (#ef4444)
  PAUSADA      → 🟠 Laranja (#f97316)

Tamanho: 24pt bold, uppercase
Posição: Canto superior direito, abaixo do número da OS
Visível a 2 metros de distância em papel A4
```

---

## 7. Endpoints Projetados

| Método | Endpoint | Documento |
|--------|----------|-----------|
| `GET` | `/api/field/os/{id}/pdf` | OS Individual (D1) |
| `POST` | `/api/field/os/batch-pdf` | OS em Lote (D2) — body: {os_ids: [...]} |
| `GET` | `/api/field/inspecao/{id}/pdf` | Roteiro de Inspeção (D3) |
| `GET` | `/api/field/os/{id}/materiais-pdf` | Lista de Materiais (D4) |
| `POST` | `/api/field/plano-diario/pdf` | Plano Diário (D5) — body: {data, turno, area_id} |
| `POST` | `/api/field/parada/{id}/pasta-pdf` | Pasta da Parada (D6) |
| `PATCH` | `/api/ordens-servico/{id}/apontamento` | Registrar apontamento digital |

### Impressão em Massa — Filtros

```
POST /api/field/os/batch-pdf
Body: {
  "filtros": {
    "area_id": "xxx",
    "data_de": "2026-07-09",
    "data_ate": "2026-07-12",
    "tipo": "preventiva",
    "disciplina": "mecanica",
    "executante_id": "xxx",
    "status": ["programada", "em_execucao"],
    "prioridade": ["emergencia", "alta"]
  }
}
→ Retorna PDF com TODAS as OS que matcham os filtros
```

---

## 8. QR Code

### Conteúdo do QR
```
https://{subdominio}.maintrix.com.br/os/{os_id}
```

### Posicionamento
- **Cabeçalho (pág 1)**: QR pequeno (25×25mm) no canto superior direito
- **Rodapé (última pág)**: QR grande (40×40mm) com texto "Escaneie para acessar"

### Futuro (v1.2+)
- Deep link direto para execução mobile
- Registro de fotos via QR scan
- Conclusão parcial via scan

---

## 9. Integração com White Label

| Elemento | Origem |
|----------|--------|
| Logo (cabeçalho) | `org_config.identidade.logo_url` |
| Nome da empresa | `org_config.identidade.nome_empresa` |
| Cor primária (badges, linhas) | `org_config.tema.cor_primaria` |
| Cor secundária (headers) | `org_config.tema.cor_secundaria` |
| Terminologia | `org_config.terminologia` (v1.1) |

---

## 10. Integração com Dossiê Permanente

### Timeline expandida (v1.1)
```
OS #2026-000145 — Dossiê
  ├── 09/07 07:05  CRIADA por José Operador
  ├── 09/07 07:15  EM ANÁLISE por Carlos Supervisor
  ├── 09/07 07:20  PROGRAMADA por Maria PCM
  ├── 09/07 07:25  📄 IMPRESSA para campo (PDF gerado)
  ├── 09/07 07:25  MATERIAL SEPARADO: 2x ROL-6205, 1x GRX-SKF
  ├── ── EXECUÇÃO EM CAMPO ──
  │    ├── Executante: João da Silva
  │    ├── Início: 09/07 08:00
  │    └── Término: 09/07 10:30
  ├── 10/07 14:30  📋 APONTAMENTO por Maria Oliveira (digitador)
  ├── 10/07 15:00  ✓ CONFERIDO por Carlos Souza (supervisor)
  └── 10/07 15:00  CONCLUÍDA — 150min
```

### Novo audit event type
```
"field_print" → Registra impressão do documento
"field_apontamento" → Registra digitação posterior
"field_conferencia" → Registra conferência do supervisor
```

---

## 11. RBAC para Field Operations

| Ação | Master | Admin | PCM | Supervisor | Técnico | Operador | Viewer |
|------|--------|-------|-----|------------|---------|----------|--------|
| Gerar PDF individual | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Gerar PDF em lote | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Gerar Plano Diário | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Gerar Pasta Parada | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Registrar apontamento | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Conferir apontamento | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 12. Estratégia de Implementação

### Sprint 1: Fundação (1 semana)
- `DocumentGenerator` base class com header/footer/QR
- Integração White Label (logo, cores, nome)
- OS Individual (D1) — versão completa
- Endpoint `GET /api/field/os/{id}/pdf`

### Sprint 2: Documentos Secundários (1 semana)
- Roteiro de Inspeção (D3)
- Lista de Materiais (D4)
- Plano Diário (D5)

### Sprint 3: Batch + Apontamento (1 semana)
- OS em Lote (D2) com filtros
- PATCH apontamento
- Integração Dossiê (timeline + audit events)

### Sprint 4: Pasta da Parada + QA (1 semana)
- Pasta da Parada (D6) — compilação automática
- Frontend: botões de impressão nas telas
- Regressão completa

### Total estimado: 4 sprints (4 semanas)

---

## 13. Compatibilidade v1.0

| Aspecto | Impacto na v1.0 |
|---------|----------------|
| Banco | ZERO — campo `apontamento` é opcional, novos audit types são aditivos |
| APIs existentes | ZERO — endpoints novos em `/api/field/*` |
| Frontend existente | ZERO — botões de impressão são adicionados, não substituem |
| RBAC | ADITIVO — novas permissões, existentes preservadas |
| Dossiê | ADITIVO — novos tipos de evento na timeline |

---

*Documento de arquitetura — NÃO IMPLEMENTADO.*
*Aguardando aprovação do CTO para inclusão no roadmap v1.1.*
