# Spec — Foto de Perfil do Utilizador (Portal ACCTA)

> **Objetivo:** permitir que **cada utilizador carregue e troque a sua própria
> foto de perfil** (avatar) pela interface, exibindo-a em todo o portal — perfil,
> sidebar/barra de topo, lista de membros e como **autor** em mural, comentários
> e projetos — com **iniciais como fallback** quando não há foto.
>
> **Natureza deste documento:** especificação de mudança. Não implementa nada —
> define o quê, onde e como mudar, e o que já foi decidido pela ACCTA.
>
> **Branch:** `feature/foto-de-perfil` (a partir de `develop`, GitFlow)

---

## 1. Diagnóstico — estado atual (o que existe hoje)

### 1.1 Backend — o "esqueleto" já existe, mas é parcial

| Peça | Estado | Localização |
|---|---|---|
| Campo `photo_url` no utilizador | ✅ **Existe** (`Optional[str] = None`) | `models.py:70` (`UserBase`) → presente em `User`/respostas |
| `photo_url` editável pelo próprio | ✅ **Existe** | `models.py:89` (`UserProfileUpdate`) |
| Endpoint de upload de avatar | ✅ **Existe** | `POST /api/upload/avatars` — `upload.py:17,26,34` |
| `PATCH /users/me/profile` aceita `photo_url` | ✅ **Existe** | `users.py:105-117` |
| `photo_url` no `UserAdminUpdate` | ❌ **Ausente** (admin não mexe na foto) | `models.py:92-107` |
| Limpeza do ficheiro ao **remover/trocar** | ⚠️ **Parcial** — só ao **apagar a conta** | `users.py:227` |

- **Upload (`upload.py`):** categoria `avatars` aceita `.jpg/.jpeg/.png`, **2 MB**,
  validação por *magic bytes* (`validate_file_content`), guardado em
  `/uploads/avatars/<uuid>.<ext>` e servido por StaticFiles. **Aberto a qualquer
  utilizador autenticado** (sem gate de role — ao contrário de `documents`/`logos`
  que são admin-only, `upload.py:37`). Devolve `{filename, file_url, size, category}`.
- **`update_own_profile` (`users.py:105-117`):** faz
  `{k: v for k, v in data.model_dump().items() if v is not None}` → **não há como
  enviar `None` para LIMPAR a foto** (null = "não alterar"). Audit log genérico
  (`create_audit_log(current_user.id, "Atualizou o próprio perfil")`).
- **Limpeza de ficheiros:** ao **trocar** a foto, o ficheiro antigo fica **órfão**
  (só é apagado no delete da conta, `users.py:227` via `delete_upload_file`).

### 1.2 Frontend — a exibição de `photo_url` **não existe em lado nenhum**

`photo_url` **não é lido em nenhum componente** (confirmado por grep). Todos os
avatares são **iniciais hand-rolled** (`name.charAt(0)` numa caixa carmesim):

| Local | Ficheiro:linha | Dado disponível |
|---|---|---|
| Header do perfil | `PerfilPage.js:166-170` | `user` (próprio) — tem `photo_url` |
| Sidebar (rodapé) | `PrivateLayout.js:308-309` | `user` (próprio) |
| Topo mobile | `PrivateLayout.js:398-399` | `user` (próprio) |
| Topo desktop | `PrivateLayout.js:415-416` | `user` (próprio) |
| Lista de membros (admin) | `AdminUsuariosPage.js:269,335,375` | `u`/`editingUser` — têm `photo_url` |
| Autor de post (mural) | `MuralPage.js:213,490` | só `post.user_name` (+ `post.user_id`) |
| Autor de comentário (mural) | `MuralPage.js:104` | só `comment.user_name` (+ `user_id`) |
| Autor de comentário (projeto) | `ProjectDetailPage.js:227` | só `c.user_name` (+ `user_id`) |
| Utilizador atual (projeto) | `ProjectDetailPage.js:202` | `user` (próprio) |

