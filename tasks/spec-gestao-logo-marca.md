# Spec — Gestão do Logo / Marca pela UI (Portal ACCTA)

> **Objetivo:** permitir **carregar o logo da ACCTA pela interface** (upload de
> imagem) e substituí-lo em todo o portal sem editar código nem fazer deploy,
> com essa função atribuída aos **cargos responsáveis (Admin + Moderador)** —
> a mesma abordagem usada para os banners (ver `tasks/spec-padronizacao-banners.md`).
>
> **Natureza deste documento:** especificação de mudança. Não implementa nada —
> define o quê, onde e como mudar, e o que já foi decidido pela ACCTA.
>
> **Branch:** `claude/standardize-banners-Em3S2`

---

## 1. Diagnóstico — estado atual (o que existe hoje)

### 1.1 O logo é um SVG **desenhado em código** (não é imagem)

`frontend/src/components/ACCTALogo.js` (140 linhas) exporta o logo como **SVG
inline**, com cores hardcoded (Carmesim `#C7202F`, Grafite `#3A3A3A`) e três
formas:

| Export / variante | Forma | Onde aparece |
|---|---|---|
| `ACCTALogo variant="full"` | Ícone "A"+trajetória + texto "ACCTA / CABO VERDE" | (definido, uso pontual) |
| `ACCTALogo variant="icon"` | Só o ícone "A" | (definido) |
| `ACCTALogoHorizontal` | Ícone + texto, com prop **`dark`** (texto branco p/ fundo escuro) | **header, rodapé, login** |

> ⚠️ **Consequência-chave:** como é vetor em código, **não há `<img>` para
> trocar**. "Carregar uma foto para atualizar o logo" exige introduzir um
> caminho baseado em imagem, mantendo o SVG atual como **fallback/default**.

### 1.2 Onde o logo aparece (e em que fundo)

| Local | Ficheiro | Variante | Fundo |
|---|---|---|---|
| Header público | `PublicLayout.js:29` | `<ACCTALogoHorizontal />` | **claro** (branco) |
| Rodapé público | `PublicLayout.js:131` | `<ACCTALogoHorizontal dark />` | **escuro** (grafite) |
| Login (painel) | `LoginPage.js:90` | `<ACCTALogoHorizontal dark />` | **escuro** |
| Login (mobile) | `LoginPage.js:123` | `<ACCTALogoHorizontal />` | **claro** |
| Sidebar (privado) | `PrivateLayout.js:160-172` | **NÃO usa o SVG** — emblema próprio: caixa carmesim com texto **"AC"** + palavra "ACCTA" | claro |

> 🔴 **Inconsistência:** a marca é renderizada de **duas formas diferentes** — o
> componente SVG (`ACCTALogoHorizontal`) no header/rodapé/login, e um **emblema
> "AC" hand-rolled** na sidebar. `PrivateLayout` importa `ACCTALogoHorizontal`
> (linha 8) mas a "Logo row" desenha a caixa "AC" à mão. Unificar isto faz parte
> do âmbito.
>
> 📌 A marca surge sobre **fundo claro E escuro** → justifica **duas versões**
> do logo (decisão D2, §3).

### 1.3 Favicon / ícones PWA / imagem social — **fora do âmbito (mas com bug)**

`index.html` e `manifest.json` referenciam `/favicon.ico`, `/logo192.png`,
`/logo512.png` e `og:image`/`twitter:image` = `logo512.png`. **Esses ficheiros
não existem em `frontend/public/`** (só há cópias do template CRA dentro de
`node_modules`) → em produção dão **404**.

- São ficheiros **estáticos referenciados por nome** em `index.html`/
  `manifest.json` — **não são troc��veis em runtime** por um valor de settings
  como um `<img src>` de React. Editá-los pela UI exigiria sobrescrever ficheiros
  no disco ou um passo de build.
- **Decisão D3 (§3):** ficam **fora do MVP**. O 404 é registado em §12 como bug
  separado a corrigir manualmente (colocar os ficheiros em `frontend/public/`).

### 1.4 Emails — sem logo

`backend/email_service.py` **não embute imagem de logo** (sem `<img>`/`cid:`).
Nada a gerir aqui. (Se um dia se adicionar, usaria a URL absoluta do logo
carregado — nota em §12.)

### 1.5 Upload e settings — infraestrutura reutilizável

- `backend/routes/upload.py`: categorias `documents`/`proofs`/`logos`/`avatars`.
  Existe `logos` (2 MB, **admin-only**) — mas é semanticamente para **logos de
  parceiros/benefícios**, não para a marca do portal. **SVG está bloqueado**
  (comentário em `upload.py:16`: risco de stored XSS). Validação por magic bytes
  (`validate_file_content`).
