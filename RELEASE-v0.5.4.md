# Release v0.5.4 — Runbook de Deploy

> Release de **manutenção** sobre v0.5.3 (só correções; sem features novas, sem
> breaking changes). Tag: **`v0.5.4`** · merge commit em `main`:
> **`409a7b4`** · imagem de backend: **`sha-409a7b4fe314`**.
>
> Procedimento canónico em [HOSTINGER_DEPLOY.md](HOSTINGER_DEPLOY.md); este
> ficheiro é o **plano específico do v0.5.4**.

---

## Conteúdo (8 correções desde v0.5.3)

| Área | Issue | Correção |
|------|-------|----------|
| Segurança | #187 | 2ª varredura: bypass de allowlist no login, injeção HTML em emails, CAS na proclamação de eleição |
| Auth | #188 | Reset de password revoga sessões/tokens ativos (`iat` + `password_changed_at`) |
| Cargos | #189 | `transfer_cargo` recomputa `cargo_history` sob lock — corrige lost-update concorrente |
| Report | #193 | `total_events` inclui eventos restritos atendidos → rácio do relatório pessoal já não excede 100% |
| Gallery | #194 | PATCH parcial de álbum sem exigir `title` (novo `GalleryAlbumUpdate`, semântica clear-vs-unset) |
| Governança/Posts/Bootstrap | #182/#183/#184 | cargo não-canónico no bootstrap, paginação de posts em memória, privilégios hardcoded |
| Vários | #185 | Erros de lógica e inconsistências em vários domínios |

> **Nota:** v0.5.1–v0.5.3 foram releases **só de frontend** (Vercel). O backend
> em produção corre ainda a imagem do **v0.5.0**, por isso o v0.5.4 é o primeiro
> deploy de backend desde então e traz as correções de segurança acima.

---

## Porque é deploy manual ("Via B")

- **Frontend = Vercel, automático.** O merge do PR #197 em `main` dispara o
  deploy do frontend v0.5.4 na Vercel. Nada a correr — só **verificar**.
- **Backend = Docker no VPS.** O CD (`deploy.yml`: build → GHCR → SSH
  `compose pull && up`) está **billing-locked** (jobs falham em ~3 s, a imagem
  nunca chega ao GHCR). Logo `docker compose pull` daria 404 — **construímos a
  imagem no VPS** e fixamo-la via `TAG`, tal como no v0.5.0.

> Os passos abaixo correm-se **no VPS** (`<vps-user>@194.164.76.72`).

---

## 0. SSH + pré-voo (registar tag de rollback)

```bash
ssh <vps-user>@194.164.76.72

# Imagem ATUALMENTE em execução — este é o alvo de rollback. ANOTAR.
docker inspect accta-backend --format '{{.Config.Image}}'
#   esperado ~ ghcr.io/hamiltonmoreno/accta-backend:sha-03a5fc060626  (v0.5.0)

docker network ls | grep proxy        # confirmar que a rede 'proxy' existe

# Gate de drift: confirmar que o compose canónico tem image ${TAG}, --port 8000 e rede proxy.
docker compose -f /docker/accta/docker-compose.yml config | grep -E 'image:|--port|proxy' -A1
```

> ⚠️ Se o `config` **não** mostrar o override `--port 8000` ou a rede `proxy`,
> **parar** e reconciliar `/docker/accta/docker-compose.yml` com
> HOSTINGER_DEPLOY.md §2.1 antes de continuar — senão o NPM dá 502.

## 1. Obter o source do v0.5.4 (dir limpo — NÃO o órfão `/opt/projetos/accta`)

```bash
sudo rm -rf /tmp/accta-build && \
sudo git clone --depth 1 --branch v0.5.4 https://github.com/hamiltonmoreno/accta.git /tmp/accta-build
cd /tmp/accta-build && git rev-parse --short=12 HEAD     # deve imprimir 409a7b4fe314
```

## 2. Construir a imagem do backend (tag a casar com o compose canónico)

```bash
sudo docker build -f backend/Dockerfile \
  -t ghcr.io/hamiltonmoreno/accta-backend:sha-409a7b4fe314 \
  -t ghcr.io/hamiltonmoreno/accta-backend:latest \
  /tmp/accta-build
#   contexto = raiz do repo (o Dockerfile faz COPY de backend/ e scripts/)
```

## 3. Deploy via compose canónico (imagem local, SEM pull)

```bash
cd /docker/accta
export TAG=sha-409a7b4fe314
docker compose up -d --no-deps backend
#   ⚠️ NÃO correr `docker compose pull` — o GHCR não tem o v0.5.4 (CD locked); o pull falharia.
```

## 4. Verificar

```bash
docker compose ps                                  # backend Up + healthy
docker compose logs --since 2m backend | grep -iE "startup complete|error"
curl -fsS https://api.controlador.cv/api/          # esperado: {"message":"ACCTA Portal API v1.0"}
```

No browser: `https://controlador.cv` carrega (Vercel), login funciona, e o
stream SSE de notificações mantém-se aberto numa conta logada.

---

## ↩️ Rollback (se a verificação falhar) — usar a tag do passo 0

```bash
cd /docker/accta
export TAG=sha-03a5fc060626        # ← a imagem registada no passo 0
docker compose up -d --no-deps backend
docker compose logs -f backend
```

---

## Notas

- **Schema da BD:** v0.5.4 **não** exige migração manual; `ensure_schema()` corre
  idempotentemente no arranque (aditivo, sem DROP). O fix #188 lê
  `password_changed_at`/`tokens_revoked` (aditivo).
- **GitFlow pós-deploy:** já feito — `main` mergeada (#197), tag `v0.5.4` criada,
  merge-back para `develop`, branch de release apagado. Só falta este deploy.
