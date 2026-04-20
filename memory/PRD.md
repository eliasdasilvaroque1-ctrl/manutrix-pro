# MANUTRIX OMNI v4.0 - Sistema Industrial de Gestão de Manutenção

## Visão Geral
CMMS/EAM enterprise para mineração e indústria pesada. Rastreabilidade completa, operação em campo, confiabilidade industrial.

## Stack: React 18 + FastAPI + MongoDB + Gemini AI
## URL: https://procure-manutrix.preview.emergentagent.com

## Implementado

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

### Dashboard + KPIs (v2.0)
- MTTR, MTBF, Disponibilidade, Confiabilidade
- Backlog, Conformidade, Custo mensal
- Alertas: OS atrasadas, estoque crítico, ativos parados

## Credenciais
- Admin: admin@manutrix.com / admin123
- Tecnico: tecnico@manutrix.com / tecnico123

## Backlog
- P1: Gráficos históricos (MTTR/MTBF trend)
- P1: Kanban visual de OS
- P2: PWA offline + Service Workers
- P2: Notificações push (FCM)
- P3: Digital Twin, IoT, ERP integration
