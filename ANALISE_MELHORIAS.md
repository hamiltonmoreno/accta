# Portal ACCTA — Análise de Implementação e Melhorias

**Última atualização:** Junho 2026 (v0.5.17)

---

## Status de Implementação

### Área Pública — Concluída

| Funcionalidade | Status |
|----------------|--------|
| Homepage hero institucional | Concluído |
| Página Sobre (órgãos sociais dinâmicos via API) | Concluído |
| Apresentação da profissão de controlador | Concluído |
| Notícias / blog com filtros e detalhe | Concluído |
| Publicações profissionais públicas (Cat 5) | Concluído |
| Validador de carteira QR | Concluído |
| Galeria pública (álbuns aprovados) | Concluído |
| Benefícios e eventos públicos | Concluído |
| Formulário de contacto (email real via Resend) | Concluído |

> Nota: a página pública de **Transparência** foi **removida** (a prestação de contas vive na área privada/governança).

### Portal do Associado — Concluído

| Funcionalidade | Status |
|----------------|--------|
| Dashboard personalizado por perfil + feed de atividade | Concluído |
| Gestão financeira (folha salarial, jóia, export PDF/CSV) | Concluído |
| Co-aprovações de atos financeiros (Art. 54) | Concluído |
| Carteira digital com QR Code SHA-256 (PWA/ícones) | Concluído |
| Votações / polls | Concluído |
| Gestão de projetos (CRUD, tarefas, milestones, orçamento) | Concluído |
| Eventos/agenda com inscrição | Concluído |
| Documentos internos (upload/download + controlo de acesso) | Concluído |
| Mural de comunicação (posts, likes, moderação) | Concluído |
| Galeria com upload e workflow de aprovação | Concluído |
| Clube de benefícios com QR Code | Concluído |
| Notificações (SSE real-time + broadcast + auto-triggers) | Concluído |
| Central de Ajuda (`/ajuda`, secções por papel + pesquisa) | Concluído |
| Regulamentos versionados + Ranking de participação | Concluído |
| Fins profissionais Cat 5 (formações, publicações, defesa, relações) | Concluído |
| Participação (petições, propostas AG, reclamações, esclarecimentos, honorários) | Concluído |

### Governança Estatutária — Concluída

| Funcionalidade | Status |
|----------------|--------|
| Assembleias (convocatória, presenças, quórum, palavra, moções, deliberações, voto) | Concluído |
| Eleições (listas, candidaturas, voto secreto, proclamação → mandatos) | Concluído |
| Disciplina / sanções por deliberação | Concluído |
| Prestação de contas (exercícios, balancetes) | Concluído |
| Comunicados (email + in-app) | Concluído |
| Gestão de cargos / órgãos sociais (`/admin/cargos`) | Concluído |

### Área Administrativa — Concluída

| Funcionalidade | Status |
|----------------|--------|
| Gestão de utilizadores (CRUD, papéis, privilégios) | Concluído |
| Pedidos de inscrição (auto-registo) | Concluído |
| Dashboard financeiro com gráficos (Recharts) | Concluído |
| Aparência (marca + banners), notícias e comunicados | Concluído |
| Gestão de galeria com aprovação de fotos | Concluído |
| Audit logs com integridade HMAC | Concluído |

### Infraestrutura & Segurança — Concluída

| Componente | Status |
|------------|--------|
| Pipeline CI (lint, build, testes com Postgres em serviço) | Concluído |
| CD do backend (deploy.yml: gate → imagem → GHCR → VPS) | Concluído |
| Frontend no Vercel (deploy automático) | Concluído |
| Integração Resend (convite, reset, boas-vindas, contacto, comunicados) | Concluído |
| Rate limiting + lockout de login | Concluído |
| JWT em cookie httpOnly + invalidação por `password_changed_at` | Concluído |
| RLS-ON deny-all no Postgres (defesa em profundidade) | Concluído |
| MFA/2FA **removido** por decisão do dono (login = email + password) | Concluído |
| `.claude/` — agentes, hooks, regras, skills, settings | Concluído |

---

## Melhorias Pendentes

### P2 — Prioridade Média
- **Export Calendário** — exportar eventos para Google/Apple Calendar (.ics)
- **Evento em Destaque** — countdown na homepage para o próximo evento
- Agendar o cron de rebuild do ranking (operador)

### P3 — Sugestões Futuras
- Dashboard de impacto pessoal (benefícios usados, eventos participados)
- Gamificação leve (badges de participação) — ranking já dá a base
- Dashboard para parceiros do clube de benefícios + geolocalização em mapa
- Relatório anual interativo (PDF automático)
- Notificações Push (Web Push API / PWA)

---

## Regras de Negócio

| Regra | Detalhe |
|-------|---------|
| Sem "inadimplente" | Quotas descontadas em folha; statuses: `ativo`, `inativo`, `pendente_convite`, `pendente_aprovacao`, `rejeitado` |
| Uma conta para a vida | `member_id` imutável; contas `technical` fora de listagens/scoring/AGAs |
| Cargos canónicos | Persistidos como chave (`dir_tesoureiro`); atribuídos só via `/admin/cargos` ou proclamação |
| RBAC aditivo | `role OR privilege` |
| Modo escuro | Desativado por decisão de design |
| Aprovação de fotos | Fotos de sócios requerem aprovação admin |
| QR Code da carteira | Hash SHA-256 com salt interno — imutável em produção |

---

## Métricas de Escalabilidade

| KPI | Abordagem |
|-----|-----------|
| 500 sócios simultâneos | Índices SQL (expressão/parciais/GIN) via `ensure_schema()` + pool asyncpg sobre o pooler do Supabase |
| Concorrência em votos/quotas | Locks `FOR UPDATE` / advisory locks (resolução de races TOCTOU) |
| Eficiência admin | Automatização via folha salarial + auto-triggers de notificações |
