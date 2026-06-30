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

**Valores atuais (v0.5.46 — Pendências v2 / spec 015: avisos de Atos PENDENTES → `/pendencias`, PR #386/#385):**

| Variável | Valor |
|----------|-------|
| `TAG` (imagem nova) | `sha-c9c5430c1c2b` |
| Tag git da release | `v0.5.46` (= `c9c5430`, HEAD de `main`, merge #386) |
| Rollback (prod anterior, v0.5.43) | `sha-dab25397254e` |
| Teste decisivo desta release | **Sem rota nova** (a feature muda o valor do `link` de avisos já existentes): a confirmação é a **imagem viva `sha-c9c5430c1c2b`** (`docker inspect`, Up healthy) + **código presente no container** (`docker exec accta-backend grep -c '_LINK_PENDENTE' routes/atos.py` → **4** [1 def + 3 usos]; `grep -c '"/pendencias"' routes/atos.py` → 1) + arranque limpo (`overdue_atos_loop ... iniciado` 2×). Sanidade da rota: `POST /api/atos/notify-overdue` sem auth → **401**. **Validação funcional** (aviso de Ato pendente leva a `/pendencias`; aviso de Ato decidido leva a co-aprovações; contador da sidebar ≡ painel) = Princípio VII, dono. |

> **Nota:** a v0.5.46 **toca em `backend/`** (só `routes/atos.py`): nasce a 2.ª constante
> `_LINK_PENDENTE = "/pendencias"` aplicada **só** aos 3 avisos de Atos **pendentes**
> (`create_ato` + varrimento Direção + varrimento proponente, specs 010/012/013); os 2 avisos de
> Atos **decididos** (`sign_ato` aprovação/rejeição incl. motivo spec 011; `execute_ato`) **mantêm**
> `_LINK = "/financeiro/co-aprovacoes"` (**não é swap cego**). O backend em prod antes da v0.5.46
> está na **v0.5.43** (`sha-dab25397254e`). **Sem migração/DAO/schema, zero deps novas.** O **frontend**
> (contador na sidebar — hook `usePendencias` — + **fix do `framer-motion`** que repara o `/pendencias`
> da spec 014, cujo build de v0.5.45 falhava) vai pela **Vercel**, fora desta Via B. **Sem pós-deploy
> obrigatório.** Confirma sempre a imagem em execução antes de deploy: `docker compose ps` (coluna
> IMAGE) ou `docker inspect accta-backend --format '{{.Config.Image}}'`.

---

## 2. Passos (SSH no VPS)

### 2.1 Construir a imagem no VPS, no commit da release
```bash
rm -rf /tmp/accta-build
git clone https://github.com/hamiltonmoreno/accta.git /tmp/accta-build
cd /tmp/accta-build && git checkout v0.5.46       # <- tag git da release
docker build -f backend/Dockerfile \
  -t ghcr.io/hamiltonmoreno/accta-backend:sha-c9c5430c1c2b .   # <- TAG
```

### 2.2 Arrancar via o compose canónico (só muda o TAG)
```bash
cd /docker/accta
export TAG=sha-c9c5430c1c2b
docker compose up -d --no-deps backend
```

### 2.3 Verificar
```bash
docker compose ps                         # backend = Up (healthy)
docker inspect accta-backend --format '{{.Config.Image}}'   # confirmação decisiva: ...:sha-c9c5430c1c2b
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
export TAG=sha-dab25397254e        # <- rollback (v0.5.43, imagem que corria antes da v0.5.46)
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
  → v0.5.43 (`sha-dab25397254e`) → **v0.5.46 (`sha-c9c5430c1c2b`, este deploy)**.
  As v0.5.28/v0.5.29/v0.5.30, v0.5.32/v0.5.33, v0.5.36 e **v0.5.44/v0.5.45** não
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
