# Portal ACCTA - Associacao de Controladores de Trafego Aereo de Cabo Verde

## Visao Geral

Portal institucional completo e sistema de gestao associativa (SGA) para a ACCTA, oferecendo transparencia institucional, eficiencia administrativa e valorizacao da profissao de Controlador de Trafego Aereo em Cabo Verde.

## Funcionalidades

### Area Publica (Institucional)
- **Homepage Hero**: Apresentacao impactante com tematica aeronautica
- **Sobre a Profissao**: Informacoes completas sobre controladores de trafego aereo
- **Transparencia Financeira**: Pagina publica com metricas e prestacao de contas
- **Galeria de Fotos**: Albums publicos com fotos dos aeroportos e equipa
- **Validador de Carteira**: Validacao publica de carteiras de socios via QR Code

### Area Privada (Portal do Associado)
- **Dashboard Personalizado**: Resumo financeiro, votacoes abertas, eventos proximos, feed de atividade recente
- **Carteira Digital**: Identificacao digital com QR Code criptografado (SHA-256)
- **Gestao Financeira**: Acompanhamento de contribuicoes (desconto em folha salarial) com export PDF/CSV
- **Sistema de Votacoes**: Participacao democratica em decisoes da associacao
- **Gestao de Projetos**: CRUD completo com tarefas, milestones, comentarios e orcamento
- **Eventos/Agenda**: Sistema de eventos com inscricao e calendario
- **Documentos**: Acesso a atas, estatutos e balancetes (upload/download admin)
- **Mural de Comunicacao**: Canal de interacao entre socios com pesquisa, filtros, likes e moderacao
- **Galeria de Fotos Privada**: Upload com workflow de aprovacao, albuns privados
- **Clube de Beneficios**: Descontos exclusivos com validacao QR Code
- **Notificacoes Avancadas**: Central de notificacoes com broadcast admin, filtros por tipo, auto-trigger

### Area Administrativa
- **Gestao de Utilizadores**: CRUD com alteracao de cargo, funcao e privilegios
- **Dashboard Financeiro**: Graficos de receitas/despesas, DRE, cash flow
- **Gestao de Galeria**: Aprovacao de fotos, CRUD de albuns
- **Audit Logs**: Rastreio completo de acoes administrativas

## Credenciais de Demonstracao

| Perfil | Email | Senha |
|--------|-------|-------|
| Administrador | admin@controlador.cv | admin123 |
| Financeiro | financeiro@controlador.cv | fin123 |
| Socio Ativo | socio1@controlador.cv | socio123 |

> **Nota:** Nao existe o conceito de "socio inadimplente" nesta associacao. Todas as quotas sao descontadas diretamente na folha salarial.

## Stack Tecnico

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19 + Tailwind CSS + Framer Motion + Shadcn/UI + Recharts |
| Backend | FastAPI (Python) + Motor (async MongoDB) |
| Base de Dados | MongoDB (colecoes: users, invoices, polls, events, documents, wall_posts, notifications, projects, gallery_albums, gallery_photos) |
| Autenticacao | JWT + RBAC (admin, socio, financeiro, moderador) |
| CI/CD | GitHub Actions (ci.yml + deploy.yml) |
| Design | Identidade visual ACCTA (Vermelho Carmesim #C7202F, Cinza Grafite #3A3A3A, Open Sans) |

## Regras de Negocio Importantes

- Quotas sao descontadas em folha salarial — nao existem cotas pendentes
- Nao existe o status "inadimplente" — apenas ativo e inativo
- Modo escuro esta desativado
- Fotos submetidas por socios requerem aprovacao do admin

## URLs

- **Frontend**: https://traffic-portal-2.preview.emergentagent.com
- **Backend API**: https://traffic-portal-2.preview.emergentagent.com/api

## Estrutura do Projeto

```
/app
├── .github/workflows/          # CI/CD (ci.yml, deploy.yml)
├── frontend/
│   ├── src/
│   │   ├── components/         # Componentes reutilizaveis (ACCTALogo, NotificationBell, etc.)
│   │   ├── contexts/           # AuthContext, NotificationContext, ThemeContext
│   │   ├── layouts/            # PublicLayout, PrivateLayout
│   │   ├── pages/public/       # HomePage, Sobre, Profissao, Transparencia, Galeria
│   │   ├── pages/private/      # Dashboard, Financeiro, Projetos, Votacoes, Eventos, etc.
│   │   └── utils/api.js        # Camada de API centralizada
│   └── tailwind.config.js
├── backend/
│   ├── routes/                 # Routers modulares (gallery, activity, notifications, etc.)
│   ├── models.py               # Modelos Pydantic
│   ├── server.py               # Entry point FastAPI
│   └── .env                    # Variaveis de ambiente
├── scripts/seed_data.py        # Seed de dados de demonstracao
├── DEPLOY.md                   # Guia de deploy
└── SSH_SETUP.md                # Configuracao SSH para CI/CD
```

---

Desenvolvido com Emergent AI | 2025-2026
