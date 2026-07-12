# MAINTRIX — Functional Specification V6

**Versão:** 6.0 (Arquitetura Alvo)  
**Data:** 2026-07-12  
**Status:** ESPECIFICAÇÃO — Nenhum código implementado  
**Classificação:** Documento de referência oficial do sistema  

---

## 1. Objetivo do Sistema

O MAINTRIX é um **Enterprise Asset Management (EAM)** orientado ao ativo, projetado para plantas industriais brasileiras. Seu propósito é centralizar toda a gestão do ciclo de vida de ativos industriais — da inspeção preventiva à manutenção corretiva — com rastreabilidade completa, compliance regulatório (NR-13, LGPD) e operação offline em campo.

**Diferencial:** Modelo asset-centric onde toda informação (inspeções, ordens, custos, documentos, histórico) pertence hierarquicamente ao ativo.

---

## 2. Entidades Principais

### 2.1 Organização

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador único |
| nome | string | Nome da empresa |
| slug | string | Identificador URL |
| config | object | Configuração white-label (cores, logos, textos) |
| plano | enum | free / starter / professional / enterprise |
| created_at | datetime | Data de criação |

**Relacionamentos:** 1:N Usuários, 1:N Unidades, 1:N Setores, 1:N Ativos  
**Regras:** Isolamento total de dados (multi-tenant). Toda query filtra por `organization_id`.  
**Permissões:** Master pode gerenciar todas as orgs. Admin gerencia sua org.

### 2.2 Usuário

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador único |
| nome | string | Nome completo |
| email | string | E-mail (login) |
| password_hash | string | bcrypt hash |
| role | enum | Perfil de acesso (ver §5) |
| organization_id | UUID | FK → Organização |
| disciplinas | array[string] | Disciplinas técnicas |
| turno | enum | ADM / A / B / C / D |
| unidade_ids | array[UUID] | Unidades de acesso |
| area_ids | array[UUID] | Áreas de acesso |
| force_password_change | boolean | Forçar troca na próxima sessão |
| deleted_at | datetime | Soft delete |

**Relacionamentos:** N:1 Organização, N:M Unidades, N:M Áreas  
**Regras:** E-mail único por organização. Soft delete preserva histórico. Login por email + org.  
**Permissões:** Admin cria/edita/remove. Próprio usuário troca senha.

### 2.3 Perfil (Role)

12 perfis hierárquicos:

| Perfil | Grupo | Descrição |
|--------|-------|-----------|
| master | Plataforma | Acesso total cross-tenant, white-label, cleanup |
| admin | Gestão | Administrador da organização |
| pcm | Gestão | Planejamento e Controle de Manutenção |
| supervisor | Gestão | Supervisão de equipe e execução |
| gerente | Gestão | Visão gerencial, aprovações, relatórios |
| tec_mecanico | Execução | Técnico de manutenção mecânica |
| tec_eletrico | Execução | Técnico de manutenção elétrica |
| instrumentista | Execução | Instrumentação e automação |
| lubrificador | Execução | Lubrificação industrial |
| inspetor | Execução | Inspeções técnicas |
| operador | Operacional | Operador de produção (cria solicitações) |
| visualizador | Leitura | Apenas visualização |

### 2.4 Turno

| Valor | Descrição |
|-------|-----------|
| ADM | Administrativo (horário comercial) |
| A | Turno A (manhã) |
| B | Turno B (tarde) |
| C | Turno C (noturno) |
| D | Turno D (reserva) |

**Uso:** Filtro de equipe no dashboard, escala de plantão, notificações.

### 2.5 Disciplina

| Valor | Descrição |
|-------|-----------|
| mecanica | Manutenção mecânica |
| eletrica | Manutenção elétrica |
| instrumentacao | Instrumentação e automação |
| lubrificacao | Lubrificação |
| caldeiraria | Caldeiraria e soldagem |
| civil | Manutenção civil |
| utilidades | Utilidades (ar comprimido, vapor, água) |

**Uso:** Vinculação de técnicos, filtro de OS, classificação de planos.

### 2.6 Equipe

Conceito virtual — não é uma collection separada. Equipe é a composição de:
- Usuários da mesma organização
- Filtrados por turno, disciplina, área
- Gerenciados pelo admin/supervisor

### 2.7 Setor (Área)

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| nome | string | Nome da área (ex: "Área de Britagem") |
| codigo | string | Código (ex: "BRIT-01") |
| organization_id | UUID | FK → Organização |
| unidade_id | UUID | FK → Unidade |

**Relacionamentos:** N:1 Unidade, 1:N Ativos  
**Regras:** Ativos herdam o setor. Técnicos podem ser restritos a áreas específicas.

### 2.8 Unidade (Planta)

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| nome | string | Nome da unidade industrial |
| localizacao | string | Endereço/cidade |
| organization_id | UUID | FK → Organização |

