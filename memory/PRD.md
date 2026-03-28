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
- [x] Galeria de Fotos Publica
- [x] **Evento em Destaque** com countdown timer animado na homepage

### Area Privada - Painel
- [x] Dashboard redesenhado (Recharts) + Feed Atividade Recente
- [x] **Relatorio de Atividade Pessoal** (8 metricas: eventos, votacoes, publicacoes, likes, projetos, fotos, beneficios, documentos)
- [x] Meu Perfil, Autenticacao JWT
- [x] Carteira Digital com QR Code

### Area Privada - Gestao
- [x] Modulo Financeiro (REFATORADO) — CashFlowTab, DRETab, SettingsTab, Export PDF/CSV
- [x] Modulo Projetos — CRUD, tarefas, milestones, comentarios, orcamento
- [x] Votacoes — Sistema de votacao interna
- [x] Eventos/Agenda — CRUD com inscricao
- [x] Documentos — Upload/download admin

### Area Privada - Comunidade
- [x] Mural de Comunicacao (MELHORADO)
- [x] Galeria de Fotos — Upload com workflow de aprovacao
- [x] Clube de Beneficios (basico)

### Sistema
- [x] Notificacoes Avancadas + Automaticas
- [x] Feed de Atividade Recente
- [x] CI/CD — GitHub Actions
- [x] Dark Mode REMOVIDO
- [x] Quotas pendentes REMOVIDAS

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline e identificacao digital
- [ ] Clube de Beneficios - QR Code validation avancado

### P2
- [ ] Exportar eventos para Google/Apple Calendar

## Regras de Negocio
- NAO existe "Socio inadimplente" — quotas descontadas em folha salarial
- NAO existem "Quotas Pendentes" — contribuicoes automaticas via folha
- Dark Mode DESATIVADO e CSS dark mode REMOVIDO do codebase
- Apenas estatutos: ativo e inativo

## API Endpoints Novos (esta sessao)
- `GET /api/events/featured` — Proximo evento publico (sem auth)
- `GET /api/report/personal` — Relatorio de atividade pessoal (com auth)

## Arquitectura
```
/app/backend/routes/
├── gallery.py, activity.py, finances.py, projects.py
├── notifications.py, wall.py, auth_routes.py, events.py, stats.py
├── report.py (NOVO - relatorio pessoal)

/app/frontend/src/
├── pages/public/HomePage.js (featured event countdown)
├── pages/private/DashboardPage.js (personal report widget)
├── utils/api.js (eventsAPI.getFeatured, reportAPI.getPersonal)
```
