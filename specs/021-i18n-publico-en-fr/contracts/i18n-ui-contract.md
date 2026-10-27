# Contrato UI — i18n público (spec 021)

Sem contrato de API (zero backend). Este é o contrato entre o módulo `src/i18n/` e as
páginas públicas, mais o contrato observável (URL/HTML) que os testes e a validação usam.

## 1. Módulo `src/i18n/`

```text
I18nProvider            envolve as rotas públicas; deriva locale do URL; carrega o
                        dicionário (pt estático, en/fr lazy); spinner enquanto carrega
useI18n() → {
  locale,               'pt' | 'en' | 'fr'
  t(key, vars?),        string; fallback locale → pt → key; warn em dev
  lp(path),             '/sobre' → '/en/sobre' (pt: inalterado; '/' → '/en')
  formatDate(d, fmt),   date-fns com o locale correto
  switchPath(target)    URL atual com o prefixo trocado (preserva search/hash)
}
usePageMeta({ titleKey, descriptionKey })   title, description, html lang, hreflang×4
<LanguageSwitcher />                        dropdown nativo-rotulado, grava preferência
<PortugueseContentNotice />                 null em pt; banner discreto em en/fr
<NotFoundPage />                            404 traduzida (só sob /en e /fr)
```

Regra: **nenhuma página pública contém literais de UI em PT** depois da migração — só
`t('…')`. Literais permitidos: nomes próprios (ACCTA, CV-CAR, IFATCA, ICAO), dados da API.

## 2. Contrato observável (URL → resultado)

| Pedido | Resultado |
|--------|-----------|
| `/sobre`, sem preferência, `navigator.languages=['fr-FR']`, browser normal | redirect `replace` → `/fr/sobre` |
| `/sobre`, sem preferência, UA Googlebot | fica em `/sobre`, PT |
| `/sobre`, preferência `en` | → `/en/sobre` |
| `/en/sobre`, preferência `pt` | fica em `/en/sobre`, EN (URL prevalece); preferência não muda |
| seletor FR em `/en/noticias/x?y=1#z` | → `/fr/noticias/x?y=1#z`; `localStorage['accta.locale']='fr'` |
| seletor PT em `/fr/sobre` | → `/sobre`; preferência `pt` |
| `/en/inexistente` | 404 EN «Page not found», link `/en`, seletor visível |
| `/inexistente` | `Navigate` → `/` (comportamento atual, R10) |
| `/en/dashboard` | 404 EN (privado não tem variante) |
| `/dashboard` com preferência `en` | PT, sem seletor, `lang=pt-CV` (FR-002, SC-008) |

## 3. `<head>` de cada página pública (ex.: `/en/sobre`)

```html
<html lang="en">
<title>…EN…</title>
<meta name="description" content="…EN…">
<link rel="alternate" hreflang="pt-PT"     href="https://controlador.cv/sobre">
<link rel="alternate" hreflang="en"        href="https://controlador.cv/en/sobre">
<link rel="alternate" hreflang="fr"        href="https://controlador.cv/fr/sobre">
<link rel="alternate" hreflang="x-default" href="https://controlador.cv/sobre">
```

URLs absolutas a partir de `window.location.origin`; sem `search`/`hash`.
Rotas com parâmetro (`/noticias/:slug`) usam o path concreto.

## 4. Acessibilidade do seletor

- Botão: `aria-label` = `t('languageSwitcher.label')` + idioma ativo; foco visível
  (`focus-visible:ring-2 ring-[#C7202F]/40`, padrão do layout).
- Itens: texto nativo («Português», «English», «Français»), atributo `lang` por item,
  `aria-current="true"` no ativo; anúncio «ativo/active/actif» via `sr-only`.