- **`<Avatar>` shadcn já existe** (`components/ui/avatar.jsx`: `Avatar`,
  `AvatarImage`, `AvatarFallback`) mas **nunca é usado**.
- **API client já tem as primitivas:** `uploadAPI.uploadFile(category, file)`
  (`api.js:198`), `uploadAPI.deleteFile` (`api.js:205`), `usersAPI.updateProfile`
  (`api.js:135`). O formulário do perfil (`PerfilPage.js:87-91`) só edita
  `name`/`phone_number`/`bio` — **não tem campo de foto**.
- **Conteúdo (mural/comentários/projeto) só guarda `user_name` denormalizado**, mas
  guarda **também `user_id`** (`wall.py:56,181`; `projects.py:455`) → dá para
  resolver a foto do autor por `user_id` na leitura.

### 1.3 Resolução de URL de imagem `/uploads/...`

`api.js` define `baseURL = ${BACKEND_URL}/api`, mas `/uploads/...` é servido na
**raiz** do backend (fora de `/api`). O `BrandLogo.js:35` usa o caminho relativo
**tal-qual** (`src={url}`) — funciona em produção (mesma origem via Nginx) mas em
**dev** (frontend e backend em portas diferentes) a imagem **não carrega** e cai
no fallback. Para o avatar carregar em **dev e prod**, é preciso prefixar
`BACKEND_URL` em caminhos `/uploads/...` (helper `mediaUrl`, §6.2).

### 1.4 Precedentes de moderação (cultura do projeto)
- **Galeria:** toda a foto exige **aprovação** antes de aparecer (pending →
  approved/rejected) — `gallery.py`.
- **Mural:** posts passam por moderação.
- ⚠️ **Decisão D1 (§3):** o avatar **não** segue este fluxo (é pessoal, baixo
  risco) — aplica-se de imediato, com **remoção reativa** por admin/moderador.

---

## 2. Objetivos e não-objetivos

### Objetivos
1. **Carregar/trocar a própria foto** pela página de Perfil (recorte quadrado no
   cliente → upload → grava `photo_url`).
2. **Remover a própria foto** (volta às iniciais) — convenção de "limpar".
3. **Exibir a foto em todo o portal** (D3): perfil, sidebar/topo, lista de membros
   e como **autor** em mural, comentários e projetos — **iniciais como fallback**.
4. **Moderação reativa:** admin/moderador podem **remover** a foto de um membro
   (foto inadequada), com audit log e notificação ao próprio.
5. **Higiene de ficheiros:** apagar o ficheiro antigo ao **trocar/remover**.
6. **Não-destrutivo:** sem foto → iniciais (exatamente como hoje).

### Não-objetivos
- **Aprovação prévia** de avatares (D1 — só remoção reativa).
- Galeria/histórico de avatares anteriores.
- Editor avançado (filtros, rotação livre, brilho) — só recorte quadrado.
- Fotos para contas **technical** (system) — ficam com iniciais, sem prioridade.
- Sincronizar com Gravatar / fontes externas.

---

## 3. Decisões da ACCTA (já confirmadas)

| # | Decisão | Escolha |
|---|---|---|
| D1 | Moderação | **Imediata, sem aprovação prévia** + **remoção reativa** por admin/moderador |
| D2 | Enquadramento/tamanho | **Recorte quadrado no cliente** antes do upload |
| D3 | Onde aparece | **Tudo** — próprio (perfil/sidebar/topo), lista de membros e **autor** em mural/comentários/projetos |

---

## 4. Design da solução

### 4.1 Componente único `<UserAvatar>` (novo) — fonte única de exibição

`frontend/src/components/UserAvatar.js`, wrapper sobre o `<Avatar>` shadcn:

```jsx
// Pseudocódigo
<Avatar className={sizeClass}>
  {photoUrl && <AvatarImage src={mediaUrl(photoUrl)} alt={name} />}
  <AvatarFallback className="bg-carmesim text-white font-bold">
    {name?.charAt(0)?.toUpperCase() || '?'}
  </AvatarFallback>
</Avatar>
```

