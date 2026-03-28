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
- [x] HomePage, Sobre, Profissão, Transparência, Benefícios
- [x] Validador QR Code
- [x] **Galeria de Fotos Pública** (28/03/2026) — Álbuns públicos com fotos aprovadas

### Área Privada - Painel
- [x] Dashboard redesenhado (Recharts) + Feed Atividade Recente
- [x] Meu Perfil, Autenticação JWT

### Área Privada - Gestão
- [x] **Módulo Financeiro** (REFATORADO) — CashFlowTab, DRETab, SettingsTab, Export PDF/CSV
- [x] **Módulo Projetos** — CRUD, tarefas, milestones, comentários, orçamento
- [x] **Votações** — Sistema de votação interna
- [x] **Eventos/Agenda** — CRUD com inscrição
- [x] **Documentos** — Upload/download admin

### Área Privada - Comunidade
- [x] **Mural de Comunicação** (MELHORADO) — pesquisa, filtros, likes, comentários, moderação
- [x] **Galeria de Fotos** (IMPLEMENTADO em 28/03/2026):
  - Galeria pública (3 álbuns, só fotos aprovadas) + privada (4 álbuns, inclui privados)
  - Upload por sócios com workflow de aprovação (admin aprova/rejeita)
  - Admin: upload auto-aprovado, CRUD álbuns, gestão de visibilidade (público/privado)
  - Lightbox, grid responsive, 22 fotos iniciais em 4 álbuns (Aeroportos, Torre de Controlo, Cabo Verde, Equipa)
  - Notificação automática: admin notificado de submissões, sócio notificado de aprovação/rejeição
- [x] **Clube de Benefícios** (básico)

### Sistema
- [x] **Notificações Avançadas** — Central com stats, broadcast admin, filtros por tipo
- [x] **Notificações Automáticas** — Projetos + Finanças + Galeria
- [x] **Feed de Atividade Recente** — Dashboard widget
- [x] **Dark Mode** global

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline e identificação digital
- [ ] Clube de Benefícios - QR Code validation avançado

### P2
- [ ] Evento em Destaque com countdown na homepage
- [ ] Exportar eventos para Google/Apple Calendar

## Regras de Negócio
- NÃO existe "Sócio inadimplente" - quotas descontadas em folha
- CSS variables obrigatórias para Dark Mode
- Todos os elementos interativos precisam de data-testid

## Arquitetura
```
/app/backend/routes/
├── gallery.py (CRUD álbuns, upload com aprovação, endpoints públicos)
├── activity.py, finances.py, projects.py, notifications.py, wall.py, auth_routes.py, events.py

/app/frontend/src/
├── pages/private/GaleriaAdminPage.js (galeria privada com upload, aprovação, lightbox)
├── pages/public/GaleriaPage.js (galeria pública)
├── pages/private/financeiro/ (módulos refatorados)
```