**Relacionamentos:** 1:N Setores, 1:N Ativos (via setor)

### 2.9 Ativo (Asset-Centric)

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| tag | string | Tag industrial (ex: "BM-001") |
| nome | string | Nome descritivo |
| tipo_equipamento | string | Bomba, Motor, Válvula, etc. |
| fabricante | string | Fabricante |
| modelo | string | Modelo |
| numero_serie | string | Número de série |
| sector | object | Setor embutido (desnormalizado) |
| criticidade | enum | A (crítico) / B (importante) / C (auxiliar) |
| status_operacional | enum | operando / parado / reserva / em_manutencao |
| data_instalacao | date | Data de instalação |
| organization_id | UUID | FK → Organização |
| manual_url | string | URL do manual técnico |
| images | array[string] | URLs de fotos |
| qr_code | string | Código QR vinculado |

**Relacionamentos:** 1:N Inspeções, 1:N OS, 1:N Planos, 1:N Documentos, 1:N Movimentações  
**Regras:** Tag única por organização. Soft delete preserva histórico.

**Modelo Asset-Centric:**
```
Ativo
├── Informações (fabricante, modelo, série, criticidade)
├── Documentos (manuais PDF, fotos)
├── Histórico (audit_logs por entity_id)
├── Inspeções (vinculadas por ativo_id)
├── Planos de Inspeção (vinculados por ativo_id ou tipo)
├── Solicitações (vinculadas por ativo_id)
├── Ordens de Serviço (vinculadas por ativo_id)
├── Custos (materiais consumidos, HH)
└── Indicadores (MTBF, MTTR, disponibilidade)
```

### 2.10 Plano de Inspeção

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| nome | string | Nome do plano |
| tipo | enum | inspecao / preventiva / lubrificacao / limpeza |
| disciplina | string | Disciplina técnica |
| ativo_id | UUID | FK → Ativo (ou null para genérico) |
| tipo_equipamento | string | Para planos genéricos |
| perguntas | array[object] | Checklist de perguntas |
| status | enum | rascunho / aprovado |
| versao | integer | Versão do plano |
| frequencia | string | diario / semanal / mensal / trimestral |
| organization_id | UUID | FK → Organização |

**Relacionamentos:** N:1 Ativo (ou N:tipo_equipamento), 1:N Inspeções  
**Regras:** Só planos "aprovados" podem gerar execuções. Perguntas tipadas (boolean, numerico, temperatura, vibração, opção, texto, observação).

### 2.11 Inspeção (Execução)

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| ativo_id | UUID | FK → Ativo |
| plano_id | UUID | FK → Plano de Inspeção |
| tipo | string | Tipo herdado do plano |
| status | enum | pendente / em_andamento / concluida / com_pendencias |
| resultado | enum | conforme / nao_conforme / com_ressalvas |
| checklist | array[object] | Respostas do checklist |
| responsavel_id | UUID | FK → Usuário |
| executantes | array[UUID] | FKs → Usuários executantes |
| data_programada | date | Data planejada |
| data_inicio | datetime | Início real |
| data_conclusao | datetime | Fim real |
| duracao_minutos | number | Duração calculada |
| fotos | array[object] | Fotos capturadas |
| observacoes | string | Observações gerais |
| organization_id | UUID | FK → Organização |

**Relacionamentos:** N:1 Ativo, N:1 Plano, N:M Usuários  
**Regras:** Não conforme gera solicitação automática. Fotos podem ser capturadas offline.

### 2.12 Solicitação de Serviço

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| ativo_id | UUID | FK → Ativo |
| descricao | string | Descrição do problema |
| tipo | enum | corretiva / melhoria / seguranca |
| prioridade | enum | baixa / media / alta / critica |
| status | enum | aberta / em_analise / aprovada / rejeitada / convertida |
| solicitante_id | UUID | FK → Usuário |
| inspecao_origem_id | UUID | FK → Inspeção (se gerada por não conformidade) |
| os_gerada_id | UUID | FK → OS (quando convertida) |
| organization_id | UUID | FK → Organização |

**Relacionamentos:** N:1 Ativo, N:1 Inspeção (opcional), 1:1 OS (quando convertida)  
**Regras:** Qualquer usuário pode criar (exceto visualizador). PCM analisa e converte em OS.

