# Runbook — 1.º cutover do backend para GHCR (v0.4.0)

> **Objetivo:** passar o backend de produção da imagem **local** atual
> (`accta-backend:latest`, construída no VPS) para a imagem **do GHCR**
> publicada pelo CD (`ghcr.io/hamiltonmoreno/accta-backend:sha-<12>`),
> **sem perder o serviço** e **com rollback imediato pronto**.
>
> **Âmbito:** só o **backend** (container `accta-backend`). O frontend é a
> Vercel e não é tocado. Toda a operação é em **`/docker/accta`**.
>
> ⚠️ **NUNCA** correr `/opt/projetos/accta/deploy.sh` nem o `docker compose`
> do compose **órfão** desse diretório — buildam para 8001, fora da rede
> `proxy`, e partem o routing do NPM.

---

## ⚠️ Landmine conhecido (ler antes de tudo)

A imagem **viva** atual em produção é **não-recriável**: tem um blob de layer
em falta no content store, por isso `docker commit`/`save`/`--force-recreate`
sobre ela falham com `content digest … not found`. O container só corre porque
o rootfs já está desempacotado. **Consequência:** assim que recriarmos o
container (o cutover), **não há volta atrás pela imagem antiga** — o rollback
tem de ser uma imagem **achatada a partir do rootfs vivo** (`docker export`),
criada **antes** do cutover. É a Fase 1.

---

## Pré-condições (gate de entrada — confirmar TODAS)

- [ ] **Billing do GitHub Actions desbloqueada** (os jobs arrancam; sem isto não há build).
- [ ] Os 6 secrets presentes (já confirmado: `DEPLOY_HOST/USER/SSH_KEY/PORT/APP_DIR`, `PRODUCTION_URL`).
- [ ] `PRODUCTION_URL` = **`https://api.controlador.cv`** (o backend, não o frontend) — o health-check faz `GET $PRODUCTION_URL/api/`.
- [ ] **Login baseline confirmado**: abrir `https://controlador.cv`, autenticar com sucesso **agora** (referência do "antes").
- [ ] **Janela fora de pico** + 2 terminais SSH abertos no VPS (um para operar, outro para `logs -f`).
- [ ] Chave SSH antiga (`github-actions-deploy` exposta) **já removida** do `authorized_keys`.

---

## Fase 1 — Armar o rollback (ANTES de tocar em qualquer coisa)

No VPS:

```bash
cd /docker/accta

# 1. Snapshot do estado atual (anotar tudo o que sai)
docker compose ps
docker inspect accta-backend --format 'IMG={{.Image}} CMD={{.Config.Cmd}}'

# 2. Backup do compose canónico
cp docker-compose.yml docker-compose.yml.bak.pre-v0.4.0

# 3. Rollback à prova de imagem-danificada: ACHATAR o rootfs vivo (export, NÃO commit)
docker export accta-backend -o /root/accta-backend-pre-cutover.tar
docker import \
  --change 'WORKDIR /app' \
  --change 'CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8000","--workers","2"]' \
  /root/accta-backend-pre-cutover.tar accta-backend:pre-cutover

# 4. Confirmar que a imagem de rollback existe
docker image ls | grep pre-cutover
```

> **`WORKDIR /app` é OBRIGATÓRIO** no `import` — sem ele a config perde-se e o
> `CMD` não encontra `/app/server.py`. A imagem fica 8000-native, alinhada com
> o NPM.

**Gate:** só avançar se `accta-backend:pre-cutover` aparecer no `image ls`.

---

## Fase 2 — Preparar o VPS para o GHCR (sem ainda recriar o container)

Estes passos **não** mexem no container vivo — só autenticam e reescrevem a
linha `image:`. O backend continua a correr a imagem antiga até ao `up` da Fase 4.

```bash
# 1. Autenticar no GHCR (PAT classic com scope read:packages)
echo <PAT> | docker login ghcr.io -u hamiltonmoreno --password-stdin

# 2. Apontar o compose para a imagem do GHCR (parametrizada por TAG)
#    Editar /docker/accta/docker-compose.yml:
#      image: accta-backend:latest
#    ->  image: ghcr.io/hamiltonmoreno/accta-backend:${TAG:-latest}
#    (confirmar tambem: command --port 8000, networks: [proxy],
#     healthcheck em 8000, volume /srv/accta/uploads — ver HOSTINGER_DEPLOY.md §2.1)
nano docker-compose.yml

# 3. Validar a sintaxe sem aplicar
docker compose config
```

