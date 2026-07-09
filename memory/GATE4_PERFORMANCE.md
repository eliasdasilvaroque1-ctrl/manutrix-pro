# GATE 4 — Performance Architecture Review
## MAINTRIX Enterprise — Piloto ASTEC | 2026-07-09

## Top 3 Gargalos

### 1. N+1 na Central de Trabalho (P0)
- Cada OS/inspeção retornada faz db.ativos.find_one() individual
- 50 OS abertas = 50 queries extras. Pior caso: ~150 queries N+1
- **Fix**: Bulk lookup com 1 query $in de todos ativo_id distintos

### 2. N+1 no Dashboard (P1)
- /os-por-setor: loop por setor → busca ativos → conta OS (20+ queries)
- /ativos-mais-falhas: busca 5000 OS → loop top 10 → busca ativo+setor (20+ queries)
- **Fix**: Usar $group aggregation pipeline

### 3. Dashboard Trend Lento (P2)
- Loop 6 meses × 2 queries = 12+ queries
- **Fix**: Single aggregation pipeline com $match + $group por mês

## Por Módulo

| Módulo | HTTP | Mongo | N+1 | Severidade |
|--------|------|-------|-----|------------|
| Central | 1 | 25-35 | SEVERO (~150) | ALTA |
| Dashboard | 6 | 39 | SIM (setor/falhas) | MÉDIA |
| Ativos | 3 | 5 | Não | BAIXA |
| OS | 5 | 8 | Não | BAIXA |
| Inspeções | 6 | 10 | Não | BAIXA |
| Estoque | 1 | 2 | Não | MÍNIMA |
| Auditoria | 2 | 3 | Não | MÍNIMA |

## O que já está bem
- Frontend usa Promise.all em todos os módulos
- Estoque e Auditoria são muito eficientes
- Nenhum full collection scan sem filtro org_id
