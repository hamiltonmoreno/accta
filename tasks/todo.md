# Cat 5 F3 — Defesa Profissional (5.2) + Relações/IFATCA (5.4)

> Origem: `tasks/spec-fins-profissionais.md` §5, §7, F3 do roadmap §11.
> Ramo: `feature/cat5-f3-defesa-relacoes` (parte de `develop`).
> Antecedentes: F1 (#134) e F2 (#135) já em `develop`.

## Decisões confirmadas com o dono (2026-05-29)

- **§14 #3** — tomadas de posição passam por **aprovação interna da Direcção**.
  Fluxo: `rascunho → submetido → publicado` (ou de volta a `rascunho` se rejeitado) → `arquivado`.
- **Segregação de funções** — quem cria não pode aprovar a sua própria tomada
  de posição (mitigar abuso). Direcção ≠ criador para o passo `aprovar`.
- **§14 #4** — `RelacaoExterna.visibility` por instância (`socios`/`publico`,
  default `socios`); IFATCA seedada com `publico` (faz sentido editorial).

## Backend

- [ ] `models.py`: `DefesaProfissional` + Create/Update + constantes
  `DEFESA_TIPOS`, `DEFESA_STATUSES`. Campos extras: `submetido_em`/`_por`,
  `aprovado_em`/`_por`, `motivo_rejeicao`.
- [ ] `models.py`: `RelacaoExterna` + Create/Update + constantes `RELACAO_TIPOS`,
  `ESTADOS_FILIACAO`.
- [ ] `database.py`: 2 coleções + 4 índices + seed idempotente da IFATCA.
- [ ] `routes/profissional.py`: CRUD `defesa-profissional` + transições
  `submeter` (autor) · `aprovar` (Direcção ≠ autor) · `rejeitar` (Direcção, com
  `motivo`) · `arquivar` (Direcção).
- [ ] `routes/profissional.py`: CRUD `relacoes-externas`.
- [ ] Audit em todas as escritas + notificação ao autor em aprovado/rejeitado.

## Testes backend (~30)

- [ ] CRUD + RBAC (sócio comum 403 em escritas).
- [ ] Fluxo: rascunho→submetido (autor); submetido→publicado (Direcção ≠ autor);
  submetido→rascunho com motivo (rejeitar); publicado→arquivado.
- [ ] **Segregação**: autor tenta aprovar a sua submissão → 403.
- [ ] Visibilidade: rascunhos não vazam; `publico` só vê publicado+publico.
- [ ] IFATCA seedada (idempotente).
- [ ] Audit log existe em cada transição.

## Frontend

- [ ] `utils/api.js`: `defesaAPI` + `relacoesAPI`.
- [ ] `DefesaProfissionalPage.js`: tabs por status + ações contextuais
  (autor/Direcção × status).
- [ ] `RelacoesPage.js`: diretório com cards + badges de `estado_filiacao`.
- [ ] `PrivateLayout.js`: 2 novas entradas em "Profissional".
- [ ] `App.js`: rotas lazy.

## Verificação

- [ ] `pytest tests/test_profissional_routes.py` verde.
- [ ] `ruff check . && ruff format --check .`
- [ ] `eslint src/ --max-warnings=60` e `yarn build`.
- [ ] PR para `develop`.

## Fora de âmbito

- F4 superfícies públicas; F5 venda (gates abertos).
