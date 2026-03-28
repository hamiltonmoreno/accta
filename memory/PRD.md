# Portal ACTACV - Product Requirements Document

## Problema Original
Ecossistema digital integrado para a Associação dos Controladores de Tráfego Aéreo de Cabo Verde (ACTACV). Portal institucional público + área reservada para associados.

## Stack Técnica
- **Frontend:** React, Tailwind CSS, Recharts, Framer Motion, CSS Variables (Dark Mode)
- **Backend:** Python FastAPI (Router modular), MongoDB (Motor async), JWT Auth
- **Extras:** fpdf2 (PDF), date-fns (datas)

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Sócio: socio1@accta.cv / socio123

## Módulos Implementados

### Área Pública (COMPLETA)
- [x] HomePage com hero, sobre, CTA
- [x] Página Sobre Nós
- [x] Página Profissão
- [x] Página Transparência
- [x] Página Benefícios públicos
- [x] Validador QR Code

### Área Privada - Painel
- [x] Dashboard redesenhado (Recharts - donut, area charts)
- [x] Meu Perfil (edição de dados, foto)
- [x] Autenticação JWT

### Área Privada - Gestão
- [x] **Módulo Financeiro** (REFATORADO em 28/03/2026)
  - CashFlowTab: listagem, filtros, pesquisa, paginação, CRUD transações
  - DRETab: relatório anual com gráficos de barras, categorias
  - SettingsTab: configuração de quotas, geração automática
  - Export PDF e CSV
- [x] **Módulo Projetos** - CRUD completo, tarefas, milestones, comentários, orçamento
- [x] **Votações** - Sistema de votação interna
- [x] **Eventos/Agenda** - CRUD com inscrição
- [x] **Documentos** - Upload/download admin

### Área Privada - Comunidade
- [x] **Mural de Comunicação** (MELHORADO em 28/03/2026)
  - Feed de posts com categorias (geral, sugestão, discussão, aviso)
  - Pesquisa full-text por conteúdo/autor
  - Filtros por categoria
  - Likes e comentários
  - Moderação (aprovação/rejeição por admin)
  - Pin de posts
- [x] **Clube de Benefícios** (básico)

### Sistema
- [x] **Notificações** (MELHORADO em 28/03/2026)
  - Central de Notificações com stats cards
  - Painel de broadcast (admin envia para todos os sócios)
  - Filtros por tipo (geral, financeiro, evento, projeto, mural, sistema)
  - Toggle "Não lidas"
  - Eliminar notificação individual
  - Limpar notificações lidas
  - Marcar todas como lidas
  - Ícones e cores por tipo de notificação
- [x] **Dark Mode** global com persistência localStorage

## Refatoração Realizada (28/03/2026)
- FinanceiroPage.js (1067 linhas) → 6 ficheiros:
  - `financeiro/CashFlowTab.js`
  - `financeiro/DRETab.js`
  - `financeiro/SettingsTab.js`
  - `financeiro/TransactionModal.js`
  - `financeiro/MemberFinanceView.js`
  - `financeiro/constants.js`

## Backlog (Próximas Tarefas)

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline e identificação digital
- [ ] Clube de Benefícios - QR Code validation avançado
- [ ] Notificações automáticas em mudanças de projeto/finanças

### P2
- [ ] Evento em Destaque com countdown na homepage
- [ ] Exportar eventos para Google/Apple Calendar
- [ ] Galeria de fotos (equipa, aeroportos de Cabo Verde)

## Regras de Negócio
- NÃO existe "Sócio inadimplente" - quotas descontadas em folha
- CSS variables obrigatórias para Dark Mode (var(--bg-primary), var(--text-primary), etc.)
- Todos os elementos interativos precisam de data-testid

## Arquitetura
```
/app/frontend/src/
├── pages/private/
│   ├── financeiro/ (CashFlowTab, DRETab, SettingsTab, TransactionModal, MemberFinanceView, constants)
│   ├── DashboardPage.js
│   ├── FinanceiroPage.js (orchestrator)
│   ├── MuralPage.js
│   ├── NotificacoesPage.js
│   ├── ProjectsPage.js / ProjectDetailPage.js
│   └── ...
├── contexts/ (AuthContext, ThemeContext, NotificationContext)
└── layouts/ (PublicLayout, PrivateLayout)

/app/backend/
├── routes/ (finances.py, projects.py, notifications.py, wall.py, auth_routes.py, ...)
├── models.py, auth.py, database.py, helpers.py
└── server.py
```
