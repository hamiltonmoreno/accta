# Portal ACTACV - Product Requirements Document

## Visão Geral
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV).

## Stack Tecnológica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios, PWA (Service Worker)
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication
- **UI Components:** Shadcn/UI, Lucide React

## Arquitetura Backend (Refatorado)
```
backend/
├── server.py         (40 linhas - setup, middleware, monta routers)
├── database.py       (Conexão MongoDB, UPLOAD_DIR)
├── auth.py           (JWT, passwords, get_current_user)
├── models.py         (Todos os modelos Pydantic)
├── helpers.py        (audit_log, notificações)
├── routes/
│   ├── __init__.py   (Regista 13 route modules)
│   ├── auth_routes.py
│   ├── users.py
│   ├── invoices.py
│   ├── polls.py
│   ├── posts.py
│   ├── documents.py
│   ├── benefits.py
│   ├── wall.py
│   ├── events.py
│   ├── gallery.py
│   ├── notifications.py
│   ├── stats.py
│   └── upload.py
├── tests/
│   └── test_refactoring_all_endpoints.py
├── requirements.txt
└── .env
```

## Funcionalidades Implementadas

### Área Pública
- [x] Homepage com hero responsivo
- [x] Sobre Nós, A Profissão, Transparência, Benefícios, Contactos
- [x] Galeria de Fotos (álbuns, lightbox, admin upload)
- [x] Validador QR Code Público
- [x] Notícias e Eventos Públicos

### Área Reservada (Portal do Associado)
- [x] Dashboard, Gestão Financeira, Carteira Digital PWA
- [x] Votações, Eventos/Agenda, Documentos
- [x] Mural de Comunicação (categorias, likes, comentários, moderação)
- [x] Clube de Benefícios, Notificações In-App

### Identidade Visual
- [x] Cores ACCTA: Carmesim (#C7202F), Grafite (#3A3A3A), Navy (#1B2B4B), Amber (#D4A843)
- [x] Tipografia: Open Sans + JetBrains Mono
- [x] Acentuação portuguesa corrigida em TODAS as páginas

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Status de Testes
- iteration_7: 100% - Refactoring backend (38/38 endpoints + frontend)
- iteration_6: 100% - UX/Legibilidade (acentos e contrastes)

## Data: 27 Fevereiro 2026

## Próximas Tarefas (Backlog)
- P1: Clube de Benefícios - Lógica de validação QR Code
- P2: Evento em Destaque com countdown na homepage
- P2: Exportar eventos para Google/Apple Calendar
- P2: Sistema de recuperação de senha
