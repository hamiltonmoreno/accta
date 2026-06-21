# Phase 1 — Data Model: Comunicados Segmentados (v2)

Entidades, campos, validações e transições de estado. Tudo aditivo sobre a
colecção `comunicados` existente (PostgreSQL/jsonb via DAO). Datas = strings
ISO-8601. Sem `_id` real; `id = str(uuid4())`.

---

## 1. AudienceFilter (modelo Pydantic NOVO)

Estrutura tipada com sub-conjuntos opcionais. Pelo menos um preenchido.
Composição: **OR dentro do tipo, AND entre tipos** (FR-014, ver research R2).

| Campo | Tipo | Notas |
|-------|------|-------|
| `cargos` | `list[str]` = `[]` | keys canónicas de `governance.py` (ex. `dir_tesoureiro`), nunca labels |
| `orgaos` | `list[str]` = `[]` | keys canónicas **aceites por `helpers.members_of_orgao`**: `direcao` / `mesa_ag` / `conselho_fiscal` (FR-012). ⚠ A key da Assembleia Geral é **`mesa_ag`** (Mesa da AG: Presidente/VP/Secretário) — NÃO `assembleia_geral`, que devolveria `None` → fallback silencioso p/ admins. O atalho "Órgão: Assembleia Geral" resolve para a **Mesa da AG**; o plenário completo (todos os votantes) obtém-se por `categorias`/`statuses`, não por este atalho. |
| `categorias` | `list[str]` = `[]` | `fundador` / `ordinario` / `honorario` (de `MEMBER_CATEGORIES`) |
| `statuses` | `list[str]` = `[]` | subconjunto de `ativo`/`inativo`/`pendente_convite`/`pendente_aprovacao`/`rejeitado`; vazio ⇒ default `["ativo"]` |
| `joined_after` | `Optional[str]` | data ISO; `admission_date >= joined_after` |
| `joined_before` | `Optional[str]` | data ISO; `admission_date <= joined_before` |
| `nominal_member_ids` | `list[str]` = `[]` | `member_id` (ex. `ACCTA-0042`) |
| `nominal_emails` | `list[str]` = `[]` | emails; OR interno com `nominal_member_ids` (um único tipo "nominal") |

**Validações** (Pydantic `model_validator`):
- pelo menos um sub-conjunto não vazio / data presente — senão `422`
- `cargos` ⊆ keys válidas de `governance.CARGO_KEYS`; `orgaos` ⊆ órgãos válidos;
  `categorias` ⊆ `MEMBER_CATEGORIES`; `statuses` ⊆ status válidos
- valores inválidos em `cargos`/`orgaos`/`categorias`/`statuses` → `422`
  (são enumerações fechadas); `nominal_*` inexistentes **não** são erro de
  validação — são tratados na resolução (ignorar + warning, ver edge cases)
- `joined_after <= joined_before` quando ambos presentes

---

## 2. Comunicado (documento — ESTENDIDO)

Campos existentes mantêm-se; novos campos a **negrito**. Documentos antigos
continuam válidos (campos novos são opcionais/derivados no envio).

| Campo | Tipo | Origem |
|-------|------|--------|
| `id` | str (uuid) | existente |
| `subject` | str | existente |
| `body` | str | existente |
| `tipo` | `oficial`\|`informativo` | existente |
| `channels` | `list[in_app\|email]` | existente |
| `segment` | dict (legado) | existente — mantido p/ gatilhos de governança |
| **`audience_filter`** | dict (AudienceFilter) \| null | **NOVO** — definição original (FR-004a) |
| **`audience_resolved`** | `list[str]` (member_id) \| null | **NOVO** — snapshot no envio (FR-004b) |
| `recipients_total` / **`recipients_count`** | int | existente / **alias explícito no doc** |
| `inapp_created`, `email_sent`, `email_failed` | int | existente |
| **`failed_member_ids`** | `list[str]` | **NOVO** — quem falhou no email (FR-013) |
| **`dry_run`** | bool = False | **NOVO** (FR-009) |
| `notification_type`, `cta_label`, `cta_url` | str/opt | existente |
| `status` | enum (ver §4) | existente + valores novos |
| `source_kind`, `source_ref_id` | str/null | existente (gatilhos auto) |
| `created_by`, `created_at`, `sent_at`, `error` | str/null | existente |

