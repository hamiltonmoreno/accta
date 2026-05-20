# Spec — Padronização e Gestão de Banners das Páginas (Portal ACCTA)

> **Objetivo:** uniformizar os banners (hero) das páginas públicas para que
> tenham **o mesmo tamanho e a mesma estrutura visual**, com **uma única
> exceção** — o banner principal da página inicial (`Home`), que pode ser
> maior. Além disso, permitir que **fotos sejam carregadas pela interface**
> para atualizar a imagem de cada banner, com essa função atribuída aos
> **cargos responsáveis (Admin + Moderador)**.
>
> **Natureza deste documento:** especificação de mudança. Não implementa nada —
> define o quê, onde e como mudar, e o que já foi decidido pela ACCTA.
>
> **Branch:** `claude/standardize-banners-Em3S2`

---

## 1. Diagnóstico — estado atual (o que existe hoje)

### 1.1 Inventário de banners (páginas públicas)

Cada página pública tem uma `<section>` de hero no topo. Hoje **não há padrão
único** — três variantes de dimensão coexistem e duas páginas não têm banner:

| Página | Ficheiro | Classes do hero (atual) | Imagem | Estado |
|---|---|---|---|---|
| **Home** | `HomePage.js:111` | `relative min-h-[600px] sm:min-h-[85vh] lg:min-h-[90vh] flex items-center` | Unsplash inline | 🟢 Banner **principal** (grande) — *exceção permitida* |
| Sobre | `SobrePage.js:24` | `relative py-20 sm:py-28 overflow-hidden` | Unsplash inline + gradiente grafite | 🟡 "Padrão" de-facto |
| Profissão | `ProfissaoPage.js:50` | `relative py-20 sm:py-28 overflow-hidden` | Unsplash inline | 🟡 "Padrão" de-facto |
| Contactos | `ContactosPage.js:68` | `relative py-20 sm:py-28 overflow-hidden` | Unsplash inline | 🟡 "Padrão" de-facto |
| Benefícios | `BeneficiosPublicoPage.js:66` | `relative py-20 sm:py-28 overflow-hidden` | Unsplash inline | 🟡 "Padrão" de-facto |
| Transparência | `TransparenciaPage.js:51` | `relative py-20 sm:py-28 overflow-hidden` | Unsplash inline | 🟡 "Padrão" de-facto |
| **Galeria** | `GaleriaPage.js:199` | `relative h-64 sm:h-80 md:h-96 flex items-center` | Unsplash inline + gradiente | 🔴 **Diferente** — altura fixa própria |
| **Eventos** | `EventosPublicoPage.js:62` | `relative py-12 sm:py-20 lg:py-24 bg-grafite overflow-hidden` | **sem imagem** (grafite sólido + grelha) | 🔴 **Diferente** — padding menor, sem foto |
| **Notícias** | `NoticiasPage.js:31` | `<div className="py-16">` | **nenhuma** | 🔴 **Sem banner** |
| **Validador** | `ValidadorPage.js:39` | `<div className="py-16 min-h-[70vh]">` | **nenhuma** | 🔴 **Sem banner** |

Páginas de autenticação (`Login`, `ForgotPassword`, `ResetPassword`,
`CriarConta`, `SetupAccount`) são formulários e **não têm/precisam** de banner —
**fora do âmbito** desta spec.

**Conclusão:** existem **3 alturas diferentes** (`min-h-[85vh]`,
`py-20 sm:py-28`, `h-64 sm:h-80 md:h-96`, `py-12 sm:py-20 lg:py-24`) + 2 páginas
sem banner. É exatamente a inconsistência que esta spec resolve.

### 1.2 Imagens hardcoded (Unsplash inline)

Todas as imagens de banner são **URLs Unsplash escritas à mão dentro de cada
`.js`**, repetidas em `src` + `srcSet` (via `frontend/src/utils/unsplash.js`,
`unsplashSrcSet()`). Não há fonte central, não há forma de trocar a imagem sem
editar código e fazer deploy. Exemplos:

```jsx
// SobrePage.js:26
src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?q=80&w=1280&auto=format&fit=crop"
// ProfissaoPage.js:52, ContactosPage.js:70, BeneficiosPublicoPage.js:68, ...
```

### 1.3 Sistema de upload — `backend/routes/upload.py`

- Endpoint único: `POST /api/upload/{category}` + `DELETE /api/upload/{category}/{filename}`.
- Categorias existentes: `documents` (10MB), `proofs` (5MB), `logos` (2MB),
  `avatars` (2MB). **Não existe categoria `banners`.**
