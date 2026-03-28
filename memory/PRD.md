# Portal ACTACV - Product Requirements Document

## Problema Original
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV). Portal institucional público + área reservada para associados.

## Stack Técnica
- **Frontend:** React, Tailwind CSS, Recharts, Framer Motion
- **Backend:** Python FastAPI (Router modular), MongoDB (Motor async), JWT Auth
- **Extras:** fpdf2 (PDF), date-fns (datas)

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Módulos Implementados

### Área Pública (COMPLETA)
- [x] HomePage, Sobre, Profissão, Transparência, Benefícios
- [x] Validador QR Code
- [x] **Galeria de Fotos Pública** — Álbuns públicos com fotos aprovadas

### Área Privada - Painel
- [x] Dashboard redesenhado (Recharts) + Feed Atividade Recente
- [x] Meu Perfil, Autenticação JWT

### Área Privada - Gestão
- [x] **Módulo Financeiro** (REFATORADO) — CashFlowTab, DRETab, SettingsTab, Export PDF/CSV
- [x] **Módulo Projetos** — CRUD, tarefas, milestones, comentários, orçamento
- [x] **Votações** — Sistema de votação interna
- [x] **Eventos/Agenda** — CRUD com inscrição
- [x] **Documentos** — Upload/download admin

### Área Privada - Comunidade
- [x] **Mural de Comunicação** (MELHORADO) — pesquisa, filtros, likes, comentários, moderação
- [x] **Galeria de Fotos** — Upload por sócios com workflow de aprovação, Lightbox, grid responsive
- [x] **Clube de Benefícios** (básico)

### Sistema
- [x] **Notificações Avançadas** — Central com stats, broadcast admin, filtros por tipo
- [x] **Notificações Automáticas** — Projetos + Finanças + Galeria
- [x] **Feed de Atividade Recente** — Dashboard widget
- [x] **Dark Mode** desativado (removido a pedido do utilizador)
- [x] **Quotas pendentes removidas** — Não existe conceito de inadimplência (desconto em folha)
- [x] **CI/CD** — GitHub Actions (ci.yml, deploy.yml)

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline e identificação digital
- [ ] Clube de Benefícios - QR Code validation avançado

### P2
- [ ] Evento em Destaque com countdown na homepage
- [ ] Exportar eventos para Google/Apple Calendar

## Regras de Negócio
- NÃO existe "Sócio inadimplente" - quotas descontadas em folha salarial
- NÃO existe "Quotas Pendentes" - todas as contribuições são automáticas via folha
- Dark Mode desativado a pedido do utilizador
- Todos os elementos interativos precisam de data-testid

## Arquitetura
```
/app/backend/routes/
├── gallery.py, activity.py, finances.py, projects.py, notifications.py, wall.py, auth_routes.py, events.py, stats.py

/app/frontend/src/
├── pages/private/DashboardPage.js (sem quotas pendentes, com "Contribuições - Desconto em Folha")
├── pages/private/GaleriaAdminPage.js
├── pages/public/GaleriaPage.js
├── pages/private/financeiro/ (módulos refatorados)
├── pages/private/AdminUsuariosPage.js (sem status inadimplente)
```
