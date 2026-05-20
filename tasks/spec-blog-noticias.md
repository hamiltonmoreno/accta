# Spec — Blog / Notícias do Portal ACCTA (gestão completa)

> **Objetivo:** transformar o módulo de notícias — hoje um "esqueleto" só de
> leitura (listar + criar via API, sem UI de gestão e sem página de detalhe) —
> num blog institucional completo: CRUD de posts com ecrã de gestão para staff,
> página pública de detalhe (ler o artigo inteiro), capa, rascunho/publicado e
> RBAC consistente.
>
> **Natureza deste documento:** especificação de mudança. Não implementa nada —
> define o quê, onde e como mudar, e o que precisa de decisão da ACCTA.
>
> **Branch:** `claude/blog-analysis-spec-dAgjL`

---

## 1. Diagnóstico — estado atual (o que existe hoje)

### 1.1 Backend — `backend/routes/posts.py` (56 linhas)

| Endpoint | Estado | Detalhe |
|---|---|---|
| `GET /api/posts?visibility=` | ✅ existe | Lista visibility-aware: anónimo → só `publico`; sócio autenticado → `publico` + `socios`; staff (`admin`/`moderador`) → tudo (ou filtra pela `visibility` pedida). Ordena por `created_at` desc, limite 1000. |
| `POST /api/posts` | ✅ existe | Cria post. Restrito a **`admin`** e **`moderador`**. Cria audit log (`create_audit_log(user_id, "Criou post {id}", target_id)`). |
| `GET /api/posts/{id}` | ❌ **falta** | Não há leitura de um post individual. |
| `PUT/PATCH /api/posts/{id}` | ❌ **falta** | **Não há forma de editar um post.** |
| `DELETE /api/posts/{id}` | ❌ **falta** | **Não há forma de eliminar um post.** |

### 1.2 Modelo — `backend/models.py` (`Post` / `PostCreate`)

```python
class Post(BaseModel):
    id: str               # uuid4
    title: str
    content: str
    type: str = "noticia"      # string livre, sem validação
    visibility: str = "publico" # string livre, sem validação
    tags: List[str] = []
    created_at: datetime
```

Campos **em falta** para um blog real: `author` / `author_id`, `cover_url`
(imagem de capa), `slug`, `excerpt`/`summary`, `updated_at`, `status`
(rascunho/publicado), `published_at`.
`type` e `visibility` são strings livres sem `Literal`/enum (risco de valores
inconsistentes; o frontend assume `noticia`/`institucional`/`educativo` e
`publico`/`socios`/`privado`).

### 1.3 Frontend — API client `frontend/src/utils/api.js`

```js
export const postsAPI = {
  getAll: (visibility) => api.get('/posts', { params: { visibility } }),
  create: (data) => api.post('/posts', data),
};
```

`getById`, `update`, `remove` **não existem**. E `create` é **código morto** —
**nenhuma página o invoca** (ver §1.5).

### 1.4 Frontend — página pública `NoticiasPage.js` (`/noticias`)

- Grid de cards com filtro **client-side** por `type` (Todas / Notícias /
  Institucional / Educativo).
- Cada card mostra: badge do tipo, data, título, conteúdo **truncado**
  (`line-clamp-3`) e até 3 tags.
- ❌ **Não há página de detalhe** — clicar num card não faz nada; é impossível
  ler a notícia completa. Não existe rota `/noticias/:id`.
- ❌ Sem imagem de capa, sem autor, sem paginação, sem pesquisa.
- ⚠️ Usa o padrão legado `useState + useEffect + axios` (as regras de frontend
  pedem TanStack Query — `lib/queryClient.js` — para páginas migradas).
- `HomePage.js` também mostra as 3 notícias mais recentes (mesmo padrão legado).

### 1.5 Gestão do blog — **NÃO EXISTE**

- Não há página privada de gestão de posts (em `frontend/src/pages/private/`).
- Não há item no menu lateral (`PrivateLayout.js`) para "Notícias"/"Blog".
- Não há rota em `App.js`.
- Conclusão: embora o backend permita a `admin`/`moderador` **criar** posts, **na
  prática não há nenhuma interface para o fazer**, e **ninguém consegue editar ou
  eliminar** (endpoints inexistentes). O blog é hoje, efetivamente, **só de
  leitura, alimentado pelo `scripts/seed_data.py`** (que insere alguns posts).

### 1.6 Testes

