# Contract: POST /api/comunicados/preview-audience

Calcula a audiência de um `AudienceFilter` **sem enviar nada**. Partilha a
lógica de resolução com o envio (paridade — assumption da spec). Suporta
FR-002, FR-003, FR-014 e os edge cases de preview.

## Auth

- `Authorization: Bearer {token}` obrigatório.
- RBAC à entrada: `has_role_or_privilege(user, ("admin",), "send_comunicados")`
  (+ `comunicar_intra_orgao` se D1 confirmar US4). Sem privilégio → **403**
  `{"detail": "Sem permissão"}`.

## Request

```json
{
  "tipo": "informativo",                 // oficial | informativo
  "channels": ["in_app", "email"],
  "audience_filter": {
    "cargos": ["dir_tesoureiro"],
    "orgaos": ["direcao"],
    "categorias": ["ordinario"],
    "statuses": ["ativo"],
    "joined_after": "2023-01-01",
    "joined_before": "2024-12-31",
    "nominal_member_ids": ["ACCTA-0042"],
    "nominal_emails": []
  }
}
```

- `audience_filter` valida como em data-model §1 (pelo menos um critério;
  enums fechadas validadas → **422** se inválido).
- `orgaos[]` aceita **só** as keys `direcao` / `mesa_ag` / `conselho_fiscal`
  (as que `helpers.members_of_orgao` reconhece; `assembleia_geral` é inválido e
  daria 422 — a Assembleia Geral é a key `mesa_ag`).

## Response 200

```json
{
  "recipients_count": 12,
  "sample": ["Ana Silva", "João Lopes", "Maria Brito", "Rui Tavares", "Zé Pina"],
  "more": 7,
  "per_type_counts": { "cargos": 5, "orgaos": 8, "categorias": 40, "nominal": 2 },
  "intersected_count": 12,
  "warnings": [
    { "code": "intersection_reduced", "below": "categorias" },
    { "code": "nominal_not_found", "values": ["ACCTA-9999"] },
    { "code": "technical_excluded", "member_ids": ["ACCTA-0007"] },
    { "code": "includes_unapproved", "statuses": ["pendente_aprovacao"] }
  ]
}
```

| Campo | Significado |
|-------|-------------|
| `recipients_count` | total de sócios reais após intersecção + exclusão de `technical` |
| `sample` | até 5 nomes (FR-002b) |
| `more` | `recipients_count - len(sample)` (FR-002c, "…mais N") |
| `per_type_counts` | contagem por tipo de critério, **antes** da intersecção (FR-014) |
| `intersected_count` | = `recipients_count`; explicita a redução AND |
| `warnings[]` | ver tabela de códigos abaixo |

### Códigos de warning

| `code` | Quando | Campos |
|--------|--------|--------|
| `intersection_reduced` | contagem após intersecção < contagem do tipo mais restritivo (FR-014) | `below` |
| `nominal_not_found` | `member_id`/email da lista nominal não existe (ignorado) | `values` |
| `technical_excluded` | conta `technical` resolvida (ex. via nominal) foi excluída (FR-003) | `member_ids` |
| `includes_unapproved` | filtro inclui `pendente_aprovacao`/não-aprovados (US3-AS2) | `statuses` |

## Notas

- `recipients_count == 0` **não** é erro aqui (preview informativo). O bloqueio
  é no envio (ver create-comunicado / FR-006).
- Sem efeitos colaterais: não persiste, não escreve audit log, não envia.
- Idealmente debounced no frontend (já há `useDebounced`).
