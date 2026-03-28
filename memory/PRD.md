# Portal ACTACV - Product Requirements Document

## Visão Geral
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV).

## Stack Tecnológica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios, PWA
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication

## Funcionalidades Implementadas

### Área Pública
- [x] Homepage, Sobre, Profissão, Transparência, Benefícios, Contactos, Galeria, Eventos

### Área Reservada
- [x] Dashboard, Financeiro, Carteira Digital PWA
- [x] Votações, Eventos/Agenda, Documentos
- [x] Mural de Comunicação (categorias, likes, comentários, moderação)
- [x] Clube de Benefícios, Notificações In-App
- [x] Recuperação de Senha (modo demo)
- [x] **CRUD Perfil do Membro** (novo)
  - Página de perfil (/perfil) com edição de nome, telefone, biografia
  - Gestão de membros (/admin/usuarios) com pesquisa e filtros
  - Modal de edição com dropdowns para Função, Estado, Cargo
  - 7 cargos: Presidente, Vice-Presidente, Secretário-Geral, Tesoureiro, Vogal, Membro da Direção, Sócio
  - 7 privilégios granulares: manage_users, manage_finances, manage_events, manage_documents, moderate_content, manage_benefits, view_audit_logs
  - Validação backend de cargos/privilégios/roles inválidos
  - Notificação automática ao membro quando perfil é editado pelo admin
  - Proteção contra auto-eliminação

### Design & UX
- [x] Identidade Visual ACCTA (Carmesim, Grafite, Open Sans)
- [x] Sidebar collapsível com lock/hover (fundo branco, secções agrupadas)
- [x] Responsividade 320-1920px (mobile/tablet/desktop)
- [x] Acentuação portuguesa completa

### Backend (Modular)
```
server.py (40L) → database.py, auth.py, models.py, helpers.py
routes/ → 13 módulos (auth, users, invoices, polls, posts, documents,
          benefits, wall, events, gallery, notifications, stats, upload)
```

## Credenciais
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Testes
- iteration_11: 100% (19/19 backend + frontend) - CRUD Perfil Membro
- iteration_10: 100% (17/17) - Sidebar
- iteration_9: 100% (16/16) - Responsividade
- iteration_8: 100% (15/15) - Recuperação de senha
- iteration_7: 100% (38/38) - Refactoring backend

## Próximas Tarefas
- P1: Clube de Benefícios — Lógica de validação QR Code
- P2: Evento em Destaque com countdown na homepage
- P2: Exportar eventos para Google/Apple Calendar
