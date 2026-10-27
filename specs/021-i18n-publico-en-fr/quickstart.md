# Quickstart — validação da spec 021

## Pré-requisitos

- `cd frontend && yarn start` (backend local opcional: só necessário para Notícias/Galeria/
  Eventos com dados; ver memória `local-dev-run`). Nunca apontar para o `.env` de prod
  em testes de escrita.
- Janela anónima por cenário (preferência limpa).

## Automático

```bash
cd frontend && yarn test --testPathPattern=i18n      # paridade de chaves + t()/lp()/switchPath + detecção
cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60
cd frontend && yarn build                             # en/fr aparecem como chunks separados
```

Verificar que **nenhuma** página pública mantém literais PT de UI:
`grep` dos textos PT conhecidos (ex.: «Saltar para o conteúdo», «Início») em
`src/pages/public` e `src/layouts/PublicLayout.js` → 0 ocorrências fora de `src/i18n/`.

## Manual em navegador (Princípio VII)

1. **Detecção** — Chrome com idioma preferido FR, abrir `/` → URL vira `/fr`, Home em FR,
   seletor mostra «Français». Repetir com EN; com `es` → fica em `/` PT.
2. **Navegação** — em `/fr`, percorrer as 16 páginas pelo menu/links: URL sempre `/fr/…`,
   0 strings de UI em PT (exceto conteúdos da API).
3. **Seletor preserva página** — em `/en/sobre` escolher FR → `/fr/sobre`. Fechar e reabrir
   `/sobre` → vai para `/fr/sobre`.
4. **URL prevalece** — com preferência FR, abrir `/en/contactos` → EN; voltar a `/` → FR.
5. **Teclado/AT** — Tab até ao seletor, Enter abre, setas + Enter trocam; leitor de ecrã
   anuncia o ativo.
6. **SEO** — DevTools em `/en/sobre`: `<html lang="en">`, title/description EN, 4 `hreflang`
   (contrato §3). Ver também `/sobre` com UA Googlebot (DevTools → Network conditions) →
   não redireciona.
7. **Conteúdo dinâmico** — `/en/noticias/<slug>`: shell EN + aviso «This content is in
   Portuguese»; corpo em PT. Em `/` (Home) não há aviso.
8. **404** — `/fr/xyz` → «Page introuvable», link para `/fr`. `/xyz` → Home (inalterado).
9. **Auth** — `/en/login`, `/en/forgot-password`: seletor visível, formulário e Turnstile
   em EN; mensagens de erro do backend podem vir em PT (aceite).
10. **Privado intacto (SC-008)** — login, `/dashboard`: PT, sem seletor, `lang="pt-CV"`.
11. **Mobile 360px** — seletor acessível no menu mobile, sem overflow.

## Gate de go-live (STOP)

- Dono/tradutor revê `en.js` e `fr.js` (FR-020) e remove `// REVISÃO HUMANA PENDENTE`.
- `PENDING` vazio.
- Emenda constitucional v1.2.0 merged.
