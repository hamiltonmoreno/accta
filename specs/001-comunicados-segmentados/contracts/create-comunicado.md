# Contract: POST /api/comunicados (estendido) + envio

Cria um comunicado segmentado. Estende o endpoint existente para aceitar
`audience_filter` (caminho v2) mantendo `segment` (caminho legado/auto).

> Depende de **D2** (ciclo de rascunho). Abaixo descreve-se o fluxo **com**
> rascunho (recomendado). Sem rascunho, `create` entra direto em `a_enviar`
> como hoje, e os endpoints PATCH/`/enviar`/DELETE colapsam num único POST.

## Auth

`Authorization: Bearer`. RBAC: `has_role_or_privilege(user, ("admin",),
"send_comunicados")` (+ `comunicar_intra_orgao` se D1). Sem privilégio → **403**.

## Request (criar)

```json
{
  "subject": "Reunião de Direcção — quinta 18h",
  "body": "Texto do comunicado…",
  "tipo": "informativo",
  "channels": ["in_app", "email"],
  "audience_filter": { "orgaos": ["direcao"] },
  "cta_label": null,
  "cta_url": null,
  "dry_run": false
}
```

**Validação**:
- exactamente um de `audience_filter` / `segment` (data-model §3) → senão **422**.
- `audience_filter` validado (data-model §1).
- `dry_run=true` só honrado se `IS_PROD` for falso (R7); em prod é ignorado/recusado.

## Response 201 (criar rascunho)

```json
{ "id": "uuid", "status": "rascunho" }
```

## Envio — POST /api/comunicados/{id}/enviar

Resolve a audiência **no momento do envio** (FR-010), persiste snapshot
(`audience_resolved`, `recipients_count`, `failed_member_ids`), dispara
in-app + email (ou simula se `dry_run`), e escreve audit log.

**Regras de envio**:
- **FR-006**: se a audiência resolvida = 0 destinatários → **422**
  `{"detail": "Filtro não selecciona nenhum sócio — revê os critérios"}`.
- **FR-003**: contas `technical` excluídas incondicionalmente.
- **FR-010**: re-resolve (cargos/status podem ter mudado desde o rascunho).
- **FR-004/005**: snapshot no doc; audit log `comunicado_enviado` com
  `audience_filter` + `recipients_count` + `recipients_sample` (≤5) + `dry_run`.
- CAS idempotente `a_enviar→enviando` (já existe no dispatch).
- `dry_run=true`: persiste + audit (com `dry_run=true`), **não** envia email
  nem cria notificações in-app.

**Response 200**:
```json
{
  "status": "enviado",            // enviado | parcial | falhado
  "recipients_count": 12,
  "inapp_created": 12,
  "email_sent": 11,
  "email_failed": 1,
  "failed_member_ids": ["ACCTA-0099"],
  "dry_run": false
}
```

## Histórico — GET /api/comunicados/{id} (estendido, FR-013)

Inclui: `status`, `created_by`, `created_at`, `sent_at`, `audience_filter`,
`audience_resolved`, `recipients_count`, `failed_member_ids`, `dry_run`.

## Erros

| Código | Caso |
|--------|------|
| 403 | sem privilégio (FR-008) |
| 422 | filtro inválido / nem segment nem audience_filter / 0 destinatários no envio (FR-006) |
| 404 | comunicado inexistente |
| 409 | tentar enviar/eliminar um comunicado em estado terminal (imutável, FR-011) |
