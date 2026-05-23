# Spec — Verificação de Segurança "SaaS Production-Ready" (adaptada ao Portal ACCTA)

> **Origem**: prompt genérico de "build a production-ready SaaS with secure-by-design
> principles" (brute-force, MFA, sessões seguras, SQLi/XSS/CSRF, IDOR, RBAC/ABAC, API
> segura, headers, monitorização/logging, backup/DR, arquitetura limpa). **Adaptado** ao
> Portal ACCTA, que **já está a meio do desenvolvimento** — logo este NÃO é um spec de
> "construir do zero", é um **spec de verificação + fecho de lacunas**: para cada exigência
> do prompt, confirmamos o que **já existe** (com evidência `ficheiro:linha`), **como provar
> que funciona** (teste/comando), e **só** então o que falta.
>
> **Objetivo**: dar ao Portal ACCTA uma checklist executável de prontidão de segurança para
> produção, sem reconstruir controlos que já existem nem inventar vulnerabilidades.
>
> **Estado do sistema (2026-05-23)**: app **ainda não em produção**, **sem dados reais** →
> aditivo é o padrão; migração/drop de dados é _stop condition_. Stack: FastAPI (Python 3.11)
> + asyncpg/Postgres (Supabase) via DAO Mongo-compatível (`database.py`), React 19, JWT HS256,
> RBAC (admin/financeiro/moderador/socio) + privilégios aditivos.
>
> **Base prévia**: `tasks/spec-security-review-concluido.md` — `/security-review` do branch de
> integração fechou com **0 achados HIGH/MEDIUM** e o único LOW (auto-edição de licença)
> resolvido por decisão de produto. Este spec é mais largo (todo o sistema, não só um diff).
>
> **Regras do projeto** (`.claude/rules/*`, `CLAUDE.md`): PT em texto de utilizador; Pydantic
> em todo body; `async/await`; **RBAC em toda rota protegida**; **audit log em toda ação
> admin**; sem SQL bruto nas rotas; datas ISO-8601; nunca expor `password`; enviar emails reais
> e push para `main` são _stop conditions_; `pytest` verde antes de "done".

---

## 0. Como usar este spec (protocolo de verificação)

Cada controlo é avaliado com **veredito + evidência + método de verificação**:

| Veredito | Significado |
|---|---|
| ✅ **Implementado** | Existe no código; ação = **provar com teste/comando** (regressão) |
| ⚠️ **Parcial** | Existe mas com lacuna ou por reforçar |
| ❌ **Ausente** | Lacuna real a fechar |
| 🛠️ **Infra** | Fora do código da app (Nginx/Render/Vercel/Supabase) — documentar e confirmar com o operador |

Princípio condutor: **não reconstruir o que já existe**. A maior parte do trabalho deste spec é
**cobertura de testes** (provar que os controlos existentes funcionam) + **3–4 lacunas reais**.

---

## 1. Resumo executivo — estado por área