- Idiom **single-doc settings** (`finance_settings`) e o futuro `page_banners`
  (spec dos banners) são o **molde** para um `brand_settings`.
- Padrão de leitura pública `GET /…/public` sem auth (o logo aparece no login e
  páginas públicas **antes** de autenticar → precisa de endpoint público).
- RBAC: `admin`/`moderador` já é o par "gestão de conteúdo/marca" (alinha com a
  spec dos banners).

---

## 2. Objetivos e não-objetivos

### Objetivos
1. **Upload do logo pela UI**, substituindo a marca em **header, rodapé, login e
   sidebar** sem deploy.
2. **Duas versões** geríveis: logo para **fundo claro** e logo para **fundo
   escuro** (D2).
3. **SVG atual como fallback** — sem nenhuma imagem carregada, o portal mantém
   exatamente o aspeto de hoje (rollout não-destrutivo).
4. **RBAC:** Admin + Moderador gerem o logo (D1); audit log em toda a escrita.
5. **Unificar** a renderização da marca (sidebar deixa de ter o emblema "AC"
   divergente e passa a usar a marca gerida).

### Não-objetivos
- Favicon, ícones PWA (192/512) e imagem social/OG (D3 — ver §1.3 e §12).
- Tornar o **ícone quadrado** (sidebar recolhida / app icon) carregável —
  extensão futura (§12).
- Aceitar **SVG** no upload (bloqueado por XSS — §12).
- Editor de recorte/cor do logo; gestão de logos de parceiros (categoria `logos`
  existente, intocada).

---

## 3. Decisões da ACCTA (já confirmadas)

| # | Decisão | Escolha |
|---|---|---|
| D1 | Cargos que gerem o logo | **Admin + Moderador** (igual aos banners) |
| D2 | Versões | **Duas** — logo p/ fundo **claro** + logo p/ fundo **escuro** |
| D3 | Âmbito | **Só o logo na app** (header/rodapé/login/sidebar); favicon/PWA/OG ficam manuais |

---

## 4. Design da solução

### 4.1 Componente `<BrandLogo>` (novo) — fonte única da marca

`frontend/src/components/BrandLogo.js`. Lê a config da marca e decide entre
**imagem carregada** e **SVG fallback**:

```jsx
// Pseudocódigo
const { logo_light_url, logo_dark_url, alt } = useBrandLogo();  // TanStack Query, staleTime alto
const url = dark ? logo_dark_url : logo_light_url;

if (url) {
  return <img src={url} alt={alt}
              className="h-9 w-auto max-h-9 max-w-[180px] object-contain" />;
}
// fallback: SVG atual (preserva o aspeto de hoje, e funciona offline/erro)
return <ACCTALogoHorizontal dark={dark} className={className} />;
```

- **Imagem inclui o wordmark** (logo completo) → quando há imagem, **não** se
  desenha o texto "ACCTA / CABO VERDE" (vem na imagem). No fallback SVG, mantém-se
  texto+ícone como hoje.
- **Tamanho consistente:** `h-9` (~36 px, igual ao atual) + `w-auto object-contain`
  → logos de proporções diferentes não rebentam o layout.
- **Claro vs escuro:** usa `logo_dark_url` em fundo escuro; se não houver, cai
  para `logo_light_url`; se não houver nenhum, SVG (`dark`).
- `ACCTALogo.js` mantém-se como **default vetorial**; `BrandLogo` é o wrapper que
  todos os locais passam a usar.

### 4.2 Sidebar (privado)
- **Expandida:** mostra `<BrandLogo />` (logo claro gerido / SVG fallback),
  substituindo a palavra "ACCTA" hand-rolled.
- **Recolhida:** mantém um **mark compacto** (a caixa "AC" atual ou o
  `ACCTALogo variant="icon"`). Tornar esse ícone carregável é **extensão futura**
  (precisaria de um `logo_icon_url` quadrado — §12), fora do MVP.

---

## 5. Backend — mudanças

### 5.1 Nova categoria de upload `brand` — `backend/routes/upload.py`
```python
ALLOWED_EXTENSIONS["brand"] = [".png", ".jpg", ".jpeg", ".webp"]  # PNG p/ transparência
MAX_FILE_SIZES["brand"] = 2 * 1024 * 1024  # 2 MB
```
- Adicionar `"brand"` à whitelist de categorias no `POST` e `DELETE`.
- **RBAC:** `if category == "brand" and current_user.role not in ("admin", "moderador"): 403`.
- **SVG continua bloqueado** (XSS). Recomendar **PNG transparente** na UI.
- ⚠️ WebP depende de `validate_file_content` (igual à nota da spec dos banners):
  confirmar suporte ou restringir a `.png/.jpg/.jpeg`.
- *Não* alterar a regra existente de `logos` (parceiros) — `brand` é separado.

