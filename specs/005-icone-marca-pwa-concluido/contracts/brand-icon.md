# Contrato — Ícone quadrado da marca

Estende o router de marca (`backend/routes/brand.py`, prefixo `/api/brand`). Um endpoint
público novo + extensão dos endpoints existentes para incluir `icon_url`. Sem alteração
ao contrato JS de `brandAPI` (continua `getPublic`/`getAll`/`update`).

---

## `GET /api/brand/icon` — **NOVO** (público)

Resolve e entrega o ícone quadrado **atual** da marca. URL **estável** referenciado pelo
`manifest.json` (ícones PWA) e pelo `og:image`/`twitter:image` do `index.html`.

- **Auth**: nenhuma (público; a marca aparece antes do login e é lida por SO/crawlers).
- **Request**: sem parâmetros.
- **Comportamento**:
  - Se `brand_settings.icon_url` definido → **302** `Location: <icon_url>`
    (ex.: `/uploads/brand/<uuid>.png`, servido estaticamente no mesmo origin).
  - Senão → **302** `Location: {FRONTEND_URL}/logo512.png` (default estático atual).
  - Header `Cache-Control: public, max-age=3600` (frescura vs. carga; ajustável).
- **Respostas**:
  | Código | Quando |
  |---|---|
  | 302 | Sempre (redirect para o ícone atual ou default). |
- **Notas**:
  - Plano B documentado (se algum crawler relevante não seguir o redirect): servir os
    bytes diretamente via `FileResponse` em vez de 302.
  - O endpoint **não grava** nada (leitura pura).

---

## `GET /api/brand/public` — estendido (público)

Acrescenta `icon_url` ao payload já existente.

```json
{
  "logo_light_url": "string | null",
  "logo_dark_url":  "string | null",
  "favicon_url":    "string | null",
  "icon_url":       "string | null",   // NOVO
  "alt":            "string"
}
```

Consumido pelo componente in-app `BrandIcon` (mark da sidebar recolhida).

---

## `GET /api/brand` — estendido (admin + moderador)

Igual ao `public` + metadados (`updated_at`, `updated_by`); passa a incluir `icon_url`
(via o `_public_view` partilhado). RBAC: 403 para financeiro/socio; 401 sem token.

---

## `PATCH /api/brand` — estendido (admin + moderador)

Aceita `icon_url` no corpo, com a mesma semântica dos restantes URLs.

- **Auth**: admin + moderador (403 caso contrário; 401 sem token).
- **Body** (`BrandSettingsUpdate`, todos opcionais):
  ```json
  { "logo_light_url": "…", "logo_dark_url": "…", "favicon_url": "…",
    "icon_url": "…", "alt": "…" }
  ```
- **Semântica de `icon_url`**: `""` repõe default (`None`); ausente mantém; URL substitui.
- **Efeitos**:
  - Grava `icon_url` no `set_fields` (via `url_fields`);
  - Limpa ficheiros `/uploads/brand/...` órfãos (deduplicando os referenciados por outros
    campos);
  - `create_audit_log("brand_updated", …, request=request, details={… "icon_url" …})`.
- **Resposta**: `_public_view(...)` atualizado (inclui `icon_url`).
- **Erros**: 400 se nenhum campo fornecido; 403/401 RBAC.

---

## Fluxo de troca do ícone (UI)

```
POST /api/upload/brand  (multipart, admin/moderador)  → { file_url: "/uploads/brand/<uuid>.png" }
PATCH /api/brand        { "icon_url": "/uploads/brand/<uuid>.png" }   → marca atualizada
# manifest/og já apontam para GET /api/brand/icon → refletem o novo ícone sem deploy
```

---

## Referências estáticas no frontend (uma vez)

- `frontend/public/manifest.json` — substituir a entrada de ícone PWA por:
  ```json
  { "src": "https://api.controlador.cv/api/brand/icon", "sizes": "any", "purpose": "any", "type": "image/png" }
  ```
  (mantendo/`favicon.ico` para o atalho mínimo, se desejado).
- `frontend/public/index.html` — `og:image` e `twitter:image` →
  `https://api.controlador.cv/api/brand/icon`.

---

## Testes do contrato (`backend/tests/test_brand_routes.py`)

- `GET /api/brand/public` inclui `icon_url` (null quando vazio; valor quando gravado).
- `PATCH /api/brand` define `icon_url` (admin/moderador); 403 financeiro/socio.
- `PATCH /api/brand` com `icon_url=""` repõe `None` e apaga o upload anterior.
- `GET /api/brand/icon`: com `icon_url` → 302 para esse URL; sem `icon_url` → 302 para o
  default (`{FRONTEND_URL}/logo512.png`).
- `icon_url` partilhado com outro campo não é apagado ao limpar só um (dedup de órfãos).
