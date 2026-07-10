# MAINTRIX Field Operations — Arquitetura v1.1
## Processo de Apontamento Enterprise
### Data: 2026-07-09 | Status: PROJETO (não implementado)

---

## 1. Visão do Produto

### Antes (v1.0)
```
Operação 100% Digital
  └── Tablet/Celular/Desktop
```

### Depois (v1.1)
```
MAINTRIX Field Operations
  ├── 📱 Operação Digital — Tablet, celular, desktop
  └── 📄 Operação em Campo — Impressão, execução manual, apontamento posterior
```

**Posicionamento comercial**: Plataforma que permite evolução gradual do papel para o digital, sem quebrar a operação.

---

## 2. Fluxo da Operação em Campo

```
PCM Planeja OS
    ↓
Imprime OS (com seção de apontamento)
    ↓
Executante recebe folha impressa
    ↓
Executa serviço em campo (sem sistema)
    ↓
Preenche manualmente na folha:
  • Hora início / Hora término
  • Materiais utilizados
  • Checklist (C/NC)
  • Observações
  • Assinatura
    ↓
Retorna ao escritório
    ↓
Apontador (pode ser outra pessoa) digitaliza no MAINTRIX:
  • Lança dados da folha
  • Registra "Digitado por: Maria Oliveira"
  • Registra "Executante: João da Silva"
    ↓
Supervisor confere e aprova:
  • Registra "Conferido por: Carlos Souza"
    ↓
Dossiê permanente preserva TODA a cadeia
```

---

## 3. Modelo de Dados (projeção)

### Novos campos em `ordens_servico`

```javascript
{
  // ... campos existentes v1.0 ...

  // v1.1 — Field Operations: Apontamento
  "apontamento": {
    "modo": "digital" | "campo",        // Como foi executada
    "executante_id": "uuid",            // Quem fez o serviço (pode ser != digitador)
    "executante_nome": "João da Silva", // Denormalizado para impressão
    "digitador_id": "uuid",            // Quem lançou no sistema
    "digitador_nome": "Maria Oliveira",
    "data_digitacao": "2026-07-10T14:30:00Z",
    "conferido_por_id": "uuid",        // Quem conferiu
    "conferido_por_nome": "Carlos Souza",
    "data_conferencia": "2026-07-10T15:00:00Z",
    "revisado_por_id": "uuid",         // Revisor (opcional)
    "revisado_por_nome": null,
    "observacoes_digitador": "Dados coletados da folha #2026-0040",
    "assinatura_digitador": null        // Futuro: assinatura digital/foto
  }
}
```

### Regra fundamental
> O campo `executante` é INDEPENDENTE do `digitador`.
> O `concluido_por` da v1.0 registra quem clicou "concluir" no sistema.
> O `apontamento.executante_id` registra quem realmente executou o serviço.
> Ambos coexistem no dossiê.

---

## 4. Impacto na Impressão (OS impressa)

### Seção adicionada à folha impressa

```
┌────────────────────────────────────────────────┐
│           APONTAMENTO PARA DIGITAÇÃO           │
├────────────────────────────────────────────────┤
│ Data da Digitação: ___/___/______              │
│ Hora da Digitação: ___:___                     │
│                                                │
│ Digitado por: _______________________________  │
│                                                │
│ Conferido por: ______________________________  │
│                                                │
│ Revisado por: _______________________________  │
│                                                │
│ Observações do Digitador:                      │
│ ______________________________________________ │
│ ______________________________________________ │
│                                                │
│ Assinatura: __________________________________ │
└────────────────────────────────────────────────┘
```

---

## 5. Dossiê Permanente (impacto)

### Timeline v1.0 (atual)
```
OS #2026-0040
  ├── Criada por Admin (09/07 07:05)
  ├── Programada por PCM (09/07 07:20)
  ├── Em Execução (09/07 07:30)
  ├── Material consumido: 2x Rolamento (09/07 07:35)
  └── Concluída por Técnico (09/07 09:00) — 90min
```

### Timeline v1.1 (projetada)
```
OS #2026-0040
  ├── Criada por Admin (09/07 07:05)
  ├── Programada por PCM (09/07 07:20)
  ├── Impressa para campo (09/07 07:25)
  ├── ── EXECUÇÃO EM CAMPO ──
  │    ├── Executante: João da Silva
  │    ├── Início real: 09/07 08:00 (preenchido na folha)
  │    └── Término real: 09/07 10:30 (preenchido na folha)
  ├── ── APONTAMENTO ──
  │    ├── Digitado por: Maria Oliveira (10/07 14:30)
  │    ├── Conferido por: Carlos Souza (10/07 15:00)
  │    └── Obs: "Dados da folha #2026-0040, original arquivado"
  ├── Material consumido: 2x Rolamento
  └── Concluída — 150min (calculado: 08:00→10:30)
```

---

## 6. Endpoints Projetados (v1.1)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `PATCH` | `/api/ordens-servico/{id}/apontamento` | Registra dados de apontamento (digitador, executante, conferente) |
| `GET` | `/api/ordens-servico/{id}/apontamento` | Retorna dados de apontamento |
| `GET` | `/api/ordens-servico/{id}/print?mode=campo` | Gera PDF com seção de apontamento |

### Nenhum endpoint existente é alterado.

---

## 7. RBAC Projetado

| Ação | Master | Admin | PCM | Supervisor | Técnico | Operador | Viewer |
|------|--------|-------|-----|------------|---------|----------|--------|
| Imprimir OS | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Registrar apontamento | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Conferir apontamento | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Revisar apontamento | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 8. Compatibilidade v1.0

| Aspecto | Impacto |
|---------|---------|
| Banco | Campo `apontamento` é **opcional**. OS v1.0 sem apontamento continuam funcionando. |
| API | Nenhum endpoint existente alterado. Novos endpoints adicionados. |
| Frontend | Modal de conclusão ganha seção condicional "Apontamento" quando modo=campo. |
| Dossiê | Timeline exibe entries de apontamento quando presentes, ignora quando ausentes. |
| KPIs | Sem impacto. Tempo de execução vem de `data_inicio`/`data_conclusao` (já existente). |
| RBAC | Permissões existentes preservadas. Novas permissões de apontamento adicionadas. |

---

## 9. Implementação Sugerida (ordem)

1. **Modelo**: Adicionar campo `apontamento` (opcional) ao schema
2. **Endpoint PATCH**: Registrar/atualizar apontamento
3. **Impressão PDF**: Seção "APONTAMENTO PARA DIGITAÇÃO" no template
4. **Frontend**: Toggle "📱 Digital / 📄 Campo" no modal de conclusão
5. **Dossiê**: Renderizar entries de apontamento na timeline
6. **Audit log**: Registrar quem digitou, conferiu, revisou

### Estimativa: 2-3 sprints

---

## 10. Decisões Arquiteturais

1. **Apontamento é um subdocumento** (não nova coleção) — mantém o dossiê integrado
2. **Executante é campo separado de digitador** — rastreabilidade completa
3. **Modo digital/campo é por OS** (não global) — empresa pode ter OS digitais e em papel simultaneamente
4. **Conferência é obrigatória para modo campo** — garante 4 olhos
5. **Assinatura digital é futuro** (v1.2) — por agora, campo texto/foto

---

*Documento de arquitetura — NÃO IMPLEMENTADO.*
*Aguardando aprovação do CTO para inclusão no roadmap v1.1.*