- ❌ Não existe `backend/tests/test_posts.py` (nenhuma cobertura dedicada).
- ⚠️ `conftest.py` **não tem a coleção `posts` no `mock_db`** (só `wall_posts`).
  Qualquer teste novo tem de a ligar em-teste:
  `mock_db.posts = MagicMock(...)` com `find/find_one/insert_one/...` como `AsyncMock`.

### 1.7 Resposta direta às perguntas

| Pergunta | Resposta |
|---|---|
| **Como está a situação do blog?** | Esqueleto incompleto: backend só lista e cria; sem editar/eliminar; sem detalhe; sem gestão. |
| **Como está a página de notícias?** | `/noticias` lista cards com filtro por tipo, mas trunca o texto e **não liga a nenhuma página de detalhe** — não dá para ler o artigo. |
| **Que função cria/edita os posts?** | Backend permite `admin` + `moderador` **criar**. **Ninguém edita/elimina** (sem endpoints). E **não há UI** para nenhuma função gerir o blog. |
| **Como gerir o blog hoje?** | Não há forma na aplicação — apenas via seed ou chamada direta à API. É o que esta spec vem resolver. |

---

## 2. Decisões necessárias (📋 a confirmar com o dono)

Marcadas para o dono confirmar antes/durante a implementação. As **recomendações**
estão alinhadas com as convenções já existentes no projeto.

| # | Decisão | Recomendação | Porquê |
|---|---|---|---|
| D1 | **Quem gere o blog?** | `admin` **+** `moderador` (criar/editar/eliminar). | O backend já autoriza ambos a criar; `moderador` já é responsável por conteúdo (Mural + Galeria). Coerente. |
| D2 | **Rascunho vs. publicado?** | Sim — adicionar `status: rascunho \| publicado`. Público só vê `publicado`. | Permite preparar notícias sem as expor. |
| D3 | **Imagem de capa?** | Sim — `cover_url`, via sistema de upload existente (`POST /api/upload/{category}`). | Blog sem capa fica pobre; reutiliza infra. Categoria → ver D6. |
| D4 | **Detalhe por `slug` ou `id`?** | `slug` (SEO) gerado do título, com `id` como fallback na rota. | URLs legíveis (`/noticias/nova-rota-praia-sal`). |
| D5 | **Notificar sócios ao publicar?** | Opcional, default **não**; se `visibility=socios`, oferecer toggle "notificar sócios" que chama `notify_all_active_users('system', …)`. | Evitar spam; dar controlo ao editor. ⚠️ não é email, é notificação in-app. |
| D6 | **Categoria de upload da capa** | Reutilizar `logos` (2MB, imagens) **ou** criar categoria `posts`/`covers`. | Decisão de limites/validação em `file_validation.py`. |
| D7 | **Migrar `NoticiasPage`/`HomePage` para TanStack Query?** | Sim (alinhar com as regras de frontend). | Coerência; cache; menos `console.error`. |
| D8 | **Validar `type`/`visibility` com enum?** | Sim — `Literal[...]` no modelo. | Evita lixo nos dados; o frontend já assume valores fixos. |

> **Âmbito faseado:** §7 separa **MVP** (fecha o ciclo: editar/eliminar/detalhe/
> gestão) das **melhorias** (capa, rascunho, slug, notificação, migração TanStack
> Query). Se o dono quiser só o essencial, parar no fim da Fase 2.

---

## 3. Arquitetura proposta

```
PÚBLICO                                    PRIVADO (staff: admin + moderador)
─────────────────────────────             ──────────────────────────────────
/noticias            (lista)               /admin/noticias        (gestão: tabela + ações)
/noticias/:slug      (detalhe) ← NOVO        ├─ Modal "Novo post"
HomePage (3 últimas)                         ├─ Modal "Editar post"
                                             └─ Eliminar (confirm)

           Backend  backend/routes/posts.py
           ─────────────────────────────────
           GET    /api/posts                 (já existe; + filtro status)
           GET    /api/posts/{id_or_slug}    ← NOVO (detalhe público)
           POST   /api/posts                 (já existe; + novos campos)
           PUT    /api/posts/{id}            ← NOVO (editar)  [admin/moderador]
           DELETE /api/posts/{id}            ← NOVO (eliminar)[admin/moderador]
```

---

## 4. Mudanças no Backend

### 4.1 Modelo (`backend/models.py`)

Estender `Post` / `PostCreate` e adicionar `PostUpdate`:

