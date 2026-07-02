# Research & Decisions — Spec 016

Todas as ambiguidades foram fechadas com o dono durante o brainstorming; não há `NEEDS CLARIFICATION`. Este documento regista as decisões de desenho e as alternativas rejeitadas.

## D1 — «Privilégios transparentes» é falta de tradução, não bug de CSS

- **Decisão**: causa-raiz confirmada por leitura direta — `PRIVILEGE_LABELS` (`frontend/src/lib/cargoLabels.js:12-22`) só define 9 dos 12 privilégios; `EditUserModal.js:179` indexa `PRIVILEGE_LABELS[priv]` **sem** fallback, logo `emit_cf_parecer`/`send_comunicados`/`comunicar_intra_orgao` renderizam como `<span>` vazio (parecem «transparentes»). Corrige-se adicionando os 3 rótulos + usando o helper `privilegeLabel()` (que já existe, `cargoLabels.js:25`, com fallback `|| priv`).
- **Rationale**: correção na origem, ~4 linhas, robusta a futuros privilégios novos (degradação graciosa para a chave).
- **Alternativas rejeitadas**: (a) investigar contraste/opacidade — descartada: o problema é ausência de texto, não cor; (b) hard-codar os 12 no componente — pior, duplica a fonte.

## D2 — Onde vive a lista de departamentos

- **Decisão**: `DEPARTAMENTOS` (backend) fica em `backend/models.py`, junto a `CARGOS_DECLARADOS`, e é exposta aditivamente por `GET /api/auth/registration-options`. Para os forms de admin, um conjunto espelho `DEPARTAMENTOS` em `frontend/src/pages/private/usuarios/tokens.js`.
- **Rationale**: departamento é uma **etiqueta organizacional**, não um conceito de governança (órgãos/cargos/categorias). `governance.py` é a fonte única *de governança* e, por contrato explícito no seu cabeçalho, **não importa de `models`** (evita ciclo). Colocar `DEPARTAMENTOS` em `governance.py` obrigaria a poluí-lo com um conceito alheio; colocá-lo em `models.py` mantém-no ao lado do análogo `CARGOS_DECLARADOS` e mantém o backend a 2 ficheiros. O `tokens.js` já alberga conjuntos pequenos e estáveis (`ROLES`, `STATUSES`), pelo que `DEPARTAMENTOS` encaixa nessa filosofia.
- **Trade-off aceite**: pequena duplicação backend↔frontend (mesma que já existe entre `models.CARGOS_DECLARADOS` e o `CARGOS_FALLBACK` de `CriarContaPage`). Aceite por consistência e por evitar o ciclo de imports; a lista é estável.
- **Alternativas rejeitadas**: (a) `governance.py` + `governance_structure()` — rejeitada pelo ciclo de imports e por misturar conceitos; (b) endpoint novo dedicado a departamentos — excesso (Princípio I); (c) tabela na BD — a lista é uma constante estável, não dados operacionais (sem migração).

## D3 — «Outro» e compatibilidade de dados

- **Decisão**: a dropdown inclui uma opção sentinela «Outro» que revela um campo de texto livre; o valor **resolvido** (item da lista ou texto do «Outro») é o que se envia/guarda. O backend **não** passa a validar `department ∈ DEPARTAMENTOS` — mantém string livre (só limite de comprimento, já existente).
- **Rationale**: «Outro» tornaria qualquer enum-enforcement contraditório; manter string livre garante que (i) «Outro» funciona, (ii) registos legados/vazios continuam válidos (FR-016), (iii) zero migração. Ao editar, um `department` legado fora da lista pré-seleciona «Outro» e mostra o valor (FR-013), sem perda.
- **Alternativas rejeitadas**: enum estrito no backend (parte «Outro» e registos legados); tornar obrigatório (o dono decidiu opcional).

## D4 — Função no convite: completar role, não introduzir cargo

- **Decisão** (confirmada pelo dono, Q1): o seletor «Função» do convite passa a listar os **4 roles** (`ROLES` de `tokens.js`, que já os tem) com `ROLE_LABELS`, rótulo «Função no Sistema». A relação função↔cargo↔privilégios materializa-se na **edição** (D5), não no convite — porque no convite ainda não há cargo (novo sócio entra como `socio`), e o cargo institucional é atribuído exclusivamente via «Cargos & Mandatos» + eleições (que registam mandato). **Fora de âmbito**: introduzir seleção de cargo no convite/inscrição.
- **Rationale**: alinha o convite com a edição (que já tem 4) com uma mudança mínima e sem cruzar a fronteira estatutária.
- **Alternativas rejeitadas**: seletor de cargo que atribui mandato no convite (maior âmbito, cruza eleições/vagas); deixar como está (não resolve o pedido).

## D5 — Predefinições do cargo: botão explícito, nunca automático

- **Decisão** (confirmada pelo dono, Q3): `EditUserModal` ganha um botão «Aplicar predefinições do cargo» que preenche `role` + `privileges` a partir de `CARGO_DEFAULTS[cargo]` (lido de `GET /api/governance/structure`, campos `role_default`/`privileges_default` já existentes). Explícito (só no clique), editável depois, nunca sobrescreve sem intenção; escondido para contas `technical`.
- **Rationale**: torna visível/acionável uma relação que já existe no backend, com zero backend novo. Evitar sincronização automática protege ajustes manuais do admin (FR-006).
- **Alternativas rejeitadas**: pré-marcar quando vazio (menos previsível); só badge (não poupa esforço); sincronizar ao mudar cargo (sobrescreve manual; e o cargo nem se muda aqui — é só-leitura).

## D6 — Sem dependências, sem migração, release por Via B

- **Decisão**: nenhuma dependência nova; nenhuma alteração de esquema. Como `backend/models.py` e `backend/routes/auth_routes.py` são tocados, a release `develop→main` requer **Via B** (`docs/runbook-deploy-backend-via-b.md`); o frontend segue pela Vercel.
- **Rationale**: alinha com a postura de deploy do projeto (CI billing-locked) e com o Princípio VI.
