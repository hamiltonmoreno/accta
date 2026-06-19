---
name: review-be-models-domain
description: Code review of models.py, governance.py, permissions.py, atos_rules.py, finance_joia.py — Pydantic validation, RBAC helpers, cargo keys, joia/quota rules
metadata:
  type: project
---

Review of the `be-models-domain` unit (models.py 2580L, governance.py 553L, permissions.py 110L, atos_rules.py 55L, finance_joia.py 76L).

**Key findings:**

1. `AtoSign.decisao: str` — no Literal; validated only in the route (`ATO_DECISOES`). Route check is correct but model-level Literal would provide 422 before route code runs.

2. `SancaoCreate.perda_direitos_ate: Optional[str] = None` — no ISO-date validator. Value is persisted as `rights_suspended_until` in the user doc; governance.rights_suspended() falls back to lexicographic comparison for non-ISO strings (correctness risk).

3. `EleicaoCreate.mandato_inicio/mandato_fim: str` — no ISO-date validation at model OR route level. Garbage strings are silently stored.

4. `TransactionCreate.amount: float` and `InvoiceCreate.amount: float` — no `gt=0` bounds at model level. Route validates (`if data.amount <= 0: raise 400`), so finance route is safe, but inconsistent with `ProjectExpenseCreate.amount = Field(gt=0)`.

5. `is_mesa_ag()` uses `startswith("ag_")` string prefix while `is_assembleia_geral()` uses `orgao_of_cargo()`. They are equivalent now but diverge if a non-"ag_" key is added to ASSEMBLEIA_GERAL or vice versa. Maintainability: `is_mesa_ag` should delegate to `is_assembleia_geral`.

6. `UserAdminUpdate.role: Optional[str]` and `UserAdminUpdate.status: Optional[str]` — no Pydantic Literal. Route validates against ROLES_VALID and USER_STATUSES. Correct at runtime, but a 400 instead of 422 on invalid values.

7. `Token.user: User` — `User` inherits `UserBase` (no password field) + has `extra="ignore"`, so password from DB doc is correctly stripped on construction. No leak.

8. `AtoCreate.tipo: str` — no Literal; validated in route against ATO_TIPOS. Produces 400, not 422.

9. `AssembleiaCreate.data: str` — no ISO validator in model; route validates via `_parse_dt()` and raises 400. Route-level validation is present and correct.

**What is clean:**
- `User` with `extra="ignore"` correctly strips `password` and MFA secrets from DB docs.
- `governance.is_voting_member` correctly gates on account_type, status, member_category, rights_suspended.
- `atos_rules.evaluate_status` pure-function logic is correct (reject-on-any-rejection, count Direcao approvals).
- `finance_joia._qualified_more_than_months` month-boundary arithmetic is correct (strictly more than 4 months).
- All cargo keys are persisted as canonical keys (not labels) throughout.
- `normalize_cargo` lookup is case-insensitive and handles legacy aliases correctly.
- `privileges_for_cargo("dir_presidente")` correctly expands "ALL" to full list.

**Why it matters:** SancaoCreate date gap means a bad perda_direitos_ate value results in incorrect rights_suspended evaluation (lexicographic fallback). EleicaoCreate date gap means stored mandato_inicio/fim could be non-parseable, breaking any date math downstream.
