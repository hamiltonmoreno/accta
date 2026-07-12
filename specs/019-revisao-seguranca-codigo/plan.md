# Implementation Plan: Revisão de Segurança do Código — verificação e endurecimento do Portal ACCTA

**Branch**: `feature/019-revisao-seguranca-codigo` | **Date**: 2026-07-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/019-revisao-seguranca-codigo/spec.md`

## Summary

Revisão de segurança sistemática de todo o código do Portal ACCTA, sobre uma base
já substancialmente endurecida. Um levantamento paralelo (9 domínios) + um desenho
de remediação por finding (7 workstreams), ambos fundamentados no código real,
identificaram **8 achados HIGH e ~17 MEDIUM** com correção concreta. A abordagem
técnica é **reutilizar padrões já existentes no repo** (o gating RBAC de
`documents`, os `field_validator` de URL, os `Limiter` slowapi, os tripwires
estilo `test_no_inline_role_checks`) para o menor diff correto, com **uma guarda de
regressão automática por correção**. Decisões do dono: auditar+corrigir+testar;
backend + frontend + config de deploy versionada (edge do VPS = recomendação com
STOP); remediar **HIGH+MEDIUM** neste ciclo, **LOW** registado e adiado.

Achado notável do desenho: **H6 (CSRF) é verify-only** — o `CSRFOriginCheckMiddleware`
já cobre todos os métodos inseguros e não é contornável pelo modelo cookie+header;
só precisa de um teste parametrizado. E o bump de dependências tem um **acoplamento
oculto**: Starlette 0.40+ impõe um teto de 1 MB por-parte em multipart que partiria
todos os uploads >1 MB — mitigado com `max_part_size` no arranque (gate obrigatório
do bump).

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript/React 19 (frontend)

**Primary Dependencies**: FastAPI + asyncpg (DAO Mongo-compatível sobre Postgres),
slowapi (rate-limit), pywebpush, Pillow, Jinja2, Resend; React 19 + CRA/Craco +
axios. Bumps coordenados nesta spec: FastAPI 0.110.1→0.115.6 + Starlette 0.37.2→0.41.3,
python-multipart 0.0.9→0.0.18, Pillow 10.3.0→11.2.1, Jinja2 3.1.3→3.1.6, requests
2.31.0→2.32.4. **`bcrypt==4.0.1` fica (off-limits).**

**Storage**: PostgreSQL (Supabase), tabelas `(pk bigserial, doc jsonb)` via o DAO.
**Esta revisão não altera esquema nem faz migração** (o único item que exigiria
migração — purga física de `mfa_secret*` legado — é **adiado**, STOP).

**Testing**: pytest (`pytest -m unit`, asyncio_mode=auto, ~1575 testes verdes hoje);
fixtures em `conftest.py` (mock_db, role fixtures, make_token). Tripwires in-process
estilo `test_no_inline_role_checks`. eslint no frontend.

**Target Platform**: Linux (Docker) atrás de NPM/openresty (`api.controlador.cv`);
SPA na Vercel; Postgres Supabase.

**Project Type**: Web (backend FastAPI + frontend React) — Opção 2.

**Performance Goals**: sem regressão de latência; `bcrypt` mantém-se CPU-bound
(uvicorn `--workers 2` preservado). Rate-limit default 200/min por-cliente real.

**Constraints**: sem alteração funcional visível ao utilizador (exceto quando o
comportamento É a vulnerabilidade); sem migração/drop; GitFlow; deploy backend por
Via B; correções de infra/prod (nginx no VPS, env de produção) são STOP conditions.

**Scale/Scope**: ~327 rotas em 34 módulos (184 recebem `id`); ~1575 testes unit;
2 níveis de role + privilégios (spec 018). 7 workstreams de remediação (A–G).

## Constitution Check

*GATE: verificado antes da Fase 0 e re-verificado após o desenho da Fase 1.*

| Princípio | Estado | Nota |
|-----------|--------|------|
| I — Simplicity First | ✅ PASS | Cada workstream escolheu a reutilização mais preguiçosa (padrão `documents`, `response_model`, `field_validator` existentes, `Limiter`). Tetos aceites marcados com `ponytail:` (2× por-worker no rate-limit; TOCTOU DNS-rebind no push). |
| II — Root-Cause (NON-NEGOTIABLE) | ✅ PASS | Correções em chokepoints partilhados: helper de streaming de upload, backstop de projeção, `client_ip()` único, nginx+app nos dois níveis. Não são pensos por-chamador. |
| III — RBAC + Audit (NON-NEGOTIABLE) | ✅ PASS | Endpoint de `proof` usa `require_view_finances`; sem raw SQL (tudo no DAO); C adiciona tripwire que impede novos checks inline e queries com role legado; nenhuma escrita admin nova sem audit. |
| IV — Language | ✅ PASS | Strings user-facing PT; identificadores EN; docs/registo em PT. |
| V — Design System (NON-NEGOTIABLE) | ✅ N/A | Ciclo maioritariamente backend; **nenhuma UI construída** (o endpoint de proof é consumido por futura UI CF, fora deste ciclo). |
| VI — GitFlow + Confirmação (STOPs) | ⚠️ PASS c/ STOPs | Vários STOPs **esperados** (não violações): deploy Via B + push a `main`; **infra** (regra nginx `/uploads/proofs/` no VPS + verificação de `ENVIRONMENT`/`SECRET_KEY≥32` em prod antes do release); vários workstreams tocam >3 ficheiros (D=6, F=7, G=5) — **âmbito aprovado da spec 019, não scope-creep** (ver Complexity Tracking). |
| VII — Verificação (NON-NEGOTIABLE) | ✅ PASS | Cada correção traz teste/tripwire; mudanças que tocam prod exigem prova server-side pós-Via B (probe + teste decisivo do runbook). |

**Gate: PASS.** Os STOPs do Princípio VI são condições de execução a confirmar com
o dono no momento do release, registadas abaixo — não bloqueiam o plano.

## Project Structure

### Documentation (this feature)

```text
specs/019-revisao-seguranca-codigo/
├── plan.md              # Este ficheiro
├── spec.md              # Especificação (US1–US5, FR-001..027, SC-001..009)
├── research.md          # Survey consolidado + decisão/racional/alternativas por workstream (= semente do registo de achados)
├── data-model.md        # Entidade Achado + taxonomia access_class + registo de achados (sem alteração de esquema prod)
├── contracts/
│   └── api-changes.md    # Deltas de contrato (proof endpoint, /uploads/proofs 404, 429, 422 URLs, boot gates)
├── quickstart.md        # Cenários de validação (mapeiam SC-001..009 + acceptance scenarios)
└── tasks.md             # (Fase 2 — gerado por /speckit-tasks, NÃO por /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── server.py            # A: bloquear /uploads/proofs no mount · D: SlowAPIMiddleware + key_func · E: gate _looks_like_production() · G: max_part_size
├── auth.py              # E: SECRET_KEY ≥32 no arranque
├── config.py            # E: (leitura IS_PROD, sem alteração de contrato)
├── helpers.py           # D: extrair client_ip()/rate_limit_key() (reutiliza _is_trusted_proxy/_TRUSTED_PROXY_NETS)
├── push_service.py      # F: SSRF DNS-resolve + no-redirect session
├── file_validation.py   # F: read_upload_capped() streaming
├── models.py            # F: field_validator de URL em Benefit/Post/Publicacao
├── requirements.txt     # G: bumps coordenados fastapi/starlette + multipart/Pillow/Jinja2/requests
└── routes/
    ├── finances.py      # A: GET /transactions/{id}/proof (RBAC) · F: (—)
    ├── users.py         # B: response_model=User em GET /users/{id} e PATCH /me/profile
    ├── upload.py        # F: read_upload_capped + @limiter.limit
    ├── gallery.py       # F: read_upload_capped
    ├── prestacao_contas.py # F: read_upload_capped
    ├── brand.py         # F: guardar target do 302 /brand/icon
    ├── wall.py          # C: resolver moderadores por moderate_content (não role literal)
    ├── stats.py         # US1: reduzir resposta do validador QR público (FR-004; rate-limit vem do default de US2)
    ├── auth_routes.py / contact.py / comunicados.py # D: key_func=rate_limit_key
    └── database.py      # FR-013: centralizar escape/cap de $regex (helper único)

