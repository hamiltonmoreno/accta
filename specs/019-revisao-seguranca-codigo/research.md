# Research & Registo de Achados — Revisão de Segurança (spec 019)

Consolidação do **levantamento da superfície de ataque** (9 domínios, 10 agentes) e
do **desenho de remediação** (7 workstreams A–G), ambos fundamentados no código real.
Este ficheiro é também a **semente do registo de achados** (FR-021/SC-007): cada
achado tem severidade e estado; o estado passa a `corrigido`/`aceite`/`adiado` à
medida que a implementação avança.

## Postura geral

Base **sólida e bem endurecida**. Fora de âmbito (confirmar que se mantêm, não
reconstruir): Turnstile, RLS deny-all + `BYPASSRLS`, HMAC de auditoria, RBAC
unificado + tripwire `test_no_inline_role_checks`, `algorithms=["HS256"]` pinned,
cookie httpOnly + `CSRFOriginCheckMiddleware`, parametrização anti-SQLi no DAO
(com fuzz test), SVG bloqueado + uuid + traversal guards, `documents` atrás de RBAC,
`bcrypt==4.0.1`, MFA removido.

## Registo de achados (HIGH + MEDIUM = âmbito deste ciclo; LOW = adiado)

| ID | Sev | Achado | WS | Estado |
|----|-----|--------|----|--------|
| H1 | HIGH | `proofs` (comprovativos financeiros) servidos sem auth pelo mount estático + nginx edge | A | **corrigido** (US1; guard `test_proof_serving.py`; nginx VPS = STOP no deploy) |
| H2 | HIGH | `SlowAPIMiddleware` ausente → default 200/min nunca aplicado (dead code) | D | aberto |
| H3 | HIGH | Rate-limit chaveia no IP do proxy → todos num balde; brute-force distribuído indetetável | D | aberto |
| H4 | HIGH | Postura de prod cai toda numa `ENVIRONMENT` mal definida (cookie/HSTS/docs/CORS) | E | aberto |
| H5 | HIGH | DAO devolve doc inteiro (hash password + `mfa_secret*`) em projeção `{"_id":0}`; sem chokepoint | B | **corrigido** (US1; `response_model=User` em GET /users/{id} + PATCH /me/profile; guard `test_users_secret_projection.py`) |
| H6 | HIGH→**verify** | CSRF em métodos de escrita — **middleware já cobre tudo e não é contornável** | E | verify-only |
| H7 | HIGH | CVE-2024-47874 `starlette` 0.37.2 multipart DoS (público) | G | aberto |
| H8 | HIGH | CVE-2024-53981 `python-multipart` 0.0.9 DoS (público) | G | aberto |
| M-IDOR | MED | Módulos grandes nunca auditados endpoint-a-endpoint (posse de objeto) | C | **corrigido** (US1; 185 rotas classificadas — SC-001=100%; `test_idor_coverage.py` + negativos em `test_idor.py`) |
| M-UPL-size | MED | Limite de upload só após ler corpo inteiro (exaustão) | F | aberto |
| M-UPL-quota | MED | Sem teto de volume de upload por utilizador | F | aberto |
| M-UPL-hdr | MED | Nginx serve `/uploads` sem os security headers da app | A/D | recomendação-infra |
| M-SSRF-dns | MED | Guarda SSRF do push cega a DNS (rebinding) | F | aberto |
| M-SSRF-redir | MED | Push segue redireções (contorna a guarda) | F | aberto |
| M-SECRET | MED | `SECRET_KEY` sem mínimo de entropia | E | aberto |
| M-PROXY | MED | Confiança em `cf-connecting-ip`/proxy a validar no VPS | D | recomendação-infra |
| M-QR | MED | Validador QR público colhe PII sem rate-limit | D/US1 | **corrigido** (US1: resposta reduzida — `admission_date` removido; `stats.py`). Rate-limit vem do default de US2 (T021) |
| M-PII | MED | Gating de PII sensível só em `users.py` | B | **corrigido/aceite** (US1; auditadas as agregações fora de `users.py` — todas allowlists sem PII sensível ⇒ superfície nula; guard `test_pii_projection_guard.py`) |
| M-AUDIT | MED | `audit_logs.details` acumula PII sem retenção | (US5) | **parcial** (US1: guard de segredos `test_audit_no_secrets.py` — details sem password/token/secret); **retenção/redação = adiado** (data-model) |
| M-REGEX | MED | `$regex` = ReDoS latente (seguro só por disciplina do chamador) | FR-013 | aberto |
| M-HREF | MED | `javascript:`/`data:` em `href` de campos da BD | F | aberto |
| M-CSP | MED | Sem CSP + scripts terceiros no `index.html` (SPA) | US2 (T025) | aberto |
| M-DEPS | MED | Pillow/Jinja2 desatualizados; sem lockfile/scanning | G | aberto |
| M-CRA | MED | `react-scripts` (CRA) EOL arrasta árvore vulnerável build-time | G | adiado-LOW |
| M-STORE | MED | Contadores de rate-limit por-worker (`--workers 2`) | D | aceite (ceiling) |
| LOW ×~30 | LOW | timing/enum, lockout-DoS, tokens em claro at-rest, `/brand/icon` open-redirect, `python-jose`/`passlib`, tabnabbing, COOP/CORP, `/api/health` unthrottled, etc. | — | **adiado (backlog)** |

