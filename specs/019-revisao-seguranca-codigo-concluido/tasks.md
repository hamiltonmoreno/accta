---
description: "Task list — Revisão de Segurança do Código (spec 019)"
---

# Tasks: Revisão de Segurança do Código — Portal ACCTA

**Input**: Design documents from `specs/019-revisao-seguranca-codigo/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-changes.md, quickstart.md

**Tests**: INCLUÍDOS — a spec exige uma **guarda de regressão automática por correção**
(FR-022, SC-008). Escrever o teste/tripwire ANTES da correção e confirmar que falha.

**Organização**: por user story (US1–US5). Cada US = um workstream de remediação e um
**release próprio** (backend → Via B). Ordem de prioridade P1→P4; US5 (registo) é
transversal. Mapa: US1=A+B+C+QR, US2=D+E, US3=F+FR-013, US4=G, US5=registo/fecho.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode correr em paralelo (ficheiro diferente, sem dependência incompleta)
- **[Story]**: US1..US5 (fases de story); Setup/Polish sem label

---

## Phase 1: Setup

**Purpose**: preparar a branch e fixar a baseline de equivalência (SC-009).

- [X] T001 Criar branch `feature/019-revisao-seguranca-codigo` a partir de `develop`
- [X] T002 Fixar baseline verde e registar contagens: `pytest -m unit` → **1576 passed, 697 deselected** (2026-07-05; prova de que qualquer vermelho posterior é regressão introduzida)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: sem trabalho foundational bloqueante — as cinco user stories são workstreams
**independentes**, cada uma um release. Nota de serialização (ver Dependencies):
`backend/server.py` é tocado por US1/US2/US4 e `backend/requirements.txt`+`server.py` por
US4 → editar em série (as stories já correm por ordem de fase).

**Checkpoint**: baseline verde → começar US1.

---

## Phase 3: User Story 1 - Nenhum dado de sócio acessível a quem não deve (Priority: P1) 🎯 MVP

**Goal**: fechar os gaps ativos de confidencialidade — `proofs` públicos, fuga de hash por
projeção vazia, cobertura IDOR provável, validador QR — sem regressão visível.

**Independent Test**: `proof` de outro sócio negado sem/ com sessão não autorizada; nenhuma
resposta contém `password`; toda rota id-taking classificada e provada (SC-001); QR expõe só
o essencial.

### Tests for User Story 1 (escrever primeiro, confirmar que falham) ⚠️

- [X] T003 [P] [US1] `backend/tests/test_proof_serving.py`: `GET /api/finances/transactions/{id}/proof` → 403 socio, 200 admin (real file, `Cache-Control: no-store`), 404 id inexistente / `proof_url` vazio / prefixo≠`/uploads/proofs/`; traversal fica sob `UPLOAD_DIR/proofs`; mount estático 404 a `proofs/` e `documents/`
- [X] T004 [P] [US1] `backend/tests/test_users_secret_projection.py`: `User(**doc)`/`Token(...)` com password+MFA+invite_token → dump não os contém; GET /users, /users/{id}, PATCH /me/profile, /auth/me, POST /auth/login declaram `response_model≠None`; `_user_projection(True/False)` exclui password+MFA e strip de sensível não-self. **(G5/FR-002)** verificado por grep: login strip explícito (auth_routes:110-111), invite não devolve token (admin:163-165), register/forgot/reset devolvem mensagem sem token
- [X] T005 [P] [US1] `backend/tests/test_idor_coverage.py`: enumera rotas id-taking do app EM RUNTIME + tripwires `test_every_id_route_classified` (`set(enumerado)==set(AUDIT)` = SC-001) e `test_owner_scoped_routes_have_behavioral_coverage`
- [X] T006 [P] [US1] `backend/tests/test_idor.py` +5 negativos «B não toca no objeto de A» (gallery photo delete, wall comment delete, sancao self-view, sancao recurso, ato cancelar)
- [X] T007 [P] [US1] `backend/tests/test_access_matrix.py`: `test_no_legacy_role_in_db_query` (+self-check de scoping) — 0 filtros `{"role": …}` com `moderador`/`financeiro`
- [X] T008 [P] [US1] `backend/tests/test_audit_no_secrets.py`: `create_audit_log` details sem chave sensível (password/token/secret/mfa) (+self-check)

### Implementation for User Story 1

- [X] T009 [US1] `backend/server.py` `UploadsStaticFiles`: `_PROTECTED_PREFIXES = ("documents", "proofs")` → 404 a ambos (defesa-em-profundidade)
- [X] T010 [US1] `backend/routes/finances.py`: `GET /transactions/{transaction_id}/proof` — `require_view_finances`, `find_one` por id, traversal guard sob `UPLOAD_DIR/proofs`, `FileResponse` + `Cache-Control: no-store`; autoriza pelo id da transação
- [X] T011 [US1] `deploy/nginx/accta.conf` **criado** (não existia versionado): `location ^~ /uploads/proofs/ { return 404; }` + bloco `documents` de paridade + cabeçalho STOP (aplicar no NPM/edge)
- [X] T012 [US1] `backend/routes/users.py`: `response_model=User` em `GET /users/{id}` e `PATCH /users/me/profile`; `_user_projection` inalterado
- [X] T013 [US1] `test_idor_coverage.py`: registo `AUDIT` com as **185** rotas (184 c/ param + proof) classificadas {public/authenticated/role/owner/parent_scoped} com citação; verificado que casa com a enumeração runtime (185==185, 0 em falta/extra)
- [X] T014 [US1] `backend/routes/wall.py`: destinatários por `{"$or": [{"role":"admin"}, {"privileges":"moderate_content"}]}` (operador `?` do DAO), não pelo literal morto `moderador`
- [X] T015 [US1] `backend/routes/stats.py`: `GET /api/validate/{qr_hash}` sem `admission_date` (só valid/name/member_id/status)
- [X] T016 [US1] Verificação frontend: `DetailsGrid`/`InfoRow` usam `value={user.X}` com fallback + guarda `date_of_birth ? …`; `null` renderiza igual a ausente ⇒ **sem alteração visível, sem código a mudar**
- [X] T053 [US1] **(G4/FR-005)** Auditadas ranking/`_VOTER_PROJ`/`_MEMBER_PROJECTION`/notify helpers/listagens admin — todas allowlists sem `SENSITIVE_PROFILE_FIELDS` ⇒ **superfície nula (aceite)**; guarda `test_pii_projection_guard.py`

**Checkpoint US1**: `pytest -m unit` verde → **RELEASE Fase 1 (Via B)**. **STOP**: a regra nginx `/uploads/proofs/` tem de entrar no VPS na MESMA janela do deploy (senão os comprovativos ficam públicos); probe pós-deploy `curl -sI /uploads/proofs/x → 404`.

---

## Phase 4: User Story 2 - Perímetro de autenticação e sessão sem arestas exploráveis (Priority: P2)

**Goal**: rate-limit real e por-cliente; postura de prod não-degradável; `SECRET_KEY` com piso; CSRF trancado.

**Independent Test**: prod sem `ENVIRONMENT` → arranque recusa; `SECRET_KEY` curto → recusa; força-bruta de muitos IPs atrás do proxy → limite por cliente real; escrita cross-origin → 403.

### Tests for User Story 2 (primeiro) ⚠️

- [X] T017 [P] [US2] `backend/tests/test_rate_limit.py`: `rate_limit_key` (peer não-confiável+XFF→peer; peer confiável+XFF→primeiro hop; clientless→fallback); `SlowAPIMiddleware` montado + key_func=`rate_limit_key` + `_default_limits` não-vazio; login 10→429 / forgot 3→429 mantidos verdes
- [X] T018 [P] [US2] `backend/tests/test_prod_posture.py`: `_looks_like_production` (https público→True; localhost/*/vazio→False) + arranque em subprocesso — recusa com https público sem `ENVIRONMENT` e com `SECRET_KEY`<32; arranca com `ENVIRONMENT=production` e em dev local
- [X] T019 [P] [US2] `backend/tests/test_csrf_middleware.py` parametrizado {POST,PUT,PATCH,DELETE}: cookie+origem hostil → 403, cookie+permitida → 200, no-cookie+hostil → passa (FR-009; H6 verify-only)

### Implementation for User Story 2

- [X] T020 [US2] `backend/helpers.py`: `client_ip(request)` + `rate_limit_key(request)` (reusam `_is_trusted_proxy`/`_TRUSTED_PROXY_NETS`); `extract_request_meta` refatorado para `client_ip`
- [X] T021 [US2] `backend/server.py`: `app.add_middleware(SlowAPIMiddleware)` (outermost, após CSRF) + `key_func=rate_limit_key` no Limiter (default 200/min) + comentário `ponytail:` (teto ~2× por-worker; upgrade Redis/`--workers 1`)
- [X] T022 [US2] `routes/auth_routes.py` + `contact.py` + `comunicados.py`: `key_func=rate_limit_key` (import de helpers; `get_remote_address` removido). **De caminho:** fixture autouse `_disable_global_rate_limit` no conftest (o SlowAPIMiddleware global daria 429 espúrios nos TestClient partilhados, ex. matriz RBAC)
- [X] T023 [US2] `backend/server.py`: `_looks_like_production()` (urlparse; https não-local) + `if _looks_like_production() and not IS_PROD: raise` após o gate de CORS
- [X] T024 [US2] `backend/auth.py`: `if len(SECRET_KEY) < 32: raise RuntimeError(...)` a seguir ao check de not-set
- [X] T025 [P] [US2] `frontend/vercel.json`: CSP **`Report-Only`** (header, scoped a fonts/posthog/turnstile/api); scripts dev-tooling deixados inertes (X-Frame-Options DENY já os mata em prod). Enforce = ação do dono após validar 0 violações no browser
- [X] T050 [US2] **(G1/FR-010)** Revogação de sessão: as 3 propriedades (status≠ativo / iat<password_changed_at / jti na blocklist) **já estavam testadas** em `test_auth_hardening.py`; +teste da **decisão do edge mesmo-segundo** — token com `iat==changed_ts` **sobrevive** (aceite, FR-022; `<=` arriscava falso-logout pós-reset)
- [X] T051 [US2] **(G2/FR-011)** `backend/models.py`: `UserLogin.password = Field(max_length=72)` (reset/setup já capam) — corpo de vários KB → 422 antes do `bcrypt.verify`

**Checkpoint US2**: `pytest -m unit` verde → **RELEASE Fase 2 (Via B)**. **STOP**: antes do release, verificar no `/docker/accta/.env` do VPS que `ENVIRONMENT=production` e `SECRET_KEY` ≥32 chars (senão o container não arranca — é o comportamento desejado).

---

## Phase 5: User Story 3 - Sem injeção, SSRF ou exaustão de recursos latentes (Priority: P3)

**Goal**: SSRF do push cego a DNS+redireção fechado; upload com limite antes de buffrar + quota; URLs armazenados/renderizados restritos; `$regex` seguro por construção.

**Independent Test**: push para host que resolve a IP interno → bloqueado; upload acima do limite → 413 sem esgotar recursos; URL `javascript:` num campo → 422 / não renderizado como link.

### Tests for User Story 3 (primeiro) ⚠️

- [X] T026 [P] [US3] `backend/tests/test_push_service.py`: `getaddrinfo`→IP privado ⇒ `_endpoint_resolves_public` False; erro de resolução ⇒ fail-closed; `_no_redirect_session` força `allow_redirects=False`; `dispatch_push` skipa endpoint que resolve p/ interno
- [X] T027 [P] [US3] `backend/tests/test_file_validation.py`: fake `UploadFile` que faz stream >max ⇒ 413 sem materializar o corpo (bytes lidos ≤ max+chunk); aceita dentro do limite
- [X] T028 [P] [US3] `backend/tests/test_url_validators.py`: Benefit/Post/Publicacao (create+update) rejeitam `javascript:`/`http(s)://externo`/`data:`/`//`/`/etc` (422) e aceitam `/uploads/…`/``/None; Base NÃO revalida legado; `_is_safe_icon_target` (uploads/FRONTEND_URL host ✓, externo/js/None ✗)
- [X] T029 [P] [US3] `test_sql_injection_fuzz.py::test_regex_call_sites_are_safe`: todo `$regex` recebe saneador ou var atribuída de saneador (senão vermelho)
- [X] T052 [P] [US3] **(G3/FR-014)** `test_sql_injection_fuzz.py` estendido: chave jsonb hostil (aspas duplicadas, contagem par), `sort` field hostil escapado, ramos `$in/$nin/$ne/$gt/$gte/$lt/$lte/$or/$and/$exists` parametrizados