- Extensões por categoria em `ALLOWED_EXTENSIONS`; limites em `MAX_FILE_SIZES`.
- Validação defense-in-depth: `validate_file_content()` (magic bytes / `Pillow.verify()`).
- RBAC atual: `documents` e `logos` são **admin-only**; restantes qualquer
  utilizador autenticado.
- Ficheiros gravados em `UPLOAD_DIR/{category}/` e servidos em
  `/uploads/{category}/{filename}`. Audit log em cada upload/delete.

### 1.4 Idiom de "settings" — `finance_settings`

O projeto já tem um padrão **single-doc settings** (`backend/routes/finances.py`):

```python
settings = await db.finance_settings.find_one({"id": "finance_settings"}, {"_id": 0})
# default criado on-first-read; PATCH para atualizar; admin-only no write; audit log.
```

A coleção `finance_settings` está registada em `backend/database.py` (lista de
~27 coleções `(pk bigserial, doc jsonb)`). É **o molde** a seguir para os banners.

### 1.5 Padrão de leitura pública (sem auth)

Já existem endpoints `GET /…/public` **sem** `Depends(get_current_user)`,
consumidos pelas páginas públicas:
`/events/public`, `/benefits/public`, `/documents/public`,
`/gallery/public/albums`. Os banners devem seguir o mesmo padrão para serem
lidos por visitantes não autenticados.

### 1.6 RBAC e navegação (sidebar)

- Cargos: `admin`, `financeiro`, `moderador`, `socio`.
- `moderador` é o cargo de **moderação de conteúdo** (mural, galeria) — encaixa
  naturalmente na gestão de banners.
- Sidebar (`frontend/src/layouts/PrivateLayout.js`) filtra itens por
  `roles: [...]`; admin vê tudo; ex.: linha 150 mostra item a
  `moderador`/`admin` quando `roles.includes('moderador')`.
- Rotas privadas usam `<ProtectedRoute allowedRoles={[...]}>`.

---

## 2. Objetivos e não-objetivos

### Objetivos
1. **Tamanho único** para todos os banners secundários (todas as páginas
   públicas exceto a Home).
2. **Exceção Home:** o banner principal mantém o seu tamanho maior.
3. **Upload de foto pela UI** para trocar a imagem de qualquer banner, sem deploy.
4. **RBAC:** Admin + Moderador podem gerir banners; restantes não.
5. **Consistência total:** Notícias e Validador passam a ter banner padrão;
   Galeria e Eventos passam a usar o padrão.
6. Cumprir o design-system ACCTA (`/frontend-design`): neutro-led, texto branco
   sobre overlay grafite, **nunca vermelho sobre fundo escuro**, foco acessível.

### Não-objetivos
- Editar o **texto** (título/subtítulo) dos banners pela UI — fica no código por
  página (ver §12, possível extensão futura).
- Tocar nos formulários de autenticação ou em banners internos do portal privado.
- Galeria de múltiplas imagens / carrossel por banner (1 imagem por banner).

---

## 3. Decisões da ACCTA (já confirmadas)

| # | Decisão | Escolha |
|---|---|---|
| D1 | Cargos que gerem banners | **Admin + Moderador** |
| D2 | Abrangência | **Adicionar banner padrão a todas** as páginas públicas (incl. Notícias e Validador) |
| D3 | Altura do banner secundário | **Médio fixo:** `h-64 sm:h-72 lg:h-80` (~256 / 288 / 320 px) |

---

## 4. Design do banner padrão

### 4.1 Componente partilhado `<PageBanner>` (novo)

`frontend/src/components/PageBanner.js` — fonte única de verdade da estrutura e
do tamanho. Substitui as `<section>` hero copiadas em cada página.

**Props:**

| Prop | Tipo | Descrição |
|---|---|---|
| `pageKey` | `string` | Chave do banner (`"sobre"`, `"eventos"`, …) — usada para ler a imagem da config. |
| `badge` | `string?` | Texto da pílula superior (ex.: "A Associação"). |
| `title` | `string` | `<h1>` do banner. |
| `subtitle` | `string?` | Parágrafo de apoio. |
| `icon` | `LucideIcon?` | Ícone opcional na badge. |

**Estrutura (Tailwind, alinhada ao design-system):**

