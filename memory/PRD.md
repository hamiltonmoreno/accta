# Portal ACTACV - Product Requirements Document

## Visão Geral
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV).

## Stack Tecnológica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication
- **UI Components:** Shadcn/UI
- **Charts:** Recharts

## Funcionalidades Implementadas

### Área Pública
- [x] Homepage com apresentação da associação
- [x] Página de Notícias
- [x] Página "A Profissão"
- [x] Transparência Institucional
- [x] Validador QR Code Público

### Área Reservada (Portal do Associado)
- [x] **Dashboard** - Resumo personalizado com quotas, votações e notificações
- [x] **Gestão Financeira** - Histórico de quotas com desconto automático em folha salarial
- [x] **Carteira Digital** - Cartão interativo com QR Code para validação
- [x] **Sistema de Votações** - Votações abertas/fechadas com resultados
- [x] **Documentos** - Secretaria digital com upload para administradores
- [x] **Mural Interno** - Comunicação entre associados
- [x] **Clube de Benefícios** - Parcerias com desconto
- [x] **Notificações In-App** - Sistema completo de alertas

### Administração
- [x] **Gestão de Usuários** - CRUD de sócios com alteração de status
- [x] **Audit Logs** - Histórico de ações
- [x] **Upload de Documentos** - Modal de upload para administradores

## Perfis de Utilizador
| Perfil | Permissões |
|--------|-----------|
| Público | Acesso às páginas públicas |
| Sócio Ativo | Acesso completo à área reservada, direito a voto |
| Sócio Inadimplente | Acesso restrito, sem direito a voto |
| Financeiro | Gestão financeira + funcionalidades de sócio |
| Admin | Acesso total + gestão de usuários |

## Credenciais de Teste
```
Admin:
  Email: admin@accta.cv
  Senha: admin123

Financeiro:
  Email: financeiro@accta.cv
  Senha: fin123

Sócio Ativo:
  Email: socio1@accta.cv
  Senha: socio123

Sócio Inadimplente:
  Email: inadimplente@accta.cv
  Senha: socio123
```

## API Endpoints Principais

### Autenticação
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Registo
- `GET /api/auth/me` - Dados do utilizador atual

### Utilizadores
- `GET /api/users` - Listar utilizadores (admin/financeiro)
- `PATCH /api/users/{id}/status` - Alterar status (admin)

### Financeiro
- `GET /api/invoices` - Listar quotas
- `POST /api/invoices` - Criar quota (admin/financeiro)
- `PATCH /api/invoices/{id}/confirm` - Confirmar pagamento

### Votações
- `GET /api/polls` - Listar votações
- `POST /api/polls` - Criar votação (admin)
- `POST /api/polls/vote` - Votar
- `GET /api/polls/{id}/results` - Resultados

### Documentos
- `GET /api/documents` - Listar documentos
- `POST /api/documents` - Criar documento (admin)
- `POST /api/upload/{category}` - Upload de ficheiro

### Notificações
- `GET /api/notifications` - Listar notificações
- `GET /api/notifications/unread/count` - Contagem não lidas
- `PATCH /api/notifications/{id}/read` - Marcar como lida
- `PATCH /api/notifications/mark-all-read` - Marcar todas como lidas

## Arquitetura de Ficheiros
```
/app
├── backend/
│   ├── server.py          # API FastAPI completa
│   ├── uploads/           # Ficheiros enviados
│   │   ├── documents/
│   │   ├── avatars/
│   │   ├── logos/
│   │   └── proofs/
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/    # Componentes reutilizáveis
│   │   ├── contexts/      # AuthContext, NotificationContext
│   │   ├── layouts/       # PublicLayout, PrivateLayout
│   │   ├── pages/
│   │   │   ├── public/    # HomePage, LoginPage, etc.
│   │   │   └── private/   # DashboardPage, VotacoesPage, etc.
│   │   └── utils/
│   │       └── api.js     # Axios config + API calls
│   └── .env
├── scripts/
│   └── seed_data.py       # Script de dados de demonstração
└── test_reports/
    ├── iteration_1.json
    └── iteration_2.json
```

## Status de Testes
- **Backend:** 100% (28/28 testes passaram)
- **Frontend:** 100% (todas as páginas funcionando)

## Data de Última Atualização
Fevereiro 2026

## Próximas Melhorias Sugeridas
1. Sistema de recuperação de senha
2. Exportação de relatórios financeiros em PDF
3. Sistema de eventos/agenda
4. Chat interno entre sócios
5. Integração com calendário para assembleias
