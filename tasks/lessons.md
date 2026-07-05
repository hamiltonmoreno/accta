# Lessons Learned

_Accumulated patterns from corrections. Reviewed at session start._

---

## Format
Each lesson follows this structure:
**Mistake**: What went wrong
**Rule**: The principle that prevents it
**Context**: Where this applies in the ACCTA project

---

### L1 — A connection-layer migration isn't "done" until the real connection mode is proven
**Mistake**: A migração MongoDB→Postgres (PR #30) foi dada como mergeável só
com testes mockados + CI em `localhost`; faltava negociação de TLS, logo a app
não ligava ao Supabase em ambiente nenhum (descoberto só pós-merge).
**Rule**: Para uma troca de driver/camada de ligação, antes de merge: ou se
exercita uma ligação real ao alvo exato (TLS/host/porta), ou — se inalcançável
no ambiente — a lógica de modo de ligação é desenhada e **testada
unitariamente** para esse alvo. Mock + localhost não validam o transporte.
**Context**: `backend/database.py` `_ssl_arg()`, pooler Supabase 6543.

### L2 — Nunca rebaixar uma definição de segurança explícita
**Mistake**: `sslmode=verify-ca/verify-full` colapsado para `require`; como o
kwarg `ssl=` do asyncpg sobrepõe o DSN, enfraquecia silenciosamente a
verificação de certificado (regressão P1, apanhada pelo Codex).
**Rule**: Config explícita relevante para segurança passa **verbatim**;
heurística só quando a definição está ausente. Mapear forte→fraco é sempre bug.
**Context**: `_ssl_arg()`; qualquer normalização de TLS/credenciais.

### L3 — Verificar a identidade do projeto antes de escrever via MCP de infra
**Mistake**: O MCP Supabase desta sessão estava ligado a outro projeto
(`rqplobwsdbceuqhjywgt`/"fiskix"), não ao accta (`wudxceylvnnvglmfzzgi`);
aplicar o schema via MCP teria atingido a base errada.
**Rule**: Antes de qualquer DDL/escrita via MCP de infraestrutura, confirmar
que o projeto-alvo (ref/host) corresponde ao que o utilizador indicou. Não
assumir que o MCP aponta para "o" projeto.
**Context**: MCP Supabase em contas multi-projeto; `apply_migration`.

### L4 — No sandbox web, egress não-HTTP(S) costuma estar bloqueado
**Mistake**: Assumi que dava para validar a DB ao vivo a partir do sandbox; a
política de rede dropa portas Postgres (5432/6543) — só 443 passa.
**Rule**: No ambiente remoto/web, tratar egress fora de 443 (sobretudo portas
de DB) como provavelmente bloqueado; planear validação via CI/host de deploy,
ou desenhar+testar a lógica em vez de esperar ligação ao vivo.
**Context**: Claude Code on the web; validação de `DATABASE_URL` Supabase.

### L5 — Cor da logomarca ≠ cor base da UI (acento único, fundação neutra)
**Mistake**: A paleta foi montada usando Carmesim `#C7202F` (cor da logo) como
cor predominante: todos os botões vermelhos (sem hierarquia) e texto vermelho
sobre fundo escuro (~2:1, reprova WCAG, ilegível).
**Rule**: Cor de marca saturada = **acento único e contido**, não a cor padrão.
Fundação neutra (branco/`#F5F5F5`/Grafite) carrega ~90% da UI; o acento entra
só no 1 botão primário por tela, estado ativo, links em branco e ação
destrutiva. **Nunca** texto vermelho em fundo escuro/colorido. Validar todo par
texto/fundo a ≥4.5:1 e fundamentar em regra de design (engine `ui-ux-pro-max`
→ Swiss Modernism AAA, contraste, foco visível), não em instinto.
**Context**: Reescrita do design system ACCTA; `frontend-design/SKILL.md`
(canônico) + sincronização do Brand Lock/CSVs da `ui-ux-pro-max`.

### L6 — Backtick em mensagem de commit via Bash = substituição de comando
**Mistake**: `git commit -m "... \`a{color}\` ..."` na ferramenta Bash: o
bash interpretou os backticks como command substitution (`a{color}: command
not found`), apagando essa parte da mensagem; foi preciso `--amend`.
**Rule**: Mensagens de commit multi-linha ou com caracteres especiais
(backtick, `$`, `!`) passam **sempre** por here-doc com delimitador entre
aspas: `git commit -F - <<'EOF' … EOF`. Nunca `-m` com backticks no shell.
**Context**: Qualquer commit via Bash tool (PowerShell/bash) nesta repo.

### L7 — Remapear token legado exige classificar o PAPEL, não só o nome
**Mistake**: Na limpeza Aero-Swiss, o map mecânico `amber → warning` do
SKILL atingiu `PublicLayout` footer (slogan em ouro decorativo sobre
`bg-grafite`): `text-amber` virou `text-[#B45309]` — warning-on-dark, o
mesmo defeito de legibilidade que a migração visa eliminar.
**Rule**: Ao migrar um token de identidade legado, classificar cada uso
pelo **papel** (semântico vs decorativo vs sobre-escuro) antes de aplicar
o mapeamento semântico. Ouro decorativo ≠ estado de aviso; sobre fundo
escuro o destino é `text-white`/neutro claro, não o `-700` semântico.
**Context**: `tasks/frontend-redesign-spec.md` Fase 4; qualquer remoção
de token com `mapeamento de uso antes de remover`.

### L8 — Nunca editar source-of-truth de design autonomamente
**Mistake**: Durante a Fase 0 da `frontend-consistency-spec.md`, ao
resolver a divergência entre `.card-technical=rounded-xl` (12px) no CSS
e `Cards: rounded-lg (8px)` no §Components do SKILL, tentei editar
`.claude/skills/frontend-design/SKILL.md` autonomamente para alinhar o
texto. O utilizador rejeitou a tool-call e disse "continue", obrigando
a reconciliar **só** code-side e a sinalizar a nota de doc para o dono.
**Rule**: Os ficheiros canónicos de design (`.claude/skills/**/SKILL.md`
e, por extensão, `.claude/rules/*`, `design_guidelines.json`) só são
editados pelo dono. Em conflito: reconciliar code-side a favor do que
está no canónico (ou da decisão explicitamente registada), e **sinalizar
a nota de doc para o dono** em vez de re-escrever a fonte. O canónico
ganha por defeito; código segue, doc não muda sem owner.
**Context**: Qualquer fase de qualquer spec que toque sistema de design.
Memória pessoal `no-autonomous-skill-edits.md` reforça esta regra.

### L9 — Modal aninhado: migrar de dentro para fora (Radix `modal=true`)
**Mistake**: Na Fase 6 da `frontend-consistency-spec.md`, o
`AdminUsuariosPage` tem o delete-confirm a ser aberto **a partir do
rodapé do edit-modal**. A ordem natural da listagem do utilizador era
"edit + invite + delete". Migrar o edit primeiro para Radix Dialog
tornaria o delete (ainda hand-rolled, `position: fixed` z-[60])
**não-clicável** no estado intermédio, porque Radix Dialog com
`modal=true` (default) aplica `pointer-events: none` em tudo fora do
seu portal — qualquer descendente do body (incluindo um fixed sibling)
herda e fica inerte.
**Rule**: Quando o modal A abre o modal B a partir de dentro, **migrar
B (interno) ANTES de A (externo)**. Cada commit deixa estado funcional:
B-Radix sobre A-hand-rolled funciona (A fica inerte por baixo de B,
comportamento desejado); depois A-Radix sobre B-Radix é nested-dialog
oficialmente suportado. O oposto produz um estado intermédio partido
no meio da revisão.
**Context**: Qualquer migração faseada de modais hand-rolled → Radix
Dialog/AlertDialog. Aplica-se também a Drawers e Sheets do Radix.

### L10 — Subagent fan-out para edição mecânica multi-ficheiro
**Mistake**: Fase 7.1 (substituir 97 inline `style={{ color: 'var(--text-X)' }}`
por classes Tailwind em 8 ficheiros) seria sequencialmente 8× Read + 97× Edit
no main agent — custo de tokens e duração proibitivos para trabalho
puramente mecânico.
**Rule**: Para edição mecânica idempotente em N ficheiros disjuntos
(mapeamento determinístico, sem decisões UX): fan-out via subagents
`general-purpose` em paralelo, **balanceados por ocorrências** (não por
ficheiros). Cada subagent recebe: lista exata de ficheiros, regra de
substituição literal (com tabela de mapeamento), scope estrito do que
NÃO tocar, regras de merge de className (string vs template literal),
e instruções para NÃO correr eslint/build/git/commit — esses gates são
do orquestrador. Pede relatório por ficheiro (contagem + grep
acceptance) para verificação cruzada. Casos exóticos (ex.: ternários
`style={cond ? {...} : undefined}`) ficam fora do regex literal e são
sinalizados como resíduos para owner — não tentar inferi-los.
**Context**: `tasks/frontend-consistency-spec.md` Fase 7.1 (4 subagents,
97/97 substituições, 6 resíduos ternários documentados).

### L11 — Confirmar "Decisões a confirmar" da spec antes de implementar
**Mistake**: Em `spec-correcoes`, comecei a implementar o item B15 (subir o
mínimo de password de 6 → 8) sem confirmar as "Decisões a confirmar" do topo
da spec. O dono já tinha decidido que o mínimo fica em **6** — a mudança teve
de ser revertida (backend `models.py` + zod `authSchemas.js` + test +
placeholders dos 2 forms).
**Rule**: Blocos "Decisões a confirmar antes da Fase 1" são **gates**.
Confirmar com o dono antes de mexer nos itens afetados, mesmo que pareçam
higiene trivial — sobretudo quando alteram um valor/política já decidido. Não
assumir que a "Proposta/Recomendação" da spec está aprovada. (Memória:
`password-min-6-owner-decision`, `confirm-spec-decisoes-before-implementing`.)
**Context**: utilizador: "já tínhamos decidido que a password poderia ser
mínimo 6". spec-correcoes está, de resto, ~toda implementada (Fases 1-3 feitas
em código; B17 adiado por design; Fase 5 = épico separado).

