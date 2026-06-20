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

**Valores atuais (v0.5.24 — fix infra-only #297 closes #294: estende `pg_advisory_xact_lock` + `lock_timeout` ao 4.º bloco DDL (`_PGCRON_DDL`) em `ensure_schema()`, fecha o INFO residual `tuple concurrently updated` do v0.5.23; sem mudança funcional):**

| Variável | Valor |
|----------|-------|
| `TAG` (imagem nova) | `sha-9c056677f181` |
| Tag git da release | `v0.5.24` (= `9c05667`, HEAD de `main`, merge #298) |
| Rollback (prod anterior, v0.5.23) | `sha-218a2bdf4e24` |
| Teste decisivo desta release | **0 hits** em `docker compose logs --tail=200 backend \| grep -E 'tuple concurrently updated'` (era 1 INFO no pg_cron na v0.5.23, 2 WARNINGs na v0.5.22). Os INFOs "audit_logs immutability trigger instalado", "RLS auto-enable event trigger instalado" e "PostgreSQL schema and indexes ensured" devem aparecer 2× cada (1 por worker), sem INFO de "pg_cron not configured". Verificação base: imagem = `sha-9c056677f181`, health 200, arranque sem tracebacks. |

> **Nota:** a v0.5.24 **toca em `backend/`** (1 ficheiro — `database.py`,
> fix #297 fecha o último bloco DDL sem lock). O backend em prod antes da
> v0.5.24 está na **v0.5.23** (`sha-218a2bdf4e24`).
> Confirma sempre a imagem em execução antes de deploy: `docker compose ps`
> (coluna IMAGE) ou `docker inspect accta-backend --format '{{.Config.Image}}'`.

---

## 2. Passos (SSH no VPS)

### 2.1 Construir a imagem no VPS, no commit da release
```bash
rm -rf /tmp/accta-build
git clone https://github.com/hamiltonmoreno/accta.git /tmp/accta-build
cd /tmp/accta-build && git checkout v0.5.24       # <- tag git da release
docker build -f backend/Dockerfile \
  -t ghcr.io/hamiltonmoreno/accta-backend:sha-9c056677f181 .   # <- TAG
```

### 2.2 Arrancar via o compose canónico (só muda o TAG)
```bash
cd /docker/accta
export TAG=sha-9c056677f181
docker compose up -d --no-deps backend
```

### 2.3 Verificar
```bash
docker compose ps                         # backend = Up (healthy)
docker inspect accta-backend --format '{{.Config.Image}}'   # confirmação decisiva: ...:sha-9c056677f181
docker compose logs --tail=80 backend     # arranque limpo: ensure_schema OK, sem tracebacks
curl -fsS https://api.controlador.cv/api/ # 200

# Invariantes de segurança (mantêm-se desde v0.5.13): docs desligados em prod.
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/openapi.json  # esperado: 404
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/docs          # esperado: 404
# (depende de ENVIRONMENT=production no backend/.env — já presente; HSTS/CORS também o exigem.)
# Mantêm-se desde v0.5.22 (subsistema invoices removido — rota inexistente, endpoint novo gated):
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/invoices          # esperado: 404
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/finances/me/quotas # esperado: 401/403
# Teste decisivo da v0.5.24: o fix do #297 fechou o último bloco DDL (pg_cron).
# Arranque agora 100% limpo: zero hits de 'tuple concurrently updated' (qualquer nível).
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
export TAG=sha-218a2bdf4e24        # <- rollback (v0.5.23, imagem que corria antes da v0.5.24)
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
  (`sha-12d24165c36a`) → v0.5.23 (`sha-218a2bdf4e24`) → **v0.5.24
  (`sha-9c056677f181`, este deploy)**. As v0.5.1/v0.5.5/v0.5.6/v0.5.7,
  v0.5.9–v0.5.12, v0.5.14–v0.5.16 e v0.5.19–v0.5.21 não tocaram no backend
  (só Vercel).
- Pós-deploy histórico (informativo, **já feitos**): v0.5.22 desbloqueou
  o **#281** (DROP da tabela órfã `invoices`, executado 2026-06-19 via
  `scripts/sql/2026-06-19-drop-invoices.sql`). v0.5.8 exigiu atribuir os
  cargos em `/admin/cargos` (com foto) para a secção Corpos Sociais
  deixar de mostrar "Vago". A v0.5.23 e v0.5.24 não têm pós-deploy.
