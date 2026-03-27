# Portal ACTACV - Product Requirements Document

## Visão Geral
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV).

## Stack Tecnológica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios, PWA (Service Worker)
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication
- **UI Components:** Shadcn/UI, Lucide React

## Funcionalidades Implementadas

### Área Pública
- [x] Homepage com hero responsivo e imagem de aviação
- [x] Sobre Nós - Banner equipa, Quem Somos, Missão, Visão, Valores
- [x] A Profissão - Banner torre controlo, educativo CTA
- [x] Clube de Benefícios - Banner parcerias, grid de parceiros
- [x] Transparência - Banner governança, documentos institucionais
- [x] Contactos - Banner Cabo Verde, formulário e FAQ
- [x] Galeria de Fotos - Álbuns (Aeroportos, Torre, CV, Equipa), lightbox, admin upload
- [x] Validador QR Code Público
- [x] Página de Notícias
- [x] Eventos Públicos

### Área Reservada (Portal do Associado)
- [x] Dashboard responsivo
- [x] Gestão Financeira (table desktop / card view mobile)
- [x] Carteira Digital PWA (offline, QR download, share)
- [x] Sistema de Votações
- [x] Sistema de Eventos/Agenda
- [x] Documentos
- [x] Mural de Comunicação (categories, likes, comments, moderation)
- [x] Clube de Benefícios
- [x] Notificações In-App

### Identidade Visual
- [x] Cores: Carmesim (#C7202F), Grafite (#3A3A3A), Navy (#1B2B4B), Amber (#D4A843)
- [x] Tipografia: Open Sans + JetBrains Mono
- [x] Banners com imagens em TODAS as páginas públicas
- [x] Logo customizado ACCTALogo

### Auditoria UX/Legibilidade (Fev 2026)
- [x] Acentuação portuguesa corrigida em TODAS as páginas (públicas e privadas)
- [x] Contraste do footer melhorado (white/70, white/60, white/50)
- [x] Botões CTA com texto branco sobre fundo carmesim
- [x] Labels de navegação com acentos (Início, Profissão, Benefícios, Transparência)
- [x] Labels privados com acentos (Votações, Notificações, Gestão, Benefícios)

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Status de Testes
- iteration_6: 100% - UX/Legibilidade verificada (todos os acentos e contrastes)
- iteration_5: 100% (64/64 backend)

## Data: 27 Fevereiro 2026

## Próximas Tarefas (Backlog)
- P1: Clube de Benefícios - Lógica de validação QR Code
- P2: Evento em Destaque com countdown na homepage
- P2: Exportar eventos para calendários (Google/Apple Calendar)
- P2: Sistema de recuperação de senha
- P3: Refactoring - Dividir server.py em routers separados (1260+ linhas)
