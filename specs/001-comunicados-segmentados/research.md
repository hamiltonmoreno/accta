# Phase 0 — Research & Decisions: Comunicados Segmentados (v2)

Resolve as incógnitas técnicas e regista as decisões fundadas no código actual
(módulo `comunicados`, PR #113). Cada decisão: **Decision / Rationale /
Alternatives considered**. Os itens **D1–D3** são decisões de produto que a
spec defere ao dono — têm recomendação mas exigem confirmação antes de
`/speckit-implement`.

---

## R1 — Onde vive a resolução de audiência

**Decision**: Adicionar `resolve_audience(audience_filter, *, channel, tipo)` em
`backend/comunicados_service.py`, ao lado do `resolve_recipients(segment, ...)`
existente. O `_base_members()` actual filtra `status=ativo` + exclui
`account_type=technical`; o v2 precisa de uma base mais larga quando há filtro
de `status`, por isso introduz-se `_filter_base(statuses)` que parametriza o
status (default `["ativo"]`) mas **mantém sempre** a exclusão de `technical`.

**Rationale**: a paridade preview↔envio (assumption da spec) exige que ambos
chamem a mesma função. Reutiliza projeção `_MEMBER_PROJECTION` (estende com
`status`, `member_id`, `admission_date`).

**Alternatives considered**: (a) resolver no endpoint — rejeitado, duplica
lógica e quebra paridade; (b) query DAO composta com `$and`/`$or`/`$in` por
critério — viável, mas a regra AND-entre-tipos + a resolução órgão→cargos
(que já é uma chamada async) ficam mais legíveis e testáveis em memória sobre o
universo de ~200 sócios. In-memory é simples e suficiente à escala.

---

## R2 — Regra de composição OR-dentro / AND-entre (FR-014)

**Decision**: `resolve_audience` constrói, para cada tipo de critério
**preenchido**, o conjunto de `id`s que casam (OR dentro do tipo) e faz a
**intersecção** desses conjuntos (AND entre tipos). Tipos:

- `cargos[]` → `u.cargo in cargos`
- `orgaos[]` → união de `helpers.members_of_orgao(o)` para cada `o` (FR-012).
  **Keys aceites: `direcao`/`mesa_ag`/`conselho_fiscal`** (a key da AG é
  `mesa_ag`, não `assembleia_geral` — esta última cairia no fallback de admins).
  O `AudienceFilter.orgaos` valida contra exactamente estas três keys.
- `categorias[]` → `u.member_category in categorias`
- `statuses[]` → base alargada a esses status (ver R1)
- `joined_after` / `joined_before` → `joined_after <= u.admission_date <= joined_before`
  (comparação de strings ISO; `admission_date` ausente ⇒ não casa o critério de
  período — ver R6)
- `nominal_member_ids[]` + `nominal_emails[]` → `u.member_id in ids OR u.email in emails`
  (um único tipo "nominal", OR interno entre ids e emails)

Critérios não preenchidos não entram na intersecção. **Pelo menos um** tipo tem
de estar preenchido (validação Pydantic). A exclusão de `technical` é aplicada
**depois** da intersecção, incondicionalmente (FR-003).

**Rationale**: corresponde exactamente a FR-014 e ao edge case da lista nominal
não ser escape-hatch aditivo. A intersecção de sets é O(n) à escala.

**Alternatives considered**: lista nominal como união aditiva (escape hatch) —
**rejeitado explicitamente pela spec** (FR-014: nominal é um tipo, AND como os
outros).

---

## R3 — Preview: forma da resposta (FR-002, FR-014, edge cases)

**Decision**: `POST /comunicados/preview-audience` recebe um `AudienceFilter` +
`tipo` + `channels` e devolve:

```json
{
  "recipients_count": 12,
  "sample": ["Ana Silva", "João Lopes", "..."],   // até 5 nomes
  "more": 7,                                        // count - len(sample)
  "per_type_counts": { "cargos": 5, "categorias": 40, "nominal": 2 },
  "intersected_count": 12,
  "warnings": [
    {"code": "technical_excluded", "member_ids": ["ACCTA-0007"]},
    {"code": "nominal_not_found", "values": ["ACCTA-9999"]},
    {"code": "intersection_reduced", "below": "categorias"},
    {"code": "includes_unapproved", "statuses": ["pendente_aprovacao"]}
  ]
}
```

- `per_type_counts` + `intersected_count` materializam o requisito de FR-014 de
  mostrar "contagem por tipo + contagem após intersecção".
- `warnings` cobre os edge cases: technical excluída via nominal (FR-003),
  nominal inexistente (ignorar+avisar), redução por intersecção (FR-014),
  e aviso de contas não aprovadas (US3-AS2).
- `recipients_count == 0` não é erro **no preview** (mostra-se o aviso); o
  **bloqueio** é no envio (FR-006).

**Rationale**: o preview é informativo e tem de explicar a redução AND; o
bloqueio pertence ao submit. Partilha `resolve_audience` (paridade).

**Alternatives considered**: estender o `POST /comunicados/recipients/count`
existente — possível, mas o count actual devolve só inteiros por canal; um
endpoint novo dedicado é mais limpo e não altera o contrato legado usado pelo
compositor v1. Mantemos `recipients/count` para retrocompatibilidade.

---

## R4 — Snapshot da audiência resolvida (FR-004, FR-010)

**Decision**: o `dispatch_comunicado` já resolve no envio (FR-010 ✓). Estende-se
para, **após** resolver, persistir no doc: `audience_resolved` (lista de
`member_id` reais notificados — união dos canais), `recipients_count`,
`failed_member_ids` (do resultado de email). O `audit_logs` `comunicado_enviado`
guarda `audience_filter` + `recipients_count` + `recipients_sample` (≤5) +
`dry_run` — **nunca** a lista completa (FR-005); a lista completa vive no doc.

**Rationale**: separa "registo auditável leve" (audit log) de "snapshot
completo" (doc), exactamente como FR-005/edge-case `recipients_sample` pede.
`member_id` é estável/imutável → snapshot resiste a mudanças de cargo (US2-AS3).

**Alternatives considered**: snapshot de `id` (uuid) em vez de `member_id` —
`member_id` é o identificador institucional estável preferido pela spec;
guardamos `member_id` (e podemos manter `id` interno se necessário para
re-tentativa). Decisão: snapshot por `member_id`.

---

## R5 — Reconciliação do vocabulário de status (D3)

**Decision (recomendada, confirmar)**: estender aditivamente
`COMUNICADO_STATUSES = ["a_enviar","enviando","enviado","parcial","falhado"]`
para incluir `"rascunho"` e `"cancelado"`. O `enviado_parcial` da spec
**mapeia para o `parcial` existente** (sem novo valor, sem rename). Tabela de
correspondência spec→código:

| Spec | Código (existente/novo) |
|------|--------------------------|
| `rascunho` | `rascunho` (NOVO) |
| `enviado` | `enviado` (existe) |
| `enviado_parcial` | `parcial` (reutiliza) |
| `cancelado` | `cancelado` (NOVO) |

**Rationale**: constituição STOP #5 — não quebrar docs existentes. Reutilizar
`parcial` evita migração e mantém o `dispatch` intacto. Aditivo é seguro.

**Alternatives considered**: renomear `parcial`→`enviado_parcial` — rejeitado
(migração destrutiva de docs em prod + toca o dispatch testado).

---

## R6 — Campo de data de filiação (`joined_after`/`joined_before`)

**Decision**: o filtro de período mapeia para `users.admission_date` (string
ISO-8601, já existente). `admission_date` é definido na aprovação
(`routes/admin.py`, `routes/participacao.py`) e pode ser `None` para contas
antigas ou em signup (`auth_routes.py:202`). **Regra**: se um filtro de período
está activo e `admission_date` é `None`, o sócio **não casa** o critério de
período (conservador — não notificar quem não tem data conhecida quando o autor
pediu explicitamente um intervalo). Mostrar contagem; sem aviso dedicado nesta
versão.

**Rationale**: comparação de strings ISO é correcta para ordenação cronológica.
Conservador evita notificações indevidas. Sem janelas relativas (assumption).

**Alternatives considered**: tratar `None` como "sempre casa" — rejeitado
(notificaria sócios sem data quando o autor restringiu por data).

---

## R7 — Dry-run em não-produção (FR-009)

**Decision**: `ComunicadoCreate.dry_run: bool = False`. O envio só permite
`dry_run=True` quando `IS_PROD` (de `config.py`) é `False` — em produção,
`dry_run=True` é rejeitado/ignorado (não há razão para dry-run em prod). Com
`dry_run=True`: o dispatch resolve a audiência, persiste o doc + snapshot,
escreve audit log com `dry_run=true`, mas **não** chama `send_comunicado_batch`
nem `notify_users`. UI marca visualmente o modo dry-run.

**Rationale**: permite validar segmentação em staging sem enviar emails reais
(mitiga STOP #6). Reutiliza `IS_PROD` existente — sem variável nova (assumption).

**Alternatives considered**: variável `COMUNICADOS_DRY_RUN` dedicada — rejeitada
pela spec (usar `ENVIRONMENT` existente).

---

## R8 — Email legível por critério (FR-007)

**Decision**: gerar um rótulo legível do `AudienceFilter` server-side
(`describe_audience(filter) -> str`, PT) e passá-lo ao corpo/cabeçalho do email
("Para: Direcção", "Para: 12 sócios — Categoria ordinário admitidos antes de
2024"). O `comunicado_email_html` existente recebe um parâmetro opcional de
linha "Para:" ou injecta-se no topo do body.

**Rationale**: FR-007 exige critério legível, não lista de emails (privacidade).
A descrição deriva do filtro, não dos destinatários.

**Alternatives considered**: listar nomes no email — rejeitado (privacidade +
FR-007).

---

## D1 — Matriz de privilégios (OWNER DECISION — confirmar)

**Contexto**: o código usa hoje uma única privilege `send_comunicados`
(`routes/comunicados.py` → `has_role_or_privilege(user, ("admin",),
"send_comunicados")`). A spec (Assumptions §298–302, US4) sugere possivelmente
`comunicar_geral` (admin/Direcção) + `comunicar_intra_orgao` (Conselho Fiscal
→ Direcção).

**Recomendação**: manter `send_comunicados` como privilege de emissão geral
(admin + Direcção via overlay) e, **só se o dono quiser US4 neste ciclo**,
adicionar uma única overlay `comunicar_intra_orgao` + helper em
`permissions.py`, restringindo a audiência desse perfil a órgãos internos.
Não inventar uma matriz fina sem confirmação.

**Decisão**: ✅ **CONFIRMADO (2026-06-20)** — adicionar `comunicar_intra_orgao`.
Mantém-se `send_comunicados` para emissão geral (admin/Direcção) **e** adiciona-se
a overlay `comunicar_intra_orgao` + helper em `permissions.py` para o Conselho
Fiscal poder dirigir-se a órgãos internos (US4 entra neste ciclo).

**Grant path (U1, post-analyze)**: a privilege é uma overlay **aditiva**
atribuída **manualmente** via gestão de privilégios (Constituição III —
privileges são overlays `role OR privilege`), **não** auto-concedida por cargo.
`can_comunicar_intra_orgao(user) = user_can(user, "comunicar_intra_orgao")`.

**Âmbito permitido (U2, post-analyze)**: um autor que tem **só**
`comunicar_intra_orgao` (sem `send_comunicados`/admin) só pode enviar para
`audience_filter` com `orgaos ⊆ {direcao, mesa_ag, conselho_fiscal}` e **nenhum
outro tipo de critério** preenchido (cargos/categorias/statuses/período/nominal
vazios). Audiência fora deste âmbito → **403**. Autores `send_comunicados`/admin
não têm esta restrição.

---

## D2 — Ciclo de rascunho (OWNER DECISION — confirmar)

**Contexto**: o `create_comunicado` actual agenda o envio imediatamente (cria em
`a_enviar` → `dispatch`). US1-AS3 + FR-011 pedem um estado `rascunho` persistido
(guardar, voltar, editar, enviar **ou** cancelar/eliminar).

**Recomendação**: incluir `rascunho` (a spec é explícita). Fluxo: create com
`status="rascunho"` (sem dispatch) → editar (PATCH) → `POST
/comunicados/{id}/enviar` (resolve+dispatch) **ou** `DELETE /comunicados/{id}`
(só permitido em `rascunho`; `enviado`/`parcial`/`cancelado` imutáveis, FR-011).

**Decisão**: ✅ **CONFIRMADO (2026-06-20)** — incluir o ciclo de rascunho. Fluxo:
create `status="rascunho"` (sem dispatch) → `PATCH /comunicados/{id}` (editar) →
`POST /comunicados/{id}/enviar` (resolve+dispatch) **ou** `DELETE
/comunicados/{id}` (→ `cancelado`, só em `rascunho`; terminais imutáveis,
FR-011). UI ganha gestão de rascunhos.

---

## D3 — Reutilizar `parcial` para `enviado_parcial`

Ver **R5**. **Decisão**: ✅ **CONFIRMADO (2026-06-20)** — reutilizar `parcial`
(`enviado_parcial` ≡ `parcial`). Extensão aditiva só para `rascunho`/`cancelado`;
sem migração de docs, sem tocar o dispatch testado.

---

## Resumo das incógnitas

| Item | Estado |
|------|--------|
| Resolução de audiência / OR-AND (R1,R2) | ✅ resolvido |
| Forma do preview + warnings (R3) | ✅ resolvido |
| Snapshot + audit (R4) | ✅ resolvido |
| Status aditivo (R5 / D3) | ✅ resolvido + confirmado |
| Campo de período (R6) | ✅ resolvido |
| Dry-run (R7) | ✅ resolvido |
| Email legível (R8) | ✅ resolvido |
| Matriz de privilégios (D1) | ✅ confirmado — `+ comunicar_intra_orgao` (US4 entra) |
| Ciclo de rascunho (D2) | ✅ confirmado — incluir rascunho |

**Todos os gates D1–D3 confirmados pelo dono em 2026-06-20.** Nenhuma incógnita
técnica ou de produto fica por resolver — pronto para `/speckit-tasks`.