**Invariante**: um comunicado v2 tem `audience_filter != null` e `segment` pode
ser `null`/ausente; um comunicado legado/auto tem `segment` e `audience_filter
== null`. A resolução escolhe o caminho conforme qual está presente.

---

## 3. ComunicadoCreate (modelo Pydantic — ESTENDIDO)

| Campo | Tipo | Notas |
|-------|------|-------|
| `subject`, `body`, `tipo`, `channels`, `cta_label`, `cta_url`, `notification_type` | (existentes) | inalterados |
| `segment` | `Optional[ComunicadoSegment]` | passa a **opcional** (era obrigatório) |
| **`audience_filter`** | `Optional[AudienceFilter]` | **NOVO** |
| **`dry_run`** | bool = False | **NOVO**; só honrado se `IS_PROD` falso (R7) |

**Validação**: exactamente um de `segment` / `audience_filter` presente
(`model_validator`). Mantém o caminho legado funcional sem ambiguidade.

---

## 4. Estados e transições (status — ADITIVO)

`COMUNICADO_STATUSES` estende para:
`["rascunho", "a_enviar", "enviando", "enviado", "parcial", "falhado", "cancelado"]`
(novos: `rascunho`, `cancelado`; `enviado_parcial` da spec ≡ `parcial`, R5/D3).

```text
            (D2: se rascunho confirmado)
  rascunho ──enviar──► a_enviar ──claim(CAS)──► enviando
     │                                              │
     │ DELETE (FR-011)                              ├─► enviado        (sem falhas)
     ▼                                              ├─► parcial        (algumas falhas de email)
  cancelado  (imutável)                             └─► falhado        (todas falham / excepção)

  enviado / parcial / falhado / cancelado  ── imutáveis (histórico) ──
```

- `rascunho`→`cancelado` via `DELETE /comunicados/{id}` (só em `rascunho`).
- `rascunho`→`a_enviar` via envio; daí o `dispatch` (CAS já existente
  `a_enviar→enviando`, idempotente).
- `dry_run=true`: o doc fica `enviado` (com `dry_run` flag) mas sem email/in-app.
- Estados terminais são imutáveis (FR-011).

> Se **D2** decidir "sem rascunho", remove-se `rascunho`/`cancelado` e o create
> entra directo em `a_enviar` (como hoje), mantendo só os campos de audiência.

---

## 5. AuditLog `comunicado_enviado` (entrada — usa tabela existente)

`audit_logs.details` inclui: `comunicado_id`, `audience_filter` (definição),
`recipients_count`, `recipients_sample` (≤5 nomes), `dry_run`. **Nunca** a lista
completa (FR-005) — essa vive em `comunicados.audience_resolved`. Acção
registada via `create_audit_log(author_id, "comunicado_enviado", comunicado_id,
request=request, details={...})`.

> Nota: o código actual usa a acção `"enviar_comunicado"`. A spec usa
> `"comunicado_enviado"`. **Alinhar para `comunicado_enviado`** (a spec e os
> Success Criteria SC-003 referem essa string para consulta de auditoria);
> registar em `tasks.md` que SC-003 depende deste nome.

---

## 6. Índices (em `ensure_schema()` — só lá, nunca nas rotas)

Existentes já cobrem `created_at`, `status`, `created_by`, `source`. Avaliar
adicionar (se o histórico filtrar por autor+estado com volume): nenhum índice
novo é necessário para a resolução de audiência (in-memory sobre `users`
activos). **Decisão**: sem índice novo nesta fase; reavaliar se o histórico
crescer. A filtragem de `users` reusa a leitura existente de `_base_members`.

---

## 7. Entidade derivada — Destinatário

Não persistida. Vista derivada de `users` (excluindo `account_type=technical`)
que casa o `AudienceFilter` no momento da resolução. Campos usados:
`id`, `name`, `email`, `member_id`, `cargo`, `member_category`, `status`,
`admission_date`, `email_opt_out_informativos`, `account_type`. Projeção
`_MEMBER_PROJECTION` estende-se com `status`, `member_id`, `admission_date`.
