# Portal ACCTA - Product Requirements Document

## Problema Original
Ecossistema digital integrado para a Associacao dos Controladores de Trafego Aereo de Cabo Verde (ACCTA). Portal institucional publico + area reservada para associados.

## Stack Tecnica
- **Frontend:** React, Tailwind CSS, Recharts, Framer Motion (Modo Claro exclusivo)
- **Backend:** Python FastAPI, PostgreSQL (Supabase) — DAO assíncrono Mongo-compatível sobre asyncpg em database.py, JWT Auth, slowapi, Resend (email)
- **Extras:** fpdf2 (PDF), date-fns (datas)

## Credenciais de Teste
- Admin: admin@controlador.cv / admin123
- Financeiro: financeiro@controlador.cv / fin123
- Socio: socio1@controlador.cv / socio123

## Modulos Implementados

### Area Publica
- [x] HomePage com Evento em Destaque + countdown
- [x] Sobre, Profissao, Transparencia, Beneficios
- [x] Validador QR Code, Galeria Publica

### Area Privada
- [x] Dashboard + Relatorio Atividade Pessoal + Feed
- [x] Financeiro (REFATORADO), Projetos, Votacoes, Eventos, Documentos
- [x] Mural, Galeria com aprovacao, Clube Beneficios, Carteira Digital

### Autenticacao (INVITE ONLY + EMAIL)
- [x] Registo publico ELIMINADO
- [x] Convite por admin com envio de email via Resend
- [x] Pagina setup-account com token
- [x] Email de boas-vindas ao ativar conta
- [x] Email de recuperacao de senha
- [x] CLI create_admin.py para bootstrap
- [x] Templates HTML branded ACCTA

### Seguranca
- [x] SECRET_KEY obrigatoria, CORS seguro, Rate limiting
- [x] SSE notificacoes, ProtectedRoute com roles, Limite upload

## Fluxo Email em Producao
```
1. Verificar dominio controlador.cv no Resend (https://resend.com/domains)
2. Configurar .env: RESEND_API_KEY=re_xxx, SENDER_EMAIL=noreply@controlador.cv
3. Admin convida socio -> email enviado automaticamente
4. Socio clica no link do email -> define senha -> conta ativa
5. Forgot password -> email com codigo -> reset
```

Nota: Sem dominio verificado, o link de convite e gerado e copiavel manualmente.

## Deploy
- [x] CI/CD GitHub Actions (.github/workflows/deploy.yml)
- [x] Guia generico DEPLOY.md
- [x] Guia Vercel VERCEL_DEPLOY.md
- [x] Checklist Hostinger VPS HOSTINGER_DEPLOY.md (Feb 2026) - passo-a-passo com comandos prontos para Ubuntu 22/24, Nginx + SSL + Supervisor + PostgreSQL (Supabase) + primeiro admin + GitHub Secrets

## Backlog

### P1
- [ ] Carteira Digital (PWA) - funcionalidade offline
- [ ] Clube de Beneficios - QR Code validation avancado

### P2
- [ ] Exportar eventos para Google/Apple Calendar
- [ ] Migrar uploads para object storage (S3/R2)
- [ ] React Query/SWR para cache de dados