> Nota de escopo: alguns MEDIUM de infra/frontend (M-UPL-hdr, M-PROXY, M-CSP)
> resolvem-se parcialmente no VPS/edge → entregues como **recomendação com STOP**
> (a parte versionada no repo é corrigida; a parte no VPS é confirmada com o dono).

## Decisões de remediação (por workstream)

### WS-A — Confidencialidade de artefactos (H1) · esforço S
- **Decision**: Classes de confidencialidade — CONFIDENCIAL = `documents` (já gated) +
  `proofs`; PÚBLICO = `avatars`/`logos`/`banners`/`brand`/`covers`/`gallery`. Gate
  `proofs` como `documents` em 3 pontos: (1) `server.py` `UploadsStaticFiles` bloqueia
  também `proofs/` (404); (2) novo `GET /api/finances/transactions/{id}/proof`
  (`require_view_finances`, `find_one` por id, resolver com traversal guard sob
  `UPLOAD_DIR/proofs`, `FileResponse` + `Cache-Control: no-store`) — **autoriza pelo
  id da transação, não pelo filename**; (3) `deploy/nginx/accta.conf`:
  `location ^~ /uploads/proofs/ { return 404; }` (a parte **load-bearing** em prod).
- **Rationale**: reutiliza o padrão `documents` (app 404 + nginx 404 + FileResponse
  RBAC). Zero referências frontend a `proofs`/`proof_url` hoje → tightening puro sem
  regressão. Raiz: só `documents` foi adicionado às block lists.
- **Alternatives**: só `server.py` (dead code em prod — nginx serve antes); apagar a
  categoria (descarta feature CF latente); endpoint por filename (enumeração); signed
  URLs/access-log (YAGNI).
- **Contract**: remove `GET /uploads/proofs/*` (404); adiciona endpoint autenticado.
- **STOP**: nginx do VPS na mesma janela de deploy (senão fica público).
- **Data model**: nenhum (`Transaction.proof_url` já existe).

### WS-B — Chokepoint de projeção de segredos (H5, FR-005) · esforço S
- **Decision**: (b)+(c). **(b)** `response_model=User` no único endpoint client-facing
  que falta — `GET /api/users/{id}` — e, quase-grátis, `PATCH /api/users/me/profile`;
  depois disto os 4 endpoints que devolvem user serializam por modelos sem password/MFA
  (`extra="ignore"`). `_user_projection` fica **inalterado** (é o gate FR-005 de PII).
  **(c)** tripwire `test_users_secret_projection.py`: (1) `User(**doc)`/`Token(...)` com
  password+MFA injetados → dump não os contém; (2) as rotas que devolvem user declaram
  `response_model≠None`; (3) `_user_projection(True/False)` exclui password+MFA e
  strip de `SENSITIVE_PROFILE_FIELDS` quando não-self.
- **Rationale**: backstop estrutural na serialização + tripwire, sem tocar o read do
  login (que precisa do hash para `verify_password`). Não purga `mfa_secret*` físico
  (migração destrutiva = STOP, e desnecessária).
- **Alternatives**: (a) strip no DAO — rejeitado (login precisa do hash internamente).
- **Contract**: leve tightening — PII de terceiros passa de «ausente» a `null`
  (verificar que o frontend não distingue).
- **Data model**: nenhum. Purga de `mfa_secret*` = **adiado (STOP)**.

### WS-C — Largura IDOR (FR-003, SC-001) · esforço M
- **Decision**: metodologia em 3 camadas, **em código de teste, provável por construção**:
  (L1) `test_idor_coverage.py` enumera de `api_router` todas as rotas com `{param}`
  (hoje 327 rotas, 184 recebem id) — calcula o denominador de SC-001 em runtime, nunca
  fica stale; (L2) registo `AUDIT` classifica cada rota id-taking numa de {public,
  authenticated, role, owner, parent_scoped} com citação do gate; tripwire
  `test_every_id_route_classified` exige `set(enumerado)==set(AUDIT)` → SC-001 =
  `len(AUDIT)/len(enumerado)==1.0`; (L3) prova comportamental só onde há superfície IDOR
  real (owner/parent_scoped): `test_owner_scoped_routes_have_behavioral_test` + estender
  `test_idor.py` com negativos «B não toca no objeto de A» (~15–25 rotas, não 184).
  **Bundle**: corrigir `wall.py:60` (resolver moderadores por `moderate_content`, não
  pelo role morto `moderador`) + tripwire `test_no_legacy_role_in_db_query`.
