# LGPD — Mapeamento de Conformidade MAINTRIX

## Base Legal por Tratamento

| Dado | Finalidade | Base Legal (Art. 7) |
|---|---|---|
| Nome, Email | Autenticação | V — Execução de contrato |
| Telefone | Contato (opcional) | I — Consentimento |
| IP, User-Agent | Segurança/Auditoria | IX — Interesse legítimo |
| Logs de ações | Auditoria operacional | V — Execução de contrato |
| Dados de OS/Inspeção | Funcionalidade core | V — Execução de contrato |
| Fotos | Evidência técnica | V — Execução de contrato |

## Medidas Técnicas Implementadas

- Isolamento multi-tenant por organization_id
- RBAC com 43 permissões
- Hash bcrypt para senhas
- Rate limiting em endpoints sensíveis
- Security Headers (HSTS, X-Frame-Options, etc.)
- Audit logs com 743+ registros
- JWT com expiração configurável
- Soft-delete (dados nunca removidos fisicamente sem solicitação)

## Direitos do Titular — Implementação

| Direito | Status | Mecanismo |
|---|---|---|
| Acesso | Implementado | GET /api/auth/me + Export |
| Correção | Implementado | PUT /api/admin/users |
| Eliminação | Parcial | Soft-delete + solicitação manual |
| Portabilidade | Implementado | Export Excel/PDF |
| Revogação | Implementado | Aceite versionado |
