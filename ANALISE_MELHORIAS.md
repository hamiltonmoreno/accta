# Portal ACCTA — Análise de Implementação e Melhorias

**Última atualização:** Maio 2026

---

## Status de Implementação

### Área Pública — 100% Concluída

| Funcionalidade | Status |
|----------------|--------|
| Homepage hero aeronáutica | Concluído |
| Apresentação da profissão de controlador | Concluído |
| Sistema de notícias com filtros | Concluído |
| Página de transparência financeira (dados reais da API) | Concluído |
| Validador de carteira QR | Concluído |
| Galeria de fotos pública (álbuns aprovados) | Concluído |
| Formulário de contacto (email real via Resend) | Concluído |

### Portal do Associado — 100% Concluído

| Funcionalidade | Status |
|----------------|--------|
| Dashboard personalizado por perfil (RBAC) + Feed de Atividade | Concluído |
| Gestão financeira com folha salarial (export PDF/CSV) | Concluído |
| Carteira digital com QR Code SHA-256 | Concluído |
| Sistema de Votações (backend + frontend) | Concluído |
| Gestão de Projetos (CRUD, tarefas, milestones, orçamento) | Concluído |
| Eventos/Agenda com inscrição | Concluído |
| Documentos internos (upload/download) | Concluído |
| Mural de comunicação (posts, likes, moderação) | Concluído |
| Galeria de fotos com upload e workflow de aprovação | Concluído |
| Clube de benefícios com QR Code | Concluído |
| Notificações avançadas (SSE real-time + broadcast + auto-trigger) | Concluído |

### Área Administrativa — 100% Concluída

| Funcionalidade | Status |
|----------------|--------|
| Gestão de utilizadores (CRUD, cargos, privilégios) | Concluído |
| Dashboard financeiro com gráficos (Recharts) | Concluído |
| Gestão de galeria com aprovação de fotos | Concluído |
| Audit logs completo | Concluído |
| Estatísticas em tempo real | Concluído |

### Infraestrutura — 100% Concluída

| Componente | Status |
|------------|--------|
| Pipeline CI/CD (GitHub Actions — lint, build, deploy) | Concluído |
| Integração Resend (convite, reset, boas-vindas, contacto) | Concluído |
| Rate limiting (login, forgot-password, geral) | Concluído |
| Documentos públicos via API (Transparência) | Concluído |
| `.claude/` — agentes, hooks, regras, skills, settings | Concluído |

---

## Melhorias Pendentes

### P1 — Prioridade Alta

- **Carteira Digital PWA** — Service worker para funcionalidade offline (visualizar carteira sem internet)
- **Clube de Benefícios** — Lógica avançada de validação QR Code com parceiros externos

### P2 — Prioridade Média

- **Evento em Destaque** — Countdown timer na homepage para próximo evento
- **Export Calendário** — Exportar eventos para Google Calendar / Apple Calendar (.ics)

### P3 — Sugestões Futuras

- Dashboard de impacto pessoal (benefícios usados, eventos participados)
- Gamificação leve (badges de participação)
- Dashboard para parceiros do clube de benefícios
- Geolocalização de benefícios em mapa
- Sistema de mentoria entre sócios
- Relatório anual interativo (PDF automático)
- Notificações Push (Web Push API / PWA)

---

## Regras de Negócio

| Regra | Detalhe |
|-------|---------|
| Sem "inadimplente" | Quotas descontadas em folha salarial — statuses: `ativo`, `inativo`, `pendente_convite` |
| Sem cotas pendentes | Contribuições automáticas via folha |
| Modo escuro | Desativado por decisão de design |
| Aprovação de fotos | Fotos submetidas por sócios requerem aprovação admin |
| QR Code da carteira | Hash SHA-256 com salt interno — imutável em produção |

---

## Métricas de Sucesso

| KPI | Meta | Status |
|-----|------|--------|
| Engajamento | +20% logins + votações | Estrutura implementada |
| Eficiência Admin | -50% tempo de gestão | Automatizado via folha salarial |
| Escalabilidade | 500 sócios simultâneos | Índices SQL (expressão/parciais/GIN) via ensure_schema() + pool asyncpg (PostgreSQL/Supabase) |