```jsx
<section className="relative h-64 sm:h-72 lg:h-80 flex items-center overflow-hidden">
  <img src={imageUrl} srcSet={…} sizes="100vw" alt={alt || ''} aria-hidden={!alt}
       loading="lazy" decoding="async"
       className="absolute inset-0 w-full h-full object-cover" />
  {/* overlay grafite — garante contraste do texto branco (nunca vermelho aqui) */}
  <div className="absolute inset-0 bg-gradient-to-r from-grafite via-grafite/85 to-grafite/50" />
  <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-6 w-full">
    {badge && <span className="… bg-carmesim/20 border border-carmesim/40 text-white …">{badge}</span>}
    <h1 className="font-bold text-3xl sm:text-4xl lg:text-5xl text-white …">{title}</h1>
    {subtitle && <p className="text-base sm:text-lg text-white/80 …">{subtitle}</p>}
  </div>
</section>
```

- **Altura:** `h-64 sm:h-72 lg:h-80` (D3) — igual em **todas** as páginas
  secundárias.
- **Imagem:** lida da config (§5/§6); fallback embebido se faltar (§9).
- **Contraste:** texto sempre branco sobre overlay grafite (par permitido);
  acento carmesim só na pílula/border, **nunca texto vermelho sobre escuro**.

### 4.2 Home — exceção

`HomePage.js` mantém o hero próprio
(`min-h-[600px] sm:min-h-[85vh] lg:min-h-[90vh]`), mas a **imagem passa a ser
editável** pela mesma config (chave `home`). Não usa `<PageBanner>` (tamanho
diferente por decisão), apenas consome `imageUrl` da config com o mesmo fallback.

---

## 5. Backend — mudanças

### 5.1 Nova categoria de upload `banners` — `backend/routes/upload.py`

```python
ALLOWED_EXTENSIONS["banners"] = [".jpg", ".jpeg", ".png", ".webp"]
MAX_FILE_SIZES["banners"] = 4 * 1024 * 1024  # 4 MB (hero wide)
```

- Adicionar `"banners"` à whitelist de categorias válidas no `POST` e `DELETE`.
- **RBAC:** `if category == "banners" and current_user.role not in ("admin", "moderador"): 403`.
- ⚠️ **Dependência:** confirmar que `file_validation.validate_file_content()`
  aceita **WebP** (magic bytes `RIFF…WEBP` + `Pillow`). Se não aceitar, ou (a)
  adicionar suporte WebP à validação, ou (b) reduzir extensões a
  `.jpg/.jpeg/.png` (decisão de implementação — ver §12 Q3).

### 5.2 Nova coleção `page_banners` (single-doc por chave)

- Registar `"page_banners"` na lista de coleções em `backend/database.py`.
- 1 documento por banner: `{"key": "sobre", "image_url": …, "alt": …, …}`.
- Sem índice dedicado necessário (≤ 10 docs).

### 5.3 Modelos Pydantic — `backend/models.py`

Seguindo o molde `FinanceSettings`:

```python
class PageBanner(BaseModel):
    model_config = ConfigDict(extra="ignore")
    key: str                       # "home" | "sobre" | … (ver §7)
    image_url: str                 # /uploads/banners/<uuid>.jpg  (ou URL fallback)
    alt: Optional[str] = None      # texto alternativo (acessibilidade/SEO)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None

class PageBannerUpdate(BaseModel):
    image_url: Optional[str] = None
    alt: Optional[str] = None
```

> Datas serializadas como ISO-8601 string (regra `.claude/rules/models.md`),
> nunca `datetime` cru no documento.

### 5.4 Novo router — `backend/routes/banners.py`

| Endpoint | Auth | Descrição |
|---|---|---|
| `GET /api/banners/public` | **público** | Devolve `{ key: {image_url, alt} }` para **todas** as chaves, fundindo defaults (§9) com os docs gravados. Consumido pelas páginas públicas. |
| `GET /api/banners` | admin + moderador | Igual, mas com metadados (`updated_at`, `updated_by`) para a UI de gestão. |
| `PUT /api/banners/{key}` | admin + moderador | Upsert da imagem/alt de uma chave. Valida `key ∈ BANNER_KEYS` (400 caso contrário). `create_audit_log(...)`. |

Fluxo de troca de imagem (frontend): `POST /api/upload/banners` → recebe
`file_url` → `PUT /api/banners/{key}` com `{ image_url: file_url }`.

- Registar o router em `backend/routes/__init__.py` (`include_router`).
- Opcional: ao gravar, `delete_upload_file()` da imagem antiga (se for um
  `/uploads/banners/...` e não um default externo) para não acumular ficheiros —
  mesmo padrão de `benefits.py:73`.
