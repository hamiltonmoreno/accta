# Portal ACTACV - Product Requirements Document

## Problema Original
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV). Portal institucional público + área reservada para associados.

## Stack Técnica
- **Frontend:** React, Tailwind CSS, Recharts, Framer Motion, CSS Variables (Dark Mode)
- **Backend:** Python FastAPI (Router modular), MongoDB (Motor async), JWT Auth
- **Extras:** fpdf2 (PDF), date-fns (datas)

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Módulos Implementados

### Área Pública (COMPLETA)
- [x] HomePage com hero, sobre, CTA
- [x] Página Sobre Nós, Profissão, Transparência, Benefícios
- [x] Validador QR Code

### Área Privada - Painel
- [x] Dashboard redesenhado (Recharts) + **Feed Atividade Recente** (28/03/2026)
- [x] Meu Perfil (edição de dados)
- [x] Autenticação JWT

### Área Privada - Gestão
- [x] **Módulo Financeiro** (REFATORADO em 28/03/2026) — CashFlowTab, DRETab, SettingsTab, Export PDF/CSV
- [x] **Módulo Projetos** - CRUD, tarefas, milestones, comentários, orçamento
- [x] **Votações** - Sistema de votação interna
- [x] **Eventos/Agenda** - CRUD com inscrição
- [x] **Documentos** - Upload/download admin

### Área Privada - Comunidade
- [x] **Mural de Comunicação** (MELHORADO em 28/03/2026) - pesquisa, filtros, likes, comentários, moderação
- [x] **Clube de Benefícios** (básico)

### Sistema
- [x] **Notificações Avançadas** (28/03/2026) — Central com stats, broadcast admin, filtros por tipo, eliminar/limpar
- [x] **Notificações Automáticas** (28/03/2026):
  - Projetos: criação, status, aprovação, responsável, tarefa, comentário, despesa, orçamento excedido
  - Finanças: nova transação, quotas geradas, configurações
- [x] **Feed de Atividade Recente** (28/03/2026) — Dashboard widget agregando mural, projetos, finanças, eventos, votações
- [x] **Dark Mode** global

## Refatoração (28/03/2026)
- FinanceiroPage.js (1067 linhas) → 6 ficheiros em `financeiro/`

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline e identificação digital
- [ ] Clube de Benefícios - QR Code validation avançado

### P2
- [ ] Evento em Destaque com countdown na homepage
- [ ] Exportar eventos para Google/Apple Calendar
- [ ] Galeria de fotos

## Regras de Negócio
- NÃO existe "Sócio inadimplente" - quotas descontadas em folha
- CSS variables obrigatórias para Dark Mode
- Todos os elementos interativos precisam de data-testid

## Arquitetura
```
/app/frontend/src/pages/private/
├── financeiro/ (CashFlowTab, DRETab, SettingsTab, TransactionModal, MemberFinanceView, constants)
├── DashboardPage.js (com ActivityFeed widget)
├── FinanceiroPage.js, MuralPage.js, NotificacoesPage.js
├── ProjectsPage.js, ProjectDetailPage.js, EventosPage.js, VotacoesPage.js

/app/backend/routes/
├── activity.py (NEW - feed de atividade recente)
├── finances.py, projects.py (com triggers de notificação automática)
├── notifications.py (CRUD avançado, broadcast)
├── wall.py, auth_routes.py, events.py, ...
├── helpers.py (notify_users, notify_admins, notify_all_active_users, get_project_stakeholder_ids)
```
