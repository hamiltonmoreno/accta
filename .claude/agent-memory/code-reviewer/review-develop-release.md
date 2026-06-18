---
name: review-develop-release
description: Findings from main→develop release-window review (255 files, ~3 weeks of PRs #129–#154). Key confirmed bugs and patterns to watch on next release.
metadata:
  type: project
---

Review of origin/main...origin/develop completed 2026-06-03.

**Key confirmed finding — btn-primary / index.css not updated (CRITICAL design)**
`.btn-primary` in `frontend/src/index.css:142` still renders `bg-carmesim` (#C7202F). PR #148 created `lib/buttonStyles.js` with `primaryBtn = bg-floresta` but did NOT update the legacy CSS class. New pages introduced in this window (Cat5: DefesaProfissionalPage, FormacoesPage, PublicacoesPage, RelacoesPage) use `btn-primary` for save/submit actions — all render red (Carmesim) instead of green (Floresta), contradicting the botoes-cor-acao spec.

Fix: change `index.css` line 142 `.btn-primary { @apply bg-floresta text-white hover:bg-floresta-dark ... }`.

**TOCTOU — All confirmed SOLID**
- `votar_deliberacao` + `apurar_deliberacao`: use `cast_assembleia_nominal_vote` / `cast_assembleia_ballot` which do `SELECT FOR UPDATE` + recheck in a single transaction (database.py). Also `pre_close` CAS pattern in `apurar_deliberacao` using `update_one({status:"aberta"})` — since DAO `update_one` itself uses `SELECT FOR UPDATE`, concurrent apurar calls are serialized. Confirmed correct.
- `votar` (eleicoes) + `apurar`: same pattern via `cast_ballot`.

**DAO correctness — `_safe_jsonb_key` added (good)**
`_safe_jsonb_key` validates jsonb key names before SQL interpolation with `re.fullmatch(r"[a-z_][a-z0-9_]*")`. Only used in `_cast_secret_ballot_locked`. The `_WhereBuilder._lit()` method handles general field interpolation safely via single-quote escaping.

**Audit log gap in atos.py (WARNING)**
`routes/atos.py` never imports `Request` and none of its `create_audit_log` calls pass `request=request`. The IP/UA columns will be NULL for all co-approval audit entries. This is a quality gap, not a security hole (the calls still log user_id, action, target_id).

**`encerrar_assembleia` non-CAS (WARNING, low risk)**
Line 1682: `update_one({"id": assembleia_id}, {"$set": {"status": "encerrada"}})` is called without filtering on current status, unlike `apurar_deliberacao`. Double-submit by Mesa is operationally low-risk but lacks the idempotency guard of the voting path.

**Why:** Botoes-cor-acao spec (PR #148) only created `lib/buttonStyles.js` and migrated explicit style strings in selected pages; it did not touch `index.css` and did not migrate pages that used the CSS class `.btn-primary`. The pages added after PR #148 (Cat5 F3 onwards) picked up the stale CSS class.
**How to apply:** On next release, check every new page for `btn-primary` class usage; require `bg-floresta` or `primaryBtn` from `lib/buttonStyles.js` instead.
