# Portal ACTACV - Product Requirements Document

## Problema Original
Ecossistema digital integrado para a Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACTACV). Portal institucional publico + area reservada para associados.

## Stack Tecnica
- **Frontend:** React, Tailwind CSS, Recharts, Framer Motion (Modo Claro exclusivo)
- **Backend:** Python FastAPI (Router modular), MongoDB (Motor async), JWT Auth, slowapi (rate limiting)
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
- [x] Evento em Destaque com countdown timer animado

### Area Privada - Painel
- [x] Dashboard redesenhado (Recharts) + Feed Atividade Recente
- [x] Relatorio de Atividade Pessoal (8 metricas)
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

### Autenticacao (REFEITO - INVITE ONLY)
- [x] Registo publico ELIMINADO
- [x] Sistema de convite por admin (POST /api/admin/invite)
- [x] Pagina setup-account com token cryptografico
- [x] Status pendente_convite bloqueia login
- [x] CLI create_admin.py para bootstrap em producao
- [x] Modal "Convidar Socio" no painel admin
- [x] Link de convite copiavel para partilhar

### Sistema e Seguranca
- [x] SSE real-time para notificacoes (com fallback polling)
- [x] SECRET_KEY obrigatoria (sem fallback)
- [x] CORS seguro
- [x] Rate limiting (login 10/min, register removido, setup 5/min)
- [x] Limite tamanho ficheiro
- [x] Auth validacao token no startup
- [x] ProtectedRoute com allowedRoles
- [x] Interceptor 401 com event dispatch
- [x] Sidebar filtrada por role
- [x] ThemeContext ELIMINADO (dark mode removido)
- [x] CI/CD — GitHub Actions

## Fluxo de Autenticacao em Producao
```
1. Deploy: python scripts/create_admin.py --email admin@controlador.cv --password <senha> --name "Admin"
2. Admin faz login → Utilizadores → "Convidar Socio"
3. Preenche nome, email, role, cargo → Recebe link de convite
4. Partilha link com novo socio
5. Socio abre link → Define senha → Conta ativada → Auto-login
```

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline
- [ ] Clube de Beneficios - QR Code validation avancado

### P2
- [ ] Exportar eventos para Google/Apple Calendar
- [ ] Migrar uploads para object storage (S3/R2)
- [ ] Integracao email para enviar convites automaticamente
- [ ] React Query/SWR para cache de dados

## Regras de Negocio
- NAO existe registo publico — apenas convite por admin
- NAO existe "Socio inadimplente" — quotas descontadas em folha
- NAO existem "Quotas Pendentes"
- Dark Mode DESATIVADO e eliminado do codigo

## Arquitectura
```
/app/backend/routes/
├── admin.py (invite, pending invites, revoke)
├── auth_routes.py (login, me, setup-account, validate-invite, forgot/reset)
├── notifications.py (SSE + CRUD)
├── gallery.py, activity.py, finances.py, projects.py
├── report.py, stats.py, events.py, wall.py, users.py, benefits.py, upload.py

/app/frontend/src/
├── pages/public/SetupAccountPage.js (definir senha via convite)
├── pages/private/AdminUsuariosPage.js (modal convidar socio)
├── contexts/AuthContext.js (sem register, com force-logout)
├── utils/api.js (adminAPI.invite, authAPI.setupAccount)

/app/scripts/
├── create_admin.py (CLI bootstrap)
├── seed_data.py (dados demo)
```