### Implementation for User Story 3

- [X] T030 [US3] `backend/push_service.py`: `_endpoint_resolves_public` (getaddrinfo, todos os IPs públicos, fail-closed) chamado em `dispatch_push` além do `is_safe_push_endpoint`; `_no_redirect_session` (`allow_redirects=False`) via `webpush(..., requests_session=...)`; `ponytail:` no TOCTOU DNS-rebind
- [X] T031 [US3] `backend/file_validation.py`: `read_upload_capped(file, max_size)` streaming/413; substituído `await file.read()` em `upload.py`, `gallery.py`, `prestacao_contas.py`
- [X] T032 [US3] `routes/upload.py` + `gallery.py`: `@limiter.limit("30/hour")` + `request: Request` nos endpoints de upload (Limiter por-módulo). Regressão: `test_posts.py::test_socio_403` chamava a função direto → +Request mínimo + limiter off (gotcha slowapi)
- [X] T033 [US3] `backend/models.py`: helper `_validate_local_upload_url` + `field_validator` em `BenefitCreate/Update.logo_url`, `PostCreate/Update.cover_url`, `PublicacaoCreate/Update.capa_url` (só ESCRITA; Base intocado — FR-024)
- [X] T034 [US3] `backend/routes/brand.py`: `_is_safe_icon_target` — 302 só se `/uploads/` OU host==FRONTEND_URL host; senão default estático
- [X] T035 [US3] `backend/helpers.py`: `safe_search_regex` (fonte única, cap-antes-de-escape); finances (alias), users, posts re-apontados; `re` órfão removido. Guard defensivo no DAO SALTADO (ponytail: truncar regex já-escapado invalida-o; o cap seguro é no helper) — tripwire garante disciplina
- [X] T036 [P] [US3] Frontend M-HREF: **achado** — `BeneficiosPublicoPage`/`ProfissaoDestaques` JÁ sanitizavam (helpers locais idênticos); `ContactosPage.site` é config estática (não-BD, sem vetor). Consolidado num util único `utils/safeUrl.js` (+teste 4✓, react-scripts) e re-apontados os 2 componentes
- [~] T037 [US3] **STOP/pendente dono**: verificação de dados prod (nenhum benefit/post/publicação com URL externo de logo/capa antes de ligar o validator) — `backend/.env` aponta p/ Supabase de PRODUÇÃO real; não corro query exploratória sem confirmação. Registado p/ o dono correr antes do release da Fase 3