| # | Área (exigência do prompt) | Veredito | Lacuna principal |
|---|---|---|---|
| 2 | Arquitetura segura por design | ✅ | doc de modelo de ameaças ausente (menor) |
| 3 | Hashing de password (bcrypt/Argon2) | ✅ | mínimo de 6 chars é fraco (⚠️) |
| 3 | MFA / 2FA | ❌ | **sem MFA** (alto valor p/ admin/financeiro) |
| 3 | Sessão segura (httpOnly/Secure/SameSite) | ✅ | sem refresh token (⚠️, aceitável) |
| 4 | Brute-force: rate limit + lockout | ✅ | sem testes de integração (⚠️) |
| 4 | CAPTCHA / deteção de anomalia IP | ⚠️ | mitigado por honeypot+lockout; sem CAPTCHA |
| 5 | SQL Injection (queries parametrizadas) | ✅ | provar com teste de fuzz (regressão) |
| 5 | XSS / CSP / output encoding | ✅ | confirmar CSP e ausência de `dangerouslySetInnerHTML` |
| 5 | CSRF (tokens / origin check) | ✅ | sem teste do middleware (⚠️) |
| 6 | IDOR / RBAC / ownership | ✅ | **sem testes de regressão IDOR** (⚠️→❌ em teste) |
| 7 | API segura (authn/authz, error handling) | ✅ | confirmar nenhuma rota sem `get_current_user` |
| 7 | HTTPS/TLS 1.2+ + HSTS | 🛠️/✅ | TLS é infra; HSTS já no código (prod) |
| 7 | Security headers | ✅ | provar com teste de headers |
| 8 | Audit logging | ✅ | sem alertas; logs no mesmo DB (⚠️) |
| 8 | Monitorização / alertas de anomalia | ❌ | **sem alertas** (logins falhados, escalada) |
| 9 | Backup / disaster recovery | 🛠️ | documentar política (Supabase/infra) |
| 10 | Segredos / `.env` | ✅ | sem rotação de `SECRET_KEY` (⚠️) |
| 11 | Cobertura de testes de segurança | ⚠️ | **lacuna transversal** (ver §11) |

**Conclusão de uma linha**: o ACCTA cobre **a esmagadora maioria** do checklist SaaS por
design; o trabalho real é **(a) escrever os testes de regressão de segurança** que faltam,
**(b) MFA para contas privilegiadas**, **(c) política de password**, **(d) alertas** e
**(e) documentar TLS/backup/DR** (infra).

---

## 2. Arquitetura segura por design

| Requisito (prompt) | Estado ACCTA | Evidência |
|---|---|---|
| Modular, documentado, extensível | ✅ Monólito modular: 1 router por domínio | [`backend/routes/`](../backend/routes/) (~27 módulos), `models.py`/`auth.py`/`helpers.py`/`database.py` separados |
| Validação/sanitização por camadas | ✅ Pydantic na borda + RBAC + DAO parametrizado | `CLAUDE.md`, `.claude/rules/api.md` |
| Documentação | ✅ `CLAUDE.md`, `.claude/rules/{api,database,models,frontend}.md`, specs em `tasks/` | — |

**Verificação**:
- [ ] Confirmar que **nenhuma** rota nova ignora o padrão (router por domínio, `Depends(get_current_user)`).
- [ ] (Menor) Acrescentar um _threat model_ curto ao topo deste spec ou a `tasks/` se a Direcção exigir.

**Veredito**: ✅ — arquitetura adequada (modular monolith). Sem ação de código.

---

## 3. Autenticação e sessões

### 3.1 Hashing de password — ✅
- **Estado**: bcrypt com **12 rounds** via passlib; nunca em plaintext; `password` excluído de
  todas as respostas (projeções `{"password": 0}`).
