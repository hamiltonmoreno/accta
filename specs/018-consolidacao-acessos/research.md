# Research — Consolidação do modelo de acessos (spec 018)

**Date**: 2026-07-03 · Decisões do dono D1–D7 já confirmadas no spec.md; este documento
resolve as incógnitas técnicas do plano.

## R1 — Inventário das superfícies com role antigo (facto, medido no código)

**Backend** (grep 2026-07-03):
- Checks canónicos `has_role_or_privilege(user, roles, priv)` (`auth.py:76`) — maioria dos
  módulos: users, events, benefits, gallery, wall, comunicados, notifications (audit),
  documents (à mão em `documents.py:19`), finances (helpers próprios `can_view_finances`/
  `can_manage_finances` em `auth.py:82-95`).
- `permissions.user_can` (2 usos: ranking, regulamentos) — duplicado de conceito.
- ~28 checks inline `role == "admin"` / `role in (...)` espalhados (projects, participacao,
  prestacao_contas, eleicoes, atos, users, regulamentos, posts, events, upload, sancoes,
  report, …).
- `helpers._ELEVATED_ROLES = {admin, financeiro, moderador}` (alerta de escalada §8.2.c).
- `routes/admin.py` invite valida `role in ("admin","socio","financeiro","moderador")` (422).
- `governance.py` CARGOS defaults: dir_tesoureiro→financeiro, dir_vogal→moderador,
  dir_presidente/vice/secretario→admin.

**Frontend**:
- `contexts/AuthContext.js` — deriva `canManageFinances` (`role==='financeiro' OU priv`),
  `isFinanceiro`, `isModerador`, `can(p)`, `hasPrivilege(p)`.
- `lib/nav/visibility.js` + `layouts/PrivateLayout.js` — menu por roles.
- `App.js` `ProtectedRoute` — já suporta `allowedRoles` + `allowedPrivileges` (3 rotas usam
  financeiro/moderador em allowedRoles).
- `usuarios/tokens.js` `ROLES`, `lib/cargoLabels.js` `ROLE_LABELS`, FiltersBar (filtro por
  role), páginas pontuais (Mural, Notificações, AdminPedidosInscricao, AdminCargos).
- Conteúdo de Ajuda (`content/ajuda/*.js`) menciona os perfis — texto, não lógica.

## R2 — Sessões durante a migração

**Decision**: nada a fazer. `auth.get_current_user` relê o doc do utilizador a cada pedido
(`auth.py:204`) — quando a migração muda `role`/`privileges`/`custom_role_id`, o pedido
seguinte já vê o estado novo. Sem invalidação de tokens, sem janela stale.
**Alternatives**: revogação forçada de sessões — desnecessária (o acesso efetivo é
equivalente por SC-001; ninguém perde nem ganha nada a meio).

## R3 — Regra de migração para utilizadores com privilégios manuais extra

**Problema**: a semântica da spec 017 é «privilégios do holder = exatamente os da função»
(a propagação sobrescreve). Um financeiro que também tenha, p.ex., `manage_events` manual
perderia esse extra na primeira propagação da função seed.
**Decision**: regra de migração por utilizador:
- `privileges_atuais ⊆ privilégios_da_seed` → migra para **função seed** (caso normal).
- caso contrário → migra para **privilégios diretos** = união(atuais, equivalentes da seed),
  sem `custom_role_id` (preserva o extra; SC-001 mantém-se).
**Rationale**: não violar o invariante de propagação da 017; equivalência exata primeiro.
**Alternatives**: (a) anexar função + manter extras — quebra a ligação viva; (b) alargar a
seed — daria o extra a todos os financeiros. Rejeitadas.

## R4 — Conteúdo das funções seed (equivalência exata)

**Decision** (deriva dos checks reais, não dos labels):
- Seed **«Financeiro»**: `manage_finances` + `manage_users` (o role financeiro passa hoje no
  gate `users.py:65` de listagem de utilizadores — sem `manage_users` perderia essa listagem,
  violando SC-001). *Confirmar no plano da F2 com a matriz de equivalência da F1 — se a F1
  provar que financeiro só passa em `manage_finances`, a seed reduz-se a isso.*
