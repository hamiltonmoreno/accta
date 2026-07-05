# Runbook — Deploy manual do backend ao VPS ("Via B")

> **Quando usar:** sempre que uma release inclua alterações de **backend** e o
> CD (GitHub Actions → GHCR → VPS) **não** correr — hoje porque a conta GitHub
> Actions está bloqueada por *billing* (jobs falham em ~2s, "account is locked
> due to a billing issue"; o Vercel continua a publicar o frontend à parte).
>
> Como o GHCR fica **sem imagem** quando o CI está bloqueado, a "Via B" **constrói
> a imagem no próprio VPS** a partir do commit da release e arranca-a pelo compose
> canónico de `/docker/accta`.
>
> Quando o billing for resolvido, volta ao caminho normal (Etapa 5).

---

## 0. Pré-requisitos e factos fixos

| Item | Valor |
|------|-------|
| VPS | `194.164.76.72` (`srv898928.hstgr.cloud`, Hostinger) |
| Pasta de deploy canónica | **`/docker/accta`** (só `docker-compose.yml` + `backend/.env`) |
| Edge | nginx-proxy-manager (NPM), rede docker `proxy`, `api.controlador.cv → accta-backend:8000` |
| Convenção de tag da imagem | `ghcr.io/hamiltonmoreno/accta-backend:sha-<12 primeiros do commit>` |
| Health público | `https://api.controlador.cv/api/` → 200 |

### ⚠️ Armadilhas que partem produção
- **NUNCA** correr `/opt/projetos/accta/deploy.sh` — builda para 8001, fora da
  rede `proxy`, e desliga o backend do NPM (já causou outage).
- **Porta 8000:** desde a **v0.5.13** o `backend/Dockerfile` é **8000-native**
  (EXPOSE/HEALTHCHECK/CMD `--port 8000`, #228) — alinhado com o NPM. O compose
  canónico de `/docker/accta` **já** tem o override
  `command: ["uvicorn","server:app","--host","0.0.0.0","--port","8000","--workers","2"]`
  + healthcheck em `:8000`, que agora é **redundante mas inofensivo**. **Não
  substituas esse compose** — só mexes no `TAG`. (Imagens ≤ v0.5.8 eram
  8001-native e dependiam mesmo desse override.)
- Construir a imagem **no VPS** é só por causa do billing lock. Não usar o clone
  órfão `/opt/projetos/accta` para arrancar serviços.

---

## 1. Valores da release a fazer (preencher a cada deploy)

Antes de começar, obtém o SHA do `main` na release (na tua máquina):

```bash
git fetch origin main && git rev-parse --short=12 main
```

**Valores atuais (v0.5.54 — spec 017 funções personalizadas + spec 018 consolidação de acessos / release #404):**

| Variável | Valor |
|----------|-------|
| `TAG` (imagem nova) | `sha-28053ebe074f` |
| Tag git da release | `v0.5.54` (= `28053eb`, HEAD de `main`, merge #404) |
| Rollback (prod anterior, v0.5.53) | `sha-aa15736d5221` |
| Teste decisivo desta release | **Rota nova gated (spec 017)**: `curl -s -o /dev/null -w '%{http_code}' https://api.controlador.cv/api/admin/custom-roles` passa de **404** (antes) a **401** (rota viva, exige admin) — prova E2E sem auth. Complemento no container: `docker exec accta-backend grep -c _require_cargo_admin routes/admin.py`→**4** (1 def + 3 usos = fix escalada W3); `ls routes/custom_roles.py`→OK. |

> ℹ️ **Executado 2026-07-05** — todas as verificações da Etapa 2.3 verdes (custom-roles 404→401;
> W3 no container ×4; invariantes 200/404/404/404/401/401; arranque limpo 0 tracebacks, 0 "tuple
> concurrently updated", audit/RLS triggers 2×, pg_cron OK; `.env` c/ `TURNSTILE_SECRET`/`VAPID_*`
> preservado no recreate).
> ⚠️ **Pós-deploy PENDENTE (STOP do dono): migração de dados `scripts/migrate_roles_018.py`** (traduz
> roles legados → socio + função seed): backup → `--dry-run` → confirmação → `--apply` → teste decisivo,
> na mesma janela. **Prod = no-op** (0 utilizadores legados após o reset de 2026-06-30; só `admin@controlador.cv`).
> ℹ️ Turnstile (v0.5.47) **continua ativo** — a env `TURNSTILE_SECRET` é preservada no `.env`. Procedimento de ativação documentado abaixo (mantém-se válido).

> **Nota:** a v0.5.47 **toca em `backend/`** (`turnstile.py` novo + `routes/auth_routes.py` +
> `routes/contact.py`): `verify_turnstile` corre **antes** das credenciais nos formulários públicos.
> **Fail-closed** quando ligado, mas **degrada graciosamente sem `TURNSTILE_SECRET`** (no-op, filosofia
> VAPID) — o deploy do código **não parte o login** mesmo antes de configurar a secret. Zero deps novas
> (`httpx` já presente). O backend em prod antes da v0.5.47 está na **v0.5.46** (`sha-c9c5430c1c2b`).
>
> **⚠️ Ativar o Turnstile (pós-deploy, FEITO 2026-06-30):** ordem obrigatória **frontend-correto-a-prod
> PRIMEIRO, secret no backend DEPOIS** (senão 403 em todos os logins).
> 1. **Frontend**: a site key (pública) tem de bater com a widget Cloudflare. ⚠️ O fallback embutido no
>    `Turnstile.js` tinha um typo (7 vs 6 A's) — corrigido em **v0.5.48** (frontend/Vercel, PR #389/release
>    #390). Confirma a key viva: `curl -s https://controlador.cv/ | grep -oE '/static/js/main\.[a-z0-9]+\.js'`
>    → `curl` desse bundle → `grep -oE '0x4A+Ds8kZrozSpCdz7g'` = **`0x4AAAAADs8kZrozSpCdz7g`** (6 A's).
> 2. **Provar a secret sem arriscar**: `curl -s https://challenges.cloudflare.com/turnstile/v0/siteverify
>    -d secret=<SECRET> -d response=dummy` → `invalid-input-response` (secret OK) vs `invalid-input-secret`
>    (errada). Opcional E2E: token real do widget + a secret → `success:true` + `hostname:controlador.cv`.
> 3. **Ligar**: `cd /docker/accta && cp -a .env .env.bak.preturnstile`, acrescentar `TURNSTILE_SECRET=<SECRET>`
>    ao `.env` (compose `env_file`, **não** `backend/.env`), `export TAG=sha-d6ed27688efd &&
>    docker compose up -d --force-recreate --no-deps backend`. **Rollback da ativação** = remover a linha +
>    recreate → volta a no-op em ~10s. **Já ativado** (secret par da site key 6 A's; backup `.env.bak.preturnstile`).
>
> Confirma sempre a imagem em execução antes de deploy: `docker compose ps` (coluna IMAGE) ou
> `docker inspect accta-backend --format '{{.Config.Image}}'`.

---

## 2. Passos (SSH no VPS)

### 2.1 Construir a imagem no VPS, no commit da release
```bash
rm -rf /tmp/accta-build
git clone https://github.com/hamiltonmoreno/accta.git /tmp/accta-build
cd /tmp/accta-build && git checkout v0.5.54       # <- tag git da release
docker build -f backend/Dockerfile \
  -t ghcr.io/hamiltonmoreno/accta-backend:sha-28053ebe074f .   # <- TAG
```

### 2.2 Arrancar via o compose canónico (só muda o TAG)
```bash
cd /docker/accta
export TAG=sha-28053ebe074f
docker compose up -d --no-deps backend
```

### 2.3 Verificar
```bash
docker compose ps                         # backend = Up (healthy)
docker inspect accta-backend --format '{{.Config.Image}}'   # confirmação decisiva: ...:sha-28053ebe074f
docker compose logs --tail=80 backend     # arranque limpo: ensure_schema OK, sem tracebacks
curl -fsS https://api.controlador.cv/api/ # 200

# Invariantes de segurança (mantêm-se desde v0.5.13): docs desligados em prod.
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/openapi.json  # esperado: 404
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/docs          # esperado: 404
# (depende de ENVIRONMENT=production no backend/.env — já presente; HSTS/CORS também o exigem.)
# Mantêm-se desde v0.5.22 (subsistema invoices removido — rota inexistente, endpoint novo gated):
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/invoices          # esperado: 404
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/finances/me/quotas # esperado: 401/403
# Regressão (spec 003, vivo desde v0.5.27): endpoints de finanças de evento.
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/events/nao-existe/expenses # esperado: 401 (NÃO 404)
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/events/nao-existe/receitas # esperado: 401 (NÃO 404)
# Teste decisivo da v0.5.39: sem rota nova → a confirmação é a imagem viva (acima) +
# arranque limpo. Sanidade da rota de preferências (gated, viva): PATCH→401, GET→405.
curl -s -o /dev/null -w '%{http_code}\n' -X PATCH https://api.controlador.cv/api/me/email-preferences  # esperado: 401
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/me/email-preferences           # esperado: 405 (só PATCH)
# Spec 007 (v0.5.38) mantém-se viva:
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/finances/me/quotas/pdf         # esperado: 401
# Validação funcional do lembrete (T006/T010) = navegador autenticado, Princípio VII (dono).
# Arranque limpo (mantém-se desde v0.5.24): zero hits de 'tuple concurrently updated'.
docker compose logs --tail=200 backend 2>&1 | grep -E 'tuple concurrently updated' | wc -l            # esperado: 0
docker compose logs --tail=200 backend 2>&1 | grep -cE 'audit_logs immutability trigger.*instalado'   # esperado: 2 (um por worker)
docker compose logs --tail=200 backend 2>&1 | grep -cE 'RLS auto-enable event trigger.*instalado'     # esperado: 2 (um por worker)
docker compose logs --tail=200 backend 2>&1 | grep -E 'pg_cron not configured'                        # esperado: vazio (pg_cron funcional + serializado)
```

---

## 3. Rollback (imediato, sem rebuild)

A imagem anterior continua no VPS; só se troca o `TAG`:
```bash
cd /docker/accta
export TAG=sha-aa15736d5221        # <- rollback (v0.5.53, imagem que corria antes da v0.5.54)
docker compose up -d --no-deps backend
```

---

## 4. Limpeza (opcional)
```bash
rm -rf /tmp/accta-build
docker image prune -f              # remove imagens dangling (NÃO as taggeadas por sha-)
```

---

## 5. Caminho normal (quando o billing do CI for resolvido)

Com o CD a correr, a imagem é construída e publicada no GHCR pelo GitHub Actions;
o VPS só faz `pull` + `up`:
```bash
cd /docker/accta
export TAG=sha-<12>                # a SHA da release; ou omitir p/ :latest
docker compose pull backend
docker compose up -d backend
```
Ver `DEPLOY.md` e `HOSTINGER_DEPLOY.md` para o setup completo (secrets SSH,
`docker login ghcr.io`, compose canónico com `image: ...:${TAG:-latest}`).

---

## 6. Notas finais
- O **frontend** é independente: a Vercel publica automaticamente no push para
  `main`. Esta "Via B" é **só backend**.
- Histórico de imagens de backend em prod: v0.4.0 (`sha-ba3e946e3add`) → v0.5.0
  (`sha-03a5fc060626`) → v0.5.4 (`sha-409a7b4fe314`) → v0.5.8
  (`sha-f149268a1fde`) → v0.5.13 (`sha-f580b90ee543`) → v0.5.17
  (`sha-6e313d80425f`) → v0.5.18 (`sha-bbf09cfa2298`) → v0.5.22
  (`sha-12d24165c36a`) → v0.5.23 (`sha-218a2bdf4e24`) → v0.5.24
  (`sha-9c056677f181`) → v0.5.25 (`sha-af16c566b25f`) → v0.5.26
  (`sha-7c38123185f9`) → v0.5.27 (`sha-e70d67cc58ed`) → v0.5.31
  (`sha-678575f73905`) → v0.5.34 (`sha-4a78080aec1e`) → v0.5.35
  (`sha-b16773a08b8a`) → v0.5.37 (`sha-482320bce1ca`) → v0.5.38
  (`sha-960e0b5367b2`) → v0.5.39 (`sha-5cfff3c9b0e1`) → v0.5.40
  (`sha-fae22c0eaab2`) → v0.5.41 (`sha-c01198d08af2`) → v0.5.42 (`sha-5343480d5d64`)
  → v0.5.43 (`sha-dab25397254e`) → v0.5.46 (`sha-c9c5430c1c2b`) → v0.5.47
  (`sha-d6ed27688efd`, Cloudflare Turnstile anti-bot, ATIVADO) → v0.5.49
  (`sha-a1b6bd7be7b3`, fix(stats) painel exclui contas técnicas) → v0.5.53
  (`sha-aa15736d5221`, spec 016: `DEPARTAMENTOS` em registration-options + convite
  aceita `role=admin` + rótulos de privilégio; `models.py`/`routes/auth_routes.py`/
  `routes/admin.py`) → **v0.5.54 (`sha-28053ebe074f`, este deploy — spec 017 funções
  personalizadas + spec 018 consolidação de acessos, release #404: role∈{admin,socio},
  `custom_roles`, tradução de legados, `MODULE_ACCESS`, fix escalada crítica W3
  `_require_cargo_admin`; 33 ficheiros backend. Pós-deploy PENDENTE: migração
  `migrate_roles_018.py`, prod=no-op)**.
  As **v0.5.50–v0.5.52** (brand refresh: favicon/logos/tagline/wordmark) foram
  frontend-only (Vercel).
  As v0.5.28/v0.5.29/v0.5.30, v0.5.32/v0.5.33, v0.5.36, **v0.5.44/v0.5.45** e
  **v0.5.48** (fix do typo na site key Turnstile, `Turnstile.js` — frontend) não
  tocaram no backend (docs/test/frontend-only). ⚠️ O frontend de **v0.5.45**
  (painel `/pendencias`, spec 014) **falhava no build** (`framer-motion` removido em
  `b84c832`) — reparado no frontend da v0.5.46. As v0.5.1/v0.5.5/v0.5.6/v0.5.7,
  v0.5.9–v0.5.12, v0.5.14–v0.5.16 e v0.5.19–v0.5.21 não tocaram no
  backend (só Vercel).
- Pós-deploy histórico (informativo, **já feitos**): v0.5.22 desbloqueou
  o **#281** (DROP da tabela órfã `invoices`, executado 2026-06-19 via
  `scripts/sql/2026-06-19-drop-invoices.sql`). v0.5.8 exigiu atribuir os
  cargos em `/admin/cargos` (com foto) para a secção Corpos Sociais
  deixar de mostrar "Vago". A v0.5.23 e v0.5.24 não têm pós-deploy.
