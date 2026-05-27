# Plano — Ranking de Atuação do Sócio

Spec: `tasks/spec-ranking-socio.md`. Branch `feature/ranking-socio` (de `develop`, GitFlow).
Feature GRANDE, faseada (F0–F5), PRs pequenos. Aditivo — sem migração destrutiva.

## Decisões fechadas com o dono (2026-05-26)
- **D1 Visibilidade**: default `all_members` (configurável em `ranking_settings`).
- **D2 Opt-out**: SIM — `ranking_opt_out` (aditivo, default false) em `UserBase`.
- **D3 status=inativo**: incluído, marcado "inativo"; fora do Top-N do dashboard.
- **D4 Pesos**: os propostos §3.1 (AGA 10 · eleição 8 · projeto 6 · voto 5 · evento 4 ·
  tarefa 4 · post 3 · foto 2 · comentário 1 · like 0.5; cap likes 50), afináveis via settings.
- **D5 Documentos acedidos** como sinal → FORA. **D6 Rebuild** → manual (MVP) + `scripts/`
  para cron depois. **D7 Notif Top-3** → OFF. **D8 Períodos** → ano civil + "all".
  **D9 Arrumação** → `member_scores` cache materializada; pessoal ao vivo.

## F0 — Fundação ✅
- [x] `backend/ranking.py`: `DEFAULT_WEIGHTS`/`MAX_LIKE_POINTS`/`SIGNAL_KEYS`;
      `_period_bounds`/`_date_match` (ano civil vs "all"); `voter_hash` (comparência
      sem tocar boletins, §3.3); `gather_signal_counts` (contagens por sinal +
      filtro de período; `include_turnout` para report); `_adjustments_total`;
      **`compute_member_score`** (fonte única: soma ponderada + cap likes + ajustes).
- [x] `database.py`: + `member_scores`/`ranking_ajustes`/`ranking_settings` em
      COLLECTIONS; índices (`ux_mscores_user_period`, `ix_mscores_period_rank`,
      `ix_rajustes_user_period`, `ix_rajustes_created`).
- [x] `routes/report.py`: reusa `gather_signal_counts(uid,"all",include_turnout=False)`
      — **contrato inalterado** (não-regressão testada).
- [x] `tests/conftest.py`: patch a `ranking.db`.
- [x] `tests/test_ranking.py`: período, score (pesos/cap/ajustes ±/pesos custom),
      `gather_signal_counts` (agregação + filtro + comparência por hash sem boletins),
      `_adjustments_total`, não-regressão do `report.personal`. **16 novos testes.**
- [x] Verificação: suíte unit **943 passed**, 0 regressões; ruff limpo.

## F1 — Score pessoal ao vivo ✅
- [x] `ranking.py`: `load_settings` (doc fundido com defaults) + `DEFAULT_SETTINGS`.
- [x] `routes/ranking.py`: `GET /ranking/me` (score+breakdown ao vivo; `rank`/`total`
      do snapshot `member_scores` se existir, senão `None`) + registo do router.
- [x] `api.js`: `rankingAPI` (grupo completo §8.4); `queryClient`: keys `ranking`.
- [x] `DashboardPage`: cartão "A Minha Participação" com cabeçalho de score+posição
      (+medalha Top-3 neutro/Carmesim) e `+N pts` por tile pontuado.
- [x] Testes: 4 novos (`/me` ao vivo, rank do snapshot, período default, pesos do
      doc) — `test_ranking.py` **20 passed**; eslint 0 erros; `craco build` OK.

## Achados da revisão F0+F1 (2026-05-26)
- ✅ N3 corrigido: tally de likes usa `to_list(None)` (preserva report.personal unbounded).
- ⏳ **F2**: o índice `ix_mscores_period_rank` ordena `rank` como TEXTO; o `_order_by`
  do DAO faz cast numérico em runtime que não casa com o índice → ao implementar o
  `sort("rank")` do leaderboard, validar plano/índice (provável `(...)::numeric` ou
  ordenar por score desc) para evitar table scan. Sem impacto em F1 (só `find_one`).
- Aceites (sem ação): N1 (ficheiro sem acentos — consistência), N2 (1 request quando
  ranking off), N4 (`_period_bounds` aceita anos absurdos → 0 resultados, inofensivo).

