# Portal ACTACV - Product Requirements Document

## Visão Geral
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV).

## Stack Tecnológica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios, PWA
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication

## Sidebar Design (Novo)
- **Desktop:** Fundo branco, sombra suave, 270px aberta / 72px colapsada
- **Lock/Hover:** Bloqueada = fica aberta, desbloqueada = colapsa ao sair do mouse, expande ao hover
- **Secções agrupadas:** PAINEL, GESTÃO, COMUNIDADE, SISTEMA
- **Perfil:** Avatar, nome, email no fundo da sidebar
- **Mobile (<768px):** Overlay sidebar com backdrop blur, hamburger no header
- **Tablet/Desktop (≥768px):** Sidebar fixa à esquerda

## Breakpoints
| Dispositivo | Largura | Tailwind |
|-------------|---------|----------|
| Min | 320px | min-width |
| Mobile xs | 360px+ | xs: |
| Mobile sm | 640px+ | sm: |
| Tablet | 768px+ | md: |
| Desktop | 1024px+ | lg: |

## Funcionalidades
- [x] Área Pública (Home, Sobre, Profissão, Transparência, Benefícios, Contactos, Galeria, Eventos)
- [x] Área Reservada (Dashboard, Financeiro, Carteira PWA, Votações, Eventos, Documentos, Mural, Benefícios, Notificações)
- [x] Recuperação de Senha (modo demo)
- [x] Identidade Visual ACCTA
- [x] Acentuação portuguesa completa
- [x] Responsividade 320-1920px
- [x] **Sidebar collapsível com lock/hover** (novo)
- [x] Backend modular (17 ficheiros)

## Credenciais
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Testes
- iteration_10: 100% (17/17) - Novo sidebar design
- iteration_9: 100% (16/16) - Responsividade
- iteration_8: 100% (15/15) - Recuperação de senha
- iteration_7: 100% (38/38) - Refactoring backend

## Próximas Tarefas
- P1: Clube de Benefícios — Lógica de validação QR Code
- P2: Evento em Destaque com countdown na homepage
- P2: Exportar eventos para Google/Apple Calendar
