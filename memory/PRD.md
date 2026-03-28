# Portal ACTACV - Product Requirements Document

## Visao Geral
Ecossistema digital integrado para a Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACTACV).

## Stack Tecnologica
- **Frontend:** React 18, Tailwind CSS, Framer Motion, React Router, Axios, PWA
- **Backend:** FastAPI (Python), MongoDB, JWT Authentication

## Funcionalidades Implementadas

### Area Publica
- [x] Homepage, Sobre, Profissao, Transparencia, Beneficios, Contactos, Galeria, Eventos

### Area Reservada
- [x] Dashboard, Carteira Digital PWA
- [x] Votacoes, Eventos/Agenda, Documentos
- [x] Mural de Comunicacao (categorias, likes, comentarios, moderacao)
- [x] Clube de Beneficios, Notificacoes In-App
- [x] Recuperacao de Senha (modo demo)
- [x] CRUD Perfil do Membro com Cargos e Privilegios
- [x] **Sistema Financeiro Completo**
  - Fluxo de Caixa: CRUD completo de transacoes (receitas/despesas)
  - Relatorio DRE com grafico mensal e categorias
  - **Export PDF do DRE** com layout profissional (header ACCTA, tabela mensal, categorias)
  - Configuracao de quota mensal (padrao 2.000 CVE)
  - Geracao em lote de quotas mensais para todos os socios ativos
  - Categorias: Quotas, Patrocinios, Doacoes, Eventos, Operacional, Juridico, Comunicacao, Viagens
  - Vista simplificada para socios (Minhas Quotas)
  - Regra: Socio ativo NUNCA fica inadimplente (desconto em folha)

### Design & UX
- [x] Identidade Visual ACCTA (Carmesim, Grafite, Open Sans)
- [x] Sidebar collapsivel com lock/hover (fundo branco, seccoes agrupadas)
- [x] Responsividade 320-1920px (mobile/tablet/desktop)

### Backend (Modular)
```
server.py (40L) -> database.py, auth.py, models.py, helpers.py
routes/ -> 14 modulos (auth, users, invoices, polls, posts, documents,
          benefits, wall, events, gallery, notifications, stats, upload, finances)
```

## Credenciais
- Admin: admin@accta.cv / admin123
- Socio: socio1@accta.cv / socio123

## Testes
- iteration_12: 100% (25/25 backend + frontend) - Sistema Financeiro
- iteration_11: 100% (19/19) - CRUD Perfil Membro
- iteration_10: 100% (17/17) - Sidebar
- iteration_9: 100% (16/16) - Responsividade
- iteration_8: 100% (15/15) - Recuperacao de senha
- iteration_7: 100% (38/38) - Refactoring backend

## Proximas Tarefas
- P1: Clube de Beneficios - Logica de validacao QR Code
- P2: Evento em Destaque com countdown na homepage
- P2: Exportar eventos para Google/Apple Calendar
