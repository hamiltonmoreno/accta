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

### Sistema e Seguranca
- [x] Notificacoes Avancadas + SSE real-time (com fallback polling)
- [x] CI/CD — GitHub Actions
- [x] Dark Mode REMOVIDO (ThemeContext eliminado)
- [x] Quotas pendentes REMOVIDAS
- [x] SECRET_KEY sem fallback inseguro
- [x] CORS seguro (credentials=true so com origens explicitas)
- [x] Registo publico forcado a role=socio
- [x] Rate limiting (login 10/min, register 5/min, forgot 3/min)
- [x] Limite de tamanho de ficheiro (docs 10MB, proofs 5MB, logos/avatars 2MB)
- [x] Auth validacao de token no startup (getMe)
- [x] ProtectedRoute com allowedRoles (financeiro, galeria-admin protegidos)
- [x] Interceptor 401 com event dispatch (sem reload completo)
- [x] Sidebar filtrada por role (socio nao ve Financeiro)

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline
- [ ] Clube de Beneficios - QR Code validation avancado

### P2
- [ ] Exportar eventos para Google/Apple Calendar
- [ ] Migrar uploads para object storage (S3/R2) para persistencia em producao
- [ ] React Query/SWR para cache de dados entre paginas

## Regras de Negocio
- NAO existe "Socio inadimplente" — quotas descontadas em folha
- NAO existem "Quotas Pendentes"
- Dark Mode DESATIVADO e ThemeContext ELIMINADO
- Registo publico so cria contas socio

## Configuracao de Producao (.env)
```
SECRET_KEY=<chave-forte-64-chars>
MONGO_URL=<connection-string>
DB_NAME=<nome-db>
CORS_ORIGINS=https://portal.accta.cv,https://www.accta.cv
```

## Arquitectura
```
/app/backend/
├── auth.py (get_current_user + get_user_from_token para SSE)
├── routes/
│   ├── notifications.py (SSE /stream endpoint)
│   ├── auth_routes.py (rate limiting via slowapi)
│   ├── upload.py (file size limits)
│   ├── report.py, activity.py, gallery.py, finances.py, projects.py
│   └── stats.py, events.py, wall.py, users.py, benefits.py

/app/frontend/src/
├── contexts/AuthContext.js (token validation on startup, force-logout event)
├── contexts/NotificationContext.js (SSE with polling fallback)
├── App.js (ProtectedRoute com allowedRoles, sem ThemeProvider)
├── layouts/PrivateLayout.js (sidebar filtrada por role)
├── utils/api.js (401 interceptor com event dispatch)
```
