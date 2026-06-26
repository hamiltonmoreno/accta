# Quickstart — Validação (Revisão do Ranking e do Perfil)

Guia de validação em navegador. Tudo frontend; **sem servidor/DB novos**. Princípio
VII: exercer em navegador nas larguras-alvo antes de marcar "done".

## Pré-requisitos

```bash
cd frontend && yarn install      # se necessário
cd frontend && yarn start        # dev server (ver memory: local-dev-run)
```

- Login de sócio com posição no ranking (idealmente com ≥3 membros calculados).
- Ter pelo menos um sócio **com** foto e um **sem** foto, para validar o fallback.
- Larguras a testar (DevTools responsive): **360, 390, 414** (telemóvel), **768**
  (tablet), **1024 / 1440** (desktop).

## US1 — Ranking responsivo no telemóvel

1. Abrir `/ranking` a 360px.
2. **Esperado**: pódio, caixa "A minha posição", tabela e paginação contidos na
   largura, sem sobreposição/distorção/corte horizontal indevido. (SC-001)
3. Repetir a 390/414px e como **gestor** (cabeçalho com mais botões — confirmar wrap).
4. Confirmar 768/1024/1440px **sem regressão** vs. atual. (SC-006)

## US2 — Distinção 1.º / 2.º / 3.º

1. Em `/ranking` (e no widget do dashboard `/dashboard`), com ≥3 membros.
2. **Esperado**: 1.º, 2.º e 3.º com destaque visual distinto entre si
   (Carmesim → Grafite → muted, default) + número/ícone; 4.º+ mostra o número. (SC-002)
3. **Acessibilidade**: a posição é percetível além da cor (número + ícone). (FR-005)
4. Com <3 membros, o pódio adapta-se sem partir.

## US3 — Fotos dos sócios

1. Em `/ranking` (pódio + tabela) e no widget do dashboard.
2. **Esperado**: sócio com foto mostra a foto; sócio sem foto mostra iniciais
   consistentes; **zero imagens quebradas**. (SC-003)
3. Confirmar que um sócio em **opt-out** não aparece nas listas públicas (a foto
   não o reexpõe). (FR-008)

## US4 — Painel de notificações sem corte

1. A 360/390/414px, em qualquer página, tocar no sino de notificações.
2. **Esperado**: o painel mantém margem ≥**16px** nos **dois** bordos, sem cortar conteúdo. (SC-004)
3. Em desktop, o painel continua alinhado ao sino (sem regressão). (SC-006)

## US5 — Perfil: editável vs. gerido

1. Abrir `/perfil` como sócio.
2. **Editar** → confirmar que todos os campos de autosserviço (dados pessoais,
   contacto, morada, emergência, profissional/licença, foto, biografia) estão
   presentes e **gravam**. (SC-005)
3. **Esperado**: Email, N.º Sócio, Cargo, Função, Estado, Categoria e Data de
   Admissão aparecem claramente **não-editáveis**, com indicação de que a alteração
   é feita pela administração. (FR-012/FR-013)
4. A fronteira "editável vs. gerido pela associação" é visualmente óbvia.

## Lint (antes do PR)

```bash
cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60
```

## Critérios de aceitação (resumo)

- SC-001..SC-006 verdes nas larguras indicadas; sem regressão desktop/tablet.
- Sem novas dependências; sem alterações de backend/API.
- Conforme ao sistema de design ACCTA (neutral-led, Carmesim acento único).
