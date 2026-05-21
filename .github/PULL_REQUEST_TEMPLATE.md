<!--
  Fluxo GitFlow do projeto: CONTRIBUTING.md é a fonte de verdade.
  Caminho normal: feature/* → develop → (release) → main. Nada vai direto para main.
-->

## Resumo

<!-- O quê e, sobretudo, porquê. 1-3 frases. -->

## Tipo de alteração

- [ ] `feat` — nova funcionalidade
- [ ] `fix` — correção de bug
- [ ] `docs` — documentação
- [ ] `refactor` — alteração sem mudança de comportamento
- [ ] `test` — testes
- [ ] `chore` — manutenção / release

## Fluxo de branches (GitFlow)

- Branch de origem: `feature/...` &nbsp;|&nbsp; `release/...` &nbsp;|&nbsp; `hotfix/...`
- **Destino deste PR:** `develop` (feature / release-back) ou `main` (release / hotfix)

## Checklist

- [ ] Branch parte de `develop` (feature) ou `main` (hotfix).
- [ ] Este PR aponta para `develop` (feature / release-back) ou `main` (release / hotfix) — **nunca push direto para `main`**.
- [ ] Commits seguem Conventional Commits com escopo (`feat(escopo): …`).
- [ ] Testes passam: `cd backend && pytest` / `cd frontend && yarn build`.
- [ ] Lint limpo: `ruff check .` (backend) / `npx eslint src/ --ext .js,.jsx` (frontend).
- [ ] Sem segredos, sem `password` exposto, audit-log em escritas de admin.

<!-- Detalhes completos do fluxo: ver CONTRIBUTING.md -->
