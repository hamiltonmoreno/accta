# Plano — F4: Hardening do audit log

Spec: `tasks/spec-verificacao-seguranca-saas.md` §8.1 + §12 (F4). Branch
`feature/seguranca-f4-audit` (de `develop`). PR → `develop` (GitFlow).

## Decisões do dono (2026-05-26)
- **Profundidade**: delegada ("faz o mais adequado") → **tamper-evidence por HMAC**
  (deteta modificação), **não** hash-chain (evita reencaminhar as ~117 escritas
  de audit por um append serializado — quebraria o seam de teste e meteria
  concorrência no caminho mais quente; a resistência a *apagamento* pertence ao
  role da BD).
- **Retenção**: **manter indefinidamente** (sem purga) — trilho completo para
  não-repúdio. (É já o comportamento: `audit_logs` não está em `_TTL_PURGE`.)
- **D7 (sink)**: manter em **Postgres** (sem store externo — sem dependência nova).

## Estado prévio (verificado)
- A app **já é append-only**: `audit_logs` só tem `insert_one` (helpers) e `find`
  read-only (notifications). **Nenhuma rota apaga/altera** audit logs.
- `audit_logs` **não** é auto-purgado.

## Trabalho (feito)
- [x] `models.AuditLog`: + `entry_hash: Optional[str]=None` (aditivo).
- [x] `helpers.py`: `audit_entry_hash` (HMAC-SHA256, chave derivada do SECRET_KEY,
  normaliza pela via jsonb p/ casar no round-trip) + `verify_audit_entry`;
  `create_audit_log` grava `entry_hash` antes do insert (sem reencaminhar — seam
  `insert_one` intacto).
- [x] `routes/notifications.py`: `GET /api/audit-logs/verify` (admin/`view_audit_logs`)
  — reverifica todas as entradas, devolve `{ok, total, verified, legacy_unhashed,
  tampered_count, tampered_ids}`. Legadas sem hash = "não verificáveis", não
  adulteradas.
- [x] Testes `tests/test_audit_integrity.py`: hash determinístico/sensível;
  verify deteta adulteração; missing-hash=False; create grava hash verificável;
  endpoint sinaliza adulterada + conta legadas; 403 p/ não-admin.

## Hand-off ao operador (F5 / infra — NÃO código)
- [ ] **Revogar `DELETE`/`UPDATE` em `audit_logs` ao role da app** no
  Postgres/Supabase (o role da app só precisa de `INSERT`+`SELECT`). É a camada
  correta para a resistência a apagamento; o HMAC cobre a deteção de modificação
  como defesa-em-profundidade (e funciona mesmo que a restrição de role não seja
  aplicada).
- [ ] Documentar a **política de retenção = indefinida** no runbook.
- ⚠️ **Rotação do `SECRET_KEY` (D6/F5)** passa a invalidar a verificação dos
  HMAC dos audit logs existentes — registar no runbook como consequência da
  rotação (gate com o operador).

## Remediação da revisão (ultrareview PR #125)
- **bug_003 (normal) — evasão por remoção do hash**: quem escreve na BD pode
  alterar um campo E pôr `entry_hash=NULL` → a entrada cai em `legacy_unhashed`,
  não em `tampered`. Fix: `/verify` passa a exigir **`ok` = zero adulteradas E
  zero não-verificáveis** (a remoção do hash faz `ok=False`); docstrings/modelo
  corrigidos (a deteção isolada cobre forja/modificação-ingénua; a resistência
  completa exige revogar **UPDATE**+DELETE no role da BD — F5).
- **bug_001 (normal) — `/verify` carregava a tabela toda + bloqueava o event
  loop**: fix → itera em **lotes de 1000** com `await asyncio.sleep(0)` entre
  lotes (memória limitada + cede o loop).
- **bug_010 (nit) — round-trip de floats ≥1e16 em `details`**: documentado em
  `audit_entry_hash` (fora do alcance do domínio: montantes CVE/contagens). Sem
  coerção numérica (o fix robusto exigiria validação contra Postgres real —
  desproporcionado para um nit).

## Verificação
- [x] `ruff` limpo; `tests/test_audit_integrity.py` (8, incl. evasão) verde.
- [x] suite unit completa **925 passed, 0 regressões** (`-m unit`).
- Sem mudança Pydantic não-aditiva, sem emails, sem tocar `main`.