**Checkpoint US3**: `pytest -m unit` verde (parte do release da Fase 3, junto com US4).

---

## Phase 6: User Story 4 - Dependências sem CVE conhecido e vigilância contínua (Priority: P4)

**Goal**: remediar as CVEs HIGH/MEDIUM + estabelecer scanning automático; sem quebrar uploads.

**Independent Test**: verificação de CVEs → 0 High/Critical alcançável; upload >1 MB continua a funcionar; Dependabot sinaliza novas CVEs.

### Tests for User Story 4 (primeiro) ⚠️

- [X] T038 [P] [US4] `backend/tests/test_upload_part_size.py` (árbitro do bump, via ENDPOINT real): `POST /api/upload/documents` c/ ficheiro 2 MB → não-400 / ausência de `Part exceeded`; >10 MB → 413 (read_upload_capped, não parser). Provado em starlette 0.41.3 instalado

### Implementation for User Story 4

- [X] T039 [US4] `backend/requirements.txt`: `fastapi 0.110.1→0.115.6` + `starlette 0.37.2→0.41.3` (par), `python-multipart 0.0.9→0.0.18`, `Pillow 10.3.0→11.2.1`, `Jinja2 3.1.3→3.1.6`, `requests 2.31.0→2.32.4`. `bcrypt==4.0.1` intocado. (Instalados no venv 5/6; Pillow 11.2.1 sem wheel p/ Python 3.14 local — prod é 3.11, wheel existe; venv corre Pillow 12.2.0 > alvo, suíte verde)
- [~] T040 [US4] **DISPENSADO com prova empírica** (reversão fundamentada do plano): a premissa «todo upload >1 MB dá 400 sem `max_part_size`» é **falsa** — em starlette 0.41.3 o `max_part_size` (1 MB) limita CAMPOS de formulário, NÃO ficheiros (spool p/ disco). Testado: ficheiro 3 MB → 200, ficheiro+campo → 200. Sem `max_part_size` custom (menos código; ver T038 = guard permanente)
- [X] T041 [US4] `.github/dependabot.yml`: `pip`→`/backend` + `npm`→`/frontend` + `github-actions`, semanal, agrupado minor/patch, ignora `react-scripts` (M-CRA) e `bcrypt`
- [X] T042 [US4] `scripts/audit_deps.sh`: `pip-audit -r backend/requirements.txt` + `yarn npm audit --severity high`; degrada c/ aviso se ferramenta ausente
- [X] T043 [US4] Gate de compat: `pytest -m unit` nas versões-alvo (0.115.6/0.41.3/0.0.18) instaladas → **1669 passed**. SC-004: `pip-audit` pendura na rede local (2× killed) → verificação **determinística** dos pins vs versão-fix de cada CVE conhecido (starlette/multipart/fastapi/Jinja2/Pillow/requests/jose todos ≥ fix; bcrypt 4.0.1) → **0 CVEs alcançáveis**. `audit_deps.sh` fica p/ ambiente com pip-audit/yarn
- [~] T044 [US4] **Ação do dono**: ativar Dependabot alerts + security updates nas Security settings do repo (GitHub UI — FR-020)