> O package GHCR só **nasce no 1.º build** (Fase 3) e nasce **privado** — por
> isso o `docker login` é obrigatório. (Alternativa: tornar o package público
> em GitHub → Packages → Package settings.)

---

## Fase 3 — Disparar o 1.º build (publica o package GHCR)

GitHub → **Actions → CD — Deploy Backend to Production → Run workflow**
(branch `main`), ou push para `main`.

O workflow corre **gate → build → deploy**:

- **build** publica `ghcr.io/hamiltonmoreno/accta-backend:latest` + `:sha-<12>`.
- **deploy** faz SSH ao VPS e executa `docker compose pull` + `up -d backend`
  com `TAG=sha-<12>` — **é aqui que o container é recriado** (o cutover real).

> Como a Fase 2 já preparou o VPS (login + `image:` GHCR), o `deploy` vai
> mesmo trocar a imagem. **Acompanhar ao vivo** no 2.º terminal:
> ```bash
> docker compose logs -f backend
> ```

**Nota sobre o schema:** se o backend vivo ainda era pré-v0.3.0, no arranque o
`ensure_schema()` vai **criar aditivamente** as tabelas novas (governança,
prestação de contas, …). É **esperado e seguro** (zero DROP/DELETE) — não
estranhar os logs de criação de tabelas/índices.

---

## Fase 4 — Verificação (smoke test do "depois")

```bash
# Container novo a correr a tag sha-<12>?
docker compose ps
docker inspect accta-backend --format '{{.Config.Image}}'   # deve ser ghcr.io/...:sha-<12>

# API viva atraves do NPM?
curl -fsS https://api.controlador.cv/api/        # {"message":"ACCTA Portal API v1.0"}
```

E no browser (o "depois" vs o baseline da pré-condição):

- [ ] `https://api.controlador.cv/api/` → JSON 200.
- [ ] **Login** em `https://controlador.cv` funciona (só email+password; sem 2.º fator — é o v0.4.0).
- [ ] Uma página autenticada carrega (ex.: Dashboard) e as **notificações SSE** ligam.
- [ ] Upload de um logo aparece em `/srv/accta/uploads/` e é servido.

**Se tudo verde → cutover concluído.** A partir daqui, cada push para `main`
deploya automaticamente (steady-state).

---

## 🔴 ROLLBACK (se a Fase 3/4 correr mal)

Sintomas: health-check vermelho, `502` no NPM, ou login partido.

```bash
cd /docker/accta

# 1. Restaurar o compose anterior (volta a apontar para a imagem local/pre-cutover)
cp docker-compose.yml.bak.pre-v0.4.0 docker-compose.yml

# 2. Forçar a imagem de rollback achatada e recriar
sed -i 's#^\(\s*image:\).*#\1 accta-backend:pre-cutover#' docker-compose.yml
docker compose up -d --no-deps --force-recreate backend

# 3. Confirmar recuperação
docker compose ps
curl -fsS https://api.controlador.cv/api/
docker compose logs -f backend
```

> O rollback usa `accta-backend:pre-cutover` (Fase 1), que é 8000-native e
> autossuficiente — não depende da imagem danificada original.

Depois de estabilizar em rollback: investigar a causa (logs do container +
do job `deploy` no Actions) **antes** de tentar o cutover de novo. Regra do
projeto: **2 tentativas falhadas → re-planear, não tentar uma 3.ª às cegas.**

---

## Pós-cutover (limpeza, quando estável ≥ 24h)

- [ ] Guardar/arquivar `/root/accta-backend-pre-cutover.tar` (rede de segurança offline).
- [ ] `docker image prune -f` (remove dangling; **mantém** as tags `sha-<12>` e `pre-cutover`).
- [ ] Opcional: adicionar **Required reviewers** ao environment `Production`
      (Settings → Environments) para um gate de aprovação manual nos próximos deploys.
- [ ] Reconciliar de raiz a porta **8000 vs 8001** (o `Dockerfile` é 8001-native;
      hoje compensado pelo override `--port 8000`) — tarefa isolada, fora deste cutover.

---

### Sequência resumida (cábula)

```
billing OK + login baseline  →  Fase 1 (rollback: export+import pre-cutover)
  →  Fase 2 (VPS: docker login + image: GHCR no compose, sem up)
  →  Fase 3 (Actions: Run workflow → build publica package → deploy recria)
  →  Fase 4 (smoke test)        →  verde = fim  |  vermelho = ROLLBACK
```
