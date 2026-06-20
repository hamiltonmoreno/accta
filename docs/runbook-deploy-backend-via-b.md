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

**Valores atuais (v0.5.22 — invoices→transactions unificado (#276), fixes de finanças (tetos de escala, jóia/UTC, audit IP/UA), N+1 em `list_regulamentos` (#287)):**

| Variável | Valor |
|----------|-------|
| `TAG` (imagem nova) | `sha-12d24165c36a` |
| Tag git da release | `v0.5.22` (= `12d2416`, HEAD de `main`, merge #288) |
| Rollback (prod anterior, v0.5.18) | `sha-bbf09cfa2298` |
| Teste decisivo desta release | a rota de invoices foi removida (#276): `GET /api/invoices` deve dar **404**, e o endpoint novo da carteira unificada `GET /api/finances/me/quotas` deve **existir** (401/403 anónimo, **não** 404). Verificação base: imagem em execução = `sha-12d24165c36a`, health 200, arranque sem tracebacks. |

> **Nota:** a v0.5.22 **toca em `backend/`** (45 ficheiros — remoção do
> subsistema `invoices`, unificação da carteira em `transactions`, fixes de
> finanças e perf em `regulamentos`) e requer mesmo este deploy. O backend em
> prod antes da v0.5.22 está na **v0.5.18** (`sha-bbf09cfa2298`); as v0.5.19–
> v0.5.21 não tocaram no backend (só Vercel).
> Confirma sempre a imagem em execução antes de deploy: `docker compose ps`
> (coluna IMAGE) ou `docker inspect accta-backend --format '{{.Config.Image}}'`.

---

## 2. Passos (SSH no VPS)

### 2.1 Construir a imagem no VPS, no commit da release
```bash
rm -rf /tmp/accta-build
git clone https://github.com/hamiltonmoreno/accta.git /tmp/accta-build
cd /tmp/accta-build && git checkout v0.5.22       # <- tag git da release
docker build -f backend/Dockerfile \
  -t ghcr.io/hamiltonmoreno/accta-backend:sha-12d24165c36a .   # <- TAG
```

### 2.2 Arrancar via o compose canónico (só muda o TAG)
```bash
cd /docker/accta
export TAG=sha-12d24165c36a
docker compose up -d --no-deps backend
```

### 2.3 Verificar
```bash
docker compose ps                         # backend = Up (healthy)
docker inspect accta-backend --format '{{.Config.Image}}'   # confirmação decisiva: ...:sha-12d24165c36a
docker compose logs --tail=80 backend     # arranque limpo: ensure_schema OK, sem tracebacks
curl -fsS https://api.controlador.cv/api/ # 200

# Invariantes de segurança (mantêm-se desde v0.5.13): docs desligados em prod.
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/openapi.json  # esperado: 404
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/docs          # esperado: 404
# (depende de ENVIRONMENT=production no backend/.env — já presente; HSTS/CORS também o exigem.)
# Teste decisivo da v0.5.22: subsistema invoices removido (#276) — rota inexistente dá 404.
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/invoices  # esperado: 404
# Carteira unificada (endpoint novo, requer auth): 401/403 anónimo confirma que EXISTE (não 404).
curl -s -o /dev/null -w '%{http_code}\n' https://api.controlador.cv/api/finances/me/quotas  # esperado: 401/403
```

---

## 3. Rollback (imediato, sem rebuild)

A imagem anterior continua no VPS; só se troca o `TAG`:
```bash
cd /docker/accta
export TAG=sha-bbf09cfa2298        # <- rollback (v0.5.18, imagem que corria antes da v0.5.22)
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
  (`sha-6e313d80425f`) → v0.5.18 (`sha-bbf09cfa2298`) → **v0.5.22
  (`sha-12d24165c36a`, este deploy)**. As
  v0.5.1/v0.5.5/v0.5.6/v0.5.7, v0.5.9–v0.5.12, v0.5.14–v0.5.16 e v0.5.19–v0.5.21
  não tocaram no backend (só Vercel).
- Pós-deploy específico da v0.5.22: assim que esta imagem estiver em prod,
  `database.COLLECTIONS` já não inclui `invoices` — isso **desbloqueia o #281**
  (DROP da tabela órfã `invoices` via Supabase, seguindo
  `scripts/sql/2026-06-19-drop-invoices.sql`, que aborta se a tabela tiver
  linhas). Sem migração de dados automática. Histórico: na v0.5.8 foi preciso
  **atribuir os cargos** em `/admin/cargos` (com foto) para a secção Corpos
  Sociais deixar de mostrar "Vago".