**Checkpoint US3+US4**: `pytest -m unit` verde → **RELEASE Fase 3 (Via B)**. Probe pós-deploy: upload real >1 MB → 200; `POST /api/push/*` gated.

---

## Phase 7: Polish & Cross-Cutting — User Story 5 (Registo & regressão)

**Goal**: registo de achados fechado, backlog dos LOW, prova de que as guardas travam regressões.

- [X] T045 [P] [US5] Registo em `research.md` atualizado a cada US: **0 achados abertos** (19 corrigidos c/ `regression_guard`, 2 aceites, 2 parciais, 2 infra, 1 verificado; LOW em backlog) — SC-007
- [X] T046 [P] [US5] `backlog-low.md`: LOW L1-L10 com condição de reabertura + **(U2/FR-012)** decisões explícitas O1-O3 (timing bcrypt-skip / mensagens do registo / lockout-DoS = **aceitar** com porquê). Tabnabbing verificado = 0 casos
- [X] T047 [US5] Meta-check SC-008 provado **2×**: remover `response_model=User` → `test_users_secret_projection` vermelho; repor `{"role":"moderador"}` → `test_no_legacy_role_in_db_query` vermelho; ambos restaurados, árvore limpa
- [X] T048 [US5] Verificação final: `pytest -m unit` **1669✓** (versões-alvo), `ruff` limpo, `eslint` 0 erros (22 warnings <60). Smoke no navegador (SC-009) = residual do dono (Princípio VII)
- [X] T049 [US5] `tasks/todo.md` (review) + memória do projeto (`spec-019-seguranca-codigo-state.md` + índice) atualizados