- Seed **«Moderador»**: `moderate_content` (+ `manage_users` só se a matriz da F1 provar o
  gate `users.py:313` como acesso real usado — mesmo critério).
**Rationale**: a fonte da equivalência é a matriz gerada na Fase 1, não a intuição; a lista
final das seeds é um output da F1.

## R5 — Nomes reservados vs funções seed («Financeiro»/«Moderador»)

**Decision**: a migração cria as seeds diretamente na coleção (script, não via API) — o
`_RESERVED_NAMES` de `routes/custom_roles.py` não se aplica a inserções do script. Após a
migração, remover `financeiro`/`moderador` de `_RESERVED_NAMES` (a unicidade normal passa a
proteger os nomes, porque as seeds existem); `admin`/`socio` continuam reservados.
**Rationale**: reserva existia para evitar confusão com níveis fixos; esses níveis deixam de
existir.

## R6 — Mecânica da transição da API (D4)

**Decision**: release de transição (F2): `_LEGACY_ROLE_MAP = {"financeiro": seed_fin,
"moderador": seed_mod}` aplicado nas 2 superfícies de escrita de role (PATCH /users e
POST /admin/invite) — traduz para socio + função seed, auditado com nota
`legacy_role_translated`. Release seguinte (spec futura, 1 linha): remover o mapa → cai no
422/400 normal. Registo/auto-registo não aceita roles (sempre socio) — fora de âmbito.
**Rationale**: 2 pontos de escrita apenas; o resto do sistema nunca escreve roles legados
depois de os defaults de cargo serem reescritos (R7).

## R7 — Defaults de cargo (D3) e quem escreve role

**Decision**: `governance.py` CARGOS passa a: presidente/vice `role="admin"` (mantêm);
dir_secretario `role="socio"` + privilégios granulares atuais (lista exata =
`["manage_users","manage_events","manage_documents","moderate_content"]`, a validar com o
dono no PR); dir_tesoureiro e dir_vogal `role="socio"` + privilégios atuais. Escritores de
role no sistema: promote/demote/transfer (`admin.py`), proclamação (`eleicoes.py`), botão
«Aplicar predefinições» (via PATCH) — todos leem os defaults de governance ⇒ 1 só ficheiro
a mudar para parar de escrever roles legados.
**Rationale**: cargos deixam de conceder role elevado exceto Presidente/Vice; privilégios
já eram granulares nos defaults.

## R8 — Redefinição do alerta de escalada (`_ELEVATED_ROLES`, FR-011)

**Decision**: substituir por `_SENSITIVE_PRIVILEGES = {manage_users, manage_finances,
view_audit_logs}` + role admin: alerta dispara quando `new_role == "admin"` (e antes não) OU
quando privilégios sensíveis novos aparecem (incl. via função personalizada). Mesma
mensagem/canal (`notify_admins`).
**Rationale**: preserva a intenção de segurança (§8.2.c) no modelo novo sem falsos negativos.

## R9 — Emenda constitucional

**Decision**: a constituição v1.0.0 fixa «Roles {admin, financeiro, moderador, socio}» em
Stack & Data Constraints — a F2 inclui PR `docs(constitution): amend to v1.1.0` (MINOR:
constraint materialmente alterada, princípios intactos) atualizando essa linha + Sync
Impact Report, reconciliado com CLAUDE.md/rules na mesma release (procedimento de
Governance da própria constituição).

## R10 — Estratégia de testes de equivalência (F1, gate da F2)

**Decision**: novo `tests/test_access_matrix.py` (unit, mock_db): para cada módulo da tabela
canónica, constrói utilizadores-perfil (admin, financeiro, moderador, socio puro, socio+priv
relevante, socio+view_finances_readonly, técnico) e afirma o resultado do gate (allow/deny).
Gerado ANTES de tocar nos checks (F1 captura o comportamento atual = baseline); corre
inalterado depois da F1 (prova higiene sem mudança) e é ATUALIZADO deliberadamente na F2
(diffs da matriz = exatamente as mudanças decididas, mais nada).
**Rationale**: é a materialização testável de SC-001/SC-005; o diff da matriz é revisável
pelo dono.