### L12 — Testar IDOR é provar divulgação cruzada, não só o 403 do não-dono
**Mistake**: No F0 de segurança (PR #119), o teste IDOR de milestone cobria
apenas "não-gestor → 403 no DELETE" e declarei "0 achados". Faltava o caso
real, apanhado por um revisor: `update_milestone` (PATCH) autoriza pelo projeto
da URL mas **relê o resultado só por `id`** (sem `project_id`) — um gestor do
projeto B obtinha o milestone do projeto A. Endpoint análogo `update_task` já
estava correto (lê o filho escopado + 404 antes do update); `update_milestone`
não tinha esse check.
**Rule**: Para cada endpoint que autoriza por um **pai** (ex. `project_id` da
URL) mas opera sobre um **filho** (`milestone_id`/`task_id`/…), o teste IDOR
tem de cobrir o caso **cross-parent de LEITURA/escrita** (B↛filho-de-A), não só
o 403 do não-autorizado. E qualquer re-leitura/`find_one` pós-update tem de
ficar **escopada pelo pai** (`{"id": child, "project_id": parent}`) + 404, igual
ao update/delete. Um teste verde prova só o que afirma — "0 achados" exige que
a matriz de casos esteja completa, não que os testes existentes passem.
**Context**: `backend/routes/projects.py::update_milestone` (corrigido);
`test_idor.py::test_update_milestone_no_cross_project_disclosure`. Auditar o
padrão "authz no pai + re-read do filho por id só" noutros routers.

### L13 — "Obrigatório" e "segredo" têm de ser garantidos no servidor, não no modelo/UI
**Mistake**: No F2 MFA (PR #120), uma revisão apanhou 4 falhas que escaparam à
implementação E à 1ª revisão: (1) MFA "obrigatório" era só uma flag
`mfa_setup_required` no `Token` que o cliente podia ignorar — o backend emitia
JWT normal e `get_current_user` aceitava-o → enforcement inexistente; (2) os
campos secretos novos (`mfa_secret`/`mfa_pending_secret`/`mfa_backup_codes`)
eram removidos só na resposta de login (+`extra="ignore"` no `User`), mas
`GET /users/{id}`/`PATCH` devolvem o **doc cru** com projeção que só excluía
`password` → vazavam; (3) backup codes com 32 bits; (4) consumo de backup code
não-atómico (read-then-`$set` → aceita o mesmo código em logins concorrentes).
**Rule**:
- **"Obrigatório"/"mandatory" impõe-se no servidor**, nunca por flag de UI: ex.
  sessão limitada via claim no token (`mfa_pending`) verificada na dependência
  central de auth contra uma allowlist de endpoints de enrolment. Uma flag que o
  cliente lê ≠ enforcement.
- **Campo secreto novo = excluí-lo em TODAS as projeções de utilizador** (uma
  constante partilhada, ex. `models.MFA_SECRET_FIELDS`) ou `response_model`
  consistente. O `pop()` numa rota + `extra="ignore"` não chega: rotas que
  devolvem o doc cru contornam o modelo. Auditar TODAS as leituras de `db.users`
  devolvidas ao cliente.
- **Credencial de uso único consome-se atomicamente** (`$pull` condicional +
  `modified_count==1`), nunca read-then-write. Segredos/códigos ≥80 bits
  (`secrets`).
- **A revisão de auth tem de ser adversarial**: procurar caminhos de auth
  alternativos (`get_user_from_token`/`get_optional_user`/SSE) e fugas residuais
  noutros routers — não só o ficheiro do diff.
**Context**: `spec-mfa-f2`, PR #120; `auth.py::MFA_PENDING_ALLOWED_PATHS` +
gate em `get_current_user`; `models.MFA_SECRET_FIELDS`; `$pull` atómico em
`auth_routes.py::login`. Itens menores diferidos p/ F3: SSE/`get_user_from_token`
não honram `mfa_pending`; audit sem IP/UA em verify/disable; lockout
partilhado password↔OTP.

---

### L14 — Nunca `git reset --hard` com alterações não-committadas presentes
**Mistake**: Para basear um novo ramo no `origin/develop` atualizado, corri
`git reset --hard origin/develop` enquanto o working tree tinha modificações
não-committadas alheias à tarefa (`FontesOficiais.jsx`, `settings.local.json`).
O reset apagou-as do working tree. Como nunca foram `git add`, não havia blob
em git e não eram recuperáveis por `fsck`/`reflog` (recuperadas, por sorte, do
histórico local do VS Code — e afinal eram triviais: 1 linha de indentação).
**Rule**: Antes de qualquer comando destrutivo de working tree (`reset --hard`,
`checkout -- .`, `clean -fd`), correr `git status` e tratar do que está sujo —
`git stash -u` (e dar pop no destino certo) ou commitar. Para "novo ramo a
partir do remoto", preferir `git fetch && git switch -c novo-ramo origin/develop`
(switch recusa se houver conflito) em vez de criar local e fazer `reset --hard`.
Nunca assumir que working-tree-only é recuperável: sem `add`/`stash`/commit não
existe em git.
**Context**: ACCTA, fluxo GitFlow de criar `feature/*` a partir de `develop`
quando o `develop` local está atrás do `origin/develop`. Liga a
[[git-pipe-tail-masks-exit]] e à preferência por worktrees com WIP ativo.

---

### L15 — Filtros por "órgão" resolvem para a chave canónica de `governance.py`, não para o rótulo nem para a leitura intuitiva
**Mistake**: Na spec de Comunicados Segmentados v2, artefactos iniciais usaram
um enum inválido `assembleia_geral` para o atalho de órgão e localizaram mal o
helper `members_of_orgao` (2 achados HIGH corrigidos em 161f4ac). O atalho
"Assembleia Geral" lê-se como "todo o plenário", mas a chave canónica é
`mesa_ag` e resolve só para a Mesa da AG (Presidente/VP/Secretário) — não para
todos os votantes. Também houve correção do dono na revisão do PR #302: editar/
enviar comunicado tinha de ser trancado a autor-ou-admin (IDOR, b29d180).
**Rule**: Antes de escrever qualquer filtro/enum de órgão ou cargo, ler
`backend/governance.py` (fonte de verdade) e usar a **chave canónica** exata
(`mesa_ag`, `direcao`, `conselho_fiscal` — nunca `assembleia_geral` nem o
rótulo). Documentar na spec que "Assembleia Geral" como atalho = Mesa da AG; o
plenário pede `categorias`/`statuses`. Em rotas que editam/enviam recursos com
dono, validar ownership (autor-ou-admin) — não basta o RBAC de papel.
**Context**: ACCTA, módulo de comunicados e qualquer feature que filtre por
órgãos/cargos. Liga a [[governanca-estatutaria-state]] e
[[comunicados-segmentados-spec-state]].

---

### L16 — Fechar uma escalada de privilégios num endpoint = fechá-la em TODOS os irmãos que escrevem o mesmo campo
**Mistake**: Na spec 018, o fix W1 (`ddd902d`) fechou a auto-promoção via
`manage_users` **só** em `PATCH /users` (`admin_update_user`), mas
`promote_user`/`demote_user`/`transfer_cargo_endpoint` (`routes/admin.py`)
gravam `role`/`privileges` do corpo e continuavam guardados só por
`_require_manage_users` (admin OU manage_users). Um detentor de `manage_users`
(seed «Financeiro»/Secretário D3) chamava `transfer` com `to_user_id=próprio,
role=admin` → tornava-se admin, contornando exatamente a invariante que o W1 e a
D3 dizem proteger. A spec ainda **agravou** o alcance ao criar (seed+migração)
uma população não-admin com `manage_users`. Apanhado em revisão adversarial, não
pelo W1.
**Rule**: Ao corrigir uma escalada por uma capacidade partilhada (aqui:
escrever `role`/`privileges`), fazer `grep` de **todos** os endpoints que
escrevem esse campo e aplicar o guard onde **todos** os caminhos passam — não só
o do ticket. O fix root-cause é um guard partilhado, não um remendo por rota. Se
uma decisão (D3) cria uma nova população com um privilégio, reavaliar **todos**
os pontos que esse privilégio agora desbloqueia.
**Context**: `routes/admin.py` mutação de cargo → `_require_cargo_admin`
(admin-only; leituras ficam em `_require_manage_users`). Liga a
[[consolidacao-acessos-spec-state]].

---

## Ranking: posição de exibição é CONTÍNUA, não o rank do servidor (2026-06-26)

**Correção do dono** (spec 006): ao mostrar a lista do ranking, NÃO usar
`entry.rank` diretamente — o backend usa *competition ranking* com empates
(pontuações iguais → 4, 4, 4, …). O dono quer numeração **contínua e a negrito**
(1, 2, 3, 4, 5, 6…) com a posição de cada sócio na lista ordenada.

**Regra**: a lista vem ordenada por `rank` asc, por isso a posição de exibição =
índice na lista + 1 (mapa `user_id → posição`). Aplicar de forma consistente no
pódio, na tabela, no widget do dashboard E na caixa "A minha posição" (`#N de M`),
para não haver inconsistência entre um sócio empatado a ver "#4" na sua caixa e
"5" na tabela. `RankBadge` recebe a posição contínua, não o rank.
