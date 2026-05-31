# Cat 5 F5 — Venda de publicações (integra Cat. 4)

> Origem: `tasks/spec-fins-profissionais.md` §8.2, §11 (F5), §14.5.
> Ramo: `feature/cat5-f5-venda-publicacoes` (empilhado sobre F4 / PR #140).
> Depende de F2 (publicações, develop) + Cat. 4 (invoices/receitas, develop) + F4
> (superfície pública, PR #140, para mostrar o preço ao público).

## Decisões confirmadas com o dono (2026-05-30)

- **Pagamento = faturas internas** (não gateway externo). A receita externa
  regista-se em **Cat. 4** com `category="venda_publicacoes"` (já existente em
  `models.py`); sem integração de pagamentos online.
- **Sócios não pagam** — descarregam grátis; a venda aplica-se a não-sócios.

## Consequência de desenho (honesta)

Como **só sócios têm conta** no portal e **não pagam**, não há comprador
in-portal: não se cria um endpoint `comprar` vestigial. F5 = **permitir marcar à
venda + preço**, **mostrar o preço** (público) e **proteger o conteúdo pago**;
a receita regista-se pela via financeira existente (`venda_publicacoes`).

## Backend

- [x] `routes/profissional.py`: remover o bloqueio de `a_venda` em
  `create_publicacao`/`update_publicacao`; validar que `a_venda` exige `preco>0`
  (estado efetivo após merge no update).
- [x] `routes/public_profissional.py`: expor `a_venda`/`preco` na projeção pública
  (catálogo público mostra o preço). Campos internos continuam ocultos.
- [x] Sem novo endpoint de transação (respeita a fronteira de domínio; a receita
  cria-se no módulo Financeiro com a categoria já existente).

## Testes backend

- [x] `create`: `a_venda=True`+`preco>0` → ok; `a_venda=True` sem preço → 400.
- [x] `update`: tornar `a_venda` sem preço → 400; com preço → ok.
- [x] Projeção pública expõe `a_venda`/`preco` e oculta `created_by`. **109 passed.**

## Frontend

- [x] `PublicacoesPage` (gestão): checkbox **À venda** + campo **Preço (CVE)**
  (validação preço>0); nota a explicar grátis-para-sócios + manter documento
  privado + registar receita no Financeiro. Badge "À venda · X CVE" no card.
- [x] `PublicacoesPublicoPage` (público): itens à venda mostram preço + CTA
  "Adquirir — contactar ACCTA" e **não** mostram download (conteúdo pago).

## Verificação

- [x] `pytest` → 109 passed; `ruff check`/`ruff format --check` limpos.
- [x] `eslint --max-warnings=0` (ficheiros F5) limpo; `craco build` → Compiled successfully.
- [ ] PR (base = `feature/cat5-f4-superficies-publicas` — stack: develop ← F3 #138 ← F4 #140 ← F5).

## Operação (não-código)

- O admin que marca à venda deve manter o **documento** com visibilidade `Sócios`
  (senão o público descarrega grátis via `/documents/public`). A publicação pode
  ser `publico` (aparece no catálogo com preço) com o documento `socios`.

## Estado da spec

- Com F5, a `spec-fins-profissionais` fica **completa (F1–F5)** assim que os PRs
  #138/#140/F5 fundirem em `develop` → renomear para `-concluido`.