- `BANNER_KEYS` (constante única, partilhada conceptualmente com o frontend §7).

---

## 6. Frontend — mudanças

### 6.1 Componente `<PageBanner>` (§4.1) — novo
`frontend/src/components/PageBanner.js`.

### 6.2 API client — `frontend/src/utils/api.js`
```js
export const bannersAPI = {
  getPublic: () => api.get('/banners/public'),
  getAll:    () => api.get('/banners'),
  update:    (key, data) => api.put(`/banners/${key}`, data),
};
```

### 6.3 Refactor das páginas públicas
Substituir cada `<section>` hero hardcoded por `<PageBanner pageKey=… title=… …/>`:

- `SobrePage`, `ProfissaoPage`, `ContactosPage`, `BeneficiosPublicoPage`,
  `TransparenciaPage` → trocar hero atual pelo componente (mantêm badge/título).
- `GaleriaPage`, `EventosPublicoPage` → substituir o hero divergente pelo padrão.
- `NoticiasPage`, `ValidadorPage` → **adicionar** `<PageBanner>` no topo (D2).
- `HomePage` → manter hero próprio, mas ler `imageUrl` da chave `home` (§4.2).

### 6.4 Leitura da config (TanStack Query)
- Hook/queryKey dedicado (ex.: `queryKeys.banners.public()`), `staleTime` alto
  (conteúdo quase-estático). `<PageBanner>` lê a config e resolve `imageUrl` por
  `pageKey`; se a query falhar ou faltar a chave, usa o **fallback embebido** (§9).
- Cumprir regras de frontend: TanStack Query (não `useState+useEffect+axios`).

### 6.5 UI de gestão — `AdminBannersPage` (nova)
- Rota `/admin/banners` com `<ProtectedRoute allowedRoles={['admin','moderador']}>`.
- Grelha de cards (1 por banner): **preview** da imagem + nome da página +
  botão **"Substituir imagem"** (file picker → `uploadAPI` → `bannersAPI.update`)
  + campo de **texto alternativo (alt)**. Indicar a Home como "banner principal".
- `useMutation` com `toast` (Sonner) e
  `qc.invalidateQueries({ queryKey: queryKeys.banners… })` no sucesso.
- Estilo: design-system ACCTA (1 botão primário carmesim por card no máximo;
  restantes neutros).

### 6.6 Navegação (sidebar) — `PrivateLayout.js`
- Novo item: `{ label: 'Banners', path: '/admin/banners', icon: Image, roles: ['admin','moderador'] }`.
- Adicionar título correspondente no mapa de `getPageTitle()`.
- Registar a rota em `App.js` (ou onde as rotas privadas são declaradas).

---

## 7. Modelo de dados — chaves de banner

`BANNER_KEYS` (10), 1 doc por chave em `page_banners`:

| Chave | Página | Tamanho |
|---|---|---|
| `home` | HomePage | **grande** (exceção) |
| `sobre` | SobrePage | padrão |
| `profissao` | ProfissaoPage | padrão |
| `contactos` | ContactosPage | padrão |
| `beneficios` | BeneficiosPublicoPage | padrão |
| `transparencia` | TransparenciaPage | padrão |
| `galeria` | GaleriaPage | padrão |
| `eventos` | EventosPublicoPage | padrão |
| `noticias` | NoticiasPage | padrão (novo) |
| `validador` | ValidadorPage | padrão (novo) |

Documento exemplo:
```json
{ "key": "sobre", "image_url": "/uploads/banners/ab12…​.jpg",
  "alt": "Equipa ACCTA em reunião", "updated_at": "2026-05-20T…Z",
  "updated_by": "<user-id>" }
```

---

## 8. Matriz RBAC

| Ação | admin | moderador | financeiro | socio | público |
|---|:--:|:--:|:--:|:--:|:--:|
| Ver banners (páginas públicas) | ✓ | ✓ | ✓ | ✓ | ✓ |
| `GET /api/banners/public` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `GET /api/banners` (gestão) | ✓ | ✓ | ✗ | ✗ | ✗ |
| `POST /api/upload/banners` | ✓ | ✓ | ✗ | ✗ | ✗ |
| `PUT /api/banners/{key}` | ✓ | ✓ | ✗ | ✗ | ✗ |
| Ver item "Banners" na sidebar | ✓ | ✓ | ✗ | ✗ | — |

Toda escrita gera **audit log** (`create_audit_log`).

---

## 9. Migração / rollout (não-destrutivo)