```python
POST_TYPES = ["noticia", "institucional", "educativo"]
POST_VISIBILITIES = ["publico", "socios", "privado"]
POST_STATUSES = ["rascunho", "publicado"]

class Post(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str                                  # D4 — derivado do título (único)
    content: str
    excerpt: Optional[str] = None              # resumo p/ cards (senão, derivar de content)
    cover_url: Optional[str] = None            # D3
    type: Literal["noticia", "institucional", "educativo"] = "noticia"   # D8
    visibility: Literal["publico", "socios", "privado"] = "publico"      # D8
    status: Literal["rascunho", "publicado"] = "publicado"               # D2
    tags: List[str] = []
    author_id: Optional[str] = None
    author_name: Optional[str] = None          # desnormalizado p/ render simples
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[str] = None           # ISO string (regra: datas como str)
    published_at: Optional[str] = None

class PostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    cover_url: Optional[str] = None
    type: Literal[...] = "noticia"
    visibility: Literal[...] = "publico"
    status: Literal[...] = "publicado"
    tags: List[str] = []

class PostUpdate(BaseModel):                    # todos opcionais (PATCH-like)
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    cover_url: Optional[str] = None
    type: Optional[Literal[...]] = None
    visibility: Optional[Literal[...]] = None
    status: Optional[Literal[...]] = None
    tags: Optional[List[str]] = None
```

> ⚠️ **Compat. com dados existentes (CLAUDE.md stop condition):** posts já
> existentes (seed) **não têm** `slug`/`status`. Como `Post` usa
> `extra="ignore"` e os novos campos têm default, a leitura não parte. Mas:
> `slug` não tem default seguro → tornar **`Optional[str] = None`** OU fazer
> backfill no `ensure_schema`/script. **Recomendação:** `slug: Optional[str]`
> + no `GET /posts/{id_or_slug}` aceitar `id` quando `slug` é nulo; gerar slug
> no create/update. Para `status`, default `publicado` mantém os posts seed
> visíveis (não esconder conteúdo já público).

### 4.2 Rotas (`backend/routes/posts.py`)

1. **`GET /api/posts`** — adicionar filtro de `status`:
   - Anónimos/sócios: forçar `status = "publicado"` (nunca ver rascunhos).
   - Staff: pode pedir `?status=rascunho` para o ecrã de gestão; por omissão, vê tudo.
2. **`GET /api/posts/{id_or_slug}`** *(novo)* — resolve por `slug` e cai para `id`.
   - Aplicar a **mesma regra de visibilidade** do `GET /posts` (anónimo só
     `publico`+`publicado`; sócio +`socios`; staff tudo). 404 se não autorizado/inexistente.
3. **`PUT /api/posts/{id}`** *(novo)* — `admin`/`moderador`. Aplica `PostUpdate`
   (só campos enviados, via `model_dump(exclude_unset=True)`), regenera `slug`
   se `title` mudou, define `updated_at`, define `published_at` na 1ª transição
   para `publicado`. **`create_audit_log(user_id, "Editou post {id}", id)`**.
4. **`DELETE /api/posts/{id}`** *(novo)* — `admin`/`moderador`. 404 se não existe.
   **`create_audit_log(user_id, "Eliminou post {id}", id)`**.
5. **`POST /api/posts`** — preencher `author_id`/`author_name` a partir do
   `current_user`, gerar `slug`, definir `published_at` se nasce `publicado`.
   Opcional D5: se `visibility=socios` e flag → `notify_all_active_users(...)`.

> **Regras do projeto a respeitar (`.claude/rules/api.md`):** RBAC explícito
> (`if current_user.role not in ["admin","moderador"]: raise HTTPException(403)`),
> **audit log em toda a escrita de staff**, datas como ISO string, sem SQL cru
> (usar o DAO Mongo-like), `HTTPException` 401/403/404 corretos.

### 4.3 Slug — utilitário

Função simples (sem dependência nova): minúsculas, remover acentos
(`unicodedata.normalize('NFKD', …)`), `[^a-z0-9]+ → "-"`, trim de `-`. Garantir
unicidade: se colidir, sufixar `-2`, `-3`… (verificar com `db.posts.find_one({"slug": s})`).

### 4.4 Índice (`database.py` — `ensure_schema`)

Adicionar índice de expressão em `(doc->>'slug')` para o lookup de detalhe
(coerente com os índices `(doc->>'field')` já existentes). **Não** criar índices
a partir das rotas (regra de DB).

---

## 5. Mudanças no Frontend

### 5.1 API client (`utils/api.js`)

