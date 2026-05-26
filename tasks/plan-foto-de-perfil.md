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

## Fase 1 — Backend (TDD) ✅ (commit 433e458)
- [x] `models.py`: `photo_url` movido de `_EditableProfileFields` → `UserProfileUpdate`.
- [x] `users.py` `update_own_profile`: `""`→None + higiene de ficheiro + audit específico.
- [x] `users.py` `DELETE /users/{id}/photo` (admin+moderador): limpa/apaga/audit/notifica.
- [x] `helpers.py` `enrich_author_photos` (1 batch query/listagem).
- [x] `wall.py`: posts + pending + comentários. `projects.py`: comentários de `get_project`.
- [x] Testes: **115 passed** (foto set/clear/keep, RBAC remoção, enrich) + ruff limpo.

## Fase 2 — Componente + resolução de URL ✅
- [x] `components/UserAvatar.js` (fallback configurável: carmesim/neutro/âmbar/squircle).
- [x] `utils/api.js`: `mediaUrl(path)` + `usersAPI.removePhoto(userId)`.
- [x] Iniciais → `<UserAvatar>`: `PrivateLayout` (3), `AdminUsuariosPage` (3),
      `MuralPage` (3), `ProjectDetailPage` (2). eslint: só avisos pré-existentes.

## Fase 3 — Perfil (upload + recorte + remover) ✅
- [x] `components/AvatarCropDialog.js` — **recorte central por canvas (ZERO deps)**:
      o `react-easy-crop` não instalou (rede instável desta máquina); o dono optou
      pelo fallback pré-aprovado. Corta o quadrado central → JPEG ~512px;
      pré-visualização circular `object-cover` (WYSIWYG). Sem pan/zoom manual.
- [x] `PerfilPage.js`: avatar + botão câmara "Alterar foto" + "Remover foto" + mutations.

## Fase 4 — Moderação (UI) ✅
- [x] `AdminUsuariosPage`: "Remover foto" no diálogo de edição → `usersAPI.removePhoto`.

## Fase 5 — Verificação ✅
- [x] `pytest` backend (115 passed) + `ruff check` limpo.
- [x] `eslint` 0 erros (9 avisos pré-existentes) + `craco build` de produção OK.
- [ ] PR `feature/foto-de-perfil → develop`.
