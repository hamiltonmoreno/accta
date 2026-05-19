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
