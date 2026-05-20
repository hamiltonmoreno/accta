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
| `PATCH /api/posts/{id}` | ❌ **falta** | **Não há forma de editar um post.** O projeto usa `PATCH` para updates parciais (`events`, `benefits`, `projects`), por isso este módulo deve seguir o mesmo padrão. |
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
  Em vez de ligar `mock_db.posts` em cada teste, adicionar `"posts"` ao fixture
  global em `backend/tests/conftest.py` para ficar coerente com `database.COLLECTIONS`
  e reduzir boilerplate nos testes novos.

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
| D3 | **Imagem de capa?** | Sim — `cover_url`, via upload (`POST /api/upload/{category}`). | Blog sem capa fica pobre; reutiliza infra. Categoria → ver D6 + §4.5. |
| D4 | **Detalhe por `slug` ou `id`?** | `slug` (SEO) gerado do título, com `id` como fallback na rota. Depois de publicado, o slug deve ficar estável. | URLs legíveis (`/noticias/nova-rota-praia-sal`) sem quebrar links partilhados quando o título é editado. |
| D5 | **Notificar sócios ao publicar?** | Opcional, default **não**; se `visibility=socios`, oferecer toggle "notificar sócios" que chama `notify_all_active_users('system', …)`. | Evitar spam; dar controlo ao editor. ⚠️ não é email, é notificação in-app. |
| D6 | **Categoria de upload da capa** | **Criar categoria `covers`** (imagens, 2MB) permitida a `admin`+`moderador`. | ⚠️ `logos`/`documents` são **admin-only** (`upload.py:33`) → reutilizá-las daria **403** ao `moderador` (D1). Nova categoria evita relaxar a RBAC de `logos`. Detalhe em §4.5. |
| D7 | **Migrar `NoticiasPage`/`HomePage` para TanStack Query?** | Sim (alinhar com as regras de frontend). | Coerência; cache; menos `console.error`. |
| D8 | **Validar `type`/`visibility` com enum?** | Sim — `Literal[...]` no modelo. | Evita lixo nos dados; o frontend já assume valores fixos. |
| D9 | **Ordenação pública** | Ordenar notícias públicas por `published_at desc`, com fallback para `created_at`. | Um rascunho criado há semanas mas publicado hoje deve aparecer como notícia recente. |
| D10 | **Formato do conteúdo** | MVP em texto simples, com quebras preservadas (`whitespace-pre-wrap` no frontend). | Evita XSS e dependências novas; Markdown/HTML pode ser fase futura com sanitização explícita. |
| D11 | **Paginação/filtros backend** | Adicionar `type`, `status`, `q`, `skip`, `limit` (cap 100) ao `GET /posts`. | A Home pode pedir `limit=3`; a gestão não precisa buscar 1000 posts para filtrar no browser. |

> **Âmbito faseado:** §7 coloca no **MVP** o ciclo completo de gestão: CRUD,
> detalhe, rascunho/publicado, capa, slug estável, paginação/filtros básicos e
> migração TanStack Query das páginas afetadas. As **melhorias** ficam para
> notificação a sócios, backfill opcional e paginação visual mais refinada.

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
           PATCH  /api/posts/{id}            ← NOVO (editar)  [admin/moderador]
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
    title: str = Field(min_length=3, max_length=180)
    slug: Optional[str] = None                 # D4 — gerado no create; estável após publicar
    content: str = Field(min_length=1, max_length=20000)
    excerpt: Optional[str] = Field(default=None, max_length=320)
    cover_url: Optional[str] = None            # D3 — /uploads/covers/... ou None
    type: Literal["noticia", "institucional", "educativo"] = "noticia"   # D8
    visibility: Literal["publico", "socios", "privado"] = "publico"      # D8
    status: Literal["rascunho", "publicado"] = "publicado"               # D2
    tags: List[str] = Field(default_factory=list, max_length=10)
    author_id: Optional[str] = None
    author_name: Optional[str] = None          # desnormalizado p/ render simples
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[str] = None           # ISO string (regra: datas como str)
    published_at: Optional[str] = None

class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    content: str = Field(min_length=1, max_length=20000)
    excerpt: Optional[str] = Field(default=None, max_length=320)
    cover_url: Optional[str] = None
    type: Literal[...] = "noticia"
    visibility: Literal[...] = "publico"
    status: Literal[...] = "publicado"
    tags: List[str] = Field(default_factory=list, max_length=10)

