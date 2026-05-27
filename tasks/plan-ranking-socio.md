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

## Fases seguintes (por fazer)
- **F2** modelos `RankingAjuste`/`MemberScore`/`RankingSettings` + `rebuild_scores` +
  `POST /rebuild` + `GET /leaderboard` + widget Top-N no dashboard.
- **F3** página `/ranking` (pódio, tabela, período, pesquisa) + sidebar + rota.
- **F4** config admin/Direcção: `settings`/`adjustments` + privilégio `manage_ranking`.
- **F5** `ranking_opt_out` + `visibility=direcao_only` + `scripts/rebuild_ranking.py` (cron).

## Stop conditions
Não tornar público com efeito reputacional sem validação (default: Top-N + breakdown
privado + opt-out); não mudar contrato do `report.personal`; sem emails; push só para
`develop` (nunca `main`).
