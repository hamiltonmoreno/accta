# Task — Spec 019: Revisão de Segurança do Código

## Contexto
Revisão sistemática de segurança sobre base já endurecida. Levantamento paralelo
(9 domínios) + desenho de remediação (7 workstreams A–G). Decisões do dono
(2026-07-05): auditar+corrigir+testar; backend+frontend+config de deploy
versionada (edge do VPS = recomendação com STOP); remediar HIGH+MEDIUM, LOW adiado.
Plano: `specs/019-revisao-seguranca-codigo/plan.md` (53 tarefas, 5 US + fases).

## Progresso — todas as US IMPLEMENTADAS (branch `feature/019-revisao-seguranca-codigo`)

- **US1 — Confidencialidade & baseline IDOR** (commit `e0f5de4`, 1605✓): H1 (proofs
  gated: app 404 + endpoint RBAC + nginx), H5 (backstop `response_model=User`),
  M-IDOR (185 rotas classificadas, **SC-001=100%**, provado vs runtime), M-QR, M-PII
  (superfície nula), M-AUDIT (guard de segredos), wall.py (privilégio, não role morto).
- **US2 — Perímetro** (commit `473da3b`, 1626✓): H2 (SlowAPIMiddleware montado),
  H3 (`rate_limit_key`=IP real nos 4 Limiters), H4 (boot gate fail-closed),
  H6 (CSRF verify-only parametrizado), M-SECRET (≥32), FR-010/011, M-CSP (CSP Report-Only).
- **US3 — SSRF/DoS/URLs** (commit `5cbacd1`, 1667✓): M-SSRF-dns/redir (push DNS-guard
  + no-redirect), M-UPL-size/quota (`read_upload_capped` + `@limiter.limit`),
  M-HREF/FR-016 (validators `/uploads`-only + `utils/safeUrl.js`), M-ICON (brand icon),
  M-REGEX/FR-013 (`safe_search_regex` fonte única + tripwire), G3/FR-014 (fuzz SQL).
- **US4 — Dependências** (commit `b60402c`, 1669✓): H7/H8 (starlette 0.41.3 +
  multipart 0.0.18, CVEs), M-DEPS (Pillow/Jinja2/requests), Dependabot + audit_deps.sh.
  **T040 (`max_part_size`) dispensado com prova empírica** (a premissa do plano era falsa).
- **US5 — Registo & regressão** (este commit): registo fechado (0 abertos), backlog
  LOW + decisões de oráculos (`backlog-low.md`), SC-008 provado 2×, verificação final.

## Review

### Resultado
- **Achados remediados**: 8 HIGH + ~17 MEDIUM. Registo em `research.md` — **0 abertos**:
  19 corrigidos, 2 aceites (superfície nula / ceiling), 2 parciais (M-AUDIT retenção,
  M-CSP enforce — partes adiadas), 2 recomendação-infra, 1 verificado (H6). LOW em backlog.
- **Guardas de regressão** (SC-008): 10 ficheiros de teste novos + tripwires. Provado
  por meta-check que reverter um fix (response_model / role legado) fica **vermelho**.
- **Gate**: `pytest -m unit` **1669 passed** nas versões-alvo de prod (fastapi 0.115.6 /
  starlette 0.41.3 / multipart 0.0.18); ruff limpo; eslint 0 erros; SC-004 (0 CVEs) por
  verificação determinística de pins.

### Decisões notáveis
- **H6 verify-only** — o middleware CSRF já cobria tudo; só faltava o teste.
- **T040 dispensado** — provei que o teto de 1 MB do starlette limita campos de
  formulário, não uploads de ficheiro (spool p/ disco). Menos código; guard permanente.
- **max_part_size** e o teste "11 MB" cego substituídos por `test_upload_part_size.py`
  (via endpoint real).

### Pendente (STOPs de release — dono)
- **Fase 1 (US1)**: aplicar a regra nginx `/uploads/proofs/ → 404` no edge NPM vivo na
  MESMA janela do deploy backend (senão os comprovativos ficam públicos).
- **Fase 2 (US2)**: verificar em `/docker/accta/.env` do VPS que `ENVIRONMENT=production`
  e `SECRET_KEY≥32` ANTES do release (senão o container recusa arrancar — desejado).
- **Fase 3 (US3+US4)**: T037 (verificar que nenhum benefit/post/publicação em prod tem
  URL externo de logo/capa — senão alargar o validator); T044 (ativar Dependabot alerts+
  security updates nas Security settings do repo).
- Cada fase toca `backend/` ⇒ release por **Via B** + PR `develop→main`.

### Não released
Nada deployed nem em `main`. 4 commits na feature branch, por revisão/release do dono.
