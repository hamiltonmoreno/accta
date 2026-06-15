# TODO — Central de Ajuda (manual do utilizador no dropdown do perfil)

Spec: `tasks/spec-central-ajuda.md`. Defaults do dono: 1-A (página `/ajuda`),
2-A (conteúdo estático em `content/ajuda/`), 3 (filtrar por role/privilégio),
4 (pesquisa client-side).

## Fase 0 — helper de visibilidade partilhado
- [ ] `lib/nav/visibility.js`: `buildNavContext(auth)` + `isNavItemVisible(item, ctx)`
      (extrai a regra do `filterItem` do `PrivateLayout`)
- [ ] `PrivateLayout.js` passa a consumir o helper (sem mudar comportamento)

## Fase 1 — manual + entrada
- [ ] `content/ajuda/`: index + primeirosPassos, meuPortal, governanca,
      comunidade, financas, administracao (artigos com passos/dicas/faq + `gate`)
- [ ] `pages/private/AjudaPage.js`: herói + pesquisa + TOC + secções (Accordion),
      filtra secções/artigos por visibilidade; conteúdo só do módulo
- [ ] `UserMenu.jsx`: item *Ajuda* (`menu-ajuda`) → `/ajuda`, neutro, todos os roles
- [ ] `App.js`: lazy import + rota privada `/ajuda` (sem gate de role)

## Testes
- [ ] `UserMenu.test.jsx`: *Ajuda* aparece p/ todos e aponta `/ajuda`
- [ ] `AjudaPage.test.jsx`: render; socio não vê Finanças/Administração; admin vê;
      pesquisa filtra
- [ ] `content/ajuda` integridade: ids únicos, secção tem ≥1 artigo, rotas válidas
- [ ] `lib/nav/visibility.test.js`: regra de RBAC aditivo + match

## Verificação
- [x] `yarn build` passa; eslint sem novos erros; testes verdes (31 novos)
- [x] `/frontend-design`: neutral-led, sem dark mode, sem primário Floresta (só links Carmesim)

---

## Revisão (feito)

Todas as caixas acima ✓. Resumo:

- **Fase 0** — `lib/nav/visibility.js` (`buildNavContext`/`isNavItemVisible`)
  extraído de `PrivateLayout.filterItem`; sidebar passa a consumi-lo (testes da
  PrivateLayout continuam verdes → sem mudança de comportamento). Fonte única
  partilhada com o manual.
- **Fase 1** — `content/ajuda/` (index + 6 secções A–F, artigos com
  passos/dicas/faq/rota/gate); `AjudaPage` consome o módulo, filtra
  secções/artigos por visibilidade real, pesquisa client-side, TOC com
  deep-link `#seccao`, rodapé p/ Esclarecimentos; item *Ajuda* (`menu-ajuda`)
  no `UserMenu` p/ todos os roles; rota privada `/ajuda` (sem gate de role).
- **Visibilidade por artigo**: secção aparece se ≥1 artigo visível (ex.:
  moderador só vê Aparência/Notícias dentro de Administração; Conselho Fiscal
  com `view_finances_readonly` vê Finanças sem ser admin).
- **Testes** (31): `visibility` (RBAC aditivo + match), `content/ajuda`
  integridade (ids únicos, rotas válidas), `AjudaPage` (socio≠Finanças/Admin,
  admin vê, CF vê Finanças, pesquisa filtra, estado vazio), `UserMenu` (Ajuda
  p/ todos os roles).
- **Fora de escopo (spec §9)**: editor via API, "?" contextual por página, tour
  interativo — ficam para fases futuras.