- **Rationale**: torna SC-001 auto-regenerável e regression-guarded; melhor que uma
  matriz manual que apodrece. Bulk das mutações grandes é role-class (já coberto por
  `test_access_matrix.py`).
- **Contract**: nenhum (só teste + fix interno de destinatários de notificação).
- **Risco**: rubber-stamping do registo → mitigado por PR review + citação obrigatória.
  `helpers.notify_admins` ({"role":"admin"}) tem gap análogo → **LOW/adiado**.

### WS-D — Correção do rate-limit (H2, H3, M-STORE) · esforço S
- **Decision**: 4 partes, sem nova dependência. (1) `app.add_middleware(SlowAPIMiddleware)`
  (outermost) → o default 200/min passa a aplicar-se; (2) extrair `client_ip(request)`
  de `helpers.extract_request_meta` (reusa `_is_trusted_proxy`/`_TRUSTED_PROXY_NETS`) +
  `rate_limit_key(request)`; trocar `key_func=get_remote_address`→`rate_limit_key` nos
  4 `Limiter` (server/auth_routes/contact/comunicados); (3) manter storage `memory://`
  por-worker com `ponytail:` a nomear o teto (≤2× nominal) e o upgrade (Redis/`--workers 1`)
  — aceitável porque o lockout por-email em Postgres é o controlo primário exato; (4)
  manter o conjunto de endpoints sensíveis explícitos; resto coberto pelo default.
  **Não** adicionar `--proxy-headers` (sobrescreveria `request.client` com o XFF
  spoofável e derrotaria `_is_trusted_proxy`).
- **Contract**: 429 do handler existente; comportamento: 200/min agora real por-cliente.
- **Decisão FR-008 (U3)**: o default 200/min por-cliente é considerado **suficiente** para
  os endpoints dispendiosos (geração de PDF/relatórios, agregações, escritas de admin)
  neste ciclo — não se adicionam limites dedicados mais estritos; reavaliar se surgir
  abuso observado. Registado como decisão explícita.
- **STOP/infra**: confirmar no VPS que o edge põe `X-Forwarded-For` e liga de um IP em
  `_TRUSTED_PROXY_NETS` (Docker bridge 172.16/12); senão degrada em segurança para o
  comportamento de hoje (balde partilhado), nunca pior.
- **Data model**: nenhum.

### WS-E — Não-degradação de prod + SECRET_KEY + CSRF (H4, FR-007, H6/FR-009) · esforço S
- **Decision**: 2 gates fail-closed no arranque + 1 lock de teste. (1) `server.py`
  `_looks_like_production()` (urlparse; True se FRONTEND_URL/CORS https não-local) →
  `if _looks_like_production() and not IS_PROD: raise` (liga os 5 controlos degradáveis
  a uma env afirmativa); (2) `auth.py` `if len(SECRET_KEY) < 32: raise` (piso 256-bit
  HS256, todos os ambientes); (3) **H6 = verify-only**: o `CSRFOriginCheckMiddleware` já
  cobre POST/PUT/PATCH/DELETE, exclui métodos seguros, escopa a cookie e **não é
  contornável** pelo modelo cookie+Authorization; em prod o boot gate de CORS garante
  `allowed_origins` não-vazio. Só parametrizar `test_csrf_middleware.py` sobre
  PUT/PATCH/DELETE (FR-009).
- **Contract**: nenhum em runtime; 2 condições de boot que só disparam em misconfig.
- **STOP/infra**: prod passa a **hard-fail** se `ENVIRONMENT≠production` / `SECRET_KEY<32`
  / CORS não definido → **verificar `/docker/accta/.env` no VPS ANTES do release**
  (comprimento do SECRET_KEY é bloqueador de deploy se <32, mas **não** roda a chave).
- **Data model**: nenhum.

