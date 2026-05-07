# Portal ACCTA

Portal institucional e sistema de gestao associativa para a Associacao dos Controladores de Trafego Aereo de Cabo Verde.

## Quick Start

### Credenciais de Teste

| Perfil | Email | Senha |
|--------|-------|-------|
| Admin | admin@controlador.cv | admin123 |
| Financeiro | financeiro@controlador.cv | fin123 |
| Socio | socio1@controlador.cv | socio123 |

### Desenvolvimento Local

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
yarn install
yarn start
```

### Seed de Dados

```bash
cd scripts
python seed_data.py
```

## Stack

- **Frontend:** React, Tailwind CSS, Framer Motion, Recharts, Shadcn/UI
- **Backend:** FastAPI (Python), Motor (async MongoDB), JWT
- **Database:** MongoDB
- **CI/CD:** GitHub Actions

## Documentacao

- [Guia de Deploy](DEPLOY.md)
- [Configuracao SSH](SSH_SETUP.md)
- [Analise de Melhorias](ANALISE_MELHORIAS.md)
- [Sistema de Notificacoes](SISTEMA_NOTIFICACOES.md)
- [Detalhes do Projeto](PROJETO_ACCTA.md)
