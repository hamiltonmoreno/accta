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
