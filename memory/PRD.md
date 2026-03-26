# Portal ACTACV - Product Requirements Document

## Visao Geral
Ecossistema digital integrado para a Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACTACV).

## Stack Tecnologica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication
- **UI Components:** Shadcn/UI
- **Charts:** Recharts

## Funcionalidades Implementadas

### Area Publica
- [x] **Homepage** com hero impactante (imagem de aviao), estatisticas, secao educativa e noticias
- [x] **Sobre Nos (A Associacao)** - Quem Somos, Missao, Visao, Valores, Corpos Sociais
- [x] **A Profissao** - Educativo sobre CTA, tipos de controlo (TWR, APP, ACC), FIR Sal
- [x] **Clube de Beneficios (Publico)** - Parcerias, como funciona, grid de parceiros
- [x] **Transparencia** - Documentos institucionais, relatorios, indicadores de governanca
- [x] **Contactos** - Formulario, informacoes de contacto, FAQ
- [x] **Validador QR Code Publico**
- [x] **Pagina de Noticias**
- [x] **Eventos Publicos**

### Area Reservada (Portal do Associado)
- [x] **Dashboard** - Resumo personalizado com quotas, votacoes, eventos e notificacoes
- [x] **Gestao Financeira** - Historico de quotas com desconto automatico em folha salarial
- [x] **Carteira Digital (PWA)** - Cartao interativo com QR Code, flip animation, download QR, partilha, acesso offline, indicador de conexao, service worker para cache
- [x] **Sistema de Votacoes** - Votacoes abertas/fechadas com resultados
- [x] **Sistema de Eventos/Agenda** - Criar, visualizar, inscrever-se em eventos
- [x] **Documentos** - Secretaria digital com upload para administradores
- [x] **Mural de Comunicacao Interna** - Posts com categorias (geral, sugestao, discussao, aviso), likes/reacoes, comentarios, moderacao admin (aprovar/rejeitar pendentes), fixar posts, filtros por categoria, auto-aprovacao para admins
- [x] **Clube de Beneficios** - Parcerias com desconto
- [x] **Notificacoes In-App** - Sistema completo de alertas

### Administracao
- [x] **Gestao de Usuarios** - CRUD de socios com alteracao de status
- [x] **Audit Logs** - Historico de acoes
- [x] **Upload de Documentos** - Modal de upload para administradores
- [x] **Moderacao do Mural** - Painel de posts pendentes, aprovar/rejeitar/fixar/deletar

### Identidade Visual
- [x] Cores ACCTA: Vermelho Carmesim (#C7202F) e Cinza Grafite (#3A3A3A)
- [x] Tipografia: Open Sans (headings + body), JetBrains Mono (dados)
- [x] Logo customizado ACCTALogo component

## Perfis de Utilizador
| Perfil | Permissoes |
|--------|-----------|
| Publico | Acesso as paginas publicas |
| Socio Ativo | Acesso completo a area reservada, direito a voto |
| Socio Inadimplente | Acesso restrito, sem direito a voto |
| Financeiro | Gestao financeira + funcionalidades de socio |
| Admin | Acesso total + gestao de usuarios + moderacao |

## Credenciais de Teste
```
Admin:
  Email: admin@accta.cv
  Senha: admin123

Financeiro:
  Email: financeiro@accta.cv
  Senha: fin123

Socio Ativo:
  Email: socio1@accta.cv
  Senha: socio123

Socio Inadimplente:
  Email: inadimplente@accta.cv
  Senha: socio123
```

## API Endpoints Principais

### Autenticacao
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Registo
- `GET /api/auth/me` - Dados do utilizador atual

### Mural (Wall) - NOVO
- `GET /api/wall` - Listar posts aprovados (filtro por categoria)
- `GET /api/wall/pending` - Posts pendentes (admin/moderador)
- `POST /api/wall` - Criar post (auto-approve para admin)
- `PATCH /api/wall/{id}/approve` - Aprovar post
- `DELETE /api/wall/{id}` - Remover post
- `PATCH /api/wall/{id}/pin` - Fixar/desfixar post
- `PATCH /api/wall/{id}/like` - Like/unlike toggle
- `GET /api/wall/{id}/comments` - Listar comentarios
- `POST /api/wall/{id}/comments` - Criar comentario
- `DELETE /api/wall/{id}/comments/{cid}` - Remover comentario

### Eventos
- `GET /api/events`, `POST /api/events`
- `PATCH /api/events/{id}/register`

### Outros
- `GET /api/users`, `GET /api/invoices`, `GET /api/polls`
- `GET /api/documents`, `GET /api/benefits`
- `GET /api/notifications`, `GET /api/stats`

## Arquitetura de Ficheiros
```
/app
├── backend/
│   ├── server.py          # API FastAPI completa
│   ├── uploads/           # Ficheiros enviados
│   ├── tests/             # Testes pytest
│   └── .env
├── frontend/
│   ├── public/
│   │   ├── sw.js          # Service Worker (PWA)
│   │   └── manifest.json  # PWA Manifest
│   ├── src/
│   │   ├── components/    # ACCTALogo, NotificationBell, etc.
│   │   ├── contexts/      # AuthContext, NotificationContext
│   │   ├── layouts/       # PublicLayout, PrivateLayout
│   │   ├── pages/
│   │   │   ├── public/    # HomePage, LoginPage, etc.
│   │   │   └── private/   # Dashboard, Mural, Carteira, etc.
│   │   └── utils/api.js   # Axios config + API calls
│   └── .env
├── scripts/seed_data.py
└── test_reports/
```

## Status de Testes
- **Backend:** 100% (51/51 testes passaram - iteration_3)
- **Frontend:** 100% (todas as paginas funcionando)

## Data de Ultima Atualizacao
Marco 2026

## Proximas Tarefas (Backlog)
- P1: Clube de Beneficios - Logica de validacao QR Code
- P2: Exportar eventos para calendarios pessoais (Google/Apple Calendar)
- P2: Galeria de fotos da equipa e aeroportos
- P2: Sistema de recuperacao de senha
- P2: Exportacao de relatorios financeiros em PDF
- P3: Refactoring - Dividir server.py em routers/models separados
