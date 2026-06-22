# Contrato: Atos de co-aprovação (vínculo a projeto)

Prefixo: `/api/atos`. Guards inalterados (`_require_execute` para executar; criação por Direção/admin).

## POST `/atos` — `project_id` opcional (NOVO campo)

`AtoCreate` ganha `project_id: Optional[str] = None`. Permite criar um Ato de pagamento já associado a um projeto (caminho disparado quando uma despesa de projeto excede o limiar).

```json
{
  "tipo": "pagamento",
  "descricao": "Aluguer de sala (projeto Workshop CTA)",
  "valor": 80000,
  "project_id": "proj-123"        // NOVO, opcional
}
```

Regras de assinatura (Art. 54) **inalteradas** (`atos_rules.py`): 2 da Direção + Presidente + Tesoureiro para pagamento.

## POST `/atos/{ato_id}/executar` — propaga `project_id`

`execute_ato` (`atos.py:197`) inalterado nas validações (tipo=pagamento, status=aprovado, sem `transaction_id`, valor>0). **Mudança**: a `Transaction` criada passa a incluir `project_id=ato.get("project_id")`:

```python
transaction = Transaction(
    type="despesa", category=category, description=..., amount=valor, date=date,
    reference=data.reference, ato_id=ato_id,
    project_id=ato.get("project_id"),     # NOVO
    created_by=current_user.id,
)
```

**Efeito**: a despesa fica ligada a Ato **e** projeto; conta para o `spent` do projeto e para o caixa.

**Acceptance**: US2 cenário 2.
