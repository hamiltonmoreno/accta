# Portal ACTACV - Product Requirements Document

## Visão Geral
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV).

## Stack Tecnológica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios, PWA
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication
- **UI Components:** Shadcn/UI, Lucide React

## Breakpoints de Responsividade
| Dispositivo | Largura | Breakpoint Tailwind |
|-------------|---------|---------------------|
| Mobile (min) | 320px | min-width no html |
| Mobile (xs) | 360px+ | xs: |
| Mobile (sm) | 640px+ | sm: |
| Tablet | 768px+ | md: |
| Desktop | 1024px+ | lg: |
| Desktop XL | 1280px+ | xl: |

## Arquitetura Backend (Modular)
```
backend/
├── server.py (40 linhas), database.py, auth.py, models.py, helpers.py
├── routes/ (13 módulos: auth, users, invoices, polls, posts, documents,
│           benefits, wall, events, gallery, notifications, stats, upload)
```

## Funcionalidades Implementadas
- [x] Área Pública completa (Home, Sobre, Profissão, Transparência, Benefícios, Contactos, Galeria, Eventos)
- [x] Área Reservada (Dashboard, Financeiro, Carteira PWA, Votações, Eventos, Documentos, Mural, Benefícios, Notificações)
- [x] Recuperação de Senha (modo demo com token)
- [x] Identidade Visual ACCTA (Carmesim, Grafite, Open Sans)
- [x] Acentuação portuguesa completa em todas as páginas
- [x] Responsividade verificada: 320px, 375px, 768px, 1024px
- [x] Backend refatorado em módulos

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Testes
- iteration_9: 100% (16/16) - Responsividade 4 viewports
- iteration_8: 100% (15/15) - Recuperação de senha
- iteration_7: 100% (38/38) - Refactoring backend

## Próximas Tarefas
- P1: Clube de Benefícios - Lógica de validação QR Code
- P2: Evento em Destaque com countdown na homepage
- P2: Exportar eventos para Google/Apple Calendar