class PostUpdate(BaseModel):                    # todos opcionais (PATCH-like)
    title: Optional[str] = Field(default=None, min_length=3, max_length=180)
    content: Optional[str] = Field(default=None, min_length=1, max_length=20000)
    excerpt: Optional[str] = Field(default=None, max_length=320)
    cover_url: Optional[str] = None
    type: Optional[Literal[...]] = None
    visibility: Optional[Literal[...]] = None
    status: Optional[Literal[...]] = None
    tags: Optional[List[str]] = Field(default=None, max_length=10)
    regenerate_slug: bool = False              # só respeitar para rascunhos
```

> ⚠️ **Compat. com dados existentes (CLAUDE.md stop condition):** posts já
> existentes (seed) **não têm** `slug`/`status`. Como `Post` usa
> `extra="ignore"` e os novos campos têm default, a leitura não parte. Mas:
> `slug` não tem default seguro → tornar **`Optional[str] = None`** OU fazer
> backfill no `ensure_schema`/script. **Recomendação:** `slug: Optional[str]`
> + no `GET /posts/{id_or_slug}` aceitar `id` quando `slug` é nulo; gerar slug
> no create. Em update, **não** regenerar o slug automaticamente se o post já
> está `publicado`; só permitir `regenerate_slug=True` enquanto `rascunho`. Para
> `status`, default `publicado` mantém os posts seed visíveis (não esconder
> conteúdo já público). Para `published_at`, usar fallback para `created_at`
> nos documentos antigos.

### 4.2 Rotas (`backend/routes/posts.py`)

1. **`GET /api/posts`** — adicionar filtros e paginação:
   - Anónimos/sócios: forçar `status = "publicado"` (nunca ver rascunhos).
   - Staff: pode pedir `?status=rascunho` para o ecrã de gestão; por omissão, vê tudo.
   - Aceitar `type`, `q`, `skip`, `limit` (cap 100). `q` deve pesquisar título
     de forma segura via regex escapada ou filtro equivalente do DAO.
   - Ordenar público por `published_at desc` com fallback para `created_at`; para
     staff, manter ordenação consistente por `updated_at/published_at/created_at`
     conforme o filtro de gestão.
2. **`GET /api/posts/{id_or_slug}`** *(novo)* — resolve por `slug` e cai para `id`.
   - Aplicar a **mesma regra de visibilidade** do `GET /posts` (anónimo só
     `publico`+`publicado`; sócio +`socios`; staff tudo). 404 se não autorizado/inexistente.
3. **`PATCH /api/posts/{id}`** *(novo)* — `admin`/`moderador`. Aplica `PostUpdate`
   (só campos enviados, via `model_dump(exclude_unset=True)`). Define
   `updated_at`, define `published_at` na 1ª transição para `publicado`, e só
   regenera `slug` se o post ainda estiver `rascunho` e `regenerate_slug=True`.
   `regenerate_slug` é flag de comando: usar para decidir, mas remover de
   `update_data` antes do `$set` para não persistir no documento.
   Se `cover_url` mudar, apagar a capa antiga com `delete_upload_file`.
   **`create_audit_log(user_id, "Editou post {id}", id)`**.
4. **`DELETE /api/posts/{id}`** *(novo)* — `admin`/`moderador`. 404 se não existe.
   Apagar a capa (`cover_url`) com `delete_upload_file` quando for `/uploads/covers/...`.
   **`create_audit_log(user_id, "Eliminou post {id}", id)`**.
5. **`POST /api/posts`** — preencher `author_id`/`author_name` a partir do
   `current_user`, gerar `slug`, definir `published_at` se nasce `publicado`.
   Opcional D5: se `visibility=socios` e flag → `notify_all_active_users(...)`.
6. **Formato do conteúdo:** armazenar `content` como texto simples. Não aceitar
   HTML renderizável no MVP; o frontend deve renderizar como texto com quebras
   preservadas.

> **Regras do projeto a respeitar (`.claude/rules/api.md`):** RBAC explícito
> (`if current_user.role not in ["admin","moderador"]: raise HTTPException(403)`),
> **audit log em toda a escrita de staff**, datas como ISO string, sem SQL cru
> (usar o DAO Mongo-like), `HTTPException` 401/403/404 corretos.

### 4.3 Slug — utilitário

Função simples (sem dependência nova): minúsculas, remover acentos
(`unicodedata.normalize('NFKD', …)`), `[^a-z0-9]+ → "-"`, trim de `-`. Garantir
unicidade: se colidir, sufixar `-2`, `-3`… (verificar com `db.posts.find_one({"slug": s})`).

**Regra de estabilidade:** o slug é gerado na criação. Enquanto o post estiver
`rascunho`, pode ser regenerado explicitamente (`regenerate_slug=True`) para
acompanhar uma mudança grande de título. Depois de `publicado`, manter o slug
existente para não quebrar links já partilhados; alterações de título mudam só o
texto visível.

### 4.4 Índice (`database.py` — `ensure_schema`)

Adicionar índices de expressão em:

- `(doc->>'slug')` para lookup de detalhe.
- `(doc->>'status'), (doc->>'visibility'), (doc->>'published_at') DESC` para listas públicas/gestão.

Coerente com os índices `(doc->>'field')` já existentes. **Não** criar índices a
partir das rotas (regra de DB). Se for feito backfill, definir `published_at =
created_at` nos posts antigos para a ordenação pública ser determinística.

### 4.5 Upload da capa — nova categoria `covers` (resolve D3/D6)

⚠️ **Restrição atual (verificada):** `POST /api/upload/{category}` em
`backend/routes/upload.py:33` faz `if category in ["documents", "logos"] and
current_user.role != "admin": 403`. Ou seja, `logos`/`documents` são
**admin-only**. Como o blog é gerido por **`admin` + `moderador`** (D1),
**reutilizar `logos` para a capa faria o `moderador` levar 403** — a workflow
documentada ficaria impossível para uma das funções previstas.

**Decisão (D6):** adicionar uma categoria dedicada **`covers`**, permitida a
`admin` + `moderador`. Mudanças mínimas em `backend/routes/upload.py`:

```python
# whitelist de categorias (linha ~30): incluir "covers"
if category not in ["documents", "proofs", "logos", "avatars", "covers"]:
    raise HTTPException(400, "Categoria inválida")

