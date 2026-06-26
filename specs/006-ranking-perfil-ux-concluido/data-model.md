# Data Model — Revisão do Ranking e do Perfil

**Sem alterações de dados.** Esta feature é frontend-only; não cria nem altera
tabelas, modelos Pydantic, schema ou índices. Documenta-se aqui apenas a forma dos
dados **já existentes** que o frontend passa a usar melhor.

## Entrada do Ranking (payload existente, não muda)

Origem: `GET /api/ranking/leaderboard` → `entries[]` e `me`. Cada entrada vem do
snapshot `member_scores` (denormalizado no rebuild — `backend/ranking.py`). Campos
relevantes para esta feature:

| Campo | Tipo | Uso nesta feature |
|-------|------|-------------------|
| `user_id` | string (uuid) | chave; deteção "(eu)" |
| `member_name` | string | nome + iniciais do avatar |
| `photo_url` | string \| null | **foto do avatar** (US3) — já presente no payload |
| `cargo` | string \| null | rótulo de cargo (já usado) |
| `status` | string | badge "Inativo" (já usado) |
| `rank` | int | posição → distinção 1/2/3 (US2) |
| `score` | number | pontuação (já usado) |
| `ranking_opt_out` | bool | filtrado no servidor; não reexposto (FR-008) |

Nenhum campo novo. A projeção do endpoint exclui apenas `_id` e `breakdown`, pelo
que `photo_url` já chega ao cliente.

## Perfil do Sócio (modelo existente, não muda)

Distinção que a UI passa a comunicar (US5) — sem alterar o backend:

- **Autosserviço (editável pelo próprio)** — `_EditableProfileFields` +
  `photo_url` (via `UserProfileUpdate`): `name`, `phone_number`, `bio`,
  `date_of_birth`, `blood_type`, `gender`, `nationality`, `nif`, `address`,
  `postal_code`, `city`, `residence_island`, `emergency_contact_*`, `profession`,
  `employer`, `license_*`, `photo_url`.
- **Identidade / associação (não-editável pelo próprio; gerido por admin)**:
  `email` (Q1 — admin-only), `member_id` (imutável), `cargo` (via `/admin/cargos`),
  `role`, `status`, `member_category`, `admission_date`.

## State transitions

N/A — nenhuma máquina de estados é introduzida ou alterada.
