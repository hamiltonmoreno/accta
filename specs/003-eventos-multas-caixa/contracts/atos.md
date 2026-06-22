# Contrato: Atos (vínculo a evento)

Prefixo: `/api/atos`. Guards inalterados.

## POST `/atos` — `event_id` opcional (NOVO)

`AtoCreate` ganha `event_id: Optional[str] = None` (a par de `project_id` da ronda 1). Permite criar um Ato de pagamento já associado a um evento (caminho disparado quando uma despesa de evento excede o limiar).

```json
{ "tipo": "pagamento", "descricao": "Catering (Evento X)", "valor": 70000, "event_id": "evt-1" }
```

Regras de assinatura (Art. 54) inalteradas.

## POST `/atos/{ato_id}/executar` — propaga `event_id`

`execute_ato` (`atos.py:197`) passa a incluir `event_id=ato.get("event_id")` na `Transaction` criada (a par de `project_id`):

```python
transaction = Transaction(
    type="despesa", category=category, description=..., amount=valor, date=date,
    reference=data.reference, ato_id=ato_id,
    project_id=ato.get("project_id"),
    event_id=ato.get("event_id"),     # NOVO
    created_by=current_user.id,
)
```

**Efeito**: despesa ligada a Ato **e** evento; conta para o resultado do evento. **Acceptance**: US3 #2.