```js
export const postsAPI = {
  getAll: (params) => api.get('/posts', { params }),     // { visibility, type, status }
  getOne: (idOrSlug) => api.get(`/posts/${idOrSlug}`),   // NOVO
  create: (data) => api.post('/posts', data),
  update: (id, data) => api.put(`/posts/${id}`, data),   // NOVO
  remove: (id) => api.delete(`/posts/${id}`),            // NOVO
};
```

### 5.2 `lib/queryClient.js` — chaves

Adicionar ao registo `queryKeys`:
```js
posts: {
  list: (params) => ['posts', params ?? {}],
  detail: (idOrSlug) => ['posts', 'detail', idOrSlug],
},
```

### 5.3 Página de gestão (NOVA) — `pages/private/AdminNoticiasPage.js`

**Modelar em `DocumentosPage.js`** (já usa o padrão correto: `useQuery` +
`useMutation` + `Dialog` + `queryKeys` + `toast` + gate por role).

- Tabela/lista de posts (título, tipo, visibilidade, status, data, autor).
- Filtros: tipo, status (rascunho/publicado), pesquisa por título.
- Botão **"Novo post"** → `Dialog` com formulário:
  título, tipo (select), visibilidade (select), status (select),
  excerpt, conteúdo (textarea), tags (input → array), **upload de capa**
  (reutilizar `uploadAPI` como em `DocumentosPage`).
- Por linha: **Editar** (mesmo `Dialog` pré-preenchido) e **Eliminar**
  (confirmação, ex.: `AlertDialog`).
- Mutations: `onSuccess → qc.invalidateQueries({ queryKey: queryKeys.posts.list() })`
  + `toast.success`; erros via `toast.error(error.response?.data?.detail)`.
- Gate: renderizar/permitir só a `admin` + `moderador` (ver §6).

### 5.4 Rota + navegação

- **`App.js`**: nova rota privada
  `"/admin/noticias"` dentro de `<ProtectedRoute allowedRoles={['admin','moderador']}>`.
- **`PrivateLayout.js`**: novo item de menu
  `{ label: 'Notícias', path: '/admin/noticias', icon: Newspaper, roles: ['admin','moderador'] }`
  (a função de filtro por role já suporta `admin`/`moderador`). Acrescentar o
  título correspondente no `getPageTitle()`.

### 5.5 Página de detalhe pública (NOVA) — `pages/public/NoticiaDetailPage.js`

- Rota pública `"/noticias/:slug"` em `App.js` dentro de `<PublicLayout>`.
- `useQuery(queryKeys.posts.detail(slug), () => postsAPI.getOne(slug))`.
- Render: capa (se existir), tipo + data + autor, título, **conteúdo completo**,
  tags. Tratar 404 (post inexistente/sem permissão) com `EmptyState` + link de volta.
- Respeitar o design **neutral-led** (skill `/frontend-design`): superfícies
  brancas/`#F5F5F5`, texto Grafite, Carmesim só como acento (≤1 botão primário,
  links). **Nunca** texto Carmesim sobre fundo escuro/colorido.

### 5.6 `NoticiasPage.js` (lista) — ligar ao detalhe + migrar

- Envolver cada card num link para `/noticias/${post.slug ?? post.id}`.
- Mostrar `excerpt` (fallback: `content` truncado) e capa, se existirem.
- (D7) Migrar de `useState+useEffect+axios` → `useQuery(queryKeys.posts.list({ visibility:'publico' }))`.
- `HomePage.js`: idem para a secção das 3 notícias (migração opcional, mesma fase).

---

## 6. RBAC — matriz final