- Props: `name`, `photoUrl`, `size` (`sm`/`md`/`lg` → classes Tailwind), `className`.
- **`AvatarFallback` = iniciais carmesim** (preserva o aspeto atual; é o que aparece
  **sem foto**, **em erro/404** e **enquanto carrega**).
- Substitui **todas** as caixas de iniciais hand-rolled (§1.2).

### 4.2 Recorte no cliente (D2)
- Ao escolher o ficheiro, abrir um **modal de recorte quadrado** (1:1) com zoom/
  arrastar; ao confirmar, exportar para `Blob` (canvas → `toBlob`, ~512×512) e
  enviar via `uploadAPI.uploadFile('avatars', blob)`.
- Biblioteca sugerida: `react-easy-crop` (leve). **Alternativa sem nova dep:**
  recorte central por canvas (sem ajuste manual) — menos UX, mesmo resultado.
- Mantém o ficheiro pequeno e dentro do limite de 2 MB.

### 4.3 Exibir o autor em conteúdo (D3) — enriquecimento na **leitura**
Mural/comentários/projeto guardam **`user_id`** mas não a foto. Em vez de
denormalizar `user_photo_url` no write (fica **desatualizado** quando o autor troca
a foto e **não cobre** conteúdo antigo), **resolver a foto na leitura**:

- Helper `enrich_author_photos(docs, id_field="user_id", out_field="user_photo_url")`
  em `helpers.py`: recolhe os `user_id`, faz **um** batch
  `db.users.find({"id": {"$in": ids}}, {"id": 1, "photo_url": 1})` e injeta
  `user_photo_url` em cada doc. Custo: **1 query agregada por listagem**.
- Aplicar nas listagens de posts do mural, comentários do mural e comentários de
  projeto. **Sempre atual e cobre conteúdo antigo automaticamente** (sem migração).

> A alternativa "denormalizar no write" fica registada em §12 com o trade-off
> (staleness + sem backfill). Recomenda-se o enriquecimento na leitura.

---

## 5. Backend — mudanças

### 5.1 `update_own_profile` — limpar foto + higiene de ficheiro (`users.py`)
- **Convenção de "limpar"** (igual à spec da marca): `photo_url == ""` → remover
  (gravar `None` / `$unset`); `None`/ausente → manter. Tratar **antes** do filtro
  `if v is not None`.
- Ao **trocar ou remover**, apagar o ficheiro antigo se for `/uploads/avatars/...`
  (`delete_upload_file(existing.get("photo_url") or "")` — mesmo padrão do delete da
  conta).
- Audit logs específicos (ex.: `"profile_photo_updated"` / `"profile_photo_removed"`).

### 5.2 Remoção reativa por admin/moderador (D1) — `users.py`
Endpoint **dedicado** (não mexer no `UserAdminUpdate`, que de propósito **não** tem
`photo_url` — admin/moderador só removem, não definem fotos):

| Endpoint | Auth | Descrição |
|---|---|---|
| `DELETE /api/users/{user_id}/photo` | **admin + moderador** | Grava `photo_url=None`, apaga o ficheiro, `create_audit_log(current_user.id, "profile_photo_removed", user_id, request=request, details={...})` e **notifica** o utilizador (`create_notification(user_id, "admin", "Foto removida", "A sua foto de perfil foi removida pela moderação.", "/perfil")`). |

- RBAC: `has_role_or_privilege(current_user, ("admin", "moderador"), …)` (padrão de
  `users.py:128`).

### 5.3 Enriquecimento de autor (D3) — `helpers.py` + rotas de leitura
- `helpers.py`: `async def enrich_author_photos(docs, id_field="user_id", out_field="user_photo_url")`.
- `wall.py`: aplicar na listagem de **posts** e de **comentários** (depois de
  carregar, antes de devolver).
- `projects.py`: aplicar em `project_comments` (`GET /{project_id}` injeta
  `comments`, `projects.py:173-180`).

> Sem novo campo Pydantic obrigatório: `user_photo_url` é adicionado ao dict de
> resposta destas listagens (devolvidas como dicts). Se algum modelo de resposta
> for estrito, adicionar `user_photo_url: Optional[str] = None`.

