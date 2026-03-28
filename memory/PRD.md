# Portal ACTACV - Product Requirements Document

## Problema Original
Ecossistema digital integrado para a Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACTACV). Portal institucional publico + area reservada para associados.

## Stack Tecnica
- **Frontend:** React, Tailwind CSS, Recharts, Framer Motion (Modo Claro exclusivo)
- **Backend:** Python FastAPI (Router modular), MongoDB (Motor async), JWT Auth, slowapi (rate limiting)
- **Extras:** fpdf2 (PDF), date-fns (datas)

## Credenciais de Teste
- Admin: admin@accta.cv / admin123
- Financeiro: financeiro@accta.cv / fin123
- Socio: socio1@accta.cv / socio123

## Modulos Implementados

### Area Publica (COMPLETA)
- [x] HomePage, Sobre, Profissao, Transparencia, Beneficios
- [x] Validador QR Code
- [x] Galeria de Fotos Publica
- [x] Evento em Destaque com countdown timer animado

### Area Privada - Painel
- [x] Dashboard redesenhado (Recharts) + Feed Atividade Recente
- [x] Relatorio de Atividade Pessoal (8 metricas)
- [x] Meu Perfil, Autenticacao JWT
- [x] Carteira Digital com QR Code

### Area Privada - Gestao
- [x] Modulo Financeiro (REFATORADO) — CashFlowTab, DRETab, SettingsTab, Export PDF/CSV
- [x] Modulo Projetos — CRUD, tarefas, milestones, comentarios, orcamento
- [x] Votacoes — Sistema de votacao interna
- [x] Eventos/Agenda — CRUD com inscricao
- [x] Documentos — Upload/download admin

### Area Privada - Comunidade
- [x] Mural de Comunicacao (MELHORADO)
- [x] Galeria de Fotos — Upload com workflow de aprovacao
- [x] Clube de Beneficios (basico)

### Sistema
- [x] Notificacoes Avancadas + Automaticas
- [x] CI/CD — GitHub Actions
- [x] Dark Mode REMOVIDO
- [x] Quotas pendentes REMOVIDAS

### Seguranca (CORRIGIDO)
- [x] SECRET_KEY sem fallback inseguro — erro se nao definida
- [x] CORS seguro — credentials=True apenas com origens explicitas
- [x] Registo publico restrito a role=socio
- [x] Rate limiting: login 10/min, register 5/min, forgot 3/min, reset 5/min

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline
- [ ] Clube de Beneficios - QR Code validation avancado

### P2
- [ ] Exportar eventos para Google/Apple Calendar

## Regras de Negocio
- NAO existe "Socio inadimplente" — quotas descontadas em folha
- NAO existem "Quotas Pendentes"
- Dark Mode DESATIVADO
- Registo publico so cria contas socio

## Configuracao de Producao (.env)
```
SECRET_KEY=<chave-forte-64-chars>
MONGO_URL=<connection-string>
DB_NAME=<nome-db>
CORS_ORIGINS=https://portal.accta.cv,https://www.accta.cv
```
Nota: CORS_ORIGINS=* desativa allow_credentials automaticamente (seguro para dev).