## F2 — Snapshot + leaderboard + widget Top-N ✅
- [x] `models.py`: `RankingAjuste`/`RankingAjusteCreate`/`MemberScore`/
      `RankingSettings`/`RankingSettingsUpdate` (auto-contidos; **não** importam
      `ranking.py` — `ranking → auth → models` seria ciclo; defaults de pesos
      aplicados em runtime por `load_settings`).
- [x] `ranking.py`: `_eligible_members` (filtro canónico §2.3: técnicos fora;
      só `ativo`/`inativo`) + `rebuild_scores` (chama `compute_member_score` por
      membro — fonte única; ranking de competição com empates partilhados
      `1,2,2,4`; idempotente `delete_many`+`insert_many`; `last_rebuild_at` via
      find-then-update/insert — o DAO não tem `upsert`).
- [x] `routes/ranking.py`: `_can_manage_ranking` (admin|`is_direcao`; F4 junta
      `manage_ranking`), `POST /ranking/rebuild` (RBAC+audit `ranking_rebuilt`),
      `GET /ranking/leaderboard` (sort `rank` asc, paginado, linha do próprio,
      **breakdown removido das linhas públicas** §2.5, **short-circuit quando
      `enabled=False`**).
- [x] `DashboardPage.js`: cartão "Ranking de Atuacao" Top-N (medalha Top-3
      neutro/Carmesim no #1, nome, cargo via `CARGO_LABELS_FALLBACK`, mini-barra
      proporcional, realce do próprio, `computed_at`); **inativos filtrados do
      Top-N (D3)**; `Skeleton`/`EmptyState`; query gated em `enabled`, `limit=50`.
- [x] Testes: rebuild (ranks/empates/idempotência/elegibilidade/vazio),
      leaderboard (entries+total+me, breakdown excluído, paginação clamp,
      disabled→vazio), RBAC rebuild (sócio/financeiro/moderador 403; admin +
      Direcção OK; audita). `test_ranking.py` **33 passed**; suíte unit 0
      regressões; ruff limpo; eslint 0 erros; `craco build` OK.

## Achados da revisão F2 (2026-05-27)
- ✅ **IMPORTANT #2 corrigido**: inativos apareciam no Top-N do dashboard
  (violava D3) → filtro `status !== 'inativo'` antes do slice + `limit=50`.
- ✅ **IMPORTANT #3 corrigido**: `enabled=False` agora curto-circuita o
  `/leaderboard` server-side (não servia a feature desligada a clientes diretos).
- ✅ **N2/N3/N4**: `limit=50` (cobre `top_n` até 50); +testes RBAC financeiro/
  moderador; comentário em `_wcoll`.
- ⏳ **IMPORTANT #1 (índice) — aceite sem ação, com fundamento**: o `_order_by`
  do DAO embrulha QUALQUER sort numérico num `CASE WHEN … THEN (col)::numeric END`
  — **nenhum** índice de expressão btree o satisfaz (nem `::numeric` nem `->`). O
  `ix_mscores_period_rank` serve o **filtro de igualdade** `period_key` (coluna
  líder); o sort é em memória sobre 1 linha por membro (centenas, DB ~vazia) →
  negligível. Um sort backed-by-index exigiria mudar o `_order_by` global (fora
  de âmbito, arriscado). Sem alteração de schema.
- **#4 (inline style na barra) — aceite**: `style={{ width: \`${pct}%\` }}` é o
  padrão existente (`PollResults.js`, `DRETab.js`) para barras proporcionais;
  alinhar com ele é o correcto.
- **N1 (acentos) — aceite**: `DashboardPage.js` é deliberadamente sem acentos
  (consistência; já aceite na revisão F0+F1).
- **N5 (N queries/membro no rebuild) — roadmap**: pré-agregação (um `$group`/
  colecção, §5) fica para quando houver volume; rebuild corre fora do request path.

## Fases seguintes (por fazer)
- **F3** página `/ranking` (pódio, tabela, período, pesquisa) + sidebar + rota.
- **F4** config admin/Direcção: `settings`/`adjustments` + privilégio `manage_ranking`.
- **F5** `ranking_opt_out` + `visibility=direcao_only` + `scripts/rebuild_ranking.py` (cron).

## Stop conditions
Não tornar público com efeito reputacional sem validação (default: Top-N + breakdown
privado + opt-out); não mudar contrato do `report.personal`; sem emails; push só para
`develop` (nunca `main`).