### 5.4 Sem alterações de schema
`photo_url` já vive no doc `users` (jsonb). **Nenhuma coleção nova**; **não** dispara
Stop Conditions (sem migração destrutiva, sem mexer em auth/CORS/email).

---

## 6. Frontend — mudanças

### 6.1 `components/UserAvatar.js` (§4.1) — novo wrapper.

### 6.2 `utils/api.js` — helper `mediaUrl` + `usersAPI.removePhoto`
```js
export const mediaUrl = (path) =>
  !path ? '' : /^https?:\/\//.test(path) ? path : `${BACKEND_URL}${path}`;
// usersAPI.removePhoto: (userId) => api.delete(`/users/${userId}/photo`)
```
(prefixa `/uploads/...` com `BACKEND_URL`; deixa URLs absolutas intactas.)

### 6.3 Upload + recorte na página de Perfil (`PerfilPage.js`)
- Substituir a caixa de iniciais do header (`:166-170`) por
  `<UserAvatar size="lg" photoUrl={user.photo_url} name={user.name} />` e adicionar
  um botão **"Alterar foto"** (ícone `Camera`); no modo de edição, **"Remover foto"**.
- Fluxo: escolher ficheiro → modal de recorte (§4.2) →
  `uploadAPI.uploadFile('avatars', blob)` →
  `usersAPI.updateProfile({ photo_url: file_url })` → `refreshUser()` + `toast`.
  "Remover" → `updateProfile({ photo_url: '' })`.
- `useMutation` + `toast` (Sonner); validar tipo/tamanho no cliente antes do upload.

### 6.4 Trocar todas as iniciais por `<UserAvatar>`
- **Próprio:** `PrivateLayout.js:308,398,415` (lê `user.photo_url`).
- **Lista de membros:** `AdminUsuariosPage.js:269,335,375` (lê `u.photo_url`).
- **Autores (D3):** `MuralPage.js:104,213,490` e `ProjectDetailPage.js:227`
  (lê `user_photo_url` vindo do enriquecimento §5.3).
- `ProjectDetailPage.js:202` (próprio) lê `user.photo_url`.

### 6.5 Moderação reativa (UI)
- Em `AdminUsuariosPage` (cartão/edição do membro), ação **"Remover foto"** (só
  admin/moderador) → `usersAPI.removePhoto(userId)` + `invalidateQueries`.

---

## 7. Modelo de dados

`users` (sem alteração de schema — o campo já existe):
```json
{ "id": "…", "name": "…", "photo_url": "/uploads/avatars/ab12….jpg", "…": "…" }
```
- `photo_url = null`/ausente → `<UserAvatar>` mostra **iniciais**.
- `user_photo_url` nas respostas de **listagem** de posts/comentários é **derivado
  na leitura** (não persistido) — reflete sempre a foto **atual** do autor.

---

## 8. Matriz RBAC

| Ação | admin | moderador | financeiro | socio | público |
|---|:--:|:--:|:--:|:--:|:--:|
| Ver avatares (toda a app) | ✓ | ✓ | ✓ | ✓ | (onde a página já é pública) |
| Carregar/trocar a **própria** foto | ✓ | ✓ | ✓ | ✓ | ✗ |
| `POST /api/upload/avatars` | ✓ | ✓ | ✓ | ✓ | ✗ |
| Remover a **própria** foto | ✓ | ✓ | ✓ | ✓ | ✗ |
| Remover a foto **de outro** (`DELETE /users/{id}/photo`) | ✓ | ✓ | ✗ | ✗ | ✗ |

Toda escrita/remoção gera **audit log**; remoção por moderação **notifica** o
utilizador.

---

## 9. Migração / rollout (não-destrutivo)
- `photo_url` já existe e está `null` para todos → **iniciais** (idêntico a hoje)
  até alguém carregar foto.
- O enriquecimento de autor é só-leitura e tolera ausência (fallback iniciais) →
  cobre conteúdo antigo **sem migração**.
