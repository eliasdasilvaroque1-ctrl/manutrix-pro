# MANUTRIX - Credenciais de Teste

## Contas de Usuário
| Role | Email | Senha |
|------|-------|-------|
| Admin | admin@manutrix.com | admin123 |
| Supervisor | supervisor@manutrix.com | supervisor123 |
| Tecnico | tecnico@manutrix.com | tecnico123 |
| Tecnico 2 | pedro@manutrix.com | pedro123 |

## Seed Data
- POST /api/seed - Cria dados de demonstração

## Permissões RBAC Industrial
| Perfil | Permissões |
|--------|------------|
| Admin | Controle total: CRUD completo, gestão de usuários, ativos, empresas |
| Gerente | Dashboard e relatórios (somente leitura), exporta dados |
| PCM | Gerencia OS, estoque, sobressalentes, relatórios, exporta |
| Supervisor | Gerencia OS, inspeções, rondas |
| Técnico | Preenche inspeções, abre anomalias, cria OS. NÃO edita/exclui |
| Inspetor | Executa inspeções |
| Viewer | Somente leitura |
