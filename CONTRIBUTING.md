# Contribuir para o Portal ACCTA

Este documento é a **fonte de verdade** do fluxo de trabalho Git do projeto.
O `CLAUDE.md` resume-o e defere a este ficheiro em caso de conflito.

---

## Modelo de branches (GitFlow)

| Branch | Papel | Origem | Destino do merge |
|--------|-------|--------|------------------|
| `main` | Produção. Apenas código lançado e estável. Cada merge é uma release. | — | — |
| `develop` | Integração. **Tudo passa aqui primeiro.** Reflete o próximo lançamento. | `main` | — |
| `feature/*` | Nova funcionalidade ou alteração. | `develop` | `develop` |
| `release/*` | Estabilização antes de lançar (bumps de versão, fixes finais). | `develop` | `main` **e** `develop` |
| `hotfix/*` | Correção urgente em produção. | `main` | `main` **e** `develop` |

**Regra de ouro:** nada vai diretamente para `main`. O caminho normal é
`feature/* → develop → (release) → main`.

### Convenção de nomes

```
feature/identidade-cargos
feature/blog-noticias
release/v1.3.0
hotfix/login-rate-limit
```

Usa kebab-case e um prefixo curto e descritivo.

---

## Fluxo de uma funcionalidade

```bash
# 1. Partir sempre de develop atualizada
git checkout develop
git pull origin develop

# 2. Criar a feature branch
git checkout -b feature/nome-curto

# 3. Trabalhar e commitar (ver convenção de commits abaixo)
git add -A
git commit -m "feat(escopo): descrição"

# 4. Publicar e abrir PR PARA develop (nunca para main)
git push -u origin feature/nome-curto
# Abrir Pull Request: feature/nome-curto  ->  develop
```

Depois do merge do PR, apaga a branch (local e remota):

```bash
git checkout develop && git pull origin develop
git branch -d feature/nome-curto
git push origin --delete feature/nome-curto
```

---

## Fluxo de release (`develop → main`)

Quando `develop` está estável e pronta a lançar:

```bash
git checkout develop && git pull origin develop
git checkout -b release/v1.3.0

# ajustes finais de release (versão, changelog, fixes pontuais)
git commit -m "chore(release): v1.3.0"
git push -u origin release/v1.3.0
```

1. Abrir PR `release/v1.3.0 → main`, rever e fazer merge.
2. Taggear a release em `main`:
   ```bash
   git checkout main && git pull origin main
   git tag -a v1.3.0 -m "Release v1.3.0"
   git push origin v1.3.0
   ```
3. **Trazer a release de volta para `develop`** (para `main` e `develop` não
   divergirem): abrir PR `main → develop` ou `release/v1.3.0 → develop` e fazer merge.

---

## Fluxo de hotfix (urgência em produção)

```bash
git checkout main && git pull origin main
git checkout -b hotfix/descricao
# corrigir
git commit -m "fix(escopo): descrição do hotfix"
git push -u origin hotfix/descricao
```

1. PR `hotfix/descricao → main`, merge, e taggear (ex.: `v1.3.1`).
2. PR `hotfix/descricao → develop` (ou `main → develop`) para propagar a correção.

---

## Convenção de commits

Conventional Commits, em português, com escopo:

```
feat(identidade-cargos): RBAC granular aditivo (role OR privilege)
fix(login): corrigir rate limit em forgot-password
docs(banners): clarificar fluxo de upload
chore(release): v1.3.0
```

Tipos comuns: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.

---

## Proteção de branches (configurar no GitHub)

Para que o fluxo seja garantido — e não apenas convencionado — configurar em
**Settings → Branches** do repositório:

- **Default branch → `develop`** (Settings → General). Assim, todos os novos PRs
  apontam para `develop` por omissão.
- **`main`**: exigir Pull Request + 1 review, proibir push direto, exigir CI verde.
- **`develop`**: exigir Pull Request (proteção mais leve).

---

## Checklist antes de abrir PR

- [ ] Branch parte de `develop` (feature) ou `main` (hotfix).
- [ ] PR aponta para `develop` (feature/release-back) ou `main` (release/hotfix).
- [ ] Testes passam: `cd backend && pytest` / `cd frontend && yarn build`.
- [ ] Lint limpo: `ruff check .` (backend) / `npx eslint src/` (frontend).
- [ ] Sem segredos, sem `password` exposto, audit-log em escritas de admin.
