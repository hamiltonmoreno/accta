# Cat 5 F4 — Superfícies públicas (ProfissaoPage + Publicações)

> Origem: `tasks/spec-fins-profissionais.md` §8.2, §10, §11 (F4), §12.
> Ramo: `feature/cat5-f4-superficies-publicas` (empilhado sobre F3 / PR #138).
> Depende de F1–F3 (F2 #135 em develop; F3 #138 aberto).

## Decisões (recomendadas, alinhadas à spec — autorizado pelo dono)

- **Router público dedicado** `routes/public_profissional.py` com prefixo
  `/public/...` (evita colisão com as rotas `/{id}` autenticadas; sem auth).
- **Recorte público** no query do DAO + **projeção** que exclui campos internos
  (`created_by`, workflow `submetido_*`/`aprovado_*`/`motivo_rejeicao`,
  `contacto`, `quota_anual`, `a_venda`, `preco`):
  - defesa: `status="publicado"` AND `visibility="publico"`.
  - relações: `visibility="publico"`.
  - publicações: `visibility="publico"` (download via `/documents/public/{id}`).
  - formações: `visibility="publico"` AND `ativo=true`.
- **Formacao ganha `visibility`** (aditivo/opcional, default `socios`; §13).
- Página pública em **`/publicacoes-publico`** (`/publicacoes` já é a rota privada
  do catálogo de sócios — não reutilizar).

## Backend

- [x] `models.py`: `Formacao`/Create/Update ganham `visibility` + `FORMACAO_VISIBILITIES`.
- [x] `database.py`: índice `ix_formacoes_vis_ativo`.
- [x] `routes/public_profissional.py`: 4 GET públicos (defesa/relacoes/formacoes/
  publicacoes) + GET-by-id (defesa/publicacoes), filtro no DAO + projeção.
- [x] `routes/__init__.py`: router registado.

## Testes backend (17 novos)

- [x] Público só vê defesa `publicado`+`publico`; relações/publicações `publico`;
  formações `publico`+`ativo`. Filtro aplicado no query; sem auth (sem `current_user`).
- [x] Projeção esconde campos internos (`created_by`, workflow, `contacto`,
  `quota_anual`, `a_venda`, `preco`).
- [x] GET-by-id aplica o mesmo recorte (404 fora dele); `tipo`/`estado` inválidos → 400.
- [x] **107 passed** (90 profissional + 17 público); F2 não regrediu com o campo novo.

## Frontend

- [x] `utils/api.js`: `getPublic()` em defesa/relacoes/formacoes/publicacoes
  (+ `getPublicOne`); `/publicacoes-publico` na lista de rotas públicas do interceptor.
- [x] `components/ProfissaoDestaques.js`: secções de defesa publicada + relações +
  formações públicas (useQuery; secção escondida quando vazia).
- [x] `pages/public/ProfissaoPage.js`: monta `<ProfissaoDestaques />` antes do CTA.
- [x] `pages/public/PublicacoesPublicoPage.js`: catálogo + filtro por tipo + download.
- [x] `App.js`: rota pública `/publicacoes-publico` (lazy).
- [x] `layouts/PublicLayout.js`: link "Publicações" na nav.
- [x] `FormacoesPage`: select de `visibility` no form de gestão.

## Verificação

- [x] `pytest` → 107 passed; `ruff check`/`ruff format --check` limpos.
- [x] `eslint --max-warnings=0` (ficheiros F4) limpo; `craco build` → Compiled successfully.
- [ ] PR (base = `feature/cat5-f3-defesa-relacoes` enquanto #138 não fundir).

## Fora de âmbito

- F5 venda (stop condition — §13; §14.5 em aberto). Tratada a seguir, com confirmação.
