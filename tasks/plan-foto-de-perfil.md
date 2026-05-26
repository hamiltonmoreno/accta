# Plano — Foto de Perfil do Utilizador

Spec: `tasks/spec-foto-de-perfil.md`. Branch `feature/foto-de-perfil` (de `develop`, GitFlow).

## Decisões fechadas com o dono (2026-05-26)
- **Recorte**: `react-easy-crop` (compat. React 19 confirmada: peer `react >=16.4.0`).
  Fallback: recorte central por canvas se houver problema de build.
- **Admin/moderador só REMOVE foto, nunca define** (honrar §5.2): retirar `photo_url`
  do `UserAdminUpdate` — move-se de `_EditableProfileFields` para `UserProfileUpdate`.
  (Verificado: a `AdminUsuariosPage` nunca envia `photo_url` no update do admin.)

## Derivações da spec corrigidas após grounding
- `UserAdminUpdate` JÁ tinha `photo_url` (via base partilhada) — corrigido pela decisão acima.
- `upload.py` avatares exigem `status == "ativo"` (não só autenticado) — refina §8.
- `delete_upload_file` (helpers) é no-op seguro em URL vazia/inexistente — reutilizável.

## Fase 1 — Backend (TDD)
- [ ] `models.py`: mover `photo_url` de `_EditableProfileFields` → `UserProfileUpdate`.
- [ ] `users.py` `update_own_profile`: ler doc atual; `photo_url==""` → limpar (None) +
      `delete_upload_file(antigo)`; troca de foto → apaga o antigo; audit
      `profile_photo_updated`/`profile_photo_removed` (genérico nos restantes campos).
- [ ] `users.py` `DELETE /users/{id}/photo` (admin+moderador): limpa, apaga ficheiro,
      audit `profile_photo_removed` (com `request`+details) + notifica o utilizador.
- [ ] `helpers.py` `enrich_author_photos(docs, id_field="user_id", out_field="user_photo_url")`
      — 1 batch `find({"id": {"$in": ids}}, {"id":1,"photo_url":1})`.
- [ ] `wall.py`: aplicar em posts (`get_wall_posts`, `get_pending_wall_posts`) e
      comentários (`get_wall_comments`).
- [ ] `projects.py`: aplicar em `comments` de `get_project`.
- [ ] Testes (extend `test_users_routes.py` + enrich): limpar/trocar/manter foto;
      DELETE RBAC (admin/moderador OK; financeiro/socio 403) + audit + notify;
      `enrich_author_photos` (injeta correto / sem foto / autor inexistente).

## Fase 2 — Componente + resolução de URL
- [ ] `components/UserAvatar.js` (wrapper do `<Avatar>` shadcn; fallback iniciais carmesim).
- [ ] `utils/api.js`: `mediaUrl(path)` + `usersAPI.removePhoto(userId)`.
- [ ] Substituir iniciais por `<UserAvatar>`: `PrivateLayout` (3), `AdminUsuariosPage`,
      `MuralPage` (post+comentário), `ProjectDetailPage` (autor+próprio).

## Fase 3 — Perfil (upload + recorte + remover)
- [ ] `PerfilPage.js`: avatar + "Alterar foto" (modal recorte `react-easy-crop`) + "Remover".
- [ ] dep `react-easy-crop` no `package.json`.

## Fase 4 — Moderação (UI)
- [ ] `AdminUsuariosPage`: ação "Remover foto" (admin/moderador) → `usersAPI.removePhoto`.

## Fase 5 — Verificação
- [ ] `pytest -m unit` (sem regressões) + `ruff check`.
- [ ] `eslint` 0/0 + `craco build`.
- [ ] PR `feature/foto-de-perfil → develop`.
