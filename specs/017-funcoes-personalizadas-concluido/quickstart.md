# Quickstart — Validação da feature 017 (Funções personalizadas)

Guia de validação end-to-end. Contratos em [contracts/custom-roles-api.md](contracts/custom-roles-api.md); modelo de dados em [data-model.md](data-model.md).

## Pré-requisitos

```bash
# Backend (porta 8001, com Postgres acessível — ver memória local-dev-run)
cd backend && uvicorn server:app --reload --port 8001

# Frontend
cd frontend && yarn start
```

Login como admin (dev: `dev@accta.cv`).

## Testes automatizados

```bash
cd backend && pytest tests/test_custom_roles.py   # novo ficheiro da feature
cd backend && pytest -m unit                      # suíte completa (regressão)
cd backend && ruff check .
cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60
cd frontend && yarn build                         # craco build tem de passar
```

Nota `conftest.py`: `custom_roles` NÃO está pré-wired no `mock_db` — ligar em-teste (`mock_db.custom_roles = MagicMock(...)` com `find_one`/`find`/`update_many` `AsyncMock`s).

## Cenários manuais (navegador, Princípio VII — dono)

1. **US1 — criar/gerir**: Utilizadores → «Funções personalizadas» → criar «Coordenador de Eventos» com 2 privilégios → aparece na lista com rótulos PT e contagem 0. Criar duplicado → recusa clara. As 4 funções fixas não aparecem como editáveis/elimináveis.
2. **US2 — aplicar**: editar um sócio → seletor «Função no Sistema» mostra grupo «Funções personalizadas» → escolher a função → checkboxes de privilégios ficam read-only com os da função → guardar. Iniciar sessão como esse sócio → menu mostra Eventos/Documentos geríveis e nada mais além do portal de sócio.
3. **Ligação viva (Q1)**: editar a função e retirar `manage_documents` → o sócio (refresh) perde o acesso a gerir documentos sem qualquer edição individual; recebe notificação «Perfil Atualizado».
4. **US3 — ciclo de vida**: com a função aplicada a 2 sócios, listagem mostra «2»; eliminar → recusa 409 com contagem; retirar dos 2 → eliminar com sucesso.
5. **Destaque**: a um sócio com função personalizada, atribuir função fixa «Financeiro» → `custom_role_id` limpo (a contagem da função desce). Usar «Aplicar predefinições do cargo» num sócio com função personalizada → aviso prévio; ao confirmar, substitui pela predefinição do cargo.
6. **Auditoria**: Registo de Auditoria mostra `custom_role_created/updated/deleted` e o before/after da atribuição.

## Resultados esperados (Success Criteria)

- SC-001: definir 1× e aplicar a 5 sócios em <2 min, sem marcar privilégios individualmente.
- SC-002: nenhum utilizador das 4 funções fixas perde/ganha acesso sem ação do admin (suíte unit verde = guarda de regressão).
- SC-003: 100% das operações auditadas.
- SC-004: menu do sócio reflete exatamente os privilégios da função.
- SC-005: eliminação em uso impossível (409 sempre).