# RBAC (linha ~33): manter logos/documents admin-only e gatear covers p/ staff
if category in ["documents", "logos"] and current_user.role != "admin":
    raise HTTPException(403, "Sem permissão")
if category == "covers" and current_user.role not in ["admin", "moderador"]:
    raise HTTPException(403, "Sem permissão")

ALLOWED_EXTENSIONS["covers"] = [".png", ".jpg", ".jpeg"]   # SVG bloqueado (XSS)
MAX_FILE_SIZES["covers"]     = 2 * 1024 * 1024              # 2 MB
```

`file_validation.py` já valida magic-bytes/Pillow para imagens — `covers` herda
o mesmo trato que `logos`/`avatars`, sem código novo de validação.

**Remoção/limpeza:** o endpoint genérico `DELETE /api/upload/{category}/{filename}`
é hoje `admin-only`. Para capas, há duas opções seguras:

- Manter o delete genérico `admin-only` e fazer a limpeza automática nas rotas de
  posts com `helpers.delete_upload_file(old_cover_url)` quando a capa é trocada
  ou o post eliminado.
- Ou permitir `DELETE /api/upload/covers/{filename}` para `admin` + `moderador`,
  preservando `documents`/`logos` como `admin-only`.

**Recomendação:** primeira opção no MVP. Evita expor mais uma operação manual e
garante que ficheiros antigos não ficam órfãos quando o editor troca a capa.

> Alternativa (não recomendada): relaxar a linha 33 para permitir `moderador`
> em `logos`. Rejeitada — `logos` é branding institucional; manter admin-only.

---

## 5. Mudanças no Frontend

### 5.1 API client (`utils/api.js`)

```js
export const postsAPI = {
  // Compat: chamadas antigas ainda fazem getAll('publico').
  getAll: (params) => api.get('/posts', {
    params: typeof params === 'string' ? { visibility: params } : params,
  }),
  getOne: (idOrSlug) => api.get(`/posts/${idOrSlug}`),
  create: (data) => api.post('/posts', data),
  update: (id, data) => api.patch(`/posts/${id}`, data),
  remove: (id) => api.delete(`/posts/${id}`),
};
```

### 5.2 `lib/queryClient.js` — chaves

Adicionar ao registo `queryKeys`:
```js
posts: {
  all: () => ['posts'],                        // prefixo p/ invalidação abrangente
  list: (params) => ['posts', params ?? {}],   // ['posts', { visibility, type, status, q, limit }]
  detail: (idOrSlug) => ['posts', 'detail', idOrSlug],
},
```

Adicionar teste em `frontend/src/lib/__tests__/queryClient.test.js` para fixar o
shape das novas chaves.

### 5.3 Página de gestão (NOVA) — `pages/private/AdminNoticiasPage.js`

**Modelar em `DocumentosPage.js`** (já usa o padrão correto: `useQuery` +
`useMutation` + `Dialog` + `queryKeys` + `toast` + gate por role).

- Tabela/lista de posts (título, tipo, visibilidade, status, data, autor).
- Filtros: tipo, status (rascunho/publicado), pesquisa por título.
- Botão **"Novo post"** → `Dialog` com formulário:
  título, tipo (select), visibilidade (select), status (select),
  excerpt, conteúdo (textarea), tags (input → array), **upload de capa**
  via `uploadAPI.uploadFile('covers', file)` (nome real do API client, padrão do
  `DocumentosPage`). **Usar a
  categoria `covers`** (§4.5) — **nunca** `logos`/`documents`, que são admin-only
  e dariam 403 ao `moderador`.
- Por linha: **Editar** (mesmo `Dialog` pré-preenchido) e **Eliminar**
  (confirmação, ex.: `AlertDialog`).
- Mutations (criar/editar/eliminar): no `onSuccess`, invalidar pelo **prefixo**
  `qc.invalidateQueries({ queryKey: queryKeys.posts.all() })` — `['posts']` faz
  *prefix match* e refresca **todas** as variantes filtradas da lista
  (`['posts', { status:'rascunho' }]`, `['posts', { type:'noticia' }]`, …) e o
  detalhe. ⚠️ **Não** usar `queryKeys.posts.list()` sozinho: resolve só para
  `['posts', {}]` e deixaria as tabelas filtradas **stale** até refresh manual.
  Em edição/eliminação, invalidar também `queryKeys.posts.detail(idOrSlug)`.
  Feedback: `toast.success`; erros via `toast.error(error.response?.data?.detail)`.
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
- Renderizar `content` como texto simples com `whitespace-pre-wrap`. Não usar
  `dangerouslySetInnerHTML` no MVP.
- Respeitar o design **neutral-led** (skill `/frontend-design`): superfícies
  brancas/`#F5F5F5`, texto Grafite, Carmesim só como acento (≤1 botão primário,
  links). **Nunca** texto Carmesim sobre fundo escuro/colorido.

