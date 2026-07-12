# SECURITY ROADMAP — MAINTRIX

**Data:** 2026-07-12  
**Baseline:** Score 68/100  
**Target:** Score 90+/100  

Priorização por: **Impacto × Risco × Esforço**

---

## FASE 1 — Críticos (Score → 78)
*Esforço: ~2h | Impacto: Alto | Risco atual: Crítico*

### 1.1 CORS Restritivo
| Aspecto | Detalhe |
|---------|---------|
| Risco | 🔴 Crítico |
| Esforço | 15 min |
| Impacto | Bloqueia requisições de domínios não autorizados |
| Ação | Configurar `CORS_ORIGINS` no .env com domínios Vercel + Railway. Restringir methods e headers. |

### 1.2 File Access Control
| Aspecto | Detalhe |
|---------|---------|
| Risco | 🔴 Crítico |
| Esforço | 30 min |
| Impacto | Impede acesso não autenticado a arquivos enviados |
| Ação | Adicionar `Depends(get_current_user)` nos endpoints `/uploads/{filename}` e `/uploads/manuals/{filename}`. Verificar org_id. |

### 1.3 CSP Básico
| Aspecto | Detalhe |
|---------|---------|
| Risco | 🔴 Crítico |
| Esforço | 45 min |
| Impacto | Restringe fontes de scripts/styles/connections |
| Ação | Adicionar `Content-Security-Policy` no security_headers_middleware: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' {API_URL}; img-src 'self' data: blob:; frame-ancestors 'none'` |

### 1.4 Error Detail Sanitization
| Aspecto | Detalhe |
|---------|---------|
| Risco | 🟡 Alto |
| Esforço | 10 min |
| Impacto | Remove info interna de respostas de erro |
| Ação | Substituir `str(e)` por mensagem genérica no endpoint assistente IA (linha 2831). |

---

## FASE 2 — Altos (Score → 85)
*Esforço: ~3h | Impacto: Alto | Risco atual: Alto*

### 2.1 File Upload Hardening
| Aspecto | Detalhe |
|---------|---------|
| Risco | 🟡 Alto |
| Esforço | 30 min |
| Ação | Limite de tamanho (10MB), validação de content-type por magic bytes, sanitização de filename |

### 2.2 Account Lockout
| Aspecto | Detalhe |
|---------|---------|
| Risco | 🟡 Alto |
| Esforço | 45 min |
| Ação | Bloquear conta após 5 tentativas falhadas em 15 min. Desbloqueio automático após 30 min ou manual por admin. Persistir contadores no MongoDB. |

### 2.3 Password Complexity
| Aspecto | Detalhe |
|---------|---------|
| Risco | 🟡 Alto |
| Esforço | 20 min |
| Ação | Validar: mín 8 chars, 1 maiúscula, 1 número. Aplicar em registro, change-password e admin-reset. |

### 2.4 Uvicorn Update
| Aspecto | Detalhe |
|---------|---------|
| Risco | 🟡 Alto |
| Esforço | 10 min |
| Ação | `pip install uvicorn==0.34.0` |

---

## FASE 3 — Médios (Score → 90)
*Esforço: ~2h | Impacto: Médio*

### 3.1 HSTS Preload
| Esforço | 5 min |
| Ação | Adicionar `preload` ao header HSTS |

### 3.2 CORS Methods/Headers Restritos
| Esforço | 10 min |
| Ação | `allow_methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS"]`, `allow_headers=["Authorization","Content-Type","X-Request-Id"]` |

### 3.3 Rate Limit Persistente
| Esforço | 45 min |
| Ação | Migrar contadores de in-memory para MongoDB collection com TTL index |

### 3.4 Rate Limit em Endpoints de Dados
| Esforço | 20 min |
| Ação | Adicionar limite genérico (300 req/min) para endpoints GET de dados |

### 3.5 JWT Refresh Token (opcional)
| Esforço | 1h |
| Ação | Par access_token (15min) + refresh_token (7 dias). Melhora UX sem reduzir segurança. |

---

## FASE 4 — Baixos (Score → 95)
*Esforço: ~1h | Impacto: Baixo*

### 4.1 Seed Password Cleanup
| Ação | Mover passwords de seed para env vars ou gerar aleatórios |

### 4.2 Data Purge Policy
| Ação | Job periódico para anonimizar/purgar dados marcados como deleted_at > 90 dias |

### 4.3 NPM Dependencies
| Ação | `yarn upgrade` para resolver vulns em dev-deps quando compatível |

---

## Cronograma Sugerido

| Fase | Score Alvo | Esforço | Prioridade |
|------|-----------|---------|-----------|
| Fase 1 (Críticos) | 68 → 78 | ~2h | IMEDIATO |
| Fase 2 (Altos) | 78 → 85 | ~3h | Esta sprint |
| Fase 3 (Médios) | 85 → 90 | ~2h | Próxima sprint |
| Fase 4 (Baixos) | 90 → 95 | ~1h | Backlog |

**Total para Score 90:** ~7h de implementação + testes

---

*Documento gerado como parte da auditoria RC2.3. Nenhuma alteração de código realizada.*