---

## Estado final (2026-07)

**53 tarefas**: 48 **[X]** feitas · 3 **[~]** = ação/validação do dono (T037 dados prod, T040
dispensado-com-prova, T044 Dependabot settings) · T043 verde. **Todas as US implementadas**
na branch `feature/019-revisao-seguranca-codigo` (4 commits, 1669 testes verdes). **Não
released** — STOPs de release por confirmar com o dono (nginx edge / env prod / Dependabot).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: nenhum bloqueio real (stories independentes).
- **User Stories (Phase 3–6)**: correm por **ordem de prioridade** P1→P4, cada uma um
  release próprio (Via B). Fase 3 = US3+US4 partilham release.
- **Polish (Phase 7 / US5)**: o registo (T045/T046) é atualizado ao fechar cada story; a
  verificação final (T047/T048/T049) é no fim.

### Serialização de ficheiros partilhados (evitar conflitos)

- `backend/server.py`: editado por T009 (US1), T021+T023 (US2), T040 (US4) → editar em série
  (as stories já correm por fase, sem conflito real).
- `backend/requirements.txt` (T039) + `server.py` `max_part_size` (T040) + teste >1 MB (T038)
  **têm de ir juntos** — o teste é o árbitro do bump.

### Within Each User Story

- Testes/tripwires primeiro (confirmar que falham) → implementação → checkpoint/release.
- STOPs de infra/prod confirmados com o dono no momento do release (ver Checkpoints).

