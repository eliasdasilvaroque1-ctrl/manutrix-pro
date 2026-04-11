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
- Se dados já existem, retorna "Dados já existem"

## Permissões RBAC
- Admin: Acesso total (CRUD completo em tudo)
- Supervisor: Criar/Editar ativos, estoque, OS, inspeções
- Tecnico: Criar OS, executar inspeções, visualizar dados
- Inspetor/Viewer: Somente leitura
