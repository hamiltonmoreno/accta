# Data Model — Funções personalizadas (017)

## Coleção nova: `custom_roles`

Tabela `(pk bigserial, doc jsonb)` criada por `ensure_schema()` ao acrescentar `"custom_roles"` a `COLLECTIONS` (`backend/database.py`). Sem índices dedicados (escala de unidades).

| Campo | Tipo | Regras |
|---|---|---|
| `id` | str (uuid4) | gerado pela app, padrão do projeto |
| `name` | str | obrigatório, 1–60 chars; único após normalização (trim + casefold); não pode colidir com os rótulos das 4 funções fixas (Administração/Admin, Financeiro, Moderador, Sócio) nem com as keys `admin/financeiro/moderador/socio` |
| `description` | str \| null | opcional, ≤200 chars |
| `privileges` | list[str] | obrigatório, ≥1, cada item ∈ `governance.PRIVILEGES` (12 canónicos); sem duplicados |
| `created_by` | str | id do admin criador |
| `created_at` | str ISO-8601 | na criação |
| `updated_at` | str ISO-8601 | em cada edição |

**Estados**: sem máquina de estados — a função existe ou não. A eliminação é bloqueada (409) enquanto `user_count > 0`.

## Campo aditivo em `users`

| Campo | Tipo | Regras |
|---|---|---|
| `custom_role_id` | str \| null | referência viva a `custom_roles.id`; `None`/ausente = utilizador sem função personalizada (comportamento atual, 100% retrocompatível) |

**Invariante (D3/FR-004)**: quando `custom_role_id` está definido ⇒ `role == "socio"` e `privileges == custom_roles[custom_role_id].privileges` (materializados). Mantido por:
- atribuição (`PATCH /users/{id}` com `custom_role_id`): escreve os 3 campos juntos;
- edição da função (`PATCH /admin/custom-roles/{id}`): propaga `privileges` por `update_many({"custom_role_id": id})`;
- destaque: qualquer escrita explícita de `role`/`privileges` (edição manual, predefinições de cargo, `/admin/cargos`, proclamação de eleição) limpa `custom_role_id`.

## Modelos Pydantic (`backend/models.py`)

- `CustomRole` (resposta): id, name, description, privileges, created_by, created_at, updated_at (+`user_count` calculado na listagem)
- `CustomRoleCreate`: name, description?, privileges (validação ≥1 ⊆ PRIVILEGES)
- `CustomRoleUpdate`: name?, description?, privileges? (todos opcionais; mesmo validador)
- `UserBase`: `+ custom_role_id: Optional[str] = None` (aditivo — não parte docs existentes)
- `UserAdminUpdate`: `+ custom_role_id: Optional[str] = None`
- `InviteCreate`: `+ custom_role_id: Optional[str] = None`

Datas sempre string ISO (regra do projeto); `password`/segredos nunca em respostas (não aplicável aqui).

## Relações

```
custom_roles 1 ──── n users (via users.custom_role_id, ligação viva)
```

- `custom_roles.privileges` ⊆ `governance.PRIVILEGES` (catálogo canónico; privilégio desconhecido em doc antigo é ignorado na apresentação, sem quebrar o resto).
- Sem relação com `cargo`/`cargo_history` — cargos estatutários têm precedência e destacam a função (D5).
