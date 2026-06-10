# Sessão 2026-06-10 — Correções da revisão de código (/code-review sobre melhorias-pos-revisao)

Branch: `claude/code-review-analysis-auES1` (merge de `claude/melhorias-pos-revisao-auES1` + fixes).
Review: 7 ângulos × verificação — 6 findings sobreviveram (4 CONFIRMED, 2 PLAUSIBLE adiados).

## Plano

- [x] 1. **SSE slot leak** (`routes/notifications.py`) — slot reservado sincronamente só é
      libertado no `finally` do generator; generator nunca iterado (disconnect antes do
      1.º chunk / erro de middleware) ⇒ leak permanente ⇒ 429 até restart. Fix: slots com
      heartbeat + TTL (auto-expiram). Atualizar testes do cap.
- [x] 2. **Validação de role depois de `next_member_id()`** (`routes/admin.py`) — invite com
      role inválido consome `nextval('member_id_seq')` (gaps em ACCTA-XXXX). Fix: mover o
      check 422 para antes.
- [x] 3. **Duplicação do shape da petição** (`routes/participacao.py`) — listagem inline e
      `_peticao_view` constroem o mesmo dict em 2 sítios. Fix: extrair `_peticao_enriched`.
- [x] 4. **`_IS_PROD` duplicado** (`server.py` + `auth.py`) — fonte única em `config.py`
      (com `load_dotenv` idempotente); HSTS continua check dinâmico por-request (testável).
- [x] 5. Testes (pytest unit dos ficheiros tocados) + ruff.
- [x] 6. Commit + push + PR.

## Adiados (PLAUSIBLE, não bloqueiam)

- `listar_peticoes` materializa todas as assinaturas (`to_list(None)`) — aceitável à escala
  atual; migrar para pipeline `$group` se crescer.
- Whitelist de roles como `Literal` no `InviteCreate` — convenção atual do projeto é
  validação inline nas rotas com mensagens PT; dívida de consistência, não defeito.

## Review

- SSE: slots agora são `{slot_id: heartbeat}` com TTL 20s (4× o poll de 5s); o loop renova
  o heartbeat por iteração e `_sse_release` limpa no finally. Slots fantasma (generator
  nunca iterado) expiram sozinhos — novo teste `test_stale_slots_expire_and_do_not_lock_user_out`.
- `invite_user`: check 422 movido para antes do `next_member_id()` (nextval consome a
  sequência mesmo em pedidos inválidos).
- `participacao`: `_peticao_enriched` é o shape único usado pela listagem batch e pelo
  `_peticao_view` do detalhe.
- `config.py` novo: `IS_PROD` único, importado por `auth.py` e `server.py` (HSTS continua
  dinâmico por-request — o teste alterna ENVIRONMENT em runtime).
- Extra (CI vermelho pré-existente no branch): `gallery._recompute_cover_if_needed` agora
  tolera foto sem `album_id` (docs jsonb são schemaless) — `test_orphan_cleanup` verde.
- Verificação: `ruff check` limpo; `pytest -m unit` → **1249 passed, 0 failed**.