| Ação | Anónimo | `socio` | `moderador` | `financeiro` | `admin` |
|---|---|---|---|---|---|
| Ver lista pública (`publico`, `publicado`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ver posts `socios` | ❌ | ✅ | ✅ | ✅ | ✅ |
| Ver `privado` / rascunhos | ❌ | ❌ | ✅ | ❌ | ✅ |
| Criar / Editar / Eliminar | ❌ | ❌ | ✅ | ❌ | ✅ |

> `financeiro` **não** gere blog (coerente: só Mural/Galeria/Notícias são
> conteúdo de `moderador`). Confirmar em D1.

---

## 7. Plano de implementação (faseado, itens verificáveis)

### Fase 1 — Backend CRUD (fecha o ciclo)
- [ ] `models.py`: estender `Post`/`PostCreate`, adicionar `PostUpdate` + enums (`Literal`). `slug` Optional p/ compat (§4.1).
- [ ] `posts.py`: `GET /posts/{id_or_slug}` (detalhe, visibility-aware).
- [ ] `posts.py`: `PUT /posts/{id}` (editar, RBAC admin/moderador, audit log, slug/updated_at/published_at).
- [ ] `posts.py`: `DELETE /posts/{id}` (eliminar, RBAC, audit log).
- [ ] `posts.py`: `GET /posts` respeita `status` (público só `publicado`).
- [ ] `posts.py`: `POST /posts` preenche autor/slug/published_at.
- [ ] util `slugify` + unicidade; índice `(doc->>'slug')` em `ensure_schema`.

### Fase 2 — Frontend gestão + detalhe (MVP utilizável)
- [ ] `api.js`: `getOne`/`update`/`remove` + `getAll(params)`.
- [ ] `queryClient.js`: chaves `posts.list`/`posts.detail`.
- [ ] `AdminNoticiasPage.js` (gestão: tabela, criar/editar/eliminar) — modelo `DocumentosPage`.
- [ ] `App.js`: rota `/admin/noticias` (`allowedRoles=['admin','moderador']`).
- [ ] `PrivateLayout.js`: item de menu "Notícias" + título.
- [ ] `NoticiaDetailPage.js` + rota pública `/noticias/:slug`.
- [ ] `NoticiasPage.js`: cards ligam ao detalhe.

### Fase 3 — Melhorias (D3/D5/D7)
- [ ] Upload de capa no formulário (categoria conforme D6) + `file_validation.py`.
- [ ] Toggle "notificar sócios" ao publicar com `visibility=socios` (D5).
- [ ] Migrar `NoticiasPage`/`HomePage` para TanStack Query (D7).
- [ ] Excerpt/capa nos cards de lista e na Home.

### Fase 4 — Testes & verificação
- [ ] `backend/tests/test_posts.py` — ligar `mock_db.posts` em-teste (§1.6).
  Casos: list visibility/status por role; detalhe por slug e id; create/edit/delete
  RBAC (403 p/ socio/financeiro/anónimo); audit log chamado; 404s.
- [ ] `ruff check .` + `ruff format .` (backend); `pytest` verde.
- [ ] `npx eslint src/ --ext .js,.jsx --max-warnings=60` (frontend).
- [ ] **Verificação manual no browser** (golden path + edge): criar → editar →
  publicar → ver em `/noticias` → abrir detalhe → eliminar; rascunho não aparece
  ao público; `socios` não aparece a anónimo.

---

## 8. Riscos / Stop conditions (CLAUDE.md)

- **Dados existentes (seed)** sem `slug`/`status`: não esconder nem partir
  leitura. Mitigação em §4.1 (defaults seguros + `slug` opcional/backfill).
- **Notificar sócios (D5)** usa `notify_all_active_users` (in-app, **não** email)
  → não é a stop condition de email, mas usar com parcimónia (toggle, default off).
- **Mudança de modelo Pydantic**: `Literal` em `type`/`visibility` pode **rejeitar**
  valores legados se o seed tiver algo fora da lista — auditar `seed_data.py`
  (linhas ~228–267) antes de aplicar enums; ajustar a lista ou os dados.
- **Sem migração destrutiva** de DB — só adição de campos jsonb + 1 índice
  idempotente. Nada de DROP.
- Manter **um só botão primário Carmesim por vista** e regras de contraste no
  detalhe/gestão (skill `/frontend-design`).

---

## 9. Ficheiros impactados (resumo)

| Ficheiro | Mudança |
|---|---|
| `backend/models.py` | `Post`/`PostCreate` estendidos, `PostUpdate` novo, enums |
| `backend/routes/posts.py` | +GET detalhe, +PUT, +DELETE, status no GET, autor/slug no POST |
| `backend/database.py` | índice `(doc->>'slug')` em `ensure_schema` |
| `backend/tests/test_posts.py` | **novo** — cobertura CRUD + RBAC |
| `frontend/src/utils/api.js` | `postsAPI`: getOne/update/remove |
| `frontend/src/lib/queryClient.js` | chaves `posts` |
| `frontend/src/pages/private/AdminNoticiasPage.js` | **novo** — gestão |
| `frontend/src/pages/public/NoticiaDetailPage.js` | **novo** — detalhe |
| `frontend/src/pages/public/NoticiasPage.js` | cards → detalhe, (migração TQ) |
| `frontend/src/pages/public/HomePage.js` | (migração TQ opcional) |
| `frontend/src/App.js` | rotas `/admin/noticias`, `/noticias/:slug` |
| `frontend/src/layouts/PrivateLayout.js` | item de menu + título |
| `scripts/seed_data.py` | (se enums) garantir `type`/`visibility` válidos; opcional `slug`/`status` |
