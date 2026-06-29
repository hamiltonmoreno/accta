# Quickstart / Validação: Pendências v2

Pré-requisitos: backend a correr (`uvicorn server:app`), frontend (`yarn start`), DB com dados.
Detalhes de fórmulas e contratos em [data-model.md](./data-model.md) e
[contracts/pendencias-contract.md](./contracts/pendencias-contract.md).

## Backend — re-apontamento dos avisos (US2)

```bash
cd backend && pytest tests/test_atos.py tests/test_atos_overdue.py -q
```

Esperado:
- O aviso de `create_ato` (Ato a aguardar assinatura) tem `link == "/pendencias"`.
- Os avisos do varrimento de atrasados (Direção e proponente) têm `link == "/pendencias"`.
- O aviso de `sign_ato` (aprovado/rejeitado, incl. motivo) tem `link == "/financeiro/co-aprovacoes"`.
- O aviso de `execute_ato` tem `link == "/financeiro/co-aprovacoes"`.
- Suíte de Atos verde (sem regressões nas specs 010–013).

## Frontend — contador (US1) — navegador (Princípio VII, dono)

1. **Sócio comum com pendências**: login como sócio com ≥1 votação aberta por votar e/ou evento
   por confirmar. Na barra lateral, «As minhas pendências» mostra um badge com o número.
   Abrir `/pendencias` → o nº de itens listados **coincide** com o badge (C1/SC-002).
2. **Direção/admin**: o badge inclui também Atos à assinatura + Atos propostos pendentes; coincide
   com o painel. Um sócio comum **não** vê contagem de Atos e não há erro 403 na consola (FR-009).
3. **Zero pendências**: resolver tudo (votar, confirmar presença, assinar) → o badge **desaparece**
   (sem bolha, sem "0" ruidoso) (FR-004).
4. **Cap "9+"**: com >9 pendências, o badge mostra **"9+"** sem alargar o item de menu (FR-003).
5. **Frescura**: resolver uma pendência e navegar entre páginas → o contador desce (recalcula no
   carregamento/navegação, sem stream) (FR-005).

## Avisos → painel (US2) — navegador

6. Disparar/abrir um aviso de **Ato pendente** (novo Ato ou lembrete de atrasado) → clicar leva a
   **`/pendencias`** (SC-003).
7. Abrir um aviso de **Ato decidido** (aprovação ou **rejeição com motivo** da spec 011) → clicar
   leva a `/financeiro/co-aprovacoes`, **não** a `/pendencias` (SC-003).

## Não-degradação (SC-004)

8. Navegar entre várias páginas privadas → a barra lateral abre sem atraso notável (queries
   pequenas, cache reutilizada, `staleTime 30s`).
