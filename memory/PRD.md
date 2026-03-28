# Portal ACTACV - Product Requirements Document

## Visão Geral
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV).

## Stack Tecnológica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios, PWA (Service Worker)
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication
- **UI Components:** Shadcn/UI, Lucide React

## Arquitetura Backend (Modular)
```
backend/
├── server.py         (40 linhas - setup, middleware, monta routers)
├── database.py       (Conexão MongoDB, UPLOAD_DIR)
├── auth.py           (JWT, passwords, get_current_user)
├── models.py         (Todos os modelos Pydantic)
├── helpers.py        (audit_log, notificações)
├── routes/
│   ├── __init__.py   (Regista 13 route modules)
│   ├── auth_routes.py (login, register, forgot-password, reset-password)
│   ├── users.py, invoices.py, polls.py, posts.py
│   ├── documents.py, benefits.py, wall.py, events.py
│   ├── gallery.py, notifications.py, stats.py, upload.py
└── tests/
```

## Funcionalidades Implementadas

### Área Pública
- [x] Homepage, Sobre, Profissão, Transparência, Benefícios, Contactos
- [x] Galeria de Fotos, Validador QR, Notícias, Eventos Públicos
- [x] **Recuperação de Senha** (forgot-password → token → reset → login)

### Área Reservada
- [x] Dashboard, Gestão Financeira, Carteira Digital PWA
- [x] Votações, Eventos/Agenda, Documentos
- [x] Mural de Comunicação, Clube de Benefícios, Notificações

### Qualidade
- [x] Acentuação portuguesa corrigida em todas as páginas
- [x] Contraste WCAG melhorado no footer e botões CTA
- [x] Backend refatorado (1389 → 40 linhas no server.py)

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Status de Testes
- iteration_8: 100% (9/9 backend + 6/6 frontend) - Recuperação de senha
- iteration_7: 100% (38/38 endpoints) - Refactoring backend
- iteration_6: 100% - UX/Legibilidade

## Data: 28 Março 2026

## Próximas Tarefas (Backlog)
- P1: Clube de Benefícios - Lógica de validação QR Code
- P2: Evento em Destaque com countdown na homepage
- P2: Exportar eventos para Google/Apple Calendar

## Nota Técnica
- A recuperação de senha funciona em modo DEMO (token retornado na resposta API). Para produção, substituir pelo envio de email real (SendGrid, Resend, etc.)
