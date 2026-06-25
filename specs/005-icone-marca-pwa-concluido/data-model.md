# Data Model — Ícone quadrado da marca / PWA

Fase 1. A feature **não cria coleções nem índices novos** — estende o documento único
`brand_settings` com um campo aditivo.

---

## Entidade: `brand_settings` (documento único existente)

Tabela `brand_settings (pk bigserial, doc jsonb)`, um único documento
`{"id": "brand_settings", ...}`. Já contém logótipos + favicon; esta feature acrescenta
`icon_url`.

| Campo | Tipo | Novo? | Descrição |
|---|---|:--:|---|
| `id` | str | — | Sempre `"brand_settings"`. |
| `logo_light_url` | `Optional[str]` | — | Logótipo fundo claro; `None` → SVG fallback. |
| `logo_dark_url` | `Optional[str]` | — | Logótipo fundo escuro; `None` → SVG fallback. |
| `favicon_url` | `Optional[str]` | — | Favicon do separador (feature anterior, v0.5.34). **Intocado.** |
| **`icon_url`** | `Optional[str]` | **✅** | **Ícone quadrado da marca** (PWA + og + mark in-app); `None` → default estático. |
| `alt` | str | — | Texto alternativo (default `"ACCTA Cabo Verde"`). |
| `updated_at` | str (ISO-8601) | — | Última escrita. |
| `updated_by` | `Optional[str]` | — | ID de quem escreveu. |

### Regras de validação / semântica

- `icon_url` segue a **semântica de "limpar"** já usada pelos outros URLs da marca:
  - `""` no PATCH → repõe default (grava `None`);
  - ausente (não enviado) → mantém;
  - URL (`/uploads/brand/<file>`) → substitui.
- Ao gravar, ficheiros de upload próprios (`/uploads/brand/...`) que deixem de estar
  referenciados por **qualquer** campo de URL da marca são apagados
  (`delete_upload_file`) — a lógica partilhada de `url_fields` já deduplica ficheiros
  referenciados por mais do que um campo.
- `icon_url` **não** tem validação de conteúdo no modelo (string livre, como os restantes
  URLs da marca); o conteúdo seguro é garantido pelo upload (`brand`: PNG/JPG/WEBP, SVG
  bloqueado, ≤ 2 MB). Validação só na fronteira (Princípio I).

### Modelos Pydantic afetados (`backend/models.py`)

- `BrandSettings`: `+ icon_url: Optional[str] = None  # ícone quadrado (PWA/og/in-app); None → default estático`
- `BrandSettingsUpdate`: `+ icon_url: Optional[str] = None  # "" = repor default; None = manter`

> **Compatibilidade**: campo **aditivo opcional** com default `None` → documentos
> existentes em DB continuam válidos; **não** aciona a STOP condition de "mudar Pydantic
> de forma que quebre documentos" (Princípio VI / Constituição §5-quebra).

---

## Entidade: Ficheiro de imagem do ícone

- Carregado via `POST /api/upload/brand` → `/uploads/brand/<uuid>.<ext>`.
- Servido estaticamente por `UploadsStaticFiles` (`server.py`) e, de forma indireta e
  estável, por `GET /api/brand/icon` (redirect).
- Ciclo de vida: criado no upload; referenciado em `icon_url`; apagado quando deixa de
  ser referenciado (substituição ou reposição).

---

## Sem alterações de schema/índices

- `database.py`: `brand_settings` já está em `COLLECTIONS`; **nenhum índice novo**
  (documento único acedido por `id`).
- Sem migração de dados (campo aditivo).
