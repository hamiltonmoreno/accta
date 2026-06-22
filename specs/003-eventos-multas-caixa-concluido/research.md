# Research & Decisions: Eventos e Multas Ligados ao Caixa

Decisões fechadas no brainstorming + verificação no código. Ancoradas no padrão da ronda 1 (spec 002).

## Decisão 1 — Vínculos novos na `Transaction`

**Decisão**: `Transaction` (`models.py:1232`) ganha `event_id: Optional[str]` e `sancao_id: Optional[str]`, aditivos-opcionais (coexistem com `project_id`/`ato_id`/`user_id`). `extra="ignore"` ⇒ não quebra docs.

**Rationale**: Fonte única; as agregações financeiras varrem `transactions` sem filtro de origem, logo despesas/receitas de evento e multas entram **automaticamente** no resumo/DRE/balancete (FR-003) a custo zero. Granularidade por domínio vem do vínculo (filtro), não de categorias.

## Decisão 2 — Eventos: despesas + receitas + resultado derivado

**Decisão**: Em `events.py`:
- `POST /events/{id}/expenses` → `Transaction(type="despesa", event_id, category default "eventos" ∈ EXPENSE_CATEGORIES)`; audit.
- `POST /events/{id}/receitas` → `Transaction(type="receita", event_id, category "extraordinarias")`; audit.
- `GET /events/{id}/expenses` e `GET /events/{id}/receitas` → `transactions.find({event_id, type})`.
- `DELETE` de cada → apaga a transação; recusa (400) se `ato_id` (reverter pelo Ato).
- `GET /events/{id}` passa a anexar `resultado_financeiro = {receitas, despesas, resultado}` por agregação; **larga o `response_model=Event`** e devolve dict enriquecido (como `get_project` faz com `spent`/`orcamento_execucao`).

**Rationale**: FR-004/005/006/009. `resultado` derivado elimina contador divergente. `get_event` (`events.py:110`) hoje usa `response_model=Event` (que com `extra="ignore"` removeria o campo novo) → larga-se o response_model estrito.

**Helper**: `_event_result(event_id)` → `{receitas, despesas, resultado}` por duas agregações `$group $sum` (ou uma com `$group` por `type`).

## Decisão 3 — Gate Art. 54 nas despesas de evento

**Decisão**: `POST /events/{id}/expenses` aplica o gate: `limiar = await coaprovacao_limiar()` (de `helpers`, #307); se `>0` e `amount>limiar` → 400 com mensagem PT a orientar para criar um Ato de pagamento com o evento. Espelha `add_expense` dos projetos.

**Rationale**: FR-007; coerência com a ronda 1 (decisão do dono confirmada para ambos os domínios).

## Decisão 4 — Ato propaga `event_id`

**Decisão**: `Ato`/`AtoCreate` (`models.py:1325`,`1349`) ganham `event_id: Optional[str]`. `execute_ato` (`atos.py:197`) copia `ato.get("event_id")` para a `Transaction` (a par de `project_id`).

**Rationale**: FR-008; despesa de evento acima do limiar fica ligada a Ato **e** evento.

## Decisão 5 — RBAC dos endpoints de evento

**Decisão**: Todos os endpoints financeiros de evento usam `has_role_or_privilege(current_user, ("admin",), "manage_events")` — o mesmo guard de `create_event`/`update_event`/`delete_event` (`events.py:123`). Audit em escritas.

**Rationale**: FR-010; quem gere o evento gere as suas finanças. (Difere dos projetos, que usam `can_manage_project`; cada domínio mantém o seu guard de gestão.)

## Decisão 6 — Guarda de eliminação de evento (409)

**Decisão**: `delete_event` (`events.py:158`) conta `transactions` com `event_id`; se `>0` → 409 (PT: remover os movimentos primeiro). Espelha `delete_project` (#C1 da ronda 1).

**Rationale**: FR-011; não deixa movimentos financeiros órfãos.

## Decisão 7 — Multas: receita idempotente ao aplicar

**Decisão**: Em `aplicar_sancao` (`sancoes.py:261`), **antes do CAS** `decidida→aplicada` (junto dos outros efeitos idempotentes), se `tipo=="multa"` e `multa_valor>0`:
```
existing = await db.transactions.find_one({"sancao_id": sancao_id, "type": "receita"})
if not existing:
    insert Transaction(type="receita", category="extraordinarias", sancao_id=sancao_id,
                       amount=multa_valor, description=f"Multa - {nome do sócio}", created_by=current_user.id)
```

**Rationale**: FR-012/013/014/015. Colocar **antes do CAS** com guarda de dedup por `sancao_id` dá exactly-once **e** re-tentabilidade (se o CAS/efeito falhar, a re-tentativa re-verifica e não duplica) — segue o mesmo princípio "efeitos idempotentes antes do CAS" já usado para perda_direitos/expulsão. Alternativa (inserir depois do CAS) rejeitada: deixava uma janela CAS-ok/insert-falha sem receita e sem re-tentativa.

## Decisão 8 — FR-016 (estorno) fora de âmbito

**Decisão**: Não implementar estorno na anulação. **Verificado**: `routes/sancoes.py` não tem qualquer transição para "anulada" (sem endpoint/handler). Sem fluxo, não há estorno. Documentado no plano; reabrir se a anulação for criada.

## Decisão 9 — Categorias: reuso de `extraordinarias`

**Decisão**: Receitas de evento e multas usam `extraordinarias`; despesas de evento usam `eventos` (default). **Sem** novas categorias.

**Rationale**: FR-017; coerente com a consolidação do dono (2026-05-21; [[finance-specs-alignment]]). Granularidade via `event_id`/`sancao_id`.

## Decisão 10 — Filtros e índices

**Decisão**: `list_transactions` (`finances.py`) ganha params `event_id` e `sancao_id`. Em `ensure_schema()`: `ix_tx_event_type (event_id, type) WHERE doc ? 'event_id'` (espelha `ix_tx_project_type`) e `ix_tx_sancao (sancao_id) WHERE doc ? 'sancao_id'` (serve filtro + a guarda de idempotência `find_one({sancao_id, type})`).

**Rationale**: FR-002 + performance da agregação de resultado e do dedup de multa.

## Decisão 11 — Migração (backfill de multas, STOP)

**Decisão**: `scripts/migrate_multas_to_transactions.py` (padrão de `migrate_project_expenses_to_transactions.py`): dry-run por defeito — lê sanções `tipo="multa"`, `status="aplicada"`, `multa_valor>0` **sem** transação `receita` com esse `sancao_id`; relatório de reconciliação; `--apply --confirm` (STOP) cria as receitas em falta. Idempotente (re-verifica `sancao_id`).

**Rationale**: FR-018. Prod provavelmente no-op (0 sanções). Eventos não têm dados a migrar.

## Decisão 12 — Modelos de request

**Decisão**: `EventExpenseCreate(description, amount>0, date?, category?)` e `EventReceitaCreate(description, amount>0, date?)` em `models.py` (espelham `ProjectExpenseCreate`).
