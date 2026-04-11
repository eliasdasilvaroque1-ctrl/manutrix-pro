# MANUTRIX v3.0 - Sistema de Gestao de Manutencao Industrial

## Visao Geral
Sistema CMMS/EAM (Computerized Maintenance Management System / Enterprise Asset Management) de classe enterprise para gestao de manutencao industrial. **Mobile-first** com tema escuro industrial otimizado para uso em campo.

## Data de Inicio
17/03/2026

## Ultima Atualizacao
11/04/2026 - v3.0 P0 Fixes Release

## Stack Tecnica
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + Lucide Icons
- **Backend**: FastAPI (Python) + aiofiles
- **Banco de Dados**: MongoDB
- **Autenticacao**: JWT com RBAC (admin, supervisor, tecnico, inspetor, viewer)
- **Upload**: Suporte a fotos (jpg, png, webp)

## User Personas

### 1. Tecnico de Manutencao (Joao)
- Executa inspecoes em campo via celular
- Escaneia QR Code dos ativos
- Registra falhas e observacoes
- Acompanha suas OS

### 2. Supervisor (Maria)
- Monitora KPIs do departamento
- Distribui OS entre tecnicos
- Aprova fechamento de inspecoes
- Analisa backlog

### 3. Administrador (Carlos)
- Configura hierarquia de ativos
- Gerencia usuarios e permissoes
- Define rotas de inspecao
- Acompanha indicadores gerenciais
- **Acesso total a todas operacoes CRUD**

## Implementado (v1.0 - v3.0)

### Autenticacao e Autorizacao
- Login com email/senha + JWT tokens
- RBAC (admin, supervisor, tecnico, inspetor, viewer)
- Multi-tenant por organization_id
- Admin bypass (acesso total)
- check_write_permission helper para RBAC

### Hierarquia de Ativos - CRUD Completo
- Organizacao > Planta > Area > Ativo
- TAG unica por organizacao (auto-gerada)
- QR Code gerado automaticamente
- Criticidade (Baixa/Media/Alta/Critica)
- Status: Operacional, Parado, Manutencao, Desativado
- Campos: fabricante, modelo, serie, MTBF, MTTR, custos, garantia

### Estoque - CRUD Completo
- SKU auto-gerado
- Categorias: rolamento, lubrificante, eletrica, mecanica, etc.
- Controle: quantidade, minimo, maximo, unidade, custo
- Alertas de estoque critico
- Movimentacoes (entrada/saida/ajuste) via body model
- Localizacao: almoxarifado, prateleira, posicao

### Ordens de Servico - CRUD Completo
- Workflow: ABERTA > INICIADA > PAUSADA > CONCLUIDA/CANCELADA
- Tipo: Preventiva, Corretiva, Preditiva, Emergencia, **FALHA** (P0 fix)
- Origem: Inspecao, Manual, Preventiva, Preditiva, Emergencia, Agendamento IA, **FALHA**
- Prioridade por criticidade
- Calculo de tempo efetivo e custos
- Vinculacao com ativo, tecnico, equipe

### Inspecoes - CRUD Completo
- Execucao via checklist digital (boolean, numero, texto)
- Geracao automatica de OS quando nao-conforme
- Workflow: Pendente > Em Andamento > Concluida/Com Pendencias
- Rotas de inspecao com templates

### KPIs Industriais
- MTTR, MTBF, Disponibilidade, Confiabilidade
- Taxa de Conformidade em Inspecoes
- Backlog de OS, OS atrasadas
- Custo manutencao mensal
- Preventiva vs Corretiva %

### Dashboard
- Cards de KPIs com cores indicativas
- Alertas: OS atrasadas, estoque critico, ativos parados
- Acoes rapidas: Escanear QR, Ronda, Nova OS, Inspecao

### UI/UX Enterprise
- Tema escuro industrial (Slate 950)
- Modais profissionais com secoes (Identificacao, Operacional, Financeiro, etc.)
- Sidebar desktop + bottom nav mobile
- Toast notifications (sonner)
- Glass-card design, status badges, priority badges
- Loading skeletons, empty states

### MongoDB _id Fix
- Todos endpoints POST usam pop('_id', None) em vez de "_id": None
- Nenhum endpoint retorna ObjectId serialization errors

## P0 Fixes Aplicados (11/04/2026)
- [x] Enum FALHA adicionado a OSTipo e OSOrigem
- [x] CRUD Ativos funcionando (criar, ler, editar, excluir)
- [x] CRUD Estoque funcionando (criar, ler, editar, excluir)
- [x] CRUD OS funcionando (criar, ler, editar, excluir, workflow)
- [x] CRUD Inspecoes funcionando (criar, ler, editar, excluir, workflow + auto-OS)
- [x] _id removido corretamente de todas as respostas POST
- [x] Admin consegue fazer todas as operacoes (check_write_permission)
- [x] ConcluirInspecaoBody/ConcluirOSBody/MovimentacaoCreateBody - proper JSON bodies
- [x] Frontend modais enterprise (Ativos, Estoque, OS, Inspecoes) todos funcionais

## Bug Fixes (11/04/2026)
- [x] Inspecao checklist: botoes Conforme/Nao Conforme nao apareciam (tipo field missing - fix: fallback + migracao)
- [x] QR Code: era apenas icone estatico, agora gera QR real escaneavel com qrcode.react (QRCodeSVG)
- [x] Scanner: camera funcional com BarcodeDetector, busca manual por TAG, resolve URLs do QR
- [x] Migracao automatica no startup para corrigir checklist items sem campo tipo

## Backlog Priorizado

### P1 - Alta Prioridade
- [ ] Melhorias visuais enterprise: glass effects, Framer Motion, loading skeletons polidos
- [ ] Dashboard avancado com graficos de OS por tipo/status (Kanban visual)
- [ ] Sistema de notificacoes funcional com badge no sino
- [ ] Relatorios PDF exportaveis
- [ ] Graficos historicos (MTTR, MTBF)

### P2 - Media Prioridade
- [ ] PWA com Service Workers para offline real
- [ ] Sincronizacao de dados offline
- [ ] Assinatura digital do tecnico
- [ ] Checklist dinamico por tipo de OS
- [ ] Notificacoes push (FCM)

### P3 - Backlog Futuro
- [ ] Integracao com sensores IoT (preditiva)
- [ ] Assistente IA para tecnicos
- [ ] Digital Twin simplificado
- [ ] Integracao ERP (SAP, TOTVS)
- [ ] SSO (SAML/OIDC)
- [ ] Dashboard executivo mobile
- [ ] Analise de custo de ciclo de vida (LCC)

## Credenciais de Teste
```
Admin: admin@manutrix.com / admin123
Supervisor: supervisor@manutrix.com / supervisor123
Tecnico 1: tecnico@manutrix.com / tecnico123
Tecnico 2: pedro@manutrix.com / pedro123
```

## URLs
- Frontend: https://procure-manutrix.preview.emergentagent.com
- API: https://procure-manutrix.preview.emergentagent.com/api

## Arquitetura
```
/app/
  backend/
    server.py          # FastAPI app, 40+ endpoints, RBAC, MongoDB
    requirements.txt
    .env
    uploads/
    tests/
  frontend/
    src/
      App.js           # Main React component (~2800 lines)
      App.css
      index.css
    package.json
    .env
  memory/
    PRD.md
    test_credentials.md
  test_reports/
    iteration_1.json
    iteration_2.json
    iteration_3.json   # P0 verification - 97% backend, 100% frontend
```
