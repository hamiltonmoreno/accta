# Portal ACTACV - Product Requirements Document

## Visao Geral
Ecossistema digital integrado para a Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACTACV).

## Stack Tecnologica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication
- **UI Components:** Shadcn/UI, Lucide React

## Funcionalidades Implementadas

### Area Publica
- [x] Homepage com hero responsivo e imagem de aviacao
- [x] Sobre Nos - Banner equipa, Quem Somos, Missao, Visao, Valores
- [x] A Profissao - Banner torre controlo, educativo CTA
- [x] Clube de Beneficios - Banner parcerias, grid de parceiros
- [x] Transparencia - Banner governanca, documentos institucionais
- [x] Contactos - Banner Cabo Verde, formulario e FAQ
- [x] Galeria de Fotos - Albuns (Aeroportos, Torre, CV, Equipa), lightbox, admin upload
- [x] Validador QR Code Publico
- [x] Pagina de Noticias
- [x] Eventos Publicos

### Area Reservada (Portal do Associado)
- [x] Dashboard responsivo
- [x] Gestao Financeira (table desktop / card view mobile)
- [x] Carteira Digital PWA (offline, QR download, share)
- [x] Sistema de Votacoes
- [x] Sistema de Eventos/Agenda
- [x] Documentos
- [x] Mural de Comunicacao (categories, likes, comments, moderation)
- [x] Clube de Beneficios
- [x] Notificacoes In-App

### Identidade Visual
- [x] Cores: Carmesim (#C7202F), Grafite (#3A3A3A), Navy (#1B2B4B), Amber (#D4A843)
- [x] Tipografia: Open Sans + JetBrains Mono
- [x] Banners com imagens em TODAS as paginas publicas
- [x] Logo customizado ACCTALogo

## API Endpoints - Galeria (NOVO)
- GET /api/gallery/albums - Listar albuns (publico)
- GET /api/gallery/albums/{id} - Album individual
- POST /api/gallery/albums - Criar album (admin)
- PATCH /api/gallery/albums/{id} - Atualizar album (admin)
- DELETE /api/gallery/albums/{id} - Remover album (admin)
- GET /api/gallery/photos?album_id=X - Fotos de um album
- POST /api/gallery/photos/upload - Upload foto (admin)
- DELETE /api/gallery/photos/{id} - Remover foto (admin)

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Socio: socio1@accta.cv / socio123

## Status de Testes
- Backend: 100% (64/64 - iteration_5)
- Frontend: 100% (todas funcionalidades verificadas)

## Data: 27 Marco 2026

## Proximas Tarefas (Backlog)
- P1: Clube de Beneficios - Logica de validacao QR Code
- P2: Exportar eventos para calendarios (Google/Apple Calendar)
- P2: Sistema de recuperacao de senha
- P3: Refactoring - Dividir server.py em routers separados
