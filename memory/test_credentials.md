# MANUTRIX - Credenciais de Teste

## Organização Principal (Dados Legados)
| Role | Email | Senha |
|------|-------|-------|
| Admin | admin@manutrix.com | admin123 |
| PCM | pcm@manutrix.com | pcm123 |
| Supervisor | supervisor@manutrix.com | supervisor123 |
| Tecnico | tecnico@manutrix.com | tecnico123 |
| Tecnico 2 | pedro@manutrix.com | pedro123 |

## Organizações Multiempresa (Teste Isolamento)
| Org | Email | Senha | Org ID |
|-----|-------|-------|--------|
| ASTEC | admin@astec.com | astec123 | 6ac926b2-3af7-449c-ab5f-f32ccc9532bd |
| VALE | admin@vale.com | vale123 | 14cf887b-5b45-432d-97e0-f335c0cd8b28 |
| CSN | admin@csn.com | csn123 | ae302c30-32d3-4cc0-b745-9c83e122fe91 |

## Auth Flow
1. Login tries Supabase first
2. Falls back to MongoDB bcrypt if Supabase fails

## Seed
- POST /api/seed - Creates demo data for the authenticated user's org