- **Evidência**: [`auth.py:12`](../backend/auth.py#L12), [`auth.py:53-58`](../backend/auth.py#L53) (`hash_password`/`verify_password`).
- **Nota**: o prompt aceita "bcrypt **ou** Argon2" → bcrypt-12 satisfaz. **Não migrar** para Argon2 (sem ganho que justifique re-hash de todos).
- **Verificação**: [ ] `pytest tests/test_password_recovery.py tests/test_auth_routes.py` verde; confirmar que resposta de login/perfil **nunca** contém `password`.

### 3.2 Política de password — ⚠️ (lacuna menor)
- **Estado atual**: mínimo de **6 caracteres** ([`auth_routes.py:283`](../backend/routes/auth_routes.py#L283), [`auth_routes.py:390`](../backend/routes/auth_routes.py#L390)); sem regras de complexidade nem verificação de _breach_.
- **Ação (P1)**: subir mínimo para **≥ 8** e centralizar a regra num único validador
  (`models.py` ou helper) usado por `setup-account` e `reset-password`. Complexidade/HIBP são opcionais (decisão D2).
- **Aceitação**: password com 7 chars → `400`; com 8 → aceite; teste cobre ambos os endpoints.

### 3.3 MFA / 2FA — ❌ (lacuna real, alto valor)
- **Estado**: **inexistente** (sem TOTP/OTP/`pyotp`, sem endpoint de _enroll_).
- **Risco**: contas `admin`/`financeiro` gerem utilizadores, finanças e moderação — roubo de
  password = comprometimento total. É o gap de maior valor do prompt.
- **Ação (P1) — desenho proposto** (aditivo, sem quebrar contas existentes):
  - `UserBase`: campos aditivos `mfa_enabled: bool=False`, `mfa_secret: Optional[str]` (cifrado/derivado), `mfa_backup_codes: Optional[list[str]]` (hash). **Nunca** devolver `mfa_secret`/códigos em respostas.
  - `POST /api/auth/mfa/setup` (autenticado) → gera segredo TOTP + QR + códigos de recuperação.
  - `POST /api/auth/mfa/verify` → confirma o 1.º código e ativa.
  - `POST /api/auth/login` passo 2: se `mfa_enabled`, exige `otp` antes de emitir o JWT/cookie.
  - `POST /api/auth/mfa/disable` (re-autenticação) + consumo de _backup code_.
  - **Política**: **obrigatório** para `role in {admin, financeiro}` (decisão D1); opcional para sócios.
  - Audit: `mfa_enabled`, `mfa_disabled`, `login_mfa_challenge`, `login_mfa_failed`.
- **Aceitação**: admin com MFA ativo não obtém sessão sem OTP válido; _backup code_ é de uso único; sócio sem MFA continua a entrar normalmente.

### 3.4 Sessão segura (cookies) — ✅
- **Estado**: JWT em **cookie httpOnly** (`accta_session`); `Secure=True` + `SameSite=None` em
  produção (cross-site Vercel↔Render), `SameSite=Lax` em dev; fallback `Authorization: Bearer`
  para compat; logout limpa cookie **e** revoga via blocklist por `jti`.
- **Evidência**: [`auth.py:20-50`](../backend/auth.py#L20) (cookie), [`auth.py:106-127`](../backend/auth.py#L106) (`is_token_revoked`/`revoke_token`), [`auth.py:98-103`](../backend/auth.py#L98) (JWT+`jti`), expiry 24h ([`auth.py:18`](../backend/auth.py#L18)).
- **Frontend**: sessão restaurada via `GET /auth/me` no _mount_ ([`AuthContext.js`](../frontend/src/contexts/AuthContext.js)).
- **⚠️ sem refresh token**: expiry 24h → re-login. **Aceitável** (decisão D3 se quiserem sliding window).
- **Verificação**: [ ] `pytest tests/test_auth_hardening.py` (cobre `jti`, blocklist, logout, tokens legacy sem `jti` tratados como revogados). [ ] Confirmar `httpOnly`/`Secure`/`SameSite` na resposta `Set-Cookie` (curl).

---

## 4. Proteção contra brute-force

| Controlo (prompt) | Estado | Evidência |
|---|---|---|
| **Account lockout** | ✅ 5 falhas / 15 min → bloqueio 15 min; verificação **antes** do bcrypt (anti-enumeração por timing); reset no sucesso | [`helpers.py:71-110`](../backend/helpers.py#L71), [`auth_routes.py:50-94`](../backend/routes/auth_routes.py#L50) |
| **Rate limiting** | ✅ login 10/min, register 3/h, setup 5/min, forgot 3/min, reset 5/min, default 200/min (slowapi por IP) | [`auth_routes.py:51,149,266,349,380`](../backend/routes/auth_routes.py#L51), [`server.py:18`](../backend/server.py#L18) |
| **Honeypot** | ✅ campo invisível `website` no registo → bots descartados | [`auth_routes.py:157`](../backend/routes/auth_routes.py#L157) |
| **CAPTCHA** | ❌ ausente | — |
| **Deteção de anomalia IP** | ❌ ausente | — |

- **Verificação (P0 — escrever testes)**:
  - [ ] Teste de **lockout de integração**: 5 logins falhados → 6.º devolve bloqueio; após janela, desbloqueia.
  - [ ] Teste de **rate-limit**: 11.ª chamada a `/auth/login` em 60s → `429` (ver `CLAUDE.md`: desativar `limiter.enabled=False` **não** aqui — aqui queremos testá-lo; usar `Request` real).
- **CAPTCHA / anomalia IP (P2)**: honeypot + rate-limit + lockout já dão fricção significativa.
  CAPTCHA só em `register`/`forgot-password` **se** houver abuso real (decisão D4). Anomalia IP é
  candidato a §8 (alertas), não bloqueio.

**Veredito**: ✅ núcleo forte; ação principal = **testes** (P0). CAPTCHA/IP-anomaly = P2 condicional.

---

## 5. Injeção e ataques client-side

### 5.1 SQL Injection — ✅
- **Estado**: DAO traduz filtros Mongo-style para SQL **100% parametrizado** (`$1,$2,…` via
  `_WhereBuilder._ph()`); identificadores de tabela com allowlist + `_quote_ident`; **zero
  f-string SQL**; **nenhum SQL bruto nas rotas**.
- **Evidência**: [`database.py:248-450`](../backend/database.py#L248) (`_WhereBuilder`), `.claude/rules/api.md` ("nunca SQL bruto nas rotas").
- **Verificação (P0)**: [ ] Teste de fuzz: passar `"' OR 1=1 --"`, `"$ne"`, payloads em filtros de pesquisa (`finances`, `posts`) → tratado como literal, sem erro SQL nem fuga. (Pesquisa de posts já faz `re.escape`; `finances` usa `_safe_search_regex` com truncagem a 100 chars — anti-ReDoS, [`finances.py:28-33`](../backend/routes/finances.py#L28).)

### 5.2 XSS / CSP / output encoding — ✅
- **Estado**: `SecurityHeadersMiddleware` injeta **CSP restritiva** (`default-src 'self'`,
  `script-src 'self'`, `object-src 'none'`, `frame-ancestors 'none'`, `base-uri 'self'`,
  `img-src 'self' data: blob:`), além de `X-Content-Type-Options: nosniff`. React auto-escapa
  output; upload de **SVG bloqueado** (XSS armazenado).
- **Evidência**: [`server.py:24-52`](../backend/server.py#L24) (middleware/CSP), [`file_validation.py`](../backend/file_validation.py) (SVG bloqueado, magic-bytes).
- **Verificação (P0)**:
  - [ ] `grep -rn "dangerouslySetInnerHTML" frontend/src` → **0 ocorrências** (ou justificadas+sanitizadas).
  - [ ] Teste de header: resposta da API contém o `Content-Security-Policy` esperado (e ausente em `/docs`).
  - [ ] Validação client + server: o servidor é a borda autoritativa (Pydantic). Validação no React é UX, não confiança.

### 5.3 CSRF — ✅
- **Estado**: `CSRFOriginCheckMiddleware` valida `Origin`/`Referer` contra `CORS_ORIGINS` em
  métodos _unsafe_ (POST/PUT/PATCH/DELETE) **quando há cookie de sessão**; clientes
  header-only (Bearer) são imunes; combinado com `SameSite`.
- **Evidência**: [`server.py:65-106`](../backend/server.py#L65), [`server.py:158`](../backend/server.py#L158) (middleware registado).
- **Nota**: o prompt pede "CSRF tokens". A abordagem **Origin-check + SameSite** é equivalente em
  garantia para auth baseada em cookie e **não** requer tokens sincronizados (browsers não deixam
  JS forjar `Origin`). Manter; tokens seriam defesa-em-profundidade opcional (D5).
- **Verificação (P0)**: [ ] Teste do middleware: POST com cookie + `Origin` não-permitido → `403`; POST com cookie sem `Origin`/`Referer` → `403`; POST Bearer (sem cookie) → passa.

---

## 6. Controlo de acesso — RBAC / IDOR

### 6.1 RBAC / privilégios — ✅
- **Estado**: roles `admin`/`financeiro`/`moderador`/`socio` + **privilégios aditivos**
  (`role OR privilege`, ex. `view_finances_readonly` p/ Conselho Fiscal). Helpers de elegibilidade
  (`is_direcao`/`is_conselho_fiscal`/`is_voting_member`) em `permissions.py`. Frontend espelha.
- **Evidência**: [`auth.py:65-95`](../backend/auth.py#L65) (`has_privilege`/`can_view_finances`/`can_manage_finances`), [`permissions.py`](../backend/permissions.py), [`AuthContext.js`](../frontend/src/contexts/AuthContext.js).
- **ABAC**: o prompt diz "RBAC **ou** ABAC". ACCTA usa RBAC + atributos (cargo/órgão/status/categoria) na elegibilidade → híbrido suficiente. **Não** introduzir motor ABAC.

### 6.2 IDOR / ownership — ✅ (verificado neste spec)
Auditei os endpoints que o survey marcou "por confirmar" — **as verificações de posse existem**:

| Recurso | Verificação de posse | Evidência |
|---|---|---|
| Notifications (GET/read/delete) | tudo _scoped_ a `{"user_id": current_user.id}` | [`notifications.py:22,84,96,104`](../backend/routes/notifications.py#L22) |
| Projetos (get/update/delete) | `can_manage/can_view_project` (admin OR criador OR responsável); lista filtra não-admin | [`projects.py:53-61,83-87,155-159,187-188`](../backend/routes/projects.py#L53) |
| Comentários de projeto (delete) | `comment["user_id"] != current_user.id and role != admin` → 403 | [`projects.py:466-476`](../backend/routes/projects.py#L466) |
| Despesas/milestones de projeto | 403 sem permissão de gestão | [`projects.py:549-559,632-642`](../backend/routes/projects.py#L549) |
| Galeria (fotos) | público e não-admin forçam `status="approved"`; só admin filtra por `status` | [`gallery.py:44,144-148`](../backend/routes/gallery.py#L144) |
| Wall posts (delete) | só moderador OR autor | [`wall.py:93-108`](../backend/routes/wall.py#L93) |
| Audit logs (query) | `has_role_or_privilege(admin, view_audit_logs)` | [`notifications.py:154-163`](../backend/routes/notifications.py#L154) |
| Documentos | servidos por rota autenticada, **não** por `/uploads/documents` (Mount bloqueia) | [`server.py:55-62,128-130`](../backend/server.py#L55) |
| Eleições (voto secreto) | recibos HMAC-SHA256, cédula separada do recibo; apuração lê só `vote_option` | `tasks/spec-security-review-concluido.md` (Apêndice A) |

- **Lacuna real (P0)**: **não há testes de regressão IDOR**. O código está correto **hoje**, mas
  nada impede uma regressão futura.
- **Ação (P0)**: criar `tests/test_idor.py` parametrizado — "utilizador B tenta ler/editar/apagar
  recurso do utilizador A → `403/404`" para: notifications, comentários/despesas/milestones de
  projeto, wall, fotos pendentes de galeria, e ler cédula/recibo de outro eleitor.
- **Verificação**: [ ] `tests/test_idor.py` cobre ≥ 8 pares (recurso × verbo) e passa.

---

## 7. Desenho seguro de API

| Requisito | Estado | Evidência / Verificação |
|---|---|---|
| authn/authz em todos os endpoints | ✅ `Depends(get_current_user)` + check de role/privilégio por rota | `.claude/rules/api.md`; [ ] **verificar** que nenhuma rota protegida ficou sem `get_current_user` (grep por `@router` sem `Depends`) |
| Rate limiting | ✅ ver §4 | — |
| Validação de input | ✅ Pydantic em todo body; enums/bounds; upload com magic-bytes + size por categoria | [`models.py`](../backend/models.py), [`file_validation.py`](../backend/file_validation.py), [`upload.py`](../backend/routes/upload.py) |
| Error handling sem fuga | ✅ `HTTPException` com mensagens limpas; `upload.py` deixou de devolver `str(e)` em 500 | `tasks/spec-security-review-concluido.md` (Apêndice B); [ ] confirmar que 500 não expõe stack trace em prod (FastAPI sem `debug`) |
| HTTPS / TLS 1.2+ | 🛠️ **infra** (Nginx/Render terminam TLS) + ✅ **HSTS no código** em prod | [`server.py:47-51`](../backend/server.py#L47); [ ] confirmar TLS≥1.2 e redireção 80→443 no Nginx/Render |
| Security headers | ✅ `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, CSP, HSTS(prod) | [`server.py:24-52`](../backend/server.py#L24); [ ] **teste de headers** (P0) |
| CORS | ✅ allowlist; **recusa arrancar com `*` em produção**; `allow_credentials` só com origens explícitas | [`server.py:134-158`](../backend/server.py#L134) |

**Verificação (P0)**: [ ] `tests/test_security_headers.py` — afirma cada header e o conteúdo do CSP; confirma HSTS quando `ENVIRONMENT=production`.

---

## 8. Monitorização, logging e alertas

### 8.1 Audit logging — ✅
- **Estado**: `create_audit_log(user_id, action, target_id, request, details)` captura IP +
  User-Agent + ação + alvo; **117+ chamadas** em login, convites, aprovação/rejeição, transições de
  cargo, finanças, uploads, moderação. Query via `GET /api/audit-logs` (admin/`view_audit_logs`).
- **Evidência**: [`helpers.py:132-161`](../backend/helpers.py#L132), [`notifications.py:154-163`](../backend/routes/notifications.py#L154).
- **⚠️ Lacuna**: logs no **mesmo Postgres** (um admin comprometido podia apagá-los) e **sem TTL/ret-policy**.
  - **Ação (P2)**: política de retenção + (opcional) _sink_ append-only externo (syslog/serviço) para
    não-repúdio. Para já, restringir `DELETE` em `audit_logs` ao nível de role do DB.

### 8.2 Alertas de atividade suspeita — ❌ (lacuna real)
- **Estado**: os eventos são **registados** (login falhado, lockout, broadcast, transições de cargo),
  mas **não há alertas** ativos.
- **Ação (P2)**: gerar `notify_admins()` (canal "system"/"admin") quando: (a) lockout disparado,
  (b) N logins falhados de IPs distintos para a mesma conta, (c) alteração de `role`/`privileges`
  (potencial escalada), (d) pico anómalo de 4xx/429. Reutiliza infra de notificações existente
  (SSE + email). Sem novo sistema externo.
- **Aceitação**: lockout de uma conta → admins recebem notificação "system"; promoção a admin → alerta.

---

## 9. Backup e recuperação de desastres — 🛠️ (infra)

- **Estado**: fora do código; depende de Supabase/Postgres e do alojamento.
- **Ação (documentar + confirmar com operador, não código)**:
  - [ ] Confirmar **backups automáticos** do Supabase (PITR / snapshots diários) e janela de retenção.
  - [ ] Documentar **RPO/RTO** alvo e um _runbook_ de restauro em `tasks/` ou `docs/`.
  - [ ] Testar um restauro de _staging_ pelo menos uma vez antes de produção.
- **Nota**: nenhuma alteração de código; é uma _gate_ operacional de prontidão para produção.

---

## 10. Segredos e configuração

| Item | Estado | Evidência |
|---|---|---|
| `SECRET_KEY` obrigatório | ✅ `RuntimeError` no arranque se ausente | [`auth.py:14-16`](../backend/auth.py#L14) |
| `DATABASE_URL` obrigatório | ✅ idem | [`database.py`](../backend/database.py) (`load_dotenv` + check) |
| Sem segredos hardcoded | ✅ confirmado (survey + security-review prévio) | `tasks/spec-security-review-concluido.md` (Apêndice A) |
| Tokens (convite/reset) com CSPRNG | ✅ `secrets.token_urlsafe`/UUID; reset 1h uso-único; convite 7 dias | [`auth_routes.py:348-402`](../backend/routes/auth_routes.py#L348), [`admin.py:38-113`](../backend/routes/admin.py#L38) |
| `.env` documentado | ✅ `CLAUDE.md` (tabela de env vars) | — |
| **Rotação de `SECRET_KEY`** | ⚠️ ausente (rotação = re-login global) | **stop condition** em `CLAUDE.md` |

- **Ação (P3, opcional)**: suportar `SECRET_KEY` + `SECRET_KEY_PREVIOUS` (verificar com ambas durante
  janela de graça) para permitir rotação sem deslogar todos. **Stop condition** — confirmar com o dono.

---

## 11. Cobertura de testes de segurança (lacuna transversal — núcleo do P0)

**Já existe**: `test_auth_hardening.py` (jti/blocklist/lockout), `test_permissions.py` (RBAC/órgãos),
`test_rbac_matrix.py`, `test_invite_auth.py`, `test_password_recovery.py`, `test_auto_registo.py`.

**Falta (escrever)**:
- [ ] `tests/test_idor.py` — matriz B-acede-a-recurso-de-A → 403/404 (§6.2).
- [ ] `tests/test_security_headers.py` — todos os headers + CSP + HSTS(prod) (§7).
- [ ] `tests/test_csrf_middleware.py` — Origin não-permitido/ausente com cookie → 403; Bearer passa (§5.3).
- [ ] `tests/test_rate_limit.py` — `429` ao exceder login/forgot (§4).
- [ ] `tests/test_lockout_integration.py` — 5 falhas → bloqueio → desbloqueio pós-janela (§4).
- [ ] `tests/test_sql_injection_fuzz.py` — payloads em filtros de pesquisa tratados como literais (§5.1).
- [ ] (após MFA) `tests/test_mfa.py` — challenge obrigatório p/ admin, backup code uso-único (§3.3).

> Nota de arquitetura de testes (`CLAUDE.md`): para rotas `@limiter.limit`, nos testes que **não**
> testam o limite usar `monkeypatch.setattr(<modulo>.limiter, "enabled", False)` + `Request` real;
> nos testes de rate-limit (`test_rate_limit.py`) **manter** o limiter ativo. `mock_db` não pré-liga
> `project_tasks/comments/expenses/milestones` — ligar in-test. bcrypt fixo em `4.0.1`.

---

## 12. Lacunas priorizadas + plano faseado

PRs pequenos, **`feature/* → develop`** (GitFlow; nunca direto a `main`).

| Fase | Entrega | Prioridade | Toca |
|---|---|---|---|
| **F0 — Provar o que já existe** | `test_idor`, `test_security_headers`, `test_csrf_middleware`, `test_rate_limit`, `test_lockout_integration`, `test_sql_injection_fuzz` | **P0** | só `tests/` |
| **F1 — Password policy** | mínimo ≥ 8 + validador único (§3.2) | P1 | `models.py`/`auth_routes.py` + teste |
| **F2 — MFA (TOTP)** | enroll/verify/disable + gate no login p/ admin/financeiro (§3.3) | P1 | `models.py`, `auth.py`, `auth_routes.py`, frontend, `test_mfa` |
| **F3 — Alertas de anomalia** | `notify_admins` em lockout/escalada/picos (§8.2) | P2 | `helpers.py`/`auth_routes.py`/`admin.py` |
| **F4 — Hardening audit log** | retenção + restrição de DELETE (§8.1) | P2 | `database.py`/política DB |
| **F5 — Infra (doc/operador)** | TLS≥1.2, backups/PITR, RPO/RTO runbook, rotação `SECRET_KEY` opcional (§7,§9,§10) | P2/P3 | docs + confirmação do operador |

**Ordem dentro de cada fase**: (models/aditivos →) endpoints + RBAC + audit → testes backend →
frontend → verificação manual.

---

## 13. Checklist executável (cole no PR)

**P0 — verificação (sem mudar comportamento, só provar):**
- [ ] `grep -rn "dangerouslySetInnerHTML" frontend/src` → 0 (ou justificado)
- [ ] grep por `@router.(get|post|put|patch|delete)` em rotas protegidas sem `Depends(get_current_user)` → 0
- [ ] `pytest tests/test_auth_hardening.py tests/test_permissions.py tests/test_rbac_matrix.py` verde
- [ ] novos: `test_idor`, `test_security_headers`, `test_csrf_middleware`, `test_rate_limit`, `test_lockout_integration`, `test_sql_injection_fuzz` verdes
- [ ] `curl -I` confirma `Set-Cookie` httpOnly/Secure/SameSite e os headers de segurança

**P1 — lacunas reais:**
- [ ] password mínimo ≥ 8 (D2)
- [ ] MFA TOTP obrigatório p/ admin/financeiro (D1)

**P2/P3 — defesa em profundidade / infra:**
- [ ] alertas de anomalia (lockout, escalada de privilégio)
- [ ] retenção/imutabilidade de audit log
- [ ] TLS≥1.2 + redireção + backups/PITR + runbook DR (operador)
- [ ] rotação de `SECRET_KEY` (D6, stop condition)

---

## 14. Stop conditions (de `CLAUDE.md` — confirmar antes de avançar)

- **Mudar `SECRET_KEY`/algoritmo de auth** (invalida todas as sessões) — F5 rotação.
- **Alterar Pydantic de forma não-aditiva** — campos de MFA/password devem ser **aditivos/opcionais**.
- **Migrar/dropar dados** — não aplicável (app sem dados reais), mas qualquer migração futura é gate.
- **Modificar `CORS_ORIGINS` em produção**; **remover rota** usada pelo frontend.
- **Enviar emails reais** (o fluxo de MFA/reset não deve disparar email a utilizadores reais em teste).
- **Push para `main`** — só via release/hotfix PR.

---

## 15. Decisões a confirmar com o dono (gates)

- **D1 — MFA obrigatório**: só `admin`+`financeiro`, ou também `moderador`? Sócios = opcional?
- **D2 — Política de password**: mínimo 8 chega, ou exigir complexidade / verificação HIBP?
- **D3 — Refresh token**: manter 24h com re-login (atual), ou introduzir refresh + access curto?
- **D4 — CAPTCHA**: adicionar em `register`/`forgot-password` agora, ou só se houver abuso?
- **D5 — CSRF tokens**: Origin-check+SameSite chega (recomendado), ou querem tokens sincronizados também?
- **D6 — Rotação `SECRET_KEY`**: implementar suporte multi-chave (stop condition) ou adiar?
- **D7 — Sink de audit log**: manter em Postgres com retenção, ou exportar para store append-only externo?

---

## Review (preencher ao concluir)

- [ ] F0 concluída — todos os testes de regressão de segurança verdes (provámos o que já existia).
- [ ] F1/F2 concluídas — password policy + MFA atrás de gates D1/D2 confirmados.
- [ ] F3/F4 concluídas ou explicitamente adiadas.
- [ ] F5 (infra) confirmada com o operador e documentada.
- **Conclusão**: _(resumo do estado de prontidão de segurança para produção)_