### 5.2 Coleção `brand_settings` (single-doc) — `backend/database.py`
- Registar `"brand_settings"` na lista de coleções.
- Um único documento `{"id": "brand_settings", ...}` (molde `finance_settings`).

### 5.3 Modelos Pydantic — `backend/models.py`
```python
class BrandSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "brand_settings"
    logo_light_url: Optional[str] = None   # fundo claro; None → SVG fallback
    logo_dark_url: Optional[str] = None    # fundo escuro; None → SVG fallback
    alt: str = "ACCTA Cabo Verde"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None

class BrandSettingsUpdate(BaseModel):
    logo_light_url: Optional[str] = None
    logo_dark_url: Optional[str] = None
    alt: Optional[str] = None
```
> ⚠️ **Semântica de "limpar":** com `Optional`+`None`=não-alterado, não há como
> *remover* um logo (voltar ao SVG). Convenção proposta: **string vazia `""` =
> repor default** (grava `None`); `None`/ausente = manter. Documentar e testar.
> Datas serializadas como **ISO-8601 string** (regra `models.md`).

### 5.4 Novo router — `backend/routes/brand.py`

| Endpoint | Auth | Descrição |
|---|---|---|
| `GET /api/brand/public` | **público** | `{ logo_light_url, logo_dark_url, alt }` (defaults se vazio). Consumido por layouts/login antes de auth. |
| `GET /api/brand` | admin + moderador | Igual + metadados (`updated_at`, `updated_by`). |
| `PATCH /api/brand` | admin + moderador | Atualiza light/dark/alt (single-doc, molde `PATCH /finances/settings`). `create_audit_log(...)`. Aplica semântica de "limpar" (§5.3). |

- Fluxo de troca: `POST /api/upload/brand` → `file_url` → `PATCH /api/brand`
  com `{ logo_light_url: file_url }` (ou `logo_dark_url`).
- Opcional: `delete_upload_file()` da imagem antiga se for `/uploads/brand/...`
  (padrão `benefits.py`).
- Registar o router em `backend/routes/__init__.py`.

---

## 6. Frontend — mudanças

### 6.1 `components/BrandLogo.js` (§4.1) — novo wrapper.
### 6.2 API client — `frontend/src/utils/api.js`
```js
export const brandAPI = {
  getPublic: () => api.get('/brand/public'),
  getAll:    () => api.get('/brand'),
  update:    (data) => api.patch('/brand', data),
};
```
+ `queryKeys.brand.public()` em `lib/queryClient.js`; hook `useBrandLogo()`
(TanStack Query, `staleTime` alto — marca é quase-estática).

### 6.3 Substituir usos do logo por `<BrandLogo>`
- `PublicLayout.js:29` (claro) e `:131` (`dark`).
- `LoginPage.js:90` (`dark`) e `:123` (claro).
- `PrivateLayout.js` "Logo row": usar `<BrandLogo />` (expandida) e mark
  compacto (recolhida) — §4.2.
- `ACCTALogo.js` permanece como fallback (não apagar).

### 6.4 UI de gestão
- **Recomendado:** co-localizar com os banners numa página única **"Aparência do
  Site"** (`/admin/aparencia`), com secções **"Logo / Marca"** e **"Banners"** —
  ambos são aparência gerida por Admin+Moderador. Em alternativa, página própria
  `/admin/marca`.
- Secção Logo: **dois slots** (claro / escuro), cada um com **preview**, botão
  "Substituir imagem" (`uploadAPI` → `brandAPI.update`) e ação "Repor default
  (SVG)". Campo **texto alternativo (alt)**.
- **Preview obrigatório nos dois contextos:** mostrar cada logo sobre um cartão
  **branco** e sobre um cartão **grafite**, para o gestor validar legibilidade.
- `useMutation` + `toast` (Sonner) + `qc.invalidateQueries({ queryKey: queryKeys.brand… })`.
- Estilo: design-system ACCTA (≤1 botão primário carmesim por secção).

### 6.5 Navegação (sidebar) — `PrivateLayout.js`
- Item "Aparência" (ou "Marca"), `icon: Image`/`Palette`,
  `roles: ['admin','moderador']`; entrada no `getPageTitle()`; rota em `App.js`
  com `<ProtectedRoute allowedRoles={['admin','moderador']}>`.

---

## 7. Modelo de dados

Documento único `brand_settings`:
```json
{ "id": "brand_settings",
  "logo_light_url": "/uploads/brand/ab12….png",
  "logo_dark_url":  "/uploads/brand/cd34….png",
  "alt": "ACCTA Cabo Verde",
  "updated_at": "2026-05-20T…Z", "updated_by": "<user-id>" }
```
`null` em qualquer `logo_*_url` → `BrandLogo` usa o SVG fallback nesse contexto.

