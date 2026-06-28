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

**Valores atuais (v0.5.39 — lembrete informativo de quotas, spec 008, PR #360):**

| Variável | Valor |
|----------|-------|
| `TAG` (imagem nova) | `sha-5cfff3c9b0e1` |
| Tag git da release | `v0.5.39` (= `5cfff3c`, HEAD de `main`, merge #361) |
| Rollback (prod anterior, v0.5.38) | `sha-960e0b5367b2` |
| Teste decisivo desta release | **Sem rota nova** (a v0.5.39 modifica comportamento autenticado, não adiciona endpoint público) → o decisivo é a **imagem em execução = `sha-5cfff3c9b0e1`** (`docker inspect`, Up healthy) + arranque limpo. Sanidade: `PATCH /api/me/email-preferences` → **401** e `GET` → **405** (rota gated viva); `api/` → 200; `openapi.json`/`docs` → 404. **Validação funcional** do lembrete (gerar quotas → notificação por-sócio a abrir `/carteira`; toggle off → não recebe) = T006/T010 em navegador autenticado (Princípio VII, dono). |

> **Nota:** a v0.5.39 **toca em `backend/`** (spec 008 — lembrete informativo de quotas,
> PR #360): `routes/finances.py` (gerador de quotas passa a notificar **por sócio** que
> recebeu quota nova — valor + total acumulado via 1 aggregate, link `/carteira` — em vez
> do aviso genérico; respeita `quota_reminder_opt_out`); `models.py` (campo aditivo
> `quota_reminder_opt_out` em `UserBase`, default `False`; `EmailPreferencesUpdate` com
> ambos os toggles opcionais); `routes/comunicados.py` (`PATCH /me/email-preferences`
> grava só os campos enviados); `database.py` (`insert_quotas_atomic` devolve os `user_id`
> NOVOS — era `int` — e **fix W1** `_safe_float`: `$sum` ignora `amount` não-numérico → 0
> em vez de `ValueError`/500, fiel ao Mongo). **Email = STOP/off no MVP.** O backend em
> prod antes da v0.5.39 está na **v0.5.38** (`sha-960e0b5367b2`). **Sem migração/pós-deploy**
> (campo aditivo, default `False`; sem schema destrutivo). Confirma sempre a imagem em
> execução antes de deploy: `docker compose ps` (coluna IMAGE) ou
> `docker inspect accta-backend --format '{{.Config.Image}}'`.

---

## 2. Passos (SSH no VPS)

### 2.1 Construir a imagem no VPS, no commit da release
```bash
rm -rf /tmp/accta-build
git clone https://github.com/hamiltonmoreno/accta.git /tmp/accta-build
cd /tmp/accta-build && git checkout v0.5.39       # <- tag git da release
docker build -f backend/Dockerfile \
  -t ghcr.io/hamiltonmoreno/accta-backend:sha-5cfff3c9b0e1 .   # <- TAG
```

### 2.2 Arrancar via o compose canónico (só muda o TAG)
```bash
cd /docker/accta
export TAG=sha-5cfff3c9b0e1
docker compose up -d --no-deps backend
```

### 2.3 Verificar
```bash
docker compose ps                         # backend = Up (healthy)
docker inspect accta-backend --format '{{.Config.Image}}'   # confirmação decisiva: ...:sha-5cfff3c9b0e1
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
export TAG=sha-960e0b5367b2        # <- rollback (v0.5.38, imagem que corria antes da v0.5.39)
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
  (`sha-960e0b5367b2`) → **v0.5.39 (`sha-5cfff3c9b0e1`, este deploy)**.
  As v0.5.28/v0.5.29/v0.5.30, v0.5.32/v0.5.33 e v0.5.36 não tocaram no
  backend (docs/test/frontend-only). As v0.5.1/v0.5.5/v0.5.6/v0.5.7,
  v0.5.9–v0.5.12, v0.5.14–v0.5.16 e v0.5.19–v0.5.21 não tocaram no
  backend (só Vercel).
- Pós-deploy histórico (informativo, **já feitos**): v0.5.22 desbloqueou
  o **#281** (DROP da tabela órfã `invoices`, executado 2026-06-19 via
  `scripts/sql/2026-06-19-drop-invoices.sql`). v0.5.8 exigiu atribuir os
  cargos em `/admin/cargos` (com foto) para a secção Corpos Sociais
  deixar de mostrar "Vago". A v0.5.23 e v0.5.24 não têm pós-deploy.
