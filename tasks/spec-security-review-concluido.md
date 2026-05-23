# SPEC — Correções do Security Review (branch `develop`, 2026-05-23)

_Especificação de execução para os achados da revisão de segurança do branch `develop` (PR de integração governança/participação/banners/marca)._
_Origem: `/security-review` — 1 subagente de identificação + verificação cruzada do diff completo (786 KB)._

> **Resultado da revisão**: **0 vulnerabilidades HIGH ou MEDIUM** introduzidas por este branch.
> Pelo contrário, o branch é **líquido positivo** em segurança (ver Apêndice B). Restava **1 item LOW** de
> _hardening_ (auto-edição de licença), abaixo do limiar de reporte.
>
> **➤ ESTADO: CONCLUÍDO SEM ALTERAÇÕES DE CÓDIGO.** Decisão do dono em **D1 = Opção B** (2026-05-23):
> a licença é **dado declarativo do sócio** (auto-reportado), por design auto-editável. A revisão já
> confirmara que não há caminho de exploração (o validador público não expõe `license_*`). Nada a fazer
> no código; este spec fica como registo de auditoria.
> **Restrição**: app ainda **não em produção** → sem migração de dados / downtime. Sem mudança de schema.
> **Regras do projeto**: PT em texto de utilizador; Pydantic em todo body; `async/await`; audit log em ação
> admin; nunca expor `password`; `pytest` verde antes de "done".

---

## Decisões a confirmar antes da Fase 1 (gates)

- [x] **D1 — Auto-edição da licença profissional** → **RESOLVIDO: Opção B** (dono, 2026-05-23): licença é
  dado **declarativo do sócio**, fica auto-editável por design. Sem alterações de código. _Contexto abaixo._