### 5.6 `NoticiasPage.js` (lista) — ligar ao detalhe + migrar

- Envolver cada card num link para `/noticias/${post.slug ?? post.id}`.
- Mostrar `excerpt` (fallback: `content` truncado) e capa, se existirem.
- (D7) Migrar de `useState+useEffect+axios` → `useQuery(queryKeys.posts.list({ visibility:'publico', status:'publicado' }))`.
- `HomePage.js`: idem para a secção das 3 notícias, pedindo `limit: 3` em vez
  de buscar tudo e cortar no frontend. O link "Ler mais" deve ir para
  `/noticias/${post.slug ?? post.id}`, não apenas `/noticias`.

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
- [ ] `models.py`: estender `Post`/`PostCreate`, adicionar `PostUpdate` + enums (`Literal`), limites de tamanho e `Field(default_factory=list)`. `slug` Optional p/ compat (§4.1).
- [ ] `posts.py`: `GET /posts/{id_or_slug}` (detalhe, visibility-aware).
- [ ] `posts.py`: `PATCH /posts/{id}` (editar, RBAC admin/moderador, audit log, slug estável, `updated_at`/`published_at`, cleanup de capa antiga).
- [ ] `posts.py`: `DELETE /posts/{id}` (eliminar, RBAC, audit log, cleanup de capa).
- [ ] `posts.py`: `GET /posts` respeita `status`, `type`, `q`, `skip`, `limit` e ordena público por `published_at`.
- [ ] `posts.py`: `POST /posts` preenche autor/slug/published_at.
- [ ] util `slugify` + unicidade; índices `(doc->>'slug')` e status/visibility/published_at em `ensure_schema`.
- [ ] `routes/upload.py`: nova categoria `covers` (RBAC `admin`+`moderador`, §4.5).
- [ ] `conftest.py`: adicionar `"posts"` ao `mock_db` global.

### Fase 2 — Frontend gestão + detalhe (MVP utilizável)
- [ ] `api.js`: `getOne`/`update`/`remove` + `getAll(params)` compatível com `getAll('publico')`.
- [ ] `queryClient.js`: chaves `posts.all()`/`posts.list`/`posts.detail` + teste de shape.
- [ ] `AdminNoticiasPage.js` (gestão: tabela, criar/editar/eliminar, upload de capa via `uploadAPI.uploadFile('covers', ...)`) — modelo `DocumentosPage`.
- [ ] `App.js`: rota `/admin/noticias` (`allowedRoles=['admin','moderador']`).
- [ ] `PrivateLayout.js`: item de menu "Notícias" + título.
- [ ] `NoticiaDetailPage.js` + rota pública `/noticias/:slug`.
- [ ] `NoticiasPage.js`: cards ligam ao detalhe, renderizam excerpt/capa e usam TanStack Query.
- [ ] `HomePage.js`: últimas 3 notícias via `GET /posts?visibility=publico&status=publicado&limit=3`, cards ligam ao detalhe.

