# MANUTRIX v2.0 - Sistema de Gestão de Manutenção Industrial

## Visão Geral
Sistema CMMS/EAM (Computerized Maintenance Management System / Enterprise Asset Management) de classe enterprise para gestão de manutenção industrial. **Mobile-first** com tema escuro industrial otimizado para uso em campo.

## Data de Início
17/03/2026

## Última Atualização
17/03/2026 - v2.0 Major Release

## Stack Técnica
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + Lucide Icons
- **Backend**: FastAPI (Python) + aiofiles
- **Banco de Dados**: MongoDB
- **Autenticação**: JWT com RBAC (admin, supervisor, técnico, inspetor, viewer)
- **Upload**: Suporte a fotos (jpg, png, webp)

## User Personas

### 1. Técnico de Manutenção (João)
- Executa inspeções em campo via celular
- Escaneia QR Code dos ativos
- Registra falhas e observações
- Acompanha suas OS

### 2. Supervisor (Maria)
- Monitora KPIs do departamento
- Distribui OS entre técnicos
- Aprova fechamento de inspeções
- Analisa backlog

### 3. Administrador (Carlos)
- Configura hierarquia de ativos
- Gerencia usuários e permissões
- Define rotas de inspeção
- Acompanha indicadores gerenciais

## Core Requirements (Implementados)

### ✅ Autenticação e Autorização
- Login com email/senha
- JWT tokens
- RBAC (admin, supervisor, técnico, inspetor, viewer)
- Multi-tenant por organization_id

### ✅ Hierarquia de Ativos
- Organização → Planta → Área → Ativo
- TAG única por organização
- QR Code gerado automaticamente
- Criticidade por Matriz de Miller (A/B/C/D)
- Status: Operacional, Parado, Falha, Manutenção, Inspeção Pendente

### ✅ Rotas de Inspeção
- Templates de checklist por tipo de ativo
- Itens: boolean, número, texto, foto
- Frequência: Diária, Semanal, Mensal, Trimestral, Anual

### ✅ Inspeções
- Execução via checklist digital
- Status: Em Andamento, Concluída, Com Pendências
- **Geração automática de OS** quando detectada não-conformidade

### ✅ Ordens de Serviço
- Workflow: ABERTA → INICIADA → PAUSADA → CONCLUÍDA/CANCELADA
- Origem: Inspeção, Manual, Preventiva, Preditiva, Emergência
- Cálculo de tempo efetivo
- Vinculação com ativo e técnico

### ✅ KPIs Industriais
- MTTR (Mean Time To Repair)
- MTBF (Mean Time Between Failures)
- Disponibilidade Física (%)
- Taxa de Conformidade em Inspeções
- Backlog de OS

### ✅ Dashboard
- Cards de KPIs com cores indicativas
- Visão geral de ativos, OS e inspeções
- Ações rápidas: Escanear QR, Nova OS

### ✅ Estoque
- Controle por SKU
- Movimentações via transações
- Alerta de estoque mínimo

### ✅ UI/UX Industrial
- Tema escuro (Slate 950)
- Mobile-first para uso em campo
- Botões touch-friendly (48x48dp)
- Navegação inferior (mobile)
- Fontes: Barlow Condensed, Inter, JetBrains Mono

## O que foi Implementado (v1.0)

### Backend (/app/backend/server.py)
- 30+ endpoints REST
- Modelos Pydantic completos
- Soft delete em todas entidades
- Auditoria de operações
- Funções RPC atômicas para fechamento de inspeção e OS
- Seed data para demonstração

### Frontend (/app/frontend/src/App.js)
- 12 páginas/telas
- Componentes reutilizáveis
- Estado global via Context API
- Interceptors Axios para auth
- Detecção de modo offline

## O que foi Implementado na v2.0 (Melhorias)

### ✅ Scanner QR Code Real
- Acesso à câmera nativa via MediaDevices API
- BarcodeDetector para leitura de QR Codes
- Flashlight automático para ambientes escuros
- Busca manual por TAG ou código QR

### ✅ Modo Ronda
- Seleção de área para iniciar ronda
- Lista sequencial de ativos por área
- Barra de progresso durante a ronda
- Navegação entre ativos (anterior/próximo)
- Priorização por criticidade e pendências

### ✅ Sistema de Notificações
- Bell com contador de não-lidas
- Notificações automáticas para:
  - OS atribuídas a técnicos
  - Falhas detectadas em inspeções
  - Estoque crítico
- Marcar como lida / marcar todas

### ✅ Upload de Fotos
- Endpoint /api/upload para imagens
- Suporte a jpg, png, webp, gif
- Storage local com nomes únicos

### ✅ Mais Dados de Demonstração
- 10 Ativos (bombas, compressor, esteiras, misturador, etc.)
- 4 Rotas de Inspeção (Diária, Mensal, Semanal)
- 10 Itens de Estoque com categorias
- 4 Usuários (admin, supervisor, 2 técnicos)

### ✅ UI/UX Melhorias
- Desktop Sidebar navigation
- KPIs expandidos com subtítulos
- OS por prioridade no dashboard
- Alertas visuais para falhas e estoque crítico
- Progress bar em inspeções e rondas
- Animações (fadeIn, slideIn, pulse-glow, scan)
- Empty states com ícones e call-to-action

## Backlog Priorizado

### P0 - Crítico
- [ ] PWA com Service Workers para offline real
- [ ] Sincronização de dados offline
- [ ] Cache de ativos frequentes

### P1 - Alta Prioridade
- [ ] Relatórios PDF exportáveis
- [ ] Gráficos históricos (MTTR, MTBF)
- [ ] Assinatura digital do técnico
- [ ] Checklist dinâmico por tipo de OS

### P2 - Média Prioridade
- [ ] Integração com sensores IoT (preditiva)
- [ ] Assistente IA para técnicos
- [ ] Agendamento inteligente de OS
- [ ] Notificações push (FCM)

### P3 - Backlog Futuro
- [ ] Digital Twin simplificado
- [ ] Integração ERP (SAP, TOTVS)
- [ ] SSO (SAML/OIDC)
- [ ] Dashboard executivo mobile
- [ ] Análise de custo de ciclo de vida (LCC)

## Credenciais de Teste
```
Admin: admin@manutrix.com / admin123
Supervisor: supervisor@manutrix.com / supervisor123
Técnico 1: tecnico@manutrix.com / tecnico123
Técnico 2: pedro@manutrix.com / pedro123
```

## Dados de Demonstração v2.0
- 1 Organização: Indústria Demo
- 1 Planta: Planta Principal (São Paulo)
- 4 Áreas: Utilidades, Produção, Embalagem, Manutenção
- 10 Ativos: BOM-001, BOM-002, CMP-001, EST-001, EST-002, MIS-001, EMB-001, EMB-002, TOR-001, FRE-001
- 4 Rotas de Inspeção: Diária/Mensal Bomba, Semanal Compressor, Diária Esteira
- 3 OS de exemplo: 1 preventiva, 1 inspeção, 1 calibração
- 10 Itens de estoque: Rolamentos, Óleos, Vedações, Correias, Filtros, Graxa

## URLs
- Frontend: https://procure-manutrix.preview.emergentagent.com
- API: https://procure-manutrix.preview.emergentagent.com/api

## Próximos Passos
1. Implementar PWA com Service Workers
2. Adicionar gráficos de tendência nos KPIs
3. Criar relatórios PDF
4. Implementar notificações push
