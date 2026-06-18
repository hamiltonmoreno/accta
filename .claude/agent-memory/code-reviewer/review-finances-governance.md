---
name: review-finances-governance
description: Findings from finances/governance backend review (finances.py, invoices.py, report.py, prestacao_contas.py, regulamentos.py, assembleias.py, eleicoes.py, sancoes.py, governance.py, atos.py, participacao.py)
metadata:
  type: project
---

## Critical finding (blocks merge)

**atos.py `sign_ato` — TOCTOU race on co-approval signatures (CONFIRMED 2026-06-18).** The read-modify-write pattern (find_one → check _has_signed → compute new array in Python → update_one $set) allows two concurrent signers to both pass the _has_signed check and the second update_one $set overwrites the first signature silently. Fix: atomic $push with filter `{"assinaturas": {"$not": {"$elemMatch": {"user_id": uid}}}}` or a DAO helper with FOR UPDATE (same pattern as cast_ballot).

**Why:** Lost-update under concurrent directors signing simultaneously. Silent data loss — ato may never reach "aprovado".

## Notable warnings (re-verified 2026-06-18)

- **participacao.py `_aplicar_honorario_eleito` (line 731-790):** `send_invite_email` is called synchronously AFTER the CAS commit (modified_count==0 guard). If the email throws, the caller gets a 500 but the nomeação is already "eleito" in the DB, leaving a new user account created with no invite email sent. Caller can't retry — retrying apurar_honorario hits the 409 guard. **CONFIRMED WARNING.**
- **participacao.py `apurar_honorario` (line 682):** votes are read from `user_votes` BEFORE the CAS update but AFTER `polls.update_one` closes the poll. A voter who submits between those two writes gets counted. Gap is small but non-zero. **WARNING (low probability, architectural).**
- **finances.py `compute_financial_summary` (lines 282-311):** `.limit(5000)` silently truncates. Larger associations will get wrong DRE totals with no error. **CONFIRMED WARNING.**
- **sancoes.py `decidir_sancao` (lines 201-212):** validates expulsion deliberation `aprovado=True` but NOT `tipo_maioria`. Spec §13 does not explicitly require a qualified majority for expulsion (unlike finance settings §14 which requires 3/4). The check enforces "approved deliberation exists" which covers the statutory gate. **CONFIRMED FALSE POSITIVE — no tipo_maioria requirement for expulsion in ACCTA statutes as implemented.**
- **regulamentos.py `list_regulamentos` (lines 109-117):** `GET /regulamentos` returns all regs including those with no approved version (status rascunho implied by missing current_version_id). get_regulamento also returns ALL versoes regardless of status. Non-manage socios see rascunho text. **CONFIRMED WARNING.**
- **eleicoes.py `_proclaim_list` (lines 474-575) and `proclamar`:** CAS is correct (apurada→proclamando, revert on exception, then →proclamada). Idempotency via eleicao_id check in cargo_history is correct. No per-user audit log on cargo transitions (only one bulk eleicao_proclamada entry). **CONFIRMED WARNING (missing per-user cargo audit trail).**

## Patterns confirmed good

- cast_ballot / cast_assembleia_ballot / insert_quotas_atomic / register_presenca_locked — all use FOR UPDATE in DAO.
- apurar (eleicoes) and proclamar use pre-close CAS (update_one with status filter, check modified_count==0) correctly.
- compute_dre_report / compute_financial_summary shared single source — correctly avoids DRE divergence.
- Finance settings monetary changes require AG deliberation with 3/4 majority and snapshot history.
- Secret ballot: receipt (voter_hash) and ballot (voto) in separate collections, ballot never carries user_id. Confirmed in eleicoes.py.
- sancoes.py `aplicar_sancao`: effects-before-CAS pattern (idempotent effects first, CAS final mark) is correct.

**How to apply:** When reviewing future atos/co-approval changes, verify atomic write pattern. When reviewing email calls after CAS commits, verify retry path exists or use BackgroundTask.
