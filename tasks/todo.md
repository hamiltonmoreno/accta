# TODO — Blog / Notícias (spec-blog-noticias.md)

Branch: `feature/blog-noticias` (off `develop`).
Âmbito: MVP completo — Fase 1 (backend CRUD), Fase 2 (frontend gestão+detalhe),
Fase 4 (testes). Fase 3 (melhorias) parcialmente incluída: toggle D5 (notificar
sócios) + backfill no seed. Decisões D1–D11 seguidas conforme recomendações.

## Fase 1 — Backend CRUD
- [x] `models.py`: `Post`/`PostCreate` estendidos, `PostUpdate` novo, enums `Literal`, limites, `slug` Optional, `notify_socios` (D5).
- [x] `posts.py`: `GET /posts/{id_or_slug}` (detalhe, visibility-aware, 404 não-leak).
- [x] `posts.py`: `PATCH /posts/{id}` (RBAC, audit, slug estável, updated_at/published_at, cleanup capa).
- [x] `posts.py`: `DELETE /posts/{id}` (RBAC, audit, cleanup capa).
- [x] `posts.py`: `GET /posts` filtros `status`/`type`/`q`/`skip`/`limit` + ordenação por data efetiva (D9).
- [x] `posts.py`: `POST /posts` preenche autor/slug/published_at + notify D5.
- [x] util `slugify` + unicidade; índices `slug` e `status/visibility/published_at` em `ensure_schema`.
- [x] `routes/upload.py`: categoria `covers` (RBAC admin+moderador, 2MB, SVG bloqueado).
- [x] `conftest.py`: `posts` adicionado ao `mock_db` global.

## Fase 2 — Frontend gestão + detalhe
- [x] `api.js`: `getOne`/`update`/`remove` + `getAll(params)` compatível com `getAll('publico')`.
- [x] `queryClient.js`: chaves `posts.all/list/detail` + teste de shape.
- [x] `AdminNoticiasPage.js` (tabela, criar/editar/eliminar, upload capa via `covers`, filtros).
- [x] `App.js`: rota `/admin/noticias` (admin/moderador) + `/noticias/:slug`.
- [x] `PrivateLayout.js`: item de menu "Notícias" + título.
- [x] `NoticiaDetailPage.js` + rota pública `/noticias/:slug` (texto simples, sem HTML).
- [x] `NoticiasPage.js`: cards ligam ao detalhe, excerpt/capa, TanStack Query.
- [x] `HomePage.js`: 3 últimas via `limit=3`, cards ligam ao detalhe.

## Fase 3 — Melhorias (parcial)
- [x] Toggle "notificar sócios" ao publicar `visibility=socios` (D5).
- [x] Backfill no `seed_data.py`: `slug`/`status`/`published_at`.
- [ ] (Adiado) Paginação visual refinada — não justificada pelo volume atual.

## Fase 4 — Testes & verificação
- [x] `backend/tests/test_posts.py` — 31 casos (list/detalhe/CRUD/RBAC/slug/published_at/cleanup/covers).
- [x] `ruff check` ✓ + `ruff format` ✓.
- [x] `pytest -m unit` → 589 passed (2 falhas pré-existentes em `test_users_routes` — regex search, não relacionadas).
- [x] `eslint` → 0 erros (1 warning pré-existente em HomePage:257, < budget 60).
- [x] `jest` queryClient → 11/11 (inclui shape das chaves `posts`).
- [ ] `craco build` — a confirmar (em execução).
- [ ] Verificação manual no browser (golden path) — pendente do dono.

## Review
- **Diagnóstico da spec confirmado 1:1** antes de implementar (posts.py só listava/criava;
  sem detalhe/edição/eliminação; sem UI de gestão; `type`/`visibility` strings livres).
- **Decisões**: seguidas as recomendações D1–D11. Conteúdo em texto simples (sem
  `dangerouslySetInnerHTML`) → anti-XSS. Slug estável após publicação (só regenera
  em rascunho a pedido). `covers` como categoria dedicada evita 403 no `moderador`.
- **Compat. dados**: enums `Literal` validados contra o seed (todos os valores já
  conformes); `slug` Optional + `published_at` com fallback para `created_at` →
  posts antigos não partem nem desaparecem. Sem migração destrutiva (só campos
  jsonb + índices idempotentes).
- **Ficheiros tocados**: 16 (7 backend, 9 frontend) — conforme tabela §9 da spec.
