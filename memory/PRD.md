# MANUTRIX - Sistema de Gestão de Manutenção Industrial

## Visão Geral
Sistema CMMS/EAM (Computerized Maintenance Management System / Enterprise Asset Management) de classe enterprise para gestão de manutenção industrial.

## Data de Início
17/03/2026

## Stack Técnica
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI (Python)
- **Banco de Dados**: MongoDB
- **Autenticação**: JWT com RBAC

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

## Backlog Priorizado

### P0 - Crítico
- [ ] Implementar PWA com Service Workers para offline real
- [ ] Scanner de QR Code nativo (react-qr-reader)
- [ ] Upload de fotos em inspeções

### P1 - Alta Prioridade
- [ ] Modo "Ronda" com lista sequencial de inspeções
- [ ] Notificações push para OS urgentes
- [ ] Relatórios PDF exportáveis

### P2 - Média Prioridade
- [ ] Integração com sensores IoT (preditiva)
- [ ] Assistente IA para técnicos
- [ ] Agendamento inteligente de OS

### P3 - Backlog Futuro
- [ ] Digital Twin simplificado
- [ ] Integração ERP (SAP, TOTVS)
- [ ] SSO (SAML/OIDC)
- [ ] Dashboard executivo mobile

## Credenciais de Teste
```
Admin: admin@manutrix.com / admin123
Técnico: tecnico@manutrix.com / tecnico123
```

## Dados de Demonstração
- 1 Organização
- 1 Planta
- 4 Áreas (Utilidades, Produção, Embalagem, Manutenção)
- 7 Ativos (bombas, compressor, esteira, etc.)
- 1 Rota de Inspeção (Bomba Centrífuga - Mensal)
- 1 OS de exemplo
- 4 Itens de estoque

## URLs
- Frontend: https://procure-manutrix.preview.emergentagent.com
- API: https://procure-manutrix.preview.emergentagent.com/api

## Próximos Passos
1. Implementar scanner QR Code real
2. Adicionar upload de fotos
3. Criar PWA com cache offline
4. Adicionar mais rotas de inspeção por tipo de ativo
