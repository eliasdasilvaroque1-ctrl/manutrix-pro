# MANUTRIX OMNI v4.0 - Sistema Industrial de Gestão de Manutenção

## Visão Geral
CMMS/EAM enterprise para mineração e indústria pesada. Rastreabilidade completa, operação em campo, confiabilidade industrial.

## Stack: React 18 + FastAPI + MongoDB + Gemini AI
## URL: https://procure-manutrix.preview.emergentagent.com

## Implementado

### Login Seguro (v5.2)
- Credenciais removidas da interface (nenhuma exposição)
- Botão "Acessar ambiente de demonstração" substitui texto de credenciais
- Tela limpa e profissional para apresentação executiva

### Registro Fotografico (v5.2)
- Componente PhotoUploader reutilizavel (camera/arquivo, grid, fullscreen, delete)
- OS: Foto Antes + Foto Depois (lado a lado) - corretiva exige foto antes
- Inspecoes: Registro Fotografico - obrigatorio quando nao conforme
- Anomalias: Fotos do Problema em cada card
- Suporte camera mobile (capture=environment)
- Visualizacao fullscreen ao clicar na foto

### Supabase Integration (v6.0)
- Supabase Auth para login/registro/reset de senha
- Auto-sync: usuarios MongoDB sao criados automaticamente no Supabase no primeiro login
- Fallback: se Supabase falhar, usa autenticacao local (MongoDB + bcrypt)
- Forgot password via Supabase (envia email real de redefinicao)
- Admin create user tambem cria no Supabase Auth
- supabase_id linkado no perfil MongoDB

### Autenticacao Profissional (v5.1)
- bcrypt para hashing de senhas (migracao automatica de SHA-256)
- "Esqueci minha senha" na tela de login com token de redefinicao
- Reset via token com validacao (minimo 6 caracteres, expiracao 1h)
- Admin pode gerar senha temporaria para qualquer usuario
- Troca de senha obrigatoria no primeiro login apos reset
- Gestao de usuarios: criar, editar (nome/email/role), desativar, redefinir senha
- Senhas nunca exibidas no sistema, hash bcrypt seguro

### RBAC Industrial (v4.0)
- Admin: controle total (CRUD + usuários + ativos + empresas)
- Gerente: dashboard e relatórios (somente leitura)
- PCM: gerencia OS, estoque, sobressalentes, relatórios, exporta
- Técnico: preenche inspeções, abre anomalias, cria OS (NÃO edita/exclui)
- Restrições no frontend (botões ocultos) e backend (403)

### Sobressalentes (v4.0)
- CRUD completo (tag, descrição, modelo, fabricante, status, localização)
- Status: estoque, em_uso, em_reforma, descartado
- Movimentações: entrada, saída, reforma, retorno
- Vinculação com ativo + anexo de nota fiscal

### Anomalias com Priorização Inteligente (v4.0)
- Report de anomalias por técnicos
- Priorização automática: score = severidade × criticidade do ativo
- Score >= 12: crítica | >= 6: alta | >= 3: média | < 3: baixa
- Geração automática de OS corretiva

### Attachments (Fotos/Documentos) (v4.0)
- Upload para qualquer entidade (inspection, work_order, anomaly, spare_asset)
- Inspeção não conforme exige foto
- OS corretiva exige foto para fechar

### Regras Operacionais (v4.0)
- OS não fecha sem: descrição do serviço + tempo gasto
- OS corretiva/falha exige foto/evidência anexada
- Inspeção não conclui se incompleta

### Knowledge Base (v4.0 - estrutura)
- CRUD: tipo_equipamento, problema, solução, tags
- Preparado para integração futura com IA

### Exportação de Dados (v4.0)
- Excel e PDF para: Ativos, OS, Estoque, Inspeções, Sobressalentes
- Botões de export em todas as páginas de listagem
- Dados prontos para Power BI

### Gestão de Usuários (v4.0)
- Admin: criar, listar, excluir usuários
- Badges coloridos por perfil
- Descrição de permissões no modal

### Assistente Técnico IA (v3.0)
- Chat com Gemini (Emergent LLM Key)
- Contexto dos manuais PDF dos ativos
- Upload de manuais por ativo
- Sugestões de perguntas rápidas

### Inspeções + Lubrificação (v3.0)
- Modal com abas: Inspeção | Lubrificação
- Frequências: Diária (5 itens), Quinzenal (7), Mensal (9)
- Lubrificação: tipo, quantidade, ponto, método, data/hora
- Checklist auto-gerado por frequência

### CRUD Completo (v3.0)
- Ativos, Estoque, OS, Inspeções: CRUD com modais enterprise
- Enum FALHA em OSTipo e OSOrigem
- QR Code real (qrcode.react) por ativo
- Scanner com câmera + busca por TAG

### Dashboard Executivo (v5.0)
- 3 blocos: Visao Executiva, Performance, Risco Operacional
- 10 KPIs com numeros grandes, legendas claras, cores por criticidade
- Grafico de tendencia MTBF/MTTR (linha, 6 meses) com recharts
- Grafico de distribuicao OS por tipo (barras clicaveis)
- Drill-down: clique em qualquer KPI abre modal com dados detalhados
- Botao "Exportar Dados" com dropdown (Excel/CSV para OS, Ativos, Inspecoes, Estoque)
- Subtitulo: "Indicadores operacionais e de confiabilidade da planta"
- Tema dark industrial, layout limpo, foco executivo

### Dashboard + KPIs (v2.0)
- MTTR, MTBF, Disponibilidade, Confiabilidade
- Backlog, Conformidade, Custo mensal
- Alertas: OS atrasadas, estoque crítico, ativos parados

## Credenciais
- Admin: admin@manutrix.com / admin123
- Tecnico: tecnico@manutrix.com / tecnico123

### Manuais PDF por Ativo (v4.2)
- Upload de PDFs no modal de criação/edição de ativos (seção "Manuais Técnicos PDF")
- Visualização, download e remoção na página de detalhe do ativo
- Extração automática de texto para contexto da IA
- Apenas Admin pode enviar/remover, todos podem visualizar
- Manuais listados no Assistente IA com contagem e badges por ativo

### Integração Power BI (v4.2)
- 4 endpoints REST JSON otimizados para Power BI:
  - GET /api/powerbi/ativos (dados flat de ativos)
  - GET /api/powerbi/ordens-servico (OS com dados do ativo)
  - GET /api/powerbi/inspecoes (inspeções com frequência e lubrificação)
  - GET /api/powerbi/kpis-historico (snapshot de KPIs)
- Dados prontos para importação direta no Power BI Desktop
- Autenticação via Bearer Token

## Backlog
- P1: Gráficos históricos (MTTR/MTBF trend)
- P1: Kanban visual de OS
- P2: PWA offline + Service Workers
- P2: Notificações push (FCM)
- P3: Digital Twin, IoT, ERP integration