- Sem alteração de schema, auth, CORS ou email → **não** dispara Stop Conditions.

---

## 10. Plano de implementação (fases)

**Fase 1 — Backend**
- [ ] `users.py`: convenção "limpar" (`""`→None) + apagar ficheiro antigo no
      trocar/remover; audit logs específicos.
- [ ] `users.py`: `DELETE /users/{id}/photo` (admin+moderador, audit + notify).
- [ ] `helpers.py`: `enrich_author_photos(...)`; aplicar em `wall.py`
      (posts + comentários) e `projects.py` (comentários).

**Fase 2 — Componente + resolução de URL**
- [ ] `components/UserAvatar.js`; `utils/api.js`: `mediaUrl` + `usersAPI.removePhoto`.
- [ ] Substituir iniciais por `<UserAvatar>` em PrivateLayout, AdminUsuariosPage,
      MuralPage, ProjectDetailPage.

**Fase 3 — Perfil (upload + recorte + remover)**
- [ ] `PerfilPage.js`: avatar + "Alterar foto" (modal de recorte §4.2) + "Remover".
- [ ] (opcional) dep `react-easy-crop` **ou** recorte central por canvas.

**Fase 4 — Moderação (UI)**
- [ ] `AdminUsuariosPage`: ação "Remover foto" (admin/moderador).

**Fase 5 — Verificação** (§11).

---

## 11. Testes

**Backend (`backend/tests/`, pytest in-process):**
- `PATCH /users/me/profile` com `photo_url="/uploads/avatars/x.jpg"` grava; com
  `""` **limpa** (None) e apaga o ficheiro antigo; ausente → mantém.
- `POST /upload/avatars`: aceita autenticado (qualquer role); rejeita `.gif`/`.svg`
  e ficheiro > 2 MB (magic bytes).
- `DELETE /users/{id}/photo`: admin e moderador OK; financeiro/socio → 403; grava
  `photo_url=None`, cria audit log e notificação.
- `enrich_author_photos`: injeta `user_photo_url` correto; autor sem foto →
  ausente/None; autor inexistente → não rebenta.

**Frontend (manual, browser):**
- Carregar foto no perfil (com recorte) → aparece de imediato no perfil, sidebar e
  topo; sem foto → iniciais.
- Foto aparece como autor em mural/comentários/projeto; conteúdo **antigo** mostra a
  foto atual do autor (ou iniciais se não tiver).
- "Remover foto" volta às iniciais; admin/moderador removem a foto de outro membro
  (e o membro recebe notificação).
- Imagem carrega em **dev** (via `mediaUrl`/`BACKEND_URL`) **e** em prod.
- Falha de carregamento da imagem → `AvatarFallback` (iniciais), nunca quebrado.

---

## 12. Riscos e questões em aberto
- **Resolução de URL (`/uploads`):** `BrandLogo` usa caminho relativo (só funciona
  same-origin); o `mediaUrl` (§6.2) corrige para dev+prod. Considerar alinhar o
  `BrandLogo` ao mesmo helper (fora do âmbito).
- **Custo do enriquecimento:** +1 query agregada por listagem de posts/comentários
  — desprezável; se um dia pesar, cachear `photo_url` por `user_id` (TTL curto).
- **Ficheiros legados órfãos:** avatares de trocas anteriores ao fix de higiene
  ficam em disco — limpeza pontual opcional.
- **Privacidade/conteúdo impróprio:** sem aprovação prévia (D1), confia-se na
  remoção reativa; ativar fila de aprovação no futuro reaproveita o padrão da
  galeria.
- **Contas `technical`:** ficam sem foto (iniciais) — aceitável; dar-lhes foto é
  fora do âmbito.
- **WebP:** não incluído (avatars só `.jpg/.jpeg/.png`); alinhar com a nota da spec
  da marca se um dia se quiser WebP (depende de `validate_file_content`).
- **Nova dependência (`react-easy-crop`):** se a ACCTA preferir zero deps novas,
  usar recorte central por canvas (sem ajuste manual).
