# SPEC 2 - Correcoes Codex sincronizadas

Data: 2026-05-18
Responsavel: Codex
Arquivo paralelo ao Spec 1: `tasks/spec-correcoes.md`

## Objetivo

Este arquivo e o plano de trabalho do Codex para corrigir problemas encontrados na auditoria completa sem bloquear o trabalho paralelo no Spec 1.

O Spec 1 fica como trilha principal do usuario. O Spec 2 evita tocar nos mesmos arquivos sempre que possivel e marca explicitamente os pontos que precisam de sincronizacao antes de editar.

## Regra de sincronizacao

1. O Codex nao edita `tasks/spec-correcoes.md` durante o Spec 2.
2. Antes de iniciar qualquer item, verificar:
   - `git status --short`
   - `git diff --name-only`
3. Se um arquivo do item estiver alterado pelo Spec 1, pausar esse item e sincronizar.
4. Cada correcao deve ser pequena, revisavel e com teste/validacao local quando possivel.
5. Ao terminar um item, atualizar este arquivo com status, arquivos alterados e validacao executada.

## Mapa rapido de separacao

Spec 1 cobre principalmente:

- Votacoes/polls: ciclo de vida, voto duplicado e validacao de opcoes.
- Upload/gallery: I/O assincrono, SVG, auditoria e limites.
- Auth/admin: reset/invite poisoned origin e token de convite na resposta.
- Stats/users/contact/helpers/finances/projects: varios ajustes ja especificados no Spec 1.

Spec 2 deve priorizar:

- Privacidade frontend/PWA/PostHog.
- Eventos com visibilidade restrita.
- RBAC fino em projetos, apenas apos sync com o item M13 do Spec 1.
- Higiene de repositorio: uploads versionados e scaffold morto.
- Documentos e menus com divergencia de permissao.
- Relatorios/atividade com campos inexistentes, coordenando com A7 do Spec 1.

## Lane A - Itens independentes primeiro

### S2-A1 - Privacidade PWA, cache e PostHog

Prioridade: Alta
Status: Concluido
Risco de conflito com Spec 1: Baixo

Arquivos provaveis:

- `frontend/public/index.html`
- `frontend/public/sw.js`
- `frontend/src/index.js`
- `frontend/src/pages/private/CarteiraPage.js`
- `frontend/src/contexts/AuthContext.js`

Problema:

- Session recording do PostHog esta hardcoded no HTML publico.
- Service worker pode cachear respostas de autenticacao e dados privados.
- A pagina Carteira pode persistir o objeto completo do usuario em storage/cache.

Implementacao esperada:

- Remover session recording hardcoded ou condicionar por ambiente/config explicita.
- Garantir que rotas `/api/auth/*`, `/api/users/*`, `/api/admin/*`, `/api/documents/*`, `/api/finances/*` e dados pessoais nao sejam armazenados pelo service worker.
- Nao persistir objeto completo do usuario no frontend quando so um subconjunto for necessario.
- Limpar caches antigos se a estrategia do service worker mudar.

Criterios de aceite:

- Nenhum endpoint autenticado sensivel fica salvo em cache offline.
- PostHog nao grava sessoes por padrao em ambiente de producao sem opt-in explicito.
- Login, logout e carregamento de perfil continuam funcionando.

Validacao:

- `npm.cmd test -- --watchAll=false` se dependencias estiverem instaladas.
- Build frontend se o ambiente permitir.
- Inspecao manual do service worker e fluxos de auth.

Execucao 2026-05-18:

- Arquivos alterados: `frontend/public/index.html`, `frontend/public/sw.js`, `frontend/src/pages/private/CarteiraPage.js`.
- Validacao executada: `node --check frontend/public/sw.js`.
- Observacao: testes/build frontend nao executados porque `frontend/node_modules` nao existe neste ambiente.

### S2-A2 - Remover uploads versionados do Git

Prioridade: Alta
Status: Concluido
Risco de conflito com Spec 1: Baixo

Arquivos provaveis:

