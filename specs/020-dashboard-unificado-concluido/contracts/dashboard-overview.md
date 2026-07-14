# Contract: `GET /api/dashboard/overview`

**Feature**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

## Verbo + rota

```
GET /api/dashboard/overview
```

## Autenticação e autorização

- **Auth**: `Authorization: Bearer <jwt>` (padrão do portal)
- **RBAC**: **qualquer utilizador autenticado** (sem role check adicional).
  - `role=admin` → 200
  - `role=socio` (com ou sem privilégios) → 200
  - conta `technical` (admin operacional) → 200
  - sem token / token inválido → 401
  - conta `inativo` / `pendente_*` / `rejeitado` → 401/403 (comportamento do
    `get_current_user` existente, herdado)

## Query params

Nenhum.

## Response 200 — `application/json`

```json
{
  "finance": {
    "saldo_atual": 425300.0,
    "receitas_ano": 380500.0,
    "despesas_ano": 320750.0,
    "resultado_ano": 59750.0,
    "quotas_mes": 32000.0,
    "monthly": [
      {"month": 1, "receitas": 32000.0, "despesas": 21500.0},
      {"month": 2, "receitas": 33500.0, "despesas": 25000.0}
    ],
    "despesas_por_categoria": {
      "material": 82000.0,
      "eventos": 45000.0,
      "administrativo": 12500.0
    },
    "mes_atual": {"receitas": 34500.0, "despesas": 28000.0},
    "mes_anterior": {"receitas": 32000.0, "despesas": 26500.0}
  },
  "socios": {
    "ativos": 148,
    "novos_90d": 6
  },
  "atos": {
    "pendentes": 3,
    "aguarda_direcao": 2,
    "aguarda_proposta": 1
  },
  "votacoes": {
    "abertas": 1,
    "ultima_fechada": {
      "id": "9c2a...",
      "titulo": "Aprovação do orçamento 2026",
      "participacao_pct": 72,
      "fechada_em": "2026-06-30T18:00:00+00:00"
    }
  },
  "assembleias": {
    "proximas": [
      {"id": "abc...", "titulo": "AGA Ordinária 2026", "data": "2026-09-15", "tipo": "ordinaria"}
    ]
  }
}
```

## Response 401

Sem token / token inválido / conta não activa.

```json
{"detail": "Não autenticado"}
```

## Regras de conteúdo (tripwire PII)

O payload **não** contém, em nenhum nível:
- `email`, `phone`, `member_id`, `name`, `cpf`, `password`, `photo_url`, `address`
- lista de transações individuais
- lista de nomes de sócios
- lista de atos com detalhes
- detalhes de deliberações ou votos por eleitor

Os únicos `id`s expostos são de objectos referenciados **institucionalmente**:
`votacoes.ultima_fechada.id` (opcional) e `assembleias.proximas[].id`, ambos já
acessíveis a qualquer autenticado nas rotas correspondentes.

## Rate limit

Herda o default de `slowapi` (200/min por IP).

## Compatibilidade

- **Novo endpoint aditivo** — não altera nenhum contrato existente.
- Endpoints antigos (`/api/stats`, `/api/finances/summary`, `/api/finances/dre`,
  `/api/atos`) mantêm-se **exactamente iguais**, com os seus gates originais. Continuam
  a ser usados por `/financeiro` no frontend.