### Parallel Opportunities

- Todos os testes `[P]` de uma story escrevem-se em paralelo (ficheiros distintos).
- Impl em ficheiros distintos dentro da story: T036/T025 (frontend) `[P]` vs. os backend.
- Entre stories: paralelismo limitado pela serialização de `server.py` + releases sequenciais
  → num só dev, seguir por fase é o caminho recomendado.

---

## Implementation Strategy

### MVP (User Story 1)

1. Setup (T001–T002) → 2. US1 (T003–T016) → 3. **STOP e VALIDAR** US1 (proofs gated, sem fuga de
   segredos, SC-001 100%) → 4. Release Fase 1 (Via B + STOP nginx VPS). É o gap de maior impacto e
   é quase invisível — bom primeiro release.

### Incremental Delivery

Fase 1 (US1) → Fase 2 (US2) → Fase 3 (US3+US4) → fecho (US5). Cada fase é um release backend
(Via B) que acrescenta postura sem quebrar o anterior; os LOW ficam no backlog (T046).

---

## Notes

- Tests requested ⇒ cada correção tem a sua guarda de regressão (tripwire/pytest) — SC-008.
- `[P]` = ficheiros diferentes, sem dependência incompleta.
- Confirmar que o teste falha antes de implementar; commit por tarefa ou grupo lógico.
- Toca `backend/` ⇒ cada fase precisa de deploy **Via B** (`docs/runbook-deploy-backend-via-b.md`).
- STOPs recorrentes: nginx VPS (US1), verificação `ENVIRONMENT`/`SECRET_KEY≥32` (US2), Dependabot
  settings + Via B (US4), push a `main` só via release PR.
- **Total: 53 tarefas** — US1: 15 · US2: 11 · US3: 13 · US4: 7 · US5/Polish: 5 · Setup: 2.
  (T050–T053 acrescentadas pós-`/speckit-analyze` para fechar FR-010/FR-011/FR-014/FR-005;
  IDs não-contíguos dentro da fase = handles, a execução é por fase.)