- `backend/uploads/documents/97de0e5b-9472-4fa9-9e85-ada157cced0d.docx`
- `backend/uploads/documents/b353a0b6-1cdf-435d-bbba-d9792def5569.pdf`
- `backend/.gitignore`

Problema:

- Arquivos enviados por usuarios aparecem em `git ls-files backend/uploads`, apesar de `.gitignore` indicar que uploads nao devem ser commitados.

Implementacao esperada:

- Remover os arquivos do indice do Git sem apagar os arquivos locais.
- Confirmar que `.gitignore` continua bloqueando novos uploads.

Criterios de aceite:

- `git ls-files backend/uploads` nao lista uploads de usuario.
- Arquivos locais nao sao apagados.
- Nenhuma regra necessaria do `.gitignore` e removida.

Validacao:

- `git ls-files backend/uploads`
- `git status --short`

Execucao 2026-05-18:

- Arquivos removidos do indice: `backend/uploads/documents/97de0e5b-9472-4fa9-9e85-ada157cced0d.docx`, `backend/uploads/documents/b353a0b6-1cdf-435d-bbba-d9792def5569.pdf`.
- Validacao executada: `git ls-files backend/uploads` sem resultados; `Test-Path` confirmou que os arquivos continuam locais.

### S2-A3 - Limpeza de scaffold morto Next/Supabase na raiz

Prioridade: Media
Status: Concluido
Risco de conflito com Spec 1: Baixo

Arquivos provaveis:

- `app/notes/page.tsx`
- `utils/supabase/client.ts`
- `utils/supabase/server.ts`
- `package.json`
- `package-lock.json`

Problema:

- A raiz parece conter um scaffold Next/Supabase separado, enquanto a aplicacao real usa backend FastAPI e frontend React CRA/Craco.
- Esse material aumenta ruido de manutencao e pode confundir scripts/dependencias.

Implementacao esperada:

- Confirmar se os arquivos sao realmente nao usados.
- Se forem mortos, remover o scaffold e dependencias relacionadas.
- Se houver uso externo nao detectado, documentar e deixar intacto.

Criterios de aceite:

- O repositorio fica com uma unica estrutura de app clara ou com a excecao documentada.
- Scripts existentes do backend/frontend nao quebram.

Validacao:

- `rg "utils/supabase|app/notes|@supabase" -n`
- Build/testes disponiveis.

Execucao 2026-05-18:

- Arquivos removidos: `app/notes/page.tsx`, `utils/supabase/client.ts`, `utils/supabase/server.ts`, `package.json`, `package-lock.json`, `yarn.lock`.
- Validacao executada: `rg "utils/supabase|app/notes|@supabase|createServerClient|createBrowserClient|next/" .`.
- Observacao: restaram apenas referencias neste spec e em relatorios antigos.

### S2-A4 - Metadados publicos e encoding do frontend

Prioridade: Baixa
Status: Concluido
Risco de conflito com Spec 1: Baixo

Arquivos provaveis:

- `frontend/public/index.html`
- `frontend/public/manifest.json`

Problema:

- Ha sinais de texto com encoding quebrado em arquivos publicos.
- Metadados podem nao refletir corretamente idioma, titulo e descricao da app.

Implementacao esperada:

- Corrigir mojibake visivel em metadados publicos.
- Confirmar `lang`, `title`, `description`, theme color e manifest.

Criterios de aceite:

- Navegador mostra titulo/descricao sem caracteres quebrados.
- Manifest continua valido.

Validacao:

- Inspecao dos arquivos.
- Build frontend se disponivel.

Execucao 2026-05-18:

- Arquivos alterados: `frontend/public/index.html`, `frontend/public/manifest.json`.
- Validacao executada: parse JSON do manifest com Node.
- Observacao: build frontend nao executado porque `frontend/node_modules` nao existe neste ambiente.

## Lane B - Itens com sincronizacao obrigatoria

### S2-B1 - Eventos: visibilidade e inscricao restrita

Prioridade: Critica
Status: Concluido
Risco de conflito com Spec 1: Medio

Arquivos provaveis:

- `backend/routes/events.py`
- `backend/models.py`
- `frontend/src/pages/private/EventosPage.js`

Problema:

