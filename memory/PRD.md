# Portal ACTACV - Product Requirements Document

## Visao Geral
Ecossistema digital integrado para a Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACTACV).

## Stack Tecnologica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication
- **UI Components:** Shadcn/UI, Lucide React
- **Charts:** Recharts

## Funcionalidades Implementadas

### Area Publica
- [x] Homepage com hero responsivo, estatisticas, secao educativa e noticias
- [x] Sobre Nos (A Associacao) - Quem Somos, Missao, Visao, Valores
- [x] A Profissao - Educativo sobre CTA, tipos de controlo
- [x] Clube de Beneficios (Publico) - Parcerias
- [x] Transparencia - Documentos institucionais
- [x] Contactos - Formulario, FAQ
- [x] Validador QR Code Publico
- [x] Pagina de Noticias
- [x] Eventos Publicos

### Area Reservada (Portal do Associado)
- [x] Dashboard responsivo - Stats 2x2 mobile / 4 cols desktop
- [x] Gestao Financeira - Table desktop / Card view mobile
- [x] Carteira Digital (PWA) - Flip card, QR download, offline cache
- [x] Sistema de Votacoes
- [x] Sistema de Eventos/Agenda - Cards responsivos
- [x] Documentos
- [x] Mural de Comunicacao - Categories, likes, comments, moderation
- [x] Clube de Beneficios
- [x] Notificacoes In-App

### UI/UX (Marco 2026)
- [x] Split-screen login page (desktop: branding + form, mobile: form only)
- [x] Sidebar melhorado - active states, mobile slide-out drawer
- [x] Mobile header com page title, avatar, notifications
- [x] Cards com hover effects e shadows
- [x] Touch-friendly targets (min 44px)
- [x] Footer responsivo com links organizados
- [x] Better scrollbar styling
- [x] Focus states acessiveis
- [x] Animate-fadeIn page transitions

### Identidade Visual
- [x] Cores ACCTA: Carmesim (#C7202F) e Grafite (#3A3A3A)
- [x] Tipografia: Open Sans + JetBrains Mono
- [x] Logo customizado ACCTALogo

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Financeiro: financeiro@accta.cv / fin123
- Socio: socio1@accta.cv / socio123
- Inadimplente: inadimplente@accta.cv / socio123

## API Endpoints Principais
- Auth: POST /api/auth/login, GET /api/auth/me
- Wall: GET/POST /api/wall, PATCH /api/wall/{id}/approve|pin|like, GET/POST /api/wall/{id}/comments
- Events: GET/POST /api/events, PATCH /api/events/{id}/register
- Users, Invoices, Polls, Documents, Benefits, Notifications

## Status de Testes
- Backend: 100% (51/51 - iteration_4)
- Frontend: 100% (todas as paginas e viewports testados)
- Viewports testados: Desktop 1920px, Mobile 390px

## Data de Ultima Atualizacao
26 Marco 2026

## Proximas Tarefas (Backlog)
- P1: Clube de Beneficios - Logica de validacao QR Code
- P2: Exportar eventos para calendarios (Google/Apple Calendar)
- P2: Galeria de fotos da equipa e aeroportos
- P2: Sistema de recuperacao de senha
- P3: Refactoring - Dividir server.py em routers separados
