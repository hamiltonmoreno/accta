# Data Model — Spec 021

**Sem alterações de backend/BD.** Zero coleções, campos, migrações ou modelos Pydantic.
Todas as entidades vivem no frontend.

## Locale

| Valor | Prefixo URL | `hreflang` | `<html lang>` | date-fns |
|-------|-------------|-----------|---------------|----------|
| `pt` (default, canónico) | *(nenhum)* | `pt-PT` (+ `x-default`) | `pt-CV` (inalterado, R4) | `ptBR` |
| `en` | `/en` | `en` | `en` | `enUS` |
| `fr` | `/fr` | `fr` | `fr` | `fr` |

Constante única: `SUPPORTED_LOCALES = ['pt', 'en', 'fr']`, `DEFAULT_LOCALE = 'pt'`.

## TranslationBundle (`src/i18n/locales/{pt,en,fr}.js`)

Objeto aninhado `namespace → chave → string | string[] | object[]`.

- Chave plana = caminho com pontos: `home.hero.title`.
- Interpolação: `{nome}` (mesmos placeholders nas 3 línguas — validado por teste).
- **PT é a fonte** (FR-026): toda a chave nasce em `pt.js`.
- Namespaces: `common`, `layout`, `languageSwitcher`, `notFound`, `contentNotice`,
  `meta.<pagina>` (title/description), e um por página (`home`, `sobre`, `profissao`,
  `plataforma`, `noticias`, `galeria`, `publicacoes`, `eventos`, `beneficios`,
  `contactos`, `validador`, `login`, `criarConta`, `forgotPassword`, `resetPassword`,
  `setupAccount`).

## Pending list (`src/i18n/pending.js`)

`export const PENDING = { en: [chaves…], fr: [chaves…] }` — chaves cuja tradução está
conscientemente desatualizada/em falta; o teste de paridade tolera-as e lista-as. Vazio no
go-live.

## LanguagePreference

- `localStorage['accta.locale']` ∈ `SUPPORTED_LOCALES`; valor inválido = ausente.
- Escrita **apenas** pelo `LanguageSwitcher`.
- Ordem de resolução numa rota pública **sem prefixo**: preferência guardada → (se ausente)
  `navigator.languages` → `pt`. Crawlers: sempre `pt`. Rotas **com prefixo**: o prefixo
  decide, sempre (FR-018).

## PublicRoute

Array único `PUBLIC_ROUTES = [{ path, element, layout: 'public' | 'auth', dynamic? }]`
(16 entradas, slugs PT/atuais inalterados) montado para `''`, `/en`, `/fr`.
`dynamic: true` marca as rotas com aviso de conteúdo em PT (notícia detalhe, etc.).
Sob `/en` e `/fr` acresce `*` → `NotFoundPage`.
