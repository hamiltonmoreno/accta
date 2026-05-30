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

- [x] `models.py`: `DefesaProfissional` + Create/Update + constantes
  `DEFESA_TIPOS`, `DEFESA_STATUSES`. Campos extras: `submetido_em`/`_por`,
  `aprovado_em`/`_por`, `motivo_rejeicao`.
- [x] `models.py`: `RelacaoExterna` + Create/Update + constantes `RELACAO_TIPOS`,
  `ESTADOS_FILIACAO`.
- [x] `database.py`: 2 coleções + 4 índices + seed idempotente da IFATCA.
- [x] `routes/profissional.py`: CRUD `defesa-profissional` + transições
  `submeter` (autor) · `aprovar` (Direcção ≠ autor) · `rejeitar` (Direcção, com
  `motivo`) · `arquivar` (Direcção).
- [x] `routes/profissional.py`: CRUD `relacoes-externas`.
- [x] Audit em todas as escritas + notificação ao autor em aprovado/rejeitado.
- [x] **Atomicidade (pós-review)**: as 4 transições usam **compare-and-swap**
  (status esperado no filtro do `update_one` + `matched_count` → 409) para
  fechar a janela TOCTOU entre `find_one` e `update_one`.

## Testes backend (86 no total, +14 pós-review)

- [x] CRUD + RBAC (sócio comum 403 em escritas).
- [x] Fluxo: rascunho→submetido (autor); submetido→publicado (Direcção ≠ autor);
  submetido→rascunho com motivo (rejeitar); publicado→arquivado.
- [x] **Segregação**: autor tenta aprovar/rejeitar a sua submissão → 403.
- [x] Visibilidade: rascunhos não vazam; rascunho `publico` alheio → 403 (gate de status).
- [x] IFATCA seedada (idempotente).
- [x] **Pós-review**: conflito CAS → 409 (4 transições); 404 nas 4 transições;
  asserção de audit-log no `submeter`; `$set` do `rejeitar` (limpa `submetido_*`,
  grava `motivo`); `arquivar` a partir de `submetido` grava `arquivado_*`;
  `relacoes` default `visibility=socios` + `publico` persistido.

## Frontend

- [x] `utils/api.js`: `defesaAPI` + `relacoesAPI`.
- [x] `DefesaProfissionalPage.js`: tabs por status + ações contextuais
  (autor/Direcção × status).
- [x] **Pós-review**: `RejeicaoModal` com validação inline + `disabled` quando
  `motivo` vazio (paridade com `DefesaModal`).
- [x] `RelacoesPage.js`: diretório com cards + badges de `estado_filiacao`.
- [x] `PrivateLayout.js`: 2 novas entradas em "Profissional".
- [x] `App.js`: rotas lazy.

## Verificação

- [x] `pytest tests/test_profissional_routes.py` → **86 passed**.
- [x] `ruff check . && ruff format --check .` → limpo.
- [x] `eslint src/ --max-warnings=60` → limpo; `craco build` → Compiled successfully.
- [ ] PR para `develop` (a abrir).

## Revisão multi-agente (pré-PR) — resultado

Duas passagens (a 1.ª com agentes `Explore` falhou na saída estruturada em 5/6
dimensões; re-corrida só do backend com o agente por omissão). 24 achados brutos,
consolidados:

- **Aplicado**: compare-and-swap nas 4 transições (TOCTOU — invariante explícito
  do projeto); +14 testes de reforço; validação inline no `RejeicaoModal`.
- **Refutado na verificação adversarial**: alegada falha de RBAC na aprovação (o
  backend **rejeita** o autor a aprovar a própria submissão, `profissional.py`
  L527-531; o frontend espelha com `!isAuthor`); achados sobre código-fantasma.

### A confirmar com o dono (NÃO alterado — decisões de máquina de estados)

1. **`arquivar` a partir de `submetido`/`rascunho`** — hoje um único membro da
   Direcção pode arquivar (descartar) uma submissão pendente sem 2.º aprovador,
   e `arquivado` é terminal (sem reabertura). Restringir a `publicado`? Permitir
   reabrir?
2. **Editar enquanto `submetido`** — `update_defesa` permite editar conteúdo em
   `submetido`; o aprovador poderia aprovar conteúdo diferente do revisto.
   Restringir edição a `rascunho` (ou re-armar para `rascunho` ao editar)?

### Latente para F4 (sem fuga hoje — todas as leituras exigem auth)

- O recorte público (`status=publicado` + `visibility=publico`) **não** está nos
  handlers atuais; **não reutilizar** `list_defesa`/`list_relacoes`/`get_*` para a
  superfície pública sem acrescentar o predicado de `visibility` no query do DAO.
- `ix_defesa_visibility` é peso morto até a query pública da F4 o usar.

## Fora de âmbito

- F4 superfícies públicas; F5 venda (gates abertos).