### WS-F — SSRF DNS+redirect, upload DoS, URLs (FR-015/016/017/018) · esforço M
- **Decision**: 3 fixes, cada um reusa um padrão do repo. (1) **SSRF push**: companheiro
  async de `is_safe_push_endpoint` que `getaddrinfo` e rejeita se QUALQUER endereço
  resolvido falhar o mesmo predicado `ipaddress` (fail-closed no erro); chamar no send
  (`dispatch_push`), mantendo o check barato no `/subscribe`. Sessão `requests` que força
  `allow_redirects=False` via `webpush(..., requests_session=...)`. TOCTOU DNS-rebind
  aceite (comentário `ponytail:`). (2) **Upload DoS**: `read_upload_capped(file, max)`
  em `file_validation.py` (streaming, 413 ao exceder — nunca buffra >max+chunk) nos 3
  call sites; per-user cap = `@limiter.limit("30/hour")` nos endpoints de upload (per-IP,
  padrão existente). (3) **URLs**: `field_validator` `_v_local_upload_url` (`/uploads/`
  ou vazio/None) em `Benefit/Post/Publicacao.{logo_url,cover_url,capa_url}`; `/brand/icon`
  302 só se `/uploads/` ou host==FRONTEND_URL, senão default estático.
- **Contract**: aditivo/hardening — 413 antes de buffrar; 429 nos uploads; 422 em URL
  não-`/uploads`; `/brand/icon` 302 p/ default se off-frontend.
- **Risco**: verificar que nenhum benefit/post/publicação em prod guarda URL externo
  (senão edit dava 422); se sim, alargar validator a `https://` (padrão brand) ou migrar.
- **Data model**: nenhum (rate-limit em vez de contador persistente).

### WS-G — Dependências + scanning (FR-019/020) · esforço M
- **Decision**: bumps em `requirements.txt`: **par coordenado** FastAPI 0.110.1→0.115.6 +
  Starlette 0.37.2→0.41.3 (fastapi 0.110 fixa starlette<0.38; move-se em par); multipart
  0.0.9→0.0.18; Pillow 10.3.0→11.2.1; Jinja2 3.1.3→3.1.6; requests 2.31.0→2.32.4.
  **Bcrypt 4.0.1 off-limits; python-jose 3.5.0 já patched (fora de âmbito).**
  **Mitigação OBRIGATÓRIA** (`server.py`, ~1 linha): subir `MultiPartParser.max_part_size`
  para ~11 MB — Starlette 0.40+ impõe 1 MB por-parte por default e o FastAPI chama
  `request.form()` sem args, o que **partiria todos os uploads >1 MB** antes do check da
  rota. **Scanning**: `.github/dependabot.yml` (pip→/backend, npm→/frontend, semanal,
  agrupado) — corre na infra do GitHub, **independente do CI billing-locked**; +
  `scripts/audit_deps.sh` (pip-audit + yarn npm audit) como gate local.
- **Contract**: nenhum SE a mitigação `max_part_size` for aplicada (o teste de upload
  >1 MB é o **árbitro** do bump). Sem ela, todos os uploads >1 MB dariam 400.
- **STOP**: Via B + push a `main`; dono ativa Dependabot alerts+security updates nas
  Security settings do repo (ação GitHub, não código).
- **Risco**: salto de 5 minors no FastAPI → correr a suíte completa (~1575) como gate;
  Pillow 11 + fpdf2 (carteira PDF spec 007) → smoke; pydantic fica em 2.6.4 (contingência
  2.9.x se surgir incompat).

### FR-013 — Centralizar escape de `$regex` (M-REGEX) · esforço S
- **Decision**: mover a lógica `_safe_search_regex` (finances) para um helper partilhado
  usado por todos os call sites de `$regex` (finances/users/posts) + tripwire que
  nenhum passa input não-escapado; opcionalmente escapar/limitar no DAO `_field_clause`
  como defesa-em-profundidade. Mantém o invariante independente de o chamador se lembrar.

## Confirmações do dono / operacionais (resolver no release, não bloqueiam o plano)

1. **[STOP]** Aplicar a regra nginx `/uploads/proofs/` no VPS na MESMA janela do deploy da Fase 1 (senão os comprovativos ficam públicos).
2. **[STOP]** Antes da Fase 2: confirmar no `/docker/accta/.env` do VPS que `ENVIRONMENT=production` e `SECRET_KEY` tem ≥32 chars (senão o container não arranca).
3. **[ação GitHub]** Ativar Dependabot alerts + security updates nas Security settings do repo (Fase 3, FR-020).
4. Aceitar o teto ~2× por-worker no rate-limit (recomendado) vs. Redis/`--workers 1` (STOP infra)? — recomendação: aceitar.
5. Verificar (grep) que nenhum benefit/post/publicação guarda URL externo de logo/capa antes de ligar o validator `/uploads`-only (WS-F).
6. Adiar (LOW) os ficheiros de galeria pendente/rejeitada públicos por UUID e o gap `notify_admins {"role":"admin"}`? — recomendação: adiar.
7. Purga física de `mfa_secret*` legado — adiar como migração gated (recomendado)?
