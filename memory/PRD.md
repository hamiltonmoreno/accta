# Portal ACTACV - Product Requirements Document

## Problema Original
Ecossistema digital integrado para a Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACTACV). Portal institucional publico + area reservada para associados.

## Stack Tecnica
- **Frontend:** React, Tailwind CSS, Recharts, Framer Motion (Modo Claro exclusivo)
- **Backend:** Python FastAPI (Router modular), MongoDB (Motor async), JWT Auth
- **Extras:** fpdf2 (PDF), date-fns (datas)

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Financeiro: financeiro@accta.cv / fin123
- Socio: socio1@accta.cv / socio123

## Modulos Implementados

### Area Publica (COMPLETA)
- [x] HomePage, Sobre, Profissao, Transparencia, Beneficios
- [x] Validador QR Code
- [x] Galeria de Fotos Publica — Albums publicos com fotos aprovadas

### Area Privada - Painel
- [x] Dashboard redesenhado (Recharts) + Feed Atividade Recente
- [x] Meu Perfil, Autenticacao JWT
- [x] Carteira Digital com QR Code

### Area Privada - Gestao
- [x] Modulo Financeiro (REFATORADO) — CashFlowTab, DRETab, SettingsTab, Export PDF/CSV
- [x] Modulo Projetos — CRUD, tarefas, milestones, comentarios, orcamento
- [x] Votacoes — Sistema de votacao interna
- [x] Eventos/Agenda — CRUD com inscricao
- [x] Documentos — Upload/download admin

### Area Privada - Comunidade
- [x] Mural de Comunicacao (MELHORADO) — pesquisa, filtros, likes, comentarios, moderacao
- [x] Galeria de Fotos — Upload com workflow de aprovacao, Lightbox, grid responsive
- [x] Clube de Beneficios (basico)

### Sistema
- [x] Notificacoes Avancadas — Central com stats, broadcast admin, filtros por tipo
- [x] Notificacoes Automaticas — Projetos + Financas + Galeria
- [x] Feed de Atividade Recente — Dashboard widget
- [x] CI/CD — GitHub Actions (ci.yml, deploy.yml)
- [x] Dark Mode REMOVIDO (codigo CSS e JS limpos)
- [x] Quotas pendentes REMOVIDAS — Nao existe conceito de inadimplencia

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline e identificacao digital
- [ ] Clube de Beneficios - QR Code validation avancado

### P2
- [ ] Evento em Destaque com countdown na homepage
- [ ] Exportar eventos para Google/Apple Calendar

## Regras de Negocio
- NAO existe "Socio inadimplente" — quotas descontadas em folha salarial
- NAO existem "Quotas Pendentes" — contribuicoes automaticas via folha
- Dark Mode DESATIVADO e CSS dark mode REMOVIDO do codebase
- Apenas estatutos: ativo e inativo
- Todos os elementos interativos precisam de data-testid

## Arquitectura
```
/app/backend/routes/
├── gallery.py, activity.py, finances.py, projects.py
├── notifications.py, wall.py, auth_routes.py, events.py, stats.py

/app/frontend/src/
├── pages/private/DashboardPage.js (sem quotas pendentes)
├── pages/private/GaleriaAdminPage.js
├── pages/public/GaleriaPage.js
├── pages/private/financeiro/ (modulos refatorados)
├── pages/private/AdminUsuariosPage.js (sem status inadimplente)
├── layouts/PrivateLayout.js (sem toggle dark mode)
├── contexts/ThemeContext.js (forcado modo claro)
```

## Documentacao do Sistema
- README.md — Quick start e overview
- PROJETO_ACCTA.md — Detalhes completos do projeto
- ANALISE_MELHORIAS.md — Estado actual e melhorias pendentes
- SISTEMA_NOTIFICACOES.md — Documentacao do sistema de notificacoes
- DEPLOY.md — Guia de deploy com GitHub Actions
- SSH_SETUP.md — Configuracao SSH para CI/CD