- ~~**D1 (enunciado original)**~~: hoje o sócio pode auto-editar `license_number`,
  `license_category` e `license_expiry_date` via `PATCH /users/me/profile`, porque estes campos vivem na
  base partilhada `_EditableProfileFields` ([models.py:192-194](../backend/models.py#L192-L194)), herdada
  tanto por `UserProfileUpdate` (auto-serviço) como por `UserAdminUpdate` (admin).
  **Pergunta ao dono**: a licença é um dado **institucional/verificável** (a associação atesta a inscrição
  e a categoria profissional) ou um dado **declarativo do sócio** (auto-reportado, sem valor de prova)?
  - **Opção A (recomendada — tratar como credencial institucional)**: tornar os 3 campos de licença
    **só-admin** (saem do auto-serviço; continuam editáveis em `PATCH /users/{id}` por admin e no convite).
  - **Opção B (manter declarativo)**: deixar como está e **fechar este spec sem alterações de código**
    (a revisão confirmou que não há caminho de exploração — ver Nota de risco).
  - **Nota de risco (porque é LOW, não HIGH/MEDIUM)**: o validador público da carteira
    (`validate_wallet` em `routes/stats.py`) expõe apenas `name`, `member_id`, `status` e `admission_date`
    — **nunca** `license_*`. Logo **não há forja explorável** via validador hoje. O risco é de
    **integridade/confiança** (um sócio afirmar uma categoria de licença que não detém) caso esses campos
    venham a ser exibidos publicamente ou usados para elegibilidade no futuro.

> **D1 ficou em Opção B** → não há trabalho de código; o spec está concluído. A Fase 1 abaixo
> **NÃO se aplica** e fica registada apenas como referência caso a decisão venha a ser revista no futuro.

---

## Fase 1 — 🟢 LOW (hardening / menor privilégio) — ❌ NÃO APLICÁVEL (D1 = Opção B)

> _Mantida só para referência futura. Não implementar enquanto D1 = Opção B._

### S1 — Campos de licença auto-editáveis pelo sócio
- **Achado** (security-review, severidade LOW / informativo): `license_number`, `license_category`,
  `license_expiry_date` estão em `_EditableProfileFields`, pelo que `UserProfileUpdate` (auto-serviço) os
  expõe. Um sócio pode definir/alterar a sua própria credencial profissional sem passar por admin.
- **Causa raiz**: os 3 campos de licença foram colocados na base partilhada por conveniência, misturando
  **dados pessoais que o sócio legitimamente possui** (`profession`, `employer`, contacto, morada, emergência)
  com **credencial institucional** (licença).
- **Solução** (elegante, segue o split que `UserAdminUpdate` já faz para `email`/`role`/`status`/`privileges`):
  mover **apenas** os 3 campos de licença e o seu `field_validator` de `_EditableProfileFields` para
  `UserAdminUpdate` (e mantê-los já presentes em `InviteCreate`, onde admin define no convite —
  [models.py:258](../backend/models.py#L258)). `profession`/`employer` **permanecem** auto-editáveis.
  - `_EditableProfileFields`: remover `license_number`, `license_category`, `license_expiry_date` e o
    `_v_license_expiry`.
  - `UserAdminUpdate`: acrescentar os 3 campos + o validador de data de validade.
  - **Defesa em profundidade**: `update_own_profile` já filtra por modelo (Pydantic ignora campos
    desconhecidos por omissão), mas confirmar `model_config` — se houver `extra="forbid"`, enviar
    `license_*` passa a dar `422` (bónus); se for o default, é silenciosamente ignorado (suficiente).
- **Arquivos**: [backend/models.py](../backend/models.py) (`_EditableProfileFields`, `UserAdminUpdate`).
  Nenhuma alteração de schema, de rota ou de frontend obrigatória — o formulário de perfil deixa de
  enviar licença (verificar `PerfilPage.js`; se mostrar esses campos, torná-los só-leitura para o sócio).
- **Aceitação**:
  - `PATCH /users/me/profile` com `{"license_number": "X"}` → campo **não** é persistido (ignorado/`422`).
  - `PATCH /users/{id}` (admin) com `license_*` → continua a persistir; audit log gerado.
  - Convite (`InviteCreate`) continua a aceitar `license_number`.
  - `profession`/`employer` continuam auto-editáveis pelo sócio.
- **Testes** ([backend/tests/test_users_routes.py](../backend/tests/test_users_routes.py)):
  - sócio tenta auto-editar `license_number` → valor inalterado na resposta;
  - admin edita `license_category` de outro user → persiste;
  - regressão: sócio auto-edita `profession` → persiste (não partir o caminho legítimo).
- **Risco/dep**: depende de **D1 = Opção A**. Toca 1 ficheiro de modelos + 1 de testes (≤2 ficheiros) →
  cabe num único PR pequeno para `develop` (GitFlow: `fix/security-review-license-fields`).

---

## Apêndice A — Verificado SEGURO (sem ação; registo para auditoria)

A revisão confirmou que **não** existem estas classes de vulnerabilidade no diff:

- **SQL injection**: o único SQL bruto novo (`register_event_attendee`, `database.py`) é totalmente
  parametrizado (`*wb.params`, `UPDATE … SET doc=$1 WHERE pk=$2`), identificador de tabela hardcoded.
- **NoSQL/regex injection**: pesquisa de posts faz `re.escape(q)` antes de `$regex`.
- **XSS**: nenhum `dangerouslySetInnerHTML` no diff; conteúdo de artigos/posts renderiza como texto (React
  auto-escapa).
- **Mass-assignment / escalada de privilégios**: `UserProfileUpdate` omite `role`/`status`/`privileges`/
  `member_id`/`account_type`/`cargo` — sócio não escala via auto-serviço.
- **RBAC / IDOR**: toda rota de escrita nova (`participacao.py`, `banners.py`, `brand.py`, novas categorias
  de `upload.py`) tem verificação de role/elegibilidade; patrocínios estão scoped a
  `sponsor_user_id == current_user.id`.
- **Voto secreto**: cédulas de eleição usam recibos HMAC-SHA256 (chaveados por `SECRET_KEY`), em coleção
  separada das cédulas; apuração de honorário lê só `vote_option` (nunca `user_id`); assinaturas de petição
  não são enumeráveis por signatário.
- **Aleatoriedade criptográfica**: tokens de convite/honorário usam `secrets.token_urlsafe(32)` (CSPRNG).
- **Segredos**: sem credenciais/chaves/tokens hardcoded nos scripts de seed nem nas rotas modificadas.

## Apêndice B — Melhorias de segurança já incluídas neste branch (sem ação)

- `is_token_revoked(None)` passa a devolver `True` (tokens sem `jti` tratados como revogados).
- Stream SSE de notificações **removeu** o vetor de fuga via query-param `?token=`.
- `get_poll_results` bloqueia apurações parciais antes do fecho para não-admins; votação exige
  `is_voting_member`.
- Nova projeção `SENSITIVE_PROFILE_FIELDS` **reduz** exposição de PII nas listagens de utilizadores.
- `upload.py` deixou de devolver `str(e)` em respostas 500.

---

## Review (concluído 2026-05-23)

- [x] D1 confirmado pelo dono: **Opção B** — licença é dado declarativo do sócio, auto-edição mantida por design.
- [x] S1 **não aplicável** (decorre de D1 = A). Sem alterações de código.
- [x] Sem PR — nenhuma mudança de código resultou da revisão.
- [x] Apêndices A/B revistos — nenhuma ação adicional necessária.
- **Conclusão**: security-review fechado com **0 achados HIGH/MEDIUM** e o único item LOW resolvido por
  decisão de produto (não é vulnerabilidade). Branch `develop` segue sem dívida de segurança aberta.