---

## 8. Matriz RBAC

| Ação | admin | moderador | financeiro | socio | público |
|---|:--:|:--:|:--:|:--:|:--:|
| Ver o logo (toda a app) | ✓ | ✓ | ✓ | ✓ | ✓ |
| `GET /api/brand/public` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `GET /api/brand` (gestão) | ✓ | ✓ | ✗ | ✗ | ✗ |
| `POST /api/upload/brand` | ✓ | ✓ | ✗ | ✗ | ✗ |
| `PATCH /api/brand` | ✓ | ✓ | ✗ | ✗ | ✗ |
| Ver item "Aparência" na sidebar | ✓ | ✓ | ✗ | ✗ | — |

Toda escrita gera **audit log** (`create_audit_log`).

---

## 9. Migração / rollout (não-destrutivo)

- `brand_settings` começa vazio; `logo_*_url = None` → **SVG fallback** → o
  portal fica **idêntico ao atual** antes de qualquer upload.
- O mesmo SVG embebido (`ACCTALogo.js`) é o fallback no frontend se a query
  falhar → a marca **nunca** fica em branco.
- Sem alteração de schema que quebre documentos; **não dispara Stop Conditions**.
- A unificação da sidebar (substituir "AC" por `<BrandLogo>`) é puramente visual
  e reversível.

---

## 10. Plano de implementação (fases)

**Fase 1 — Backend**
- [ ] `upload.py`: categoria `brand` (ext, 2 MB, RBAC admin+moderador, SVG bloqueado).
- [ ] `models.py`: `BrandSettings` + `BrandSettingsUpdate` (+ semântica "limpar").
- [ ] `database.py`: registar `brand_settings`.
- [ ] `routes/brand.py`: 3 endpoints + audit log; `__init__.py` inclui router.

**Fase 2 — Componente + integração**
- [ ] `components/BrandLogo.js` + `useBrandLogo()` + queryKey.
- [ ] `utils/api.js`: `brandAPI`.
- [ ] Substituir logo em PublicLayout, LoginPage e sidebar (PrivateLayout).

**Fase 3 — Gestão (UI)**
- [ ] Página "Aparência do Site" (secção Logo: 2 slots + preview claro/escuro +
      alt + repor default).
- [ ] Rota + sidebar + `getPageTitle` (`allowedRoles={['admin','moderador']}`).

**Fase 4 — Verificação** (§11).

---

## 11. Testes

**Backend (`backend/tests/`, pytest in-process):**
- `PATCH /api/brand` aceita admin e moderador; nega financeiro/socio (403).
- `POST /api/upload/brand` nega financeiro/socio (403); aceita admin/moderador;
  rejeita `.svg` e ficheiro > 2 MB.
- `GET /api/brand/public` sem auth devolve defaults quando vazio.
- Semântica "limpar": `""` repõe `None` (volta ao SVG); `None` mantém.
- ⚠️ Wire `mock_db.brand_settings` no `conftest.py` (coleção nova não pré-ligada).

**Frontend (manual, browser):**
- Logo carregado aparece em header, rodapé, login (claro e escuro) e sidebar.
- Sem upload → SVG atual (idêntico a hoje); falha de query → fallback (nunca vazio).
- Preview na UI mostra logo sobre branco **e** grafite; legibilidade ok.
- Upload troca o logo ao vivo após `invalidate`; "repor default" volta ao SVG.
- Sidebar expandida (logo) vs recolhida (mark compacto).

---

## 12. Riscos e questões em aberto

- **Bug separado (favicon):** `/favicon.ico`, `/logo192.png`, `/logo512.png`
  referenciados mas **ausentes** de `frontend/public/` → 404 + og:image/PWA
  partidos. Corrigir manualmente (colocar ficheiros) — fora do MVP (D3) mas
  deve ser registado como issue.
- **Ícone quadrado (extensão futura):** sidebar recolhida / app icon / favicon
  beneficiariam de um `logo_icon_url` quadrado carregável. Não no MVP.
- **SVG bloqueado:** upload de SVG continua proibido (stored XSS). Se a ACCTA
  exigir vetor, precisa de sanitização dedicada (decisão à parte).
- **Consolidar settings:** `brand_settings` + `page_banners` poderiam fundir-se
  num `site_settings`/página "Aparência" única. Recomendado co-localizar a UI
  (§6.4); manter coleções separadas é aceitável.
- **Proporção do logo:** imagens muito largas/altas são limitadas por
  `h-9 max-w-[180px] object-contain`; indicar na UI o tamanho recomendado
  (ex.: ~360×72, PNG transparente).
- **Email logo:** emails não têm logo hoje; se adicionado, usar URL absoluta do
  logo carregado (`FRONTEND_URL` + path) — fora do âmbito.
