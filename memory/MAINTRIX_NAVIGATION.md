# MAINTRIX — Navigation Map V6

**Data:** 2026-07-12  
**Status:** DOCUMENTAÇÃO — Nenhum código implementado  

---

## 1. Estrutura de Navegação

### Sidebar Desktop (perfil gestão: admin/pcm/supervisor)

```
PRINCIPAL
├── Central de Trabalho    /                    [todos exceto visualizador]
├── Dashboard              /dashboard           [gestão]
└── Equipe                 /equipe              [admin, pcm, supervisor]

OPERAÇÃO
├── Ativos                 /ativos              [todos exceto visualizador]
│   └── Detalhe Ativo      /ativos/:id          [todos]
├── Ordens de Serviço      /os                  [todos exceto visualizador]
│   └── Detalhe OS         /os/:id              [todos]
└── Inspeções              /inspecoes            [todos exceto visualizador]
    └── Detalhe Inspeção   /inspecoes/:id       [todos]

INFRAESTRUTURA
├── Unidades               /unidades            [admin]
└── Áreas                  /setores             [todos]

MATERIAIS
├── Estoque                /estoque             [todos exceto visualizador]
├── Sobressalentes         /sobressalentes      [gestão]
└── Paradas                /paradas             [gestão]

CONHECIMENTO
├── Biblioteca             /biblioteca          [admin, pcm]
├── Assistente IA          /assistente          [todos]
└── Consulta Equipamentos  /consulta            [gestão]

ADMIN
├── Usuários               /admin/usuarios      [admin]
├── Templates              /admin/templates     [admin, pcm]
├── Auditoria              /admin/auditoria     [admin, supervisor, gerente]
├── Config. Organização    /admin/config        [admin]
└── Dossiê Pesquisa        /dossie              [gestão]

MASTER (somente role master)
├── White Label            /master/white-label  [master]
└── Cleanup                /master/cleanup      [master]
```

### Sidebar Desktop (perfil operacional: técnicos/operadores)

```
PRINCIPAL
└── Minha Jornada          /                    [operacional]

OPERAÇÃO
├── Ativos                 /ativos
├── Inspeções              /inspecoes
├── Solicitar Serviço      /solicitar           [operacional]
├── Scanner QR             /scanner             [operacional]
└── Ronda                  /ronda               [operacional]

MATERIAIS
└── Estoque                /estoque
```

### Bottom Navigation (Mobile)

```
Central  │  Inspeções  │  [Scan]  │  Ativos  │  OS
   /        /inspecoes    /scanner    /ativos    /os
```

---

## 2. Rotas Completas

| # | Rota | Página | Permissão | Layout |
|---|------|--------|-----------|--------|
| 1 | `/login` | Login | Público | Standalone |
| 2 | `/` | Central de Trabalho | Todos (exceto viewer) | AppLayout |
| 3 | `/dashboard` | Dashboard | Gestão | AppLayout |
| 4 | `/ativos` | Lista de Ativos | Todos (exceto viewer) | AppLayout |
| 5 | `/ativos/:id` | Detalhe do Ativo | Todos | AppLayout |
| 6 | `/os` | Lista de OS | Todos (exceto viewer) | AppLayout |
| 7 | `/os/:id` | Detalhe da OS | Todos | AppLayout |
| 8 | `/inspecoes` | Lista de Inspeções | Todos (exceto viewer) | AppLayout |
| 9 | `/inspecoes/:id` | Detalhe da Inspeção | Todos | AppLayout |
| 10 | `/ronda` | Ronda | Operacional | AppLayout |
| 11 | `/scanner` | Scanner QR | Operacional | AppLayout |
| 12 | `/estoque` | Estoque | Todos (exceto viewer) | AppLayout |
| 13 | `/sobressalentes` | Sobressalentes | Gestão | AppLayout |
| 14 | `/paradas` | Paradas Programadas | Gestão | AppLayout |
| 15 | `/solicitar` | Nova Solicitação | Todos (exceto viewer) | AppLayout |
| 16 | `/assistente` | Assistente IA | Todos | AppLayout |
| 17 | `/equipe` | Gestão de Equipe | Admin, PCM, Supervisor | AppLayout |
| 18 | `/biblioteca` | Biblioteca | Admin, PCM | AppLayout |
| 19 | `/consulta` | Consulta Equipamentos | Gestão | AppLayout |
| 20 | `/dossie` | Dossiê Pesquisa | Gestão | AppLayout |
| 21 | `/unidades` | Unidades | Admin | AppLayout |
| 22 | `/setores` | Áreas/Setores | Todos | AppLayout |
| 23 | `/admin/usuarios` | Gestão de Usuários | Admin | AppLayout |
| 24 | `/admin/templates` | Templates Inspeção | Admin, PCM | AppLayout |
| 25 | `/admin/auditoria` | Auditoria | Admin, Supervisor, Gerente | AppLayout |
| 26 | `/admin/config` | Config Organização | Admin | AppLayout |
| 27 | `/master/white-label` | White Label Designer | Master | AppLayout |
| 28 | `/master/cleanup` | Cleanup | Master | AppLayout |
| 29 | `/portal/equipamento/:id` | Portal Público | Público | Standalone |
| 30 | `/portal/tecnico/:id` | Portal Técnico | Todos | AppLayout |
| 31 | `/termos` | Termos de Uso | Todos | AppLayout |
| 32 | `/privacidade` | Política Privacidade | Todos | AppLayout |
| 33 | `/sobre` | Sobre o MAINTRIX | Todos | AppLayout |

---

## 3. Fluxos de Navegação Principais

### Fluxo: Técnico em Campo
```
Login → Central (Minha Jornada) → OS atribuída → Iniciar → Executar → Concluir
                                 → Scanner QR → Ativo → Histórico
                                 → Ronda → Checklist → Foto → Concluir
```

### Fluxo: PCM (Planejamento)
```
Login → Central → Solicitações pendentes → Analisar → Aprovar
     → Planos de Inspeção → Criar/Editar → Aprovar
     → OS → Planejar → Programar → Acompanhar
```

### Fluxo: Operador
```
Login → Central → Solicitar Serviço → Selecionar Ativo → Descrever → Enviar
     → Scanner QR → Portal do Ativo → Ver status
```
