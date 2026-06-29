# Quickstart — Validação: painel «As minhas pendências»

Feature **frontend-only** (sem testes de backend; não toca `backend/`). Validação =
**navegador** (Princípio VII, dono) + preview Vercel.

## Pré-requisitos

- Frontend: `cd frontend && yarn start` (ou o preview Vercel da PR).
- Contas de teste: um **sócio comum** e um membro da **Direção**, ambos `ativo`.

## Cenários (navegador)

### A — Sócio comum
1. Garantir que há ≥1 **votação aberta** que o sócio não votou e ≥1 **evento futuro** sem a
   sua inscrição.
2. Abrir **`/pendencias`**.
3. Esperado: vê **Votações por votar** e **Eventos por confirmar**, cada uma com contagem e
   ligação para agir. **NÃO** vê secções de Atos (não é Direção). (SC-001)
4. Votar numa votação / confirmar um evento → voltar a `/pendencias` → o item **desaparece**.
   (SC-003, FR-005)
5. Resolver tudo → `/pendencias` mostra **estado vazio claro** ("nada pendente"). (SC-005)

### B — Direção
1. Com um membro da Direção que (a) propôs um Ato ainda `pendente` e (b) tem um Ato a
   aguardar a sua assinatura.
2. Abrir `/pendencias`.
3. Esperado: além de votações/eventos, vê **"Atos que propus"** e **"Atos à minha
   assinatura"**, com ligações (ver Ato / assinar). (FR-002/FR-003)
4. Assinar/decidir o Ato → o item sai do painel. (FR-005)

### C — Segredo do voto (negativo)
1. Com uma **eleição** em votação e/ou uma **deliberação secreta** aberta em que o utilizador
   ainda não votou.
2. Abrir `/pendencias`.
3. Esperado: **nada** sobre eleições/deliberações-secretas aparece no painel (SC-004/FR-008).

### D — Resiliência
1. Forçar falha de um dos reads (ex.: offline momentâneo).
2. Esperado: a secção afetada degrada localmente; as restantes continuam a renderizar (a
   página não rebenta).

## Não há prova server-side

Não toca `backend/` ⇒ **sem Via B**, sem `curl` decisivo. A entrega vai pela **Vercel** no
push a `main`; a confirmação é visual no preview/produção.
