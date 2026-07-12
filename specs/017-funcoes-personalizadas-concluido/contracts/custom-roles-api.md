# API Contract — /api/admin/custom-roles (017)

Todos os endpoints: header `Authorization: Bearer {token}`; guard `role == "admin"` (403 caso contrário; 401 sem token). Erros com `detail` em PT. Audit log em todas as escritas.

## GET /api/admin/custom-roles

Lista as funções personalizadas com contagem de utilizadores.

**200**:
```json
{
  "custom_roles": [
    {
      "id": "uuid",
      "name": "Coordenador de Eventos",
      "description": "Gere eventos e documentos",
      "privileges": ["manage_events", "manage_documents"],
      "created_by": "uuid-admin",
      "created_at": "2026-07-02T12:00:00+00:00",
      "updated_at": "2026-07-02T12:00:00+00:00",
      "user_count": 2
    }
  ]
}
```
`user_count` calculado numa única passagem sobre `users` (sem N+1).

## POST /api/admin/custom-roles

**Body** (`CustomRoleCreate`):
```json
{ "name": "Coordenador de Eventos", "description": "opcional", "privileges": ["manage_events", "manage_documents"] }
```

- **201/200**: doc criado (formato acima, `user_count: 0`)
- **400**: nome duplicado (após trim+casefold) OU colide com função fixa → `"Já existe uma função com este nome"`
- **422**: `privileges` vazio, com duplicados ou fora do catálogo; `name` vazio/>60; `description` >200

Audit: `custom_role_created` (details: name, privileges).

## PATCH /api/admin/custom-roles/{id}

**Body** (`CustomRoleUpdate`, campos opcionais): `name?`, `description?`, `privileges?`

- **200**: doc atualizado. Se `privileges` mudou: propaga `update_many({"custom_role_id": id}, {"$set": {"privileges": novos}})` e notifica cada afetado (`create_notification` tipo `profile_updated`, link `/perfil`). Resposta inclui `propagated_to: <n>`.
- **404**: função inexistente
- **400/422**: mesmas validações do POST

Audit: `custom_role_updated` (details: before/after de name/privileges, propagated_to).

## DELETE /api/admin/custom-roles/{id}

- **200**: eliminada (só possível com 0 utilizadores)
- **409**: em uso → `"Função atribuída a N sócio(s). Retire a função antes de eliminar."`
- **404**: inexistente

Audit: `custom_role_deleted` (details: name).

## Alterações a endpoints existentes (aditivas)

### PATCH /api/users/{user_id} (`UserAdminUpdate + custom_role_id`)

- Payload com `custom_role_id: "<uuid>"` → valida existência (400 se não existir) e escreve `role="socio"`, `privileges=<da função>`, `custom_role_id` (precedência sobre `role`/`privileges` no mesmo payload).
- Payload com `role` e/ou `privileges` explícitos sem `custom_role_id` → comportamento atual + limpa `custom_role_id` se o utilizador tinha um (destaque).
- Audit/notificação: os já existentes (before/after inclui `custom_role_id` como campo sensível).

### POST /api/admin/invite (`InviteCreate + custom_role_id`)

- `custom_role_id` opcional; se presente, valida existência e o convidado nasce `role="socio"` + privilégios materializados + `custom_role_id`. O contrato existente (422 para role desconhecida; `role=admin` aceite — decisão spec 016) mantém-se intocado.

### Fluxos de cargo (sem mudança de contrato)

`/admin/cargos` promote/demote/transfer e proclamação de eleições passam a limpar `custom_role_id` ao escrever role/privileges (destaque D5). Sem alteração de request/response.
