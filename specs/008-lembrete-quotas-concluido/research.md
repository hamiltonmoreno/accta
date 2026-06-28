# Research — Lembrete informativo de quotas

Fase 0. Decisões. Liga-se a infra existente; quase nada é novo.

---

## D1 — Ponto de integração: o gerador de quotas (orientado a evento)

**Decision**: O lembrete dispara dentro de `POST /finances/generate-quotas`, logo após
`insert_quotas_atomic`. **Substitui** o aviso genérico atual (`notify_all_active_users`,
`routes/finances.py:657`) por um **lembrete por sócio** apenas aos que receberam quota
**nova** neste run.

**Rationale**: É exatamente o evento "a quota do período foi registada" (Decisão Q1).
Sem agendador novo. O gerador já corre sob advisory lock (idempotente por mês), por isso
re-gerar o mesmo mês cria 0 quotas → 0 lembretes (FR-006 grátis).

**Alternatives considered**: Lote agendado (cron/pg_cron) — rejeitado em Q1.
Adicionar o lembrete **além** do genérico — rejeitado (duas notificações = ruído).

---

## D2 — Saber QUEM recebeu quota nova: `insert_quotas_atomic` devolve os user_ids

**Decision**: Alterar `insert_quotas_atomic(year, month, candidate_docs)` para devolver a
**lista de user_ids efetivamente inseridos** (em vez de só o `int`). O `created_count`
passa a ser `len(...)`. Único chamador: `generate-quotas` (`finances.py:645`) + testes.

**Rationale**: Notificar **só os novos** garante idempotência sem query extra de dedup
(a dedup é a própria inserção atómica). `notify_all_active_users` notificava todos
(incl. quem já tinha quota) — incorreto para "a TUA quota foi registada".

**Alternatives considered**: Marcar uma "nota de período" por sócio e verificar antes de
notificar — mais queries; redundante face à dedup da inserção.

---

## D3 — Opt-out: campo dedicado `quota_reminder_opt_out` (não reutilizar o de email)

**Decision**: Novo campo no doc `users`: `quota_reminder_opt_out: bool = False`
(aditivo, default = recebe). Surface: um 2.º toggle na secção de preferências do Perfil
(`EmailPrefs.js`). Atualização via um modelo/endpoint de preferência self-service (padrão
de `EmailPreferencesUpdate`/`comunicadosAPI.updateEmailPreferences`).

**Rationale**: O campo existente `email_opt_out_informativos` é **específico de email**
de comunicados — conflar com o canal in-app seria errado (um sócio pode querer in-app mas
não email). Campo aditivo com default não quebra docs existentes (missing → False →
recebe; **não** é STOP #5). Aplica-se a ambos os canais do lembrete (in-app e, se algum
dia ligado, email) — FR-004/FR-007.

**Alternatives considered**: Reutilizar `email_opt_out_informativos` — rejeitado (semântica
errada). Opt-in (default não recebe) — rejeitado (spec: opt-out, ativo por defeito).

---

## D4 — Total acumulado por sócio: um aggregate

**Decision**: Para os user_ids que receberam quota nova, obter o **total acumulado** com
**um** aggregate sobre `transactions` (group by `user_id`, sum `amount`, filtro
`type=receita` + `category ∈ {quotas,joias}`). O valor do período é o `quota_amount` já
conhecido no gerador.

**Rationale**: Uma query para todos os totais (não N). Coincide com o `total_pago` de
`/me/quotas` (FR-003). Para centenas de sócios é barato.

**Alternatives considered**: N queries `/me/quotas`-style — rejeitado (N+1).
Não mostrar total — rejeitado (FR-001 pede o total acumulado).

---

## D5 — Conteúdo, tom e link

**Decision**: Notificação `type="financeiro"`, **tom informativo** (transparência),
ex.: título "Quota de {Mês}/{Ano} registada"; corpo "A tua quota de {Mês}/{Ano}
({valor} CVE) foi registada e será descontada em folha. Total acumulado pago: {total}
CVE." Link **`/carteira`** (acessível ao sócio). **Proibida** linguagem de dívida/atraso.

**Rationale**: FR-002/FR-008. Corrige o link `/financeiro` (gated) do aviso atual — um
sócio clicava e era redirecionado (bug latente). `/carteira` é a "carteira" do sócio.

**Alternatives considered**: Link `/financeiro` — rejeitado (gated a admin/financeiro).

---

## D6 — Email (US3): desligado e gated (STOP)

**Decision**: O MVP é **só in-app**. O envio por email **não é construído como envio
real** sem confirmação explícita do dono (STOP #6). Se/quando ligado, fica atrás de uma
flag de configuração **off por defeito** e respeita o `quota_reminder_opt_out`.

**Rationale**: Princípio VI / Stack: enviar a utilizadores reais é condição STOP. Manter
US3 desligado evita disparar o STOP no MVP e mantém a feature entregável (US1+US2).

**Alternatives considered**: Construir o email já a enviar — rejeitado (STOP).

---

## D7 — Idempotência

**Decision**: Garantida pela **fronteira de geração**: `insert_quotas_atomic` salta quem
já tem quota do mês (advisory lock), por isso só os **novos** são notificados; re-gerar o
mês → 0 novos → 0 lembretes. Sem marcador de notificação separado.

**Rationale**: FR-006 sem estado extra. Simples e correto.

---

## Resumo de impacto

- **Backend**: `routes/finances.py` (substituir notify no gerador), `database.py`
  (`insert_quotas_atomic` devolve user_ids), `models.py` (campo + update model).
- **Frontend**: `perfil/EmailPrefs.js` (toggle) + `utils/api.js` (método de preferência).
- **Dados**: 1 campo aditivo em `users` (sem migração destrutiva). Sem deps novas.
- **Release**: toca `backend/` → **Via B**.
- **Sem decisões pendentes do dono** (email fica explicitamente gated/off).