### Fase 3 — Melhorias (D5 + polimento)
- [ ] Toggle "notificar sócios" ao publicar com `visibility=socios` (D5).
- [ ] Backfill opcional em `scripts/seed_data.py`/script auxiliar para `slug`, `status` e `published_at=created_at` nos posts existentes.
- [ ] Paginação visual na gestão e na lista pública se o volume real de posts justificar.

### Fase 4 — Testes & verificação
- [ ] `backend/tests/test_posts.py`.
  Casos: list visibility/status por role; detalhe por slug e id; create/edit/delete
  RBAC (403 p/ socio/financeiro/anónimo); audit log chamado; 404s; slug estável
  após publicação; `published_at` na transição; cleanup de capa.
- [ ] `backend/tests/test_file_validation.py`/teste de upload: `covers` aceita
  JPEG/PNG válidos, bloqueia SVG/executáveis e respeita RBAC `admin`+`moderador`.
- [ ] `ruff check .` + `ruff format .` (backend); `pytest` verde.
- [ ] `npx eslint src/ --ext .js,.jsx --max-warnings=60` (frontend).
- [ ] **Verificação manual no browser** (golden path + edge): criar → editar →
  publicar → ver em `/noticias` → abrir detalhe → eliminar; rascunho não aparece
  ao público; `socios` não aparece a anónimo.

---

## 8. Riscos / Stop conditions (CLAUDE.md)

- **Dados existentes (seed)** sem `slug`/`status`: não esconder nem partir
  leitura. Mitigação em §4.1 (defaults seguros + `slug` opcional/backfill). Para
  ordenação pública, tratar `published_at` ausente como `created_at`.
- **Slug publicado deve ser estável**: regenerar automaticamente em toda edição
  quebraria links externos. Só regenerar em rascunho e de forma explícita.
- **Conteúdo em texto simples no MVP**: não usar `dangerouslySetInnerHTML`. Se a
  ACCTA quiser Markdown/HTML no futuro, adicionar sanitização e testes antes.
- **Notificar sócios (D5)** usa `notify_all_active_users` (in-app, **não** email)
  → não é a stop condition de email, mas usar com parcimónia (toggle, default off).
- **Mudança de modelo Pydantic**: `Literal` em `type`/`visibility` pode **rejeitar**
  valores legados se o seed tiver algo fora da lista — auditar `seed_data.py`
  (linhas ~228–267) antes de aplicar enums; ajustar a lista ou os dados.
- **Capas órfãs no disco**: ao trocar `cover_url` ou eliminar post, chamar
  `delete_upload_file`. Não depender de delete manual no endpoint `/upload`.
- **Sem migração destrutiva** de DB — só adição de campos jsonb + índices
  idempotente. Nada de DROP.
- Manter **um só botão primário Carmesim por vista** e regras de contraste no
  detalhe/gestão (skill `/frontend-design`).

---

## 9. Ficheiros impactados (resumo)

| Ficheiro | Mudança |
|---|---|
| `backend/models.py` | `Post`/`PostCreate` estendidos, `PostUpdate` novo, enums |
| `backend/routes/posts.py` | +GET detalhe, +PATCH, +DELETE, status/filtros/paginação no GET, autor/slug no POST |
| `backend/database.py` | índices `(doc->>'slug')` e status/visibility/published_at em `ensure_schema` |
| `backend/routes/upload.py` | nova categoria `covers` (ext/limite/RBAC admin+moderador) — §4.5 |
| `backend/tests/conftest.py` | adicionar `posts` ao `mock_db` global |
| `backend/tests/test_posts.py` | **novo** — cobertura CRUD + RBAC |
| `frontend/src/utils/api.js` | `postsAPI`: getOne/update/remove |
| `frontend/src/lib/queryClient.js` | chaves `posts` |
| `frontend/src/lib/__tests__/queryClient.test.js` | teste das novas query keys |
| `frontend/src/pages/private/AdminNoticiasPage.js` | **novo** — gestão |
| `frontend/src/pages/public/NoticiaDetailPage.js` | **novo** — detalhe |
| `frontend/src/pages/public/NoticiasPage.js` | cards → detalhe, (migração TQ) |
| `frontend/src/pages/public/HomePage.js` | (migração TQ opcional) |
| `frontend/src/App.js` | rotas `/admin/noticias`, `/noticias/:slug` |
| `frontend/src/layouts/PrivateLayout.js` | item de menu + título |
| `scripts/seed_data.py` | (se enums) garantir `type`/`visibility` válidos; opcional `slug`/`status` |
