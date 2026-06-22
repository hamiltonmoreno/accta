# Quickstart — Validação da landing da plataforma

Guia executável para provar a feature ponta-a-ponta. Detalhes de implementação vivem em `tasks.md` (após `/speckit-tasks`) e nos `contracts/`.

## Pré-requisitos

```bash
cd frontend
yarn install          # apenas se ainda não instalado (não adicionar deps novas)
```

## Correr localmente

```bash
cd frontend
yarn start            # dev server (Craco) — abre o site público
```

> Para o site completo com backend (opcional aqui, pois a página é estática): ver [[local-dev-run]].

## Cenários de validação

### C1 — Rota e renderização (US1 / FR-001, FR-002)
1. Navegar para `http://localhost:3000/plataforma`.
2. **Esperado**: a página carrega dentro do `PublicLayout` (cabeçalho + rodapé visíveis), com banner, secção de introdução, secção de capacidades e fecho.

### C2 — Link discreto no rodapé (US1 / FR-004, SC-001)
1. Abrir qualquer página pública (ex. `/` ou `/sobre`).
2. Localizar no rodapé o link "A plataforma" (barra inferior, discreto).
3. Clicar.
4. **Esperado**: navegação SPA para `/plataforma` em **1 clique**, sem recarregar.

### C3 — Capacidades (US2 / FR-003, SC-002)
1. Na página, percorrer a secção de capacidades.
2. **Esperado**: ≥ 5 módulos descritos (título + descrição curta), factuais, sem números inventados nem preços.

### C4 — Sem CTA forte (FR-005, SC-004)
1. Inspecionar a página.
2. **Esperado**: nenhum botão de ação primário comercial proeminente ("Pedir demonstração"/"Comprar"/"Subscrever").

### C5 — Responsividade e marca (US3 / FR-007, FR-008, SC-003)
1. Com DevTools, testar larguras **360px, 768px, 1024px, 1440px**.
2. **Esperado**: secções empilham em mobile, sem overflow horizontal; tokens de marca corretos (Carmesim/Grafite/Floresta), Open Sans, sem dark mode.

## Gates automáticos (SC-005)

```bash
cd frontend
npx eslint src/ --ext .js,.jsx --max-warnings=60     # lint sem novos avisos acima do limite
yarn build                                            # build de produção conclui com sucesso
```

## Verificação de não-regressão

- Confirmar que as restantes rotas públicas continuam a funcionar (o link novo no rodapé não quebra o layout partilhado).
- `grep` por `style={{` em `PlataformaPage.js` deve devolver **0** (sem inline styles).

## Definition of Done (resumo)
- [ ] `/plataforma` renderiza no `PublicLayout` (C1).
- [ ] Link discreto no rodapé navega em 1 clique (C2).
- [ ] ≥ 5 capacidades factuais (C3).
- [ ] Sem CTA comercial forte (C4).
- [ ] Responsivo 360–1440px + marca correta (C5).
- [ ] Lint + build verdes (SC-005).
- [ ] Verificação manual no browser (Constituição VII).
