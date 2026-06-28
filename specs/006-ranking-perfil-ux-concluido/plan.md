# Implementation Plan: Revisão do Ranking e do Perfil

**Branch**: `feature/ranking-perfil-ux` | **Date**: 2026-06-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-ranking-perfil-ux/spec.md`

## Summary

Revisão de apresentação e UX, **frontend-only**, de três superfícies já existentes:
(1) tornar a página de Ranking responsiva no telemóvel; (2) distinguir 1.º/2.º/3.º
lugar de forma clara e acessível; (3) mostrar a foto de cada sócio no ranking;
(4) impedir o corte do painel de notificações junto ao bordo do ecrã; (5) clarificar
no Perfil a fronteira entre campos de autosserviço (editáveis) e campos de
identidade/associação (geridos por admin). Nenhuma alteração de backend, modelos,
schema ou API — os dados necessários (incl. `photo_url` por entrada do ranking) já
viajam nos payloads atuais.

## Technical Context

**Language/Version**: JavaScript (React 19), JSX

**Primary Dependencies**: Tailwind CSS 3, shadcn/ui (New York), Framer Motion,
lucide-react, @tanstack/react-query — todas já instaladas (zero deps novas)

**Storage**: N/A (sem alterações de dados; lê os payloads existentes de
`GET /api/ranking/leaderboard` e do utilizador autenticado)

**Testing**: verificação em navegador a 360/390/414/768/1024/1440px (Princípio VII);
sem nova suite backend (nada de backend muda)

**Target Platform**: Web (portal privado), telemóvel + desktop

**Project Type**: Web app (frontend + backend no repo) — **esta feature toca só `frontend/`**

**Performance Goals**: sem regressão; sem novas chamadas de rede

**Constraints**: Sistema de design ACCTA (neutral-led, Carmesim acento único,
sem dark mode); WCAG AA; reutilizar componentes existentes (`UserAvatar`,
shadcn/ui); zero novas dependências

**Scale/Scope**: ~5 ficheiros de frontend; algumas centenas de sócios; ranking
paginado (≤100 por página)

## Constitution Check

*GATE: avaliado antes da Fase 0 e reconfirmado após a Fase 1.*

| Princípio | Estado | Nota |
|-----------|--------|------|
| I. Simplicity First | ✅ | Reutiliza `UserAvatar`/`mediaUrl`/shadcn; zero deps; sem backend. O caminho mais curto que funciona. |
| II. Root-Cause Discipline | ✅ | US1 (mobile) exige reproduzir e corrigir a causa real (elemento que transborda), não esconder com `overflow`. |
| III. RBAC + Audit | ✅ N/A | Sem endpoints novos; nenhuma superfície protegida muda. Opt-out do ranking continua respeitado (já filtrado no servidor). |
| IV. Language Discipline | ✅ | Todo o texto UI em PT; identificadores em EN; ficheiros mantêm a língua atual. |
| V. Design System Authority (NON-NEGOTIABLE) | ⚠️ ver Complexity Tracking | Ouro/prata/bronze literais estão **fora da paleta**. Plano usa equivalente compatível (Carmesim→Grafite→muted + ordinal + ícone). Metálico real = decisão do dono (extensão sancionada da skill). |
| VI. GitFlow + Confirmation | ✅ | Em `feature/ranking-perfil-ux` (de `develop`); PR para `develop`. Sem STOP conditions (sem dados/email/main). |
| VII. Verification Before Done | ✅ | Mudança de UI → exercida em navegador nas larguras-alvo antes de "done". |

**Resultado do gate**: PASS com uma deviation registada (Princípio V) em Complexity
Tracking — resolvida por equivalente compatível com a paleta; sem edição autónoma da
skill de design ([[no-autonomous-skill-edits]]).

## Project Structure

### Documentation (this feature)

```text
specs/006-ranking-perfil-ux/
├── plan.md              # Este ficheiro
├── research.md          # Fase 0 — decisões (mobile, medalhas, avatar, notificações, perfil)
├── data-model.md        # Fase 1 — sem alterações de dados (documenta o payload existente)
├── quickstart.md        # Fase 1 — guia de validação em navegador
├── contracts/           # Fase 1 — N/A (sem alterações de API); ver nota no ficheiro
└── tasks.md             # Fase 2 (/speckit-tasks — NÃO criado aqui)
```

### Source Code (repository root) — apenas frontend

```text
frontend/src/
├── pages/private/
│   ├── RankingPage.js                 # US1 responsivo + US2 distinção 1/2/3 + US3 avatares
│   ├── PerfilPage.js                  # US5 (se necessário) reforço da fronteira editável vs. gerido
│   ├── dashboard/RankingTopN.js       # US2 + US3 no widget do dashboard (mesma fonte de dados)
│   └── perfil/
│       └── DetailsGrid.js             # US5 marcar campos geridos pela associação como não-editáveis
├── components/
│   ├── NotificationBell.js            # US4 posicionamento do painel sem corte
│   └── UserAvatar.js                  # reutilizado tal como está (foto + iniciais + mediaUrl)
```

**Structure Decision**: Web app com `frontend/` + `backend/`, mas esta feature é
**exclusivamente frontend**. Reaproveita `UserAvatar` (fonte única de avatar, já com
fallback de iniciais e `mediaUrl`) e primitivas shadcn/ui. O `RankingPage` e o widget
`RankingTopN` consomem o mesmo payload de `GET /api/ranking/leaderboard`, que **já
inclui `photo_url` por entrada** (denormalizado no rebuild — `backend/ranking.py:270`),
pelo que US3 não requer backend.

## Complexity Tracking

> Apenas a deviation do Princípio V (NON-NEGOTIABLE) precisa de justificação.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Distinção visual de 1.º/2.º/3.º sem introduzir ouro/prata/bronze literais | O dono pediu distinção clara dos três primeiros (razão de ser do ranking); a paleta ACCTA é neutral-led com Carmesim como acento único e proíbe cores fora do sistema | Metálicos literais (ouro/prata/bronze) introduziriam 3 cores novas em ícones/superfícies — viola Princípio V (não-negociável) e exigiria editar a skill de design (proibido autonomamente, [[no-autonomous-skill-edits]]). Equivalente compatível: **escala de ênfase Carmesim → Grafite → muted + número ordinal + ícone de medalha/coroa**, que cumpre "destaque distinto entre si" (FR-003) e "nunca só por cor" (FR-005). **Override do dono** para metálicos reais fica registado como decisão pendente em research.md (D2). |