backend/tests/           # US5: guarda de regressão por correção
├── test_idor_coverage.py         # C: enumeração + AUDIT registry + tripwires (SC-001)
├── test_idor.py                  # C: negativos IDOR owner/parent_scoped
├── test_access_matrix.py         # C: + test_no_legacy_role_in_db_query
├── test_users_secret_projection.py # B: model/route/projection pins (SC-003)
├── test_rate_limit.py            # D: rate_limit_key + default-limit wired
├── test_csrf_middleware.py       # E: parametrizar PUT/PATCH/DELETE (FR-009)
├── test_prod_posture.py          # E: boot gate + SECRET_KEY entropy
├── test_push_service.py          # F: SSRF resolve + no-redirect
├── test_file_validation.py       # F/G: streaming cap + Pillow 11 + >1MB upload
└── test_finances_routes.py       # A: proof serving RBAC + traversal + no-store

deploy/nginx/accta.conf  # A: location ^~ /uploads/proofs/ { return 404; } (+ comentário)
.github/dependabot.yml    # G: pip(/backend) + npm(/frontend), semanal, agrupado
scripts/audit_deps.sh     # G: pip-audit + yarn npm audit (gate local, independente do CI)
docker-compose.yml / backend/Dockerfile # D: inalterados (decisão: não mexer em --workers/--proxy-headers)
```

**Structure Decision**: Opção 2 (Web: `backend/` + `frontend/`). A revisão é
esmagadoramente backend; o frontend só é tocado de forma verificativa (grep de
consumidores de `proof_url` / campos de URL) e não constrói UI nova neste ciclo.
Config de deploy versionada (`deploy/nginx/accta.conf`, `.github/dependabot.yml`,
`scripts/audit_deps.sh`) entra no âmbito; a config de edge no VPS é recomendação
com STOP.

## Faseamento (estratégia de release)

Cada fase é um release backend próprio (Via B). Ordem P1→P3. US5 (registo + guardas)
é transversal: cada correção traz o seu teste; o registo de achados vive em
`research.md`; os LOW ficam num backlog no fecho.

- **Fase 1 — Confidencialidade & baseline provável (US1)** — workstreams **A + B + C**.
  Entrega SC-001/002/003/008. **STOP**: a regra nginx `/uploads/proofs/` tem de ir no
  MESMO deploy que o backend (senão os comprovativos ficam públicos). Maioritariamente
  invisível (tightening + testes) — bom gate para o resto.
- **Fase 2 — Perímetro (US2)** — workstreams **D + E**. Entrega SC-005/006. **STOP**:
  gates fail-closed no arranque exigem verificar em prod, ANTES do release, que
  `ENVIRONMENT=production` e `SECRET_KEY≥32` (senão o container não arranca).
- **Fase 3 — SSRF/DoS/URLs & Dependências (US3+US4)** — workstreams **F + G** + FR-013
  ($regex). Entrega FR-013..020. **STOP**: bump de deps precisa de Via B e de provar
  uploads >1 MB (mitigação `max_part_size`); dono ativa Dependabot nas Security
  settings do repo.

## Complexity Tracking

> STOP conditions e desvios que exigem justificação (Princípio VI).

| Item | Porquê é necessário | Porque não há alternativa mais simples |
|------|---------------------|----------------------------------------|
| Workstreams tocam >3 ficheiros (D=6, F=7, G=5) | Cada um é um workstream de segurança coeso (helper partilhado + call sites + testes), não um «small fix» a inchar | Dividir por ficheiro fragmentaria uma correção de causa-raiz em pensos por-chamador (viola Princípio II). Âmbito explícito da spec 019. |
| STOP infra: regra nginx `/uploads/proofs/` no VPS | Em prod o nginx serve `/uploads` do bind-mount ANTES do uvicorn; sem a regra no edge, o bloqueio na app é código morto | O bloqueio só na app não protege em prod. Tem de ir no mesmo deploy. Confirmação do dono. |
| STOP infra: verificar `ENVIRONMENT`/`SECRET_KEY≥32` em prod | Os novos gates fail-closed fazem o container recusar arrancar se mal configurado | É o comportamento desejado (não-degradação silenciosa); exige um check de 1 linha no `/docker/accta/.env` antes do release. |
| STOP deploy: Via B + push a `main` por release | Toda a fase toca `backend/` | Constituição: `main` só via release PR; backend em prod só por Via B enquanto o CI está billing-locked. |
| Adiado (fora deste ciclo): purga física de `mfa_secret*` | Seria migração destrutiva sobre `users` (STOP) e é desnecessária (a projeção + response_model já bloqueiam a exposição) | O guard permanente de projeção é suficiente; purga fica como tarefa separada gated pelo dono. |