- **Defaults embebidos:** o backend mantém um dict
  `BANNER_DEFAULTS = { "home": "<unsplash atual>", "sobre": "…", … }` com as URLs
  Unsplash que hoje estão hardcoded. `GET /api/banners/public` funde os docs
  gravados **por cima** dos defaults → antes de qualquer upload, o site fica
  **visualmente idêntico** ao atual.
- O mesmo dict (ou equivalente) embebido no frontend serve de fallback se a
  query falhar (resiliência — banner nunca fica vazio).
- **Sem migração de dados destrutiva**, sem alteração de schema que quebre docs
  existentes → não dispara nenhuma Stop Condition do `CLAUDE.md`.
- Coleção `page_banners` começa vazia e popula-se on-demand (à medida que se
  fazem uploads), tal como `finance_settings`.

---

## 10. Plano de implementação (fases)

**Fase 1 — Backend**
- [ ] `upload.py`: categoria `banners` (ext, tamanho, RBAC admin+moderador).
- [ ] Confirmar/ajustar `validate_file_content` p/ WebP (ou cair p/ jpg/png — Q3).
- [ ] `models.py`: `PageBanner` + `PageBannerUpdate`.
- [ ] `database.py`: registar coleção `page_banners`.
- [ ] `routes/banners.py`: `BANNER_KEYS`, `BANNER_DEFAULTS`, 3 endpoints, audit log.
- [ ] `routes/__init__.py`: incluir router.

**Fase 2 — Componente + páginas**
- [ ] `components/PageBanner.js` (altura D3, overlay grafite, props).
- [ ] `utils/api.js`: `bannersAPI` + queryKey.
- [ ] Refactor das 9 páginas secundárias para `<PageBanner>`.
- [ ] HomePage: ler `imageUrl` da chave `home`.

**Fase 3 — Gestão (UI)**
- [ ] `pages/private/AdminBannersPage.js` (grelha + upload + alt).
- [ ] Rota `/admin/banners` (`allowedRoles={['admin','moderador']}`).
- [ ] Sidebar + `getPageTitle`.

**Fase 4 — Verificação** (ver §11).

---

## 11. Testes

**Backend (`backend/tests/`, pytest, in-process):**
- `PUT /api/banners/{key}` aceita admin e moderador; **nega** financeiro/socio (403).
- `POST /api/upload/banners` nega financeiro/socio (403); aceita admin/moderador.
- Chave inválida em `PUT` → 400.
- `GET /api/banners/public` funde defaults + docs e devolve **todas** as chaves
  sem auth.
- ⚠️ Lembrar de wire `mock_db.page_banners` no `conftest.py` (coleções novas
  não estão pré-ligadas — ver `CLAUDE.md`).

**Frontend (manual, em browser — golden path + edge):**
- Todas as páginas secundárias mostram banner com **a mesma altura**; Home
  continua maior.
- Upload em `/admin/banners` troca a imagem ao vivo (após invalidate).
- Notícias e Validador agora têm banner.
- Visitante **não autenticado** vê os banners (endpoint público).
- Fallback: simular falha da query → banner usa default (não fica vazio).
- Contraste/acessibilidade: texto branco legível; `alt` aplicado.

---

## 12. Riscos e questões em aberto

- **Q1 — Editar texto pela UI?** MVP edita só a **imagem** (+`alt`); título/
  subtítulo ficam no código. Tornar título/subtítulo editáveis é extensão
  futura (acrescentar campos a `PageBanner` + inputs na UI).
- **Q2 — Limpeza de ficheiros antigos:** apagar a imagem anterior no `PUT`
  (recomendado, padrão `benefits.py`) vs. manter histórico. Default proposto:
  apagar se for `/uploads/banners/...`.
- **Q3 — WebP:** depende de `validate_file_content`. Se não suportar e não
  quisermos alargar a validação agora, restringir a `.jpg/.jpeg/.png` (sem
  bloquear o objetivo).
- **Q4 — Recorte/aspect ratio:** imagens muito altas/estreitas ficam cortadas
  pelo `object-cover`. Mitigação: indicar na UI o rácio recomendado (~16:5 wide)
  e tamanho mínimo (ex.: 1600×500). Sem editor de recorte no MVP.
- **Q5 — Cache:** `staleTime` alto na query pública; após upload, `invalidate`
  garante atualização imediata na sessão de gestão. Visitantes podem ver a
  imagem antiga até expirar o cache do browser (aceitável para conteúdo
  institucional).