### 2.13 Ordem de Serviço (OS)

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| numero | string | Número sequencial (ex: #2026-00021) |
| ativo_id | UUID | FK → Ativo |
| titulo | string | Título da OS |
| descricao | string | Descrição detalhada |
| tipo | enum | corretiva / preventiva / preditiva / melhoria |
| disciplina | string | Disciplina técnica |
| prioridade | enum | baixa / media / alta / critica |
| status | enum | (ver §4 — Estados) |
| responsavel_id | UUID | FK → Usuário responsável |
| executantes | array[UUID] | FKs → Técnicos executantes |
| data_abertura | datetime | Data de criação |
| data_inicio | datetime | Início da execução |
| data_conclusao | datetime | Conclusão |
| tempo_execucao_minutos | number | Tempo total de execução |
| materiais | array[object] | Materiais consumidos |
| hh_registros | array[object] | Registros de homem-hora |
| custo_total | number | Custo calculado |
| observacoes | string | Observações |
| solicitacao_id | UUID | FK → Solicitação (se originada) |
| organization_id | UUID | FK → Organização |

**Relacionamentos:** N:1 Ativo, N:M Usuários, N:M Materiais Estoque, 0:1 Solicitação  
**Regras:** Número auto-incrementado por org. Transições de status controladas (ver §4).

### 2.14 Estoque (Item)

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| sku | string | Código do item |
| nome | string | Nome |
| categoria | enum | rolamento / lubrificante / correia / vedacao / filtro / eletrico / mecanico / hidraulico / pneumatico / instrumentacao / outro |
| quantidade | number | Quantidade atual |
| estoque_minimo | number | Limite para alerta |
| estoque_maximo | number | Limite superior |
| unidade | enum | UN / L / KG / M / PC / CX |
| custo_unitario | number | Custo unitário R$ |
| fornecedor | string | Fornecedor principal |
| almoxarifado | string | Local de armazenamento |
| prateleira | string | Prateleira |
| posicao | string | Posição |
| item_critico | boolean | Item crítico |
| alertar_minimo | boolean | Alertar quando abaixo do mínimo |
| images | array[string] | URLs de fotos |
| organization_id | UUID | FK → Organização |

**Relacionamentos:** N:M OS (via materiais consumidos), 1:N Movimentações  
**Regras:** SKU único por org. Alerta automático quando `quantidade < estoque_minimo`.

### 2.15 Sobressalente (Spare Part)

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| nome | string | Nome da peça |
| part_number | string | Part number |
| fabricante | string | Fabricante |
| condicao | enum | novo / reformado / em_reforma / reservado / instalado / descartado |
| origem | enum | compra_nova / reforma_interna / reforma_externa / transferencia |
| ativo_destino_id | UUID | FK → Ativo (quando instalado) |
| valor | number | Valor R$ |
| images | array[string] | URLs de fotos |
| organization_id | UUID | FK → Organização |

**Relacionamentos:** N:1 Ativo (destino), 1:N Reformas, 1:N Movimentações

### 2.16 Biblioteca (Knowledge Base)

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| id | UUID | Identificador |
| titulo | string | Título do documento |
| tipo | enum | manual / procedimento / norma / catalogo |
| conteudo | string | Texto/descrição |
| file_url | string | URL do arquivo |
| tags | array[string] | Tags de busca |
| organization_id | UUID | FK → Organização |

**Relacionamentos:** Referenciado por Ativos (manuais), Planos (procedimentos)

---

## 3. Fluxos de Negócio

### 3.1 Fluxo de Inspeção

```
PLANO DE INSPEÇÃO (aprovado)
        │
        ▼
EXECUÇÃO DE INSPEÇÃO
   ├── Técnico abre inspeção
   ├── Preenche checklist (campo a campo)
   ├── Captura fotos
   ├── Registra observações
   │
   ▼
RESULTADO
   ├── CONFORME → Histórico do ativo
   ├── COM RESSALVAS → Histórico + observação
   └── NÃO CONFORME
           │
           ▼
     SOLICITAÇÃO AUTOMÁTICA
           │
           ▼
     PCM ANALISA
           │
           ▼
     ORDEM DE SERVIÇO
```

### 3.2 Fluxo de Solicitação

```
SOLICITAÇÃO (qualquer usuário)
        │
        ▼
EM ANÁLISE (PCM recebe)
        │
    ┌───┴───┐
    ▼       ▼
REJEITADA  APROVADA
           │
           ▼
     PLANEJAMENTO (PCM define escopo, materiais, equipe)
           │
           ▼
     PROGRAMAÇÃO (PCM agenda data, aloca recursos)
           │
           ▼
     ORDEM DE SERVIÇO CRIADA
           │
           ▼
     EXECUÇÃO → CONCLUSÃO → ENCERRAMENTO
```

### 3.3 Fluxo de Ordem Direta

```
USUÁRIO (gestão/técnico)
        │
        ▼
SELECIONA EQUIPAMENTO (ativo)
        │
        ▼
SELECIONA TIPO (corretiva/preventiva/preditiva/melhoria)
        │
        ▼
PREENCHE DESCRIÇÃO + PRIORIDADE + DISCIPLINA
        │
        ▼
OS CRIADA (status: aberta)
        │
        ▼
FLUXO NORMAL DA OS (ver §4)
```

---

## 4. Estados

### 4.1 Ordem de Serviço

```
                        ┌──────────┐
                        │ ABERTA   │ ← Criação
                        └────┬─────┘
                             │ PCM planeja
                        ┌────▼─────┐
                        │PLANEJADA │
                        └────┬─────┘
                             │ PCM programa
                        ┌────▼──────┐
                        │PROGRAMADA │
                        └────┬──────┘
                             │ Disponível para execução
                        ┌────▼──────┐
                        │DISPONÍVEL │
                        └────┬──────┘
                             │ Técnico inicia
                        ┌────▼────────┐
                   ┌───►│EM EXECUÇÃO  │◄───┐
                   │    └────┬────────┘    │
                   │         │             │
              Retoma    ┌────▼─────┐       │
                   │    │ PAUSADA  │───────┘
                   │    └──────────┘
                   │         │
                        ┌────▼──────┐
                        │ CONCLUÍDA │
                        └────┬──────┘
                             │ Gerente aprova
                        ┌────▼──────┐
                        │ENCERRADA  │
                        └───────────┘

     Qualquer estado → CANCELADA (admin/master)
```

**Estados:** `aberta`, `planejada`, `programada`, `disponivel`, `em_execucao`, `pausada`, `concluida`, `encerrada`, `cancelada`

### 4.2 Inspeção

```
PENDENTE → EM_ANDAMENTO → CONCLUÍDA
                              │
                              ├── (resultado: conforme)
                              └── COM_PENDÊNCIAS (resultado: não conforme)
```

**Estados:** `pendente`, `em_andamento`, `concluida`, `com_pendencias`

### 4.3 Plano de Inspeção

```
RASCUNHO → APROVADO
```

**Estados:** `rascunho`, `aprovado`

### 4.4 Solicitação

```
ABERTA → EM_ANÁLISE → APROVADA → CONVERTIDA (em OS)
                   └→ REJEITADA
```

**Estados:** `aberta`, `em_analise`, `aprovada`, `rejeitada`, `convertida`

---

## 5. RBAC — Matriz de Permissões

### 5.1 Legenda
- ✅ Permitido
- ❌ Negado
- 👁 Somente visualização

### 5.2 Matriz Completa

| Permissão | Master | Admin | PCM | Supervisor | Gerente | Técnicos | Operador | Visualizador |
|-----------|--------|-------|-----|-----------|---------|----------|----------|-------------|
| **ATIVOS** |
| Visualizar | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 👁 |
| Criar | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Excluir | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **ORDENS DE SERVIÇO** |
| Visualizar | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 👁 |
| Criar | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Executar | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Concluir | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Aprovar | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Programar | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **INSPEÇÕES** |
| Visualizar | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 👁 |
| Criar | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Executar | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Editar | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **PLANOS** |
| Visualizar | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Criar/Editar | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Importar | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **ESTOQUE** |
| Visualizar | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 👁 |
| Criar/Editar | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Movimentar | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **SOLICITAÇÕES** |
| Criar | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **ADMIN** |
| Usuários | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Config Org | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Auditoria | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| White Label | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **DASHBOARD** |
| Visualizar | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Equipe | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **RONDA** |
| Executar | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |

---

## 6. Asset-Centric Model

Toda informação no MAINTRIX é acessível a partir do ativo:

```
ATIVO (BM-001 — Bomba Centrífuga)
│
├── 📋 INFORMAÇÕES
│   ├── Tag, Nome, Tipo, Fabricante, Modelo, Série
│   ├── Criticidade (A/B/C)
│   ├── Status Operacional
│   └── Localização (Unidade → Setor)
│
├── 📄 DOCUMENTOS
│   ├── Manual Técnico (PDF)
│   ├── Fotos do ativo
│   └── Biblioteca vinculada
│
├── 📜 HISTÓRICO
│   ├── Audit logs (todas as alterações)
│   ├── Eventos (instalação, reforma, transferência)
│   └── Timeline completa
│
├── 🔍 INSPEÇÕES
│   ├── Planos de inspeção ativos
│   ├── Execuções realizadas
│   ├── Resultados (conforme/não conforme)
│   └── Fotos de evidência
│
├── 🔧 ORDENS DE SERVIÇO
│   ├── OS abertas/em execução
│   ├── OS concluídas (histórico)
│   ├── Materiais consumidos
│   └── HH registradas
│
├── 📨 SOLICITAÇÕES
│   ├── Solicitações abertas
│   └── Solicitações convertidas em OS
│
├── 💰 CUSTOS
│   ├── Custo de materiais
│   ├── Custo de mão de obra (HH × valor)
│   └── Custo total por período
│
└── 📊 INDICADORES
    ├── MTBF (Mean Time Between Failures)
    ├── MTTR (Mean Time To Repair)
    ├── Disponibilidade
    └── Backlog
```
