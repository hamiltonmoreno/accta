# Quickstart — Validação da Revisão de Segurança (spec 019)

Guia de validação executável. Prova cada Success Criterion (SC-001..009) e os
cenários de aceitação das US1–US5. Não contém código de implementação — só como
correr e o que observar. Detalhe de desenho em `research.md`/`contracts/`.

## Pré-requisitos

```bash
cd backend && pip install -r requirements.txt   # inclui os bumps da Fase 3 (bcrypt fica 4.0.1)
```
- Testes unit correm sem servidor/BD (`pytest -m unit`, mock_db em `conftest.py`).
- Validação de prod (Via B) usa o `docs/runbook-deploy-backend-via-b.md` (probe
  server-side + teste decisivo). Ambiente dev isolado: Docker `accta-pg-dev`.

## Gate global (correr em cada fase)

```bash
cd backend && pytest -m unit          # ~1575 + novos testes desta spec, todos verdes (SC-009)
cd backend && ruff check .            # limpo
cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60
```

## Fase 1 — Confidencialidade & baseline (US1)

**A — comprovativos protegidos (SC-002, cenário 1):**
```bash
cd backend && pytest tests/test_finances_routes.py -k proof -q
```
- `GET /api/finances/transactions/{id}/proof`: 403 socio · 200 admin/financeiro ·
  404 id inexistente / sem `proof_url`.
- Path-traversal (`proof_url` com `..`) → rejeitado, nunca sai de `UPLOAD_DIR/proofs`.
- Resposta com `Cache-Control: no-store`.
- Mount estático devolve **404** a `GET /uploads/proofs/<name>` (via TestClient).
- **Prod (Via B)**: após deploy, `curl -sI https://api.controlador.cv/uploads/proofs/x`
  → 404 (nginx do VPS com a regra); um `proof` real só sai pelo endpoint autenticado.

**B — sem fuga de segredos (SC-003, cenário 2):**
```bash
cd backend && pytest tests/test_users_secret_projection.py -q
```
- `User(**doc)`/`Token(...)` com password+MFA injetados → dump **não** os contém.
- `GET /api/users`, `/users/{id}`, `/auth/me`, `POST /auth/login` declaram `response_model≠None`.
- `_user_projection(False)` faz strip de PII sensível; `(True)` mantém (FR-005).

**C — cobertura IDOR provável (SC-001, cenário 3):**
```bash
cd backend && pytest tests/test_idor_coverage.py tests/test_idor.py -q
cd backend && pytest tests/test_access_matrix.py -k "legacy_role or inline" -q
```
- `test_every_id_route_classified`: `set(rotas id-taking) == set(AUDIT)` → **100%** (SC-001).
- `test_owner_scoped_routes_have_behavioral_test`: toda rota owner/parent_scoped mutante
  tem negativo «B não toca no objeto de A».
- `test_no_legacy_role_in_db_query`: 0 queries `{"role": …}` com `moderador`/`financeiro`.

## Fase 2 — Perímetro (US2)

**D — rate-limit real e por-cliente (SC-005, cenário 3):**
```bash
cd backend && pytest tests/test_rate_limit.py -q
```
- `rate_limit_key`: peer não-confiável + XFF → usa o peer (XFF ignorado); peer confiável
  + XFF → primeiro hop (isola o cliente real atrás do proxy).
- `SlowAPIMiddleware` presente + default não-vazio → default 200/min aplicado.
- Regressões existentes (login 10→429, forgot 3→429) verdes.
- **Prod**: confirmar no VPS que o edge põe `X-Forwarded-For` e liga de IP em
  `_TRUSTED_PROXY_NETS` (senão degrada p/ hoje, não pior).

**E — prod não degrada + SECRET_KEY + CSRF (SC-006, US2 cenários 1/2/4):**
```bash
cd backend && pytest tests/test_prod_posture.py tests/test_csrf_middleware.py -q
```
- Boot gate: FRONTEND_URL/CORS https público + `ENVIRONMENT` unset → `RuntimeError`;
  localhost/dev → arranca; https público + `ENVIRONMENT=production` → arranca.
- `SECRET_KEY` <32 → `RuntimeError`; ≥32 → OK.
- CSRF: cookie + origem hostil → 403 em **PUT/PATCH/DELETE** (parametrizado); cookie +
  origem permitida → 200.
- **[STOP] antes do release**: `grep SECRET_KEY /docker/accta/.env` no VPS ≥32 chars e
  `ENVIRONMENT=production` (senão o container não arranca).

## Fase 3 — SSRF/DoS/URLs & Dependências (US3+US4)

**F — SSRF, upload DoS, URLs (US3 cenários 1/2/3):**
```bash
cd backend && pytest tests/test_push_service.py tests/test_file_validation.py -q
cd backend && pytest tests/test_models.py -k "url or logo or cover or capa" -q
```
- Push: hostname que resolve p/ IP privado → send **skip** (sem `webpush`); erro de
  resolução → skip fail-closed; `webpush` invocado com sessão `allow_redirects=False`.
- Upload: fake `UploadFile` que faz stream >max → `413` sem materializar o corpo (bytes
  lidos ≤ max+chunk).
- Modelos: `javascript:`/`http(s)://externo`/`data:` → 422; `/uploads/…`/``/None → OK.
- `get_brand_icon`: `icon_url` externo → 302 p/ default; `/uploads/brand/x.png` → passa.

**G — dependências + scanning (SC-004, US4):**
```bash
cd backend && pytest tests/test_file_validation.py -k "part_size or oversize or pillow" -q
bash scripts/audit_deps.sh          # pip-audit + yarn npm audit → 0 High/Critical alcançável
cd backend && pytest -m unit        # suíte completa é o gate de compat starlette/fastapi
```
- **Árbitro do bump**: `POST /api/upload/documents` com ficheiro **2 MB** → 200 (não
  `400 "Part exceeded maximum size"`) → prova `starlette 0.41.3` + `max_part_size` coexistem.
- Carteira PDF (spec 007) renderiza em Pillow 11.2.1 + fpdf2.
- `.github/dependabot.yml` presente; **[ação dono]** ativar Dependabot alerts+security
  updates nas Security settings do repo.

## US5 — Registo & regressão (SC-007, SC-008)
- `research.md`: todos os HIGH+MEDIUM em `corrigido` (com `regression_guard`) ou
  `aceite`/`adiado` com justificação; LOW num backlog.
- SC-008: reintroduzir deliberadamente um fix (ex.: tirar `response_model=User`, ou
  repor `{"role":"moderador"}` na query) → um tripwire fica **vermelho**.

## Verificação final (Princípio VII)
- Cada fase: `pytest -m unit` verde + probe server-side pós-Via B (teste decisivo do
  runbook) para as fases que tocam prod.
- Nenhuma alteração funcional visível ao utilizador (SC-009) — smoke no navegador das
  áreas tocadas (finanças, perfil, uploads) sem regressão.
