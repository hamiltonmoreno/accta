# Quickstart — Validação da spec 018 (consolidação de acessos)

## Pré-requisitos

Ambiente local ISOLADO (nunca o `.env` de prod — aponta ao Supabase real):

```bash
docker start accta-pg-dev   # Postgres local :5433 (já criado na sessão de 2026-07-03)
cd backend && python -m uvicorn server:app --env-file .env.dev --host 127.0.0.1 --port 8001
cd frontend && BROWSER=none npx craco start   # :3000, proxy /api → :8001
# contas: admin@dev.cv/DevAccta2026 · socio1@dev.cv, socio2@dev.cv / Socio2026
```

## Testes automatizados

```bash
cd backend && ruff check . && pytest -m unit          # suíte inteira
cd backend && pytest tests/test_access_matrix.py -q   # matriz de equivalência (F1/F2)
cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60 && yarn build
```

## Fase 1 — validação (higiene invisível)

1. **Baseline**: `test_access_matrix.py` escrito ANTES das mudanças, verde no código atual.
2. Após a unificação dos checks: a MESMA matriz continua verde sem edições (prova de
   zero mudança de comportamento) e `grep` não encontra checks inline fora do helper.
3. Smoke no navegador: admin, sócio e um sócio com privilégio granular veem exatamente
   os mesmos menus/módulos que antes.

## Fase 2 — cenários manuais (navegador, Princípio VII — dono)

1. **Migração (dry-run primeiro)**: semear 1 user role=financeiro + 1 moderador + 1
   financeiro com privilégio extra `manage_events`; `python scripts/migrate_roles_018.py`
   (dry-run → apply). Verificar: os dois primeiros ficam socio + função seed; o terceiro
   fica socio + privilégios diretos (união), sem função; audit `role_model_migrated` ×3;
   0 docs com role legado.
2. **Equivalência**: login como o ex-financeiro → vê e opera o módulo financeiro
   exatamente como antes (criar transação); ex-moderador modera mural/galeria.
3. **Seletor novo**: editar um sócio → seletor «Nível de acesso» mostra só Administrador,
   Sócio e o grupo «Funções personalizadas» (com as seeds); convite idem.
4. **Proveniência (US3)**: o modal separa «Acesso ao sistema» (privilégios com origem:
   função X / manual) de «Identidade associativa» (cargo/categoria/departamento com nota
   «não altera acessos»).
5. **Tradução API (D4)**: `PATCH /users/{id}` com `role=financeiro` → 200, user fica
   socio+seed, audit com `legacy_role_translated`; enviar role desconhecido → 400/422.
6. **Defaults de cargo (D3)**: «Aplicar predefinições» num Tesoureiro → socio +
   {manage_finances, view_audit_logs}; num Presidente → admin. Promote a dir_vogal →
   socio + privilégios (não moderador).
7. **Alerta de escalada (R8)**: dar `manage_finances` a um sócio → notificação aos
   admins; retirar → sem alerta.
8. **Auditoria**: registo mostra a migração e as traduções; histórico antigo intacto.

## Resultados esperados

- SC-001: matriz utilizador×módulo idêntica pré/pós (cenários 1–2).
- SC-002/SC-004: um só caminho de concessão + proveniência visível (cenários 3–4).
- SC-003: zero checks fora do helper (F1, via grep + review).
- SC-005: suíte completa verde.