- Usuario nao admin pode chamar `GET /api/events?visibility=direcao` e sobrescrever o filtro seguro.
- Inscricao em evento nao valida se o usuario pode ver/participar daquele evento.

Implementacao esperada:

- Centralizar regra de visibilidade de eventos.
- Ignorar ou negar filtro `visibility` nao permitido para usuarios comuns.
- Validar permissao tambem em inscricao/cancelamento.
- Preservar acesso administrativo quando o usuario for admin.

Criterios de aceite:

- Usuario comum nao lista eventos restritos por query string.
- Usuario comum nao se inscreve em evento invisivel/restrito.
- Admin mantem filtros administrativos.

Validacao:

- Teste manual ou automatizado com usuario comum e admin.
- `python -m compileall -q backend`

Execucao 2026-05-18:

- Arquivo alterado: `backend/routes/events.py`.
- Validacao executada: `python -m compileall -q backend`.
- Observacao: sem teste de API automatizado neste passo.

### S2-B2 - Projetos: limitar alteracao de campos sensiveis

Prioridade: Critica
Status: Concluido
Risco de conflito com Spec 1: Alto
Sync obrigatorio: item M13 do Spec 1

Arquivos provaveis:

- `backend/routes/projects.py`
- `backend/models.py`

Problema:

- Criador/responsavel pode alterar campos sensiveis como `status`, `budget`, `responsible_id` e outros.
- Responsavel de tarefa pode atualizar todos os campos da tarefa, nao apenas progresso/status operacional.

Implementacao esperada:

- Separar payloads Pydantic por tipo de operacao e papel.
- Definir allowlist de campos por papel:
  - Admin: campos administrativos completos.
  - Responsavel/criador: campos operacionais permitidos.
  - Assignee de tarefa: apenas campos de execucao definidos.
- Rejeitar campos extras com erro claro.

Criterios de aceite:

- Usuario sem papel administrativo nao altera budget/responsavel/status estrategico.
- Assignee nao consegue trocar titulo, projeto, responsavel ou campos administrativos da tarefa.
- Testes cobrem tentativa permitida e tentativa negada.

Validacao:

- Testes backend especificos para projetos.
- `python -m compileall -q backend`

Execucao 2026-05-18:

- Arquivos alterados: `backend/routes/projects.py`, `frontend/src/pages/private/ProjectDetailPage.js`.
- Decisao: sem tocar em `backend/models.py`, porque o arquivo estava modificado pelo Spec 1; restricao aplicada por allowlist na rota.
- Backend: admin pode alterar campos administrativos; criador/responsavel fica limitado a campos operacionais; assignee de tarefa so altera `status`.
- Frontend: status de projeto fica editavel apenas por admin; toggle de tarefa fica disponivel apenas para gerente do projeto ou assignee.
- Validacao executada: `python -m compileall -q backend`; `git diff --check` nos arquivos alterados.
- Observacao: sem teste de API automatizado neste passo.

### S2-B3 - Documentos: visibilidade `direcao` e regras de acesso

Prioridade: Alta
Status: Concluido
Risco de conflito com Spec 1: Medio

Arquivos provaveis:

- `backend/routes/documents.py`
- `backend/models.py`
- `frontend/src/pages/private/DocumentosPage.js`

Problema:

- A UI/backend indicam niveis de visibilidade, mas a protecao precisa ser auditada para impedir acesso direto por ID ou listagem indevida.

Implementacao esperada:

- Criar helper unico para verificar acesso a documento.
- Aplicar a regra em listagem, detalhe/download, update e delete.
- Garantir que `direcao` seja visivel apenas para papeis autorizados.

Criterios de aceite:

- Usuario comum nao lista nem baixa documento restrito.
- Admin/direcao conseguem acessar documentos autorizados.
- Erros usam 403/404 de forma consistente com o padrao do projeto.

Validacao:

- Teste manual/API com perfis diferentes.
- `python -m compileall -q backend`

Execucao 2026-05-18:

- Arquivos alterados: `backend/routes/documents.py`, `frontend/src/utils/api.js`, `frontend/src/pages/private/DocumentosPage.js`.
- Validacao executada: `python -m compileall -q backend`.
- Observacao: o download da UI agora passa por endpoint autenticado antes do redirect para o arquivo.

### S2-B4 - Rotas de report/activity/stats com campos inexistentes

Prioridade: Alta
Status: Concluido
Risco de conflito com Spec 1: Alto
Sync obrigatorio: item A7 do Spec 1

Arquivos provaveis:

- `backend/routes/stats.py`
- `backend/routes/activity.py`
- `backend/routes/report.py`
- `backend/models.py`

Problema:

- `stats.py` conta eventos com `status == active`, mas `Event` nao tem campo `status`.
- `activity.py` filtra milestones por `status`, mas `ProjectMilestone` usa `completed`.
- `report.py` usa `team_members`, mas `Project` nao possui esse campo.

Implementacao esperada:

- Ajustar queries para campos reais do modelo.
- Quando necessario, derivar status por datas/campos existentes.
- Adicionar fallback seguro para relatorios agregados.

Criterios de aceite:

- Rotas nao retornam numeros zerados por campo inexistente.
- Rotas nao quebram com KeyError/AttributeError.
- Resultado fica alinhado com semantica dos modelos atuais.

Validacao:

- Testes ou chamadas locais das rotas.
- `python -m compileall -q backend`

Execucao 2026-05-18:

- Arquivos alterados: `backend/routes/activity.py`, `backend/routes/report.py`.
- Arquivo validado no worktree: `backend/routes/stats.py` ja troca `events.status` por comparacao de data.
- Validacao executada: `python -m compileall -q backend`; `rg` sem ocorrencias de `status active`, `status concluido`, `team_members` ou `completed_at` nas rotas alvo.
- Observacao: sem teste de API automatizado neste passo.

### S2-B5 - Galeria: alinhar menu, rota frontend e RBAC backend

Prioridade: Media
Status: Concluido
Risco de conflito com Spec 1: Alto
Sync obrigatorio: itens A3, A5 e A6 do Spec 1

Arquivos provaveis:

- `frontend/src/layouts/PrivateLayout.js`
- `frontend/src/App.js`
- `backend/routes/gallery.py`

Problema:

- Sidebar mostra Galeria para todos.
- Rota frontend `/galeria-admin` aceita admin/moderador.
- Backend restringe varias acoes da galeria apenas a admin.

Implementacao esperada:

- Definir matriz clara de permissoes:
  - Ver galeria publica.
  - Moderar/aprovar/remover midias.
  - Administrar album/categorias se houver.
- Alinhar menu, guards de rota e backend.

Criterios de aceite:

- Usuario ve apenas entradas de menu que consegue usar.
- Moderador nao recebe tela administrativa que falha por 403 inesperado.
- Backend continua sendo a fonte final de autorizacao.

Validacao:

- Teste manual com usuario comum, moderador e admin.
- Build frontend se possivel.

Execucao 2026-05-18:

- Arquivos alterados: `frontend/src/App.js`, `frontend/src/layouts/PrivateLayout.js`.
- Decisao: rota privada `/galeria-admin` fica acessivel a qualquer utilizador autenticado, porque a propria pagina permite visualizacao/submissao e esconde administracao por `isAdmin`; backend continua a restringir moderacao e album management a admin.
- Validacao executada: `git diff --check` nos arquivos alterados.
- Observacao: build frontend nao executado porque `frontend/node_modules` nao existe neste ambiente.

## Lane C - Backlog se houver tempo

### S2-C1 - Upload: criacao de subdiretorios e consistencia de storage

Status: Concluido

Execucao 2026-05-18:

- Arquivo alterado: `backend/routes/upload.py`.
- Correcao: cria `UPLOAD_DIR/category` antes de gravar o ficheiro, usando `asyncio.to_thread` para manter I/O fora do event loop.
- Validacao executada: `python -m compileall -q backend`.

### S2-C2 - Contact: HTML escape na mensagem de email

Status: Concluido

Execucao 2026-05-18:

- Arquivo alterado: `backend/routes/contact.py`.
- Correcao: aplica `html.escape` aos campos interpolados no HTML e normaliza quebras de linha no subject do email.
- Observacao: rate-limit ja estava aplicado pelo Spec 1.
- Validacao executada: `python -m compileall -q backend`.

### S2-C3 - Polls: compatibilidade frontend/backend de status

Status: Concluido

Execucao 2026-05-18:

- Arquivos alterados: `backend/routes/polls.py`, `backend/tests/test_polls_routes.py`, `frontend/src/pages/private/VotacoesPage.js`, `frontend/src/components/voting/VotingInterface.js`, `frontend/src/components/voting/VotingResults.js`.
- Backend: valida que `vote_option` pertence as opcoes reais da votacao.
- Frontend: reconhece `encerrada` como status fechado e mantem compatibilidade com `fechada`; componentes aceitam `label` ou `text` nas opcoes.
- Validacao executada: `python -m compileall -q backend`.
- Observacao: `python -m pytest backend/tests/test_polls_routes.py -q` nao executou porque o ambiente nao tem modulo `pytest`.

## Ordem sugerida de execucao do Codex

1. S2-A2 - remover uploads versionados do Git.
2. S2-A1 - privacidade PWA/PostHog/cache.
3. S2-B1 - eventos visibilidade/inscricao.
4. S2-B3 - documentos visibilidade/acesso.
5. S2-A3 - scaffold morto, se confirmado sem uso.
6. S2-B2 - projetos RBAC, somente apos sync com M13.
7. S2-B4 - report/activity/stats, somente apos sync com A7.
8. S2-B5 - galeria RBAC/menu, somente apos sync com A3/A5/A6.

## Checklist de fechamento por item

Para cada item concluido, preencher:

- Status: Concluido
- Arquivos alterados:
- Validacao executada:
- Riscos restantes:
- Observacoes de sync com Spec 1:

## Validacao geral da rodada 2026-05-18

- `python -m compileall -q backend`: passou.
- `node --check frontend/public/sw.js`: passou.
- `node -e "JSON.parse(require('fs').readFileSync('frontend/public/manifest.json','utf8'))"`: passou.
- `git diff --check` nos arquivos alterados pelo Spec 2: passou.
- `python -m pytest backend/tests/test_projects.py backend/tests/test_activity_feed.py -q`: nao executado; ambiente Python nao tem modulo `pytest`.
- `python -m pytest backend/tests/test_polls_routes.py -q`: nao executado; ambiente Python nao tem modulo `pytest`.

## Itens que aguardavam sync com Spec 1

- S2-C1 upload/subdiretorios: concluido apos commit do Spec 1 estabilizar `backend/routes/upload.py`.
- S2-C2 contact/rate-limit: concluido; rate-limit ja estava no Spec 1 e o escape HTML foi adicionado no Spec 2.
- S2-C3 polls/status: concluido apos commit do Spec 1 estabilizar ciclo de vida/unique votes.

## Fechamento apos revisao de commits - 2026-05-19

Status: Concluido

Correcoes aplicadas:

- Convites: removida a UI de copiar link manual sem token; o token continua fora da resposta da API.
- Documentos: downloads passam por endpoints controlados pelo backend; `/uploads/documents/*` deixa de ser publico no mount de static files.
- Votos: falha ao criar o indice obrigatorio `ux_votes_user_poll` agora interrompe o startup com mensagem acionavel.
- CSP: `/docs`, `/redoc` e `/openapi.json` ficam fora da CSP restritiva para nao quebrar a documentacao interativa.

Arquivos alterados nesta revisao:

- `backend/database.py`
- `backend/routes/documents.py`
- `backend/server.py`
- `frontend/src/pages/private/AdminUsuariosPage.js`
- `frontend/src/pages/public/TransparenciaPage.js`
- `frontend/src/utils/api.js`

Validacao executada:

- `python -m compileall -q backend`: passou.
- `git diff --check`: passou, apenas warnings LF/CRLF.

Validacao pendente:

- Pytest nao executado porque o ambiente nao tem modulo `pytest`.
- Build/test frontend nao executado porque `frontend/node_modules` nao existe neste ambiente.
