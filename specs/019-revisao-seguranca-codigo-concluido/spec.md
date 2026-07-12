# Feature Specification: Revisão de Segurança do Código — verificação e endurecimento do Portal ACCTA

**Feature Branch**: `feature/019-revisao-seguranca-codigo`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "segurança do sistema, code security review"

## Contexto de Domínio

O Portal ACCTA já passou por várias rondas de endurecimento (Turnstile anti-bot,
postura RLS deny-all no Supabase, cadeia HMAC nos registos de auditoria, camada
RBAC unificada `role OU privilégio` da spec 018, guarda SSRF no Web Push, cookie
de sessão httpOnly, `bcrypt` fixado, parametrização anti-SQLi no DAO). **Esta
funcionalidade não é uma construção de raiz** — é uma **revisão de segurança
sistemática de todo o código** que faz três coisas:

1. **Prova** que os controlos existentes se mantêm em toda a largura do sistema
   (327 rotas em 34 módulos, das quais 184 recebem `id` — medido em runtime pela
   enumeração de T005, não apenas os que já foram amostrados).
2. **Fecha** as lacunas residuais que uma revisão dirigida da superfície de ataque
   revelou (ver User Stories).
3. **Garante** que as correções não voltam a regredir (guardas automáticas) e
   deixa um registo de achados reutilizável para futuras revisões.

O diagnóstico foi obtido com um levantamento paralelo de 9 domínios de superfície
de ataque (autenticação/sessão; autorização/RBAC/IDOR; injeção/DAO; upload de
ficheiros; segredos/config/CORS; SSRF/pedidos externos; exposição de dados/logs;
frontend/cliente; dependências/cadeia de fornecimento; cabeçalhos/rate-limit/infra).
A conclusão transversal: **a base é sólida, mas há gaps concretos de confidencialidade,
de resistência a abuso (rate-limit e DoS) e de cadeia de fornecimento** que um
atacante autenticado — ou, em alguns casos, anónimo — poderia explorar hoje.

Esta funcionalidade **não** introduz funcionalidades novas para o utilizador nem
altera o modelo de dados; preserva o comportamento existente **exceto quando o
próprio comportamento é a vulnerabilidade**.

### O que está FORA de âmbito (já endurecido — não voltar a discutir)

Os controlos abaixo estão implementados e verificados por specs anteriores. A
revisão apenas **confirma que se mantêm**; não os reconstrói nem os re-litiga:

- Turnstile anti-bot nos formulários públicos (login/registo/recuperação/contacto)
- Postura RLS deny-all no Supabase + role de runtime `BYPASSRLS`
- Cadeia de integridade HMAC nos `audit_logs` (à prova de adulteração)
- Camada RBAC unificada (`has_role_or_privilege`/`is_admin`/`module_gate` +
  `governance.MODULE_ACCESS`) e o tripwire `test_no_inline_role_checks` (spec 018)
- Fixação `algorithms=["HS256"]` em todas as descodificações de JWT
- Migração do token de sessão para cookie httpOnly + `CSRFOriginCheckMiddleware`
- Fronteira de parametrização anti-SQLi no DAO (valores como parâmetros `$n`,
  allowlist de identificadores) — a revisão **estende a cobertura de teste**, não
  reconstrói a fronteira
- Pin `bcrypt==4.0.1` (deliberado, documentado — não «atualizar»)
- MFA/2FA removido (não reimplementar)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nenhum dado de sócio acessível a quem não deve (Priority: P1)

O bem mais sensível da associação são os dados dos sócios: comprovativos
financeiros, documentos pessoais, dados de saúde/contacto e o histórico
financeiro. Um sócio comum — ou, no pior caso, um visitante anónimo — **não deve
conseguir** chegar a dados de outro sócio nem a artefactos confidenciais.

A revisão dirigida encontrou aqui os gaps de maior impacto: (a) os **comprovativos
financeiros** (`proofs`) e outras categorias de upload são servidos por um ponto
estático **sem autenticação** — só a categoria `documents` está protegida, pelo
que qualquer URL de um comprovativo que vaze (referer, partilha, logs) dá acesso
permanente e não autenticado a dados financeiros pessoais; (b) o DAO devolve o
**documento inteiro** (incluindo o hash da palavra-passe) quando uma rota pede uma
projeção «vazia», por isso a segurança depende de cada autor lembrar-se de a
restringir — um único `return` descuidado expõe hashes; (c) um **validador público
de carteira por QR** devolve nome, nº de sócio e datas a qualquer chamador anónimo,
sem limite de ritmo; (d) a maior parte dos módulos grandes de rotas (assembleias,
participação, prestação de contas, sanções, atos) **nunca foi auditada endpoint a
endpoint** para confirmar que cada leitura/escrita por `id` verifica a posse do
objeto (IDOR).

**Why this priority**: é onde vive o risco de confidencialidade real e imediato,
com impacto direto em dados financeiros e pessoais de sócios. Entregar só isto já
remove a exposição mais grave.

**Independent Test**: tentar obter um comprovativo financeiro e um documento de
outro sócio **sem sessão** e **com a sessão de um sócio não autorizado** → ambos
negados; varrer os endpoints que recebem um `id` e confirmar que cada um verifica
posse/autorização antes de ler ou mutar; confirmar que nenhuma resposta contém
`password`/segredos.

**Acceptance Scenarios**:

1. **Given** um comprovativo financeiro (categoria confidencial) carregado por um
   sócio, **When** um visitante anónimo (ou outro sócio sem autorização) tenta
   descarregá-lo pelo seu URL, **Then** o pedido é negado (não servido em claro).
2. **Given** qualquer endpoint que devolve dados de utilizador ou documento,
   **When** a resposta é serializada, **Then** nunca contém o campo `password`
   (hash), segredos de MFA legados, nem tokens de convite/recuperação.
3. **Given** um endpoint que recebe o `id` de um objeto pertencente a um sócio ou a
   um órgão, **When** um sócio sem relação com esse objeto o invoca, **Then** o
   acesso é negado (com resposta que não revela a existência do objeto).
4. **Given** o validador público de carteira, **When** é invocado repetidamente com
   hashes adivinhados, **Then** existe limite de ritmo e a resposta expõe apenas os
   dados estritamente necessários à validação.

---

### User Story 2 - Perímetro de autenticação e sessão sem arestas exploráveis (Priority: P2)

O perímetro de entrada (login, recuperação de palavra-passe, convite, sessão)
está bem construído, mas a revisão encontrou arestas que enfraquecem as garantias
prometidas: (a) **todo o modo de produção depende de uma única variável de
ambiente** — se `ENVIRONMENT` não estiver definida corretamente em produção, o
cookie perde `Secure`, o HSTS cai, a documentação da API fica exposta e o CORS
deixa de ser restrito, **tudo de uma vez e em silêncio**; (b) o `SECRET_KEY`
aceita qualquer valor não vazio, sem exigência de comprimento/entropia — uma chave
fraca permite forjar tokens JWT (HS256) e escalar a admin; (c) o **rate-limiting
não protege o que promete**: o limite global «200/min» documentado nunca é
aplicado (falta o middleware), só 7 endpoints têm limite explícito, e a chave de
limite é o IP do proxy — atrás do reverse proxy de produção todos os clientes
partilham um único balde, pelo que o limite por-IP colapsa e o brute-force
distribuído passa indetetável; (d) a postura **CSRF** depende inteiramente de uma
verificação de `Origin/Referer` no backend (o cliente não envia token anti-CSRF e
o cookie é `SameSite=None`), pelo que essa verificação tem de cobrir **todos** os
métodos que alteram estado; (e) existem oráculos de **enumeração/timing** (o login
salta o `bcrypt` para emails inexistentes; o registo devolve mensagens distintas).

**Why this priority**: são vetores de tomada de conta, forja de token, força bruta
e degradação silenciosa de toda a postura de produção — de gravidade alta, mas a
seguir à confidencialidade direta porque exigem mais esforço/condições do atacante.

**Independent Test**: iniciar produção com `ENVIRONMENT` em falta → o arranque
recusa ou não degrada os controlos; arrancar com um `SECRET_KEY` curto → recusado;
gerar volume de login a partir de múltiplos IPs atrás do proxy → o limite aplica-se
por cliente real, não por IP do proxy; disparar um pedido de mutação a partir de
uma origem não autorizada → recusado.

**Acceptance Scenarios**:

1. **Given** um deploy de produção, **When** a variável que ativa a postura de
   produção está em falta ou incorreta, **Then** o sistema recusa arrancar (ou não
   permite que cookie-seguro/HSTS/docs-off/CORS caiam todos ao mesmo tempo).
2. **Given** o arranque do backend, **When** o `SECRET_KEY` não cumpre um mínimo de
   comprimento/entropia, **Then** o arranque falha de forma explícita.
3. **Given** o sistema atrás do reverse proxy de produção, **When** um atacante
   tenta força-bruta de login a partir de muitos IPs, **Then** o limite de ritmo é
   aplicado por cliente real e as tentativas abusivas são travadas.
4. **Given** um endpoint que altera estado com autenticação por cookie, **When** o
   pedido chega de uma origem fora da allowlist, **Then** é recusado.

---

### User Story 3 - Sem injeção, SSRF ou exaustão de recursos latentes (Priority: P3)

Vetores latentes que não estão a ser explorados hoje mas cuja única barreira é
frágil ou depende de disciplina por-chamador: (a) o operador de pesquisa `$regex`
do DAO corre como regex POSIX no Postgres — é seguro contra SQLi (parametrizado)
mas **cada chamador tem de escapar e limitar o input**, senão abre-se ReDoS que
derruba a base de dados; (b) a guarda SSRF do Web Push valida apenas o **literal**
do endpoint, sendo **cega a DNS e a redireções** — um sócio autenticado pode fazer
o servidor emitir pedidos a serviços internos/metadata; (c) o limite de tamanho de
upload é verificado **só depois** de ler o corpo inteiro (exaustão de
memória/disco), sem quota por-utilizador; (d) o redirect público `/brand/icon` e os
campos de URL armazenados (foto, logótipo, capa) aceitam strings arbitrárias
(redirect aberto / `javascript:` no href do frontend).

**Why this priority**: risco real mas dependente de condições (ser autenticado,
um chamador futuro esquecer-se de escapar, DNS controlado). Importante fechar, mas
depois dos gaps ativos de confidencialidade e do perímetro.

**Independent Test**: submeter um endpoint de push cujo hostname resolve para um
IP interno ou responde com redirect para um → bloqueado; enviar um corpo de upload
acima do limite → recusado antes de esgotar recursos; armazenar um URL
`javascript:` num campo e confirmar que não é renderizado como link ativo.

**Acceptance Scenarios**:

1. **Given** o envio de Web Push, **When** o endpoint alvo resolve (por DNS ou
   redireção) para um endereço interno/reservado, **Then** o pedido é bloqueado.
2. **Given** um upload, **When** o corpo excede o limite da categoria, **Then** é
   recusado sem consumir memória/disco proporcional ao tamanho enviado, e existe um
   teto de volume por utilizador.
3. **Given** um campo de URL armazenado com esquema perigoso (`javascript:`/`data:`)
   ou fora do domínio, **When** é apresentado ou usado para redirecionar, **Then**
   é rejeitado ou neutralizado.
4. **Given** qualquer construção de pesquisa `$regex`, **When** recebe input do
   utilizador, **Then** o input é escapado e limitado (sem ReDoS).

---

### User Story 4 - Dependências sem CVE conhecido e vigilância contínua (Priority: P4)

As dependências do backend estão fixadas (bom), mas congeladas em versões de
2023/início de 2024, sem verificação automática de CVEs. Duas CVEs de **negação de
serviço em multipart** (`starlette` e `python-multipart`) estão em endpoints de
formulário/upload **públicos**; `Pillow` processa imagens não confiáveis várias
gerações de CVE atrás; `Jinja2` e `requests` estão desatualizados; não há
`dependabot`/`renovate` nem `pip-audit`/`npm audit` no CI; o frontend depende de
`react-scripts` (CRA) em fim de vida.

**Why this priority**: é remediação real (bumps + processo) mas mecânica e
paralela ao resto; algumas CVEs são de DoS, não de execução, e o alerta contínuo é
tanto processo como código.

**Independent Test**: correr uma verificação de CVEs nas dependências → 0
High/Critical alcançáveis por código em produção por fim do ciclo; confirmar que
existe um mecanismo automático que sinaliza novas CVEs.

**Acceptance Scenarios**:

1. **Given** as dependências do backend e do frontend, **When** uma verificação de
   CVEs é executada ao fechar o ciclo, **Then** não há CVEs High/Critical
   alcançáveis por código em produção por remediar.
2. **Given** o repositório, **When** surge uma nova CVE numa dependência fixada,
   **Then** um mecanismo automático sinaliza-a (alerta/PR), sem depender de deteção
   manual.

---

### User Story 5 - Revisão repetível, registada e à prova de regressão (Priority: P5)

A revisão deve deixar um **registo de achados** (por domínio, com severidade e
estado de remediação), consolidar a lista de invariantes já endurecidas para que
não sejam re-litigadas, e uma **guarda automática por cada correção** para que um
problema fechado não volte a aparecer em silêncio.

**Why this priority**: transforma um esforço pontual num processo repetível e
protege o investimento; é a camada de sustentação, valiosa mas dependente das
anteriores.

**Independent Test**: abrir o registo de achados e confirmar que cada achado no
âmbito de severidade acordado tem estado `corrigido` (com teste de regressão) ou
`aceite/adiado` (com justificação); reintroduzir deliberadamente um problema
corrigido e confirmar que uma guarda automática falha.

**Acceptance Scenarios**:

1. **Given** a revisão concluída, **When** o registo de achados é consultado,
   **Then** 100% dos achados no âmbito de severidade têm estado `corrigido` ou
   `aceite/adiado` com justificação.
2. **Given** um problema já corrigido, **When** é reintroduzido no código, **Then**
   uma verificação automática (teste/tripwire) falha.

---

### Edge Cases

- **Vazamento de URL de artefacto**: um sócio partilha (ou um log regista) o URL de
  um comprovativo — continua o ficheiro protegido por autenticação/autorização?
- **Config de produção incompleta**: `ENVIRONMENT`/`SECRET_KEY`/lista de proxies de
  confiança em falta ou incorretos no deploy — o sistema degrada em silêncio?
- **Força-bruta distribuída**: muitos IPs distintos atrás do proxy contra o login —
  o limite por-IP colapsa num único balde?
- **Push para alvo interno**: hostname público que resolve (DNS/rebinding) ou
  redireciona para `127.0.0.1`/`169.254.169.254`/RFC1918.
- **Corpo malicioso**: palavra-passe de vários KB (amplificação de `bcrypt`);
  multipart malformado (CVE de DoS); bomba de descompressão em imagem.
- **URL armazenado perigoso**: campo de foto/logótipo com `javascript:`/`data:` ou
  apontando para host externo.
- **Novo endpoint sem guarda**: um endpoint adicionado após a revisão sem
  verificação de posse — existe guarda que o apanhe?
- **Janela de tradução de roles legados (D4 da spec 018)**: confirmar que é
  temporária e fecha na release seguinte (não vira alargamento permanente).

## Requirements *(mandatory)*

### Functional Requirements

**Confidencialidade e controlo de acesso (US1)**

- **FR-001**: Cada categoria de artefacto carregado MUST ter uma classe de
  confidencialidade definida; artefactos confidenciais (comprovativos financeiros,
  documentos pessoais) MUST NOT ser servidos sem autenticação e autorização.
- **FR-002**: Nenhuma resposta da API MUST conter `password` (hash), segredos de
  MFA legados, tokens de convite/recuperação, ou outros segredos — verificado em
  **todos** os endpoints que devolvem dados de utilizador ou documento.
- **FR-003**: Todos os endpoints que recebem um `id` de objeto pertencente a um
  sócio ou órgão (184 de 327 rotas, medido em runtime) MUST verificar posse ou o
  privilégio regente antes de ler ou mutar, e leituras de coleções-filhas MUST ser
  limitadas pelo `id` do pai (sem divulgação cruzada).
- **FR-004**: Superfícies públicas/anónimas (validador de carteira por QR, opções
  de registo, marca) MUST expor apenas dados não sensíveis e MUST ter limite de
  ritmo contra recolha/enumeração.
- **FR-005**: Dados de PII sensível (saúde, morada, NIF, contactos de emergência)
  MUST chegar apenas ao próprio sócio ou a staff autorizado, em **qualquer** rota
  ou agregação que exponha campos de utilizador.

**Perímetro de autenticação, sessão e configuração (US2)**

- **FR-006**: A postura de segurança de produção (cookie seguro, HSTS,
  documentação desligada, CORS restrito) MUST NOT poder ser desativada por uma
  única variável de configuração mal definida.
- **FR-007**: O arranque MUST recusar um `SECRET_KEY` que não cumpra um mínimo de
  comprimento (≥32 chars, usado como proxy de entropia para HS256).
- **FR-008**: O limite de ritmo MUST ser aplicado por cliente real atrás do reverse
  proxy de produção (não pelo IP do proxy) e MUST cobrir os endpoints sensíveis e
  dispendiosos (autenticação, upload, geração de relatórios/PDF, agregações,
  escritas de admin, leituras públicas anónimas).
- **FR-009**: Todos os métodos que alteram estado sob autenticação por cookie MUST
  estar cobertos por uma defesa anti-CSRF (verificação de origem no servidor);
  a revisão MUST confirmar que a cobertura é total.
- **FR-010**: As garantias de revogação de sessão (desativação de conta, mudança de
  palavra-passe, logout) MUST invalidar tokens em circulação em todos os caminhos.
- **FR-011**: Os campos de palavra-passe MUST ter validação de comprimento
  consistente nos três endpoints que a definem (login, recuperação, setup), sem
  amplificação de custo de hashing.
- **FR-012**: A revisão MUST avaliar e decidir explicitamente sobre os oráculos de
  enumeração/timing (login e registo) e sobre o bloqueio de conta como possível
  negação de serviço dirigida.

**Injeção, SSRF e exaustão de recursos (US3)**

- **FR-013**: Nenhum input do utilizador MUST alcançar um operador `$regex` sem ser
  escapado e limitado em comprimento; o invariante MUST ser garantido de forma que
  não dependa de cada chamador se lembrar.
- **FR-014**: Nenhum input do utilizador MUST alcançar uma posição de identificador
  SQL / chave jsonb / campo de ordenação (posições que são escapadas, nunca
  parametrizáveis).
- **FR-015**: As barreiras SSRF de pedidos externos (Web Push) MUST validar o
  endereço **resolvido** (DNS) e MUST tratar redireções, não apenas o literal do
  endpoint.
- **FR-016**: Redireções (ex.: `/brand/icon`) e campos de URL armazenados
  (foto/logótipo/capa/ícone) MUST ser restritos a esquemas/hosts seguros no momento
  da escrita e neutralizados na apresentação.
- **FR-017**: Os limites de tamanho de upload MUST ser aplicados **antes** de o
  corpo ser totalmente lido, e MUST existir um teto de volume de upload por
  cliente (rate-limit sobre o IP real do cliente; uma quota persistente por
  `user.id` fica como upgrade adiado, ver research.md).
- **FR-018**: As entradas de formulário/multipart públicas MUST estar protegidas
  contra corpos malformados que causem negação de serviço.

**Dependências e cadeia de fornecimento (US4)**

- **FR-019**: As CVEs conhecidas de severidade High/Critical alcançáveis por código
  em produção (incl. as CVEs de DoS multipart em `starlette`/`python-multipart` e o
  `Pillow` desatualizado no processamento de imagens não confiáveis) MUST ser
  remediadas.
- **FR-020**: MUST existir um mecanismo automático que sinaliza novas CVEs em
  dependências fixadas (backend e frontend), sem depender de deteção manual.

**Baseline, registo e regressão (US5)**

- **FR-021**: MUST ser produzido um registo de achados por domínio, com severidade,
  superfície afetada e estado de remediação.
- **FR-022**: Cada achado no âmbito de severidade acordado MUST ficar `corrigido`
  (com guarda de regressão automática) ou `aceite/adiado` (com justificação escrita).
- **FR-023**: A lista de invariantes já endurecidas (secção «Fora de âmbito») MUST
  ser registada como baseline a confirmar (não a reconstruir).
- **FR-024**: A revisão MUST NOT introduzir alterações funcionais visíveis ao
  utilizador nem quebrar documentos existentes na base de dados, exceto quando o
  próprio comportamento é a vulnerabilidade a corrigir (nesse caso, é uma decisão
  registada).

*Decisões de âmbito (confirmadas pelo dono 2026-07-05):*

- **FR-025**: A revisão MUST **auditar, corrigir em código e testar** cada achado
  no âmbito de severidade — com uma guarda de regressão automática por correção e
  release incremental (padrão ACCTA). Não é relatório-apenas.
- **FR-026**: A largura da revisão MUST cobrir **backend + frontend + config de
  deploy versionada no repo** (`Dockerfile`, `docker-compose.yml`, asserções de
  arranque em `server.py`/`config.py`). A config de edge no VPS (Nginx/NPM,
  flags do proxy) MUST ser entregue como **recomendação verificada com o dono**
  (STOP condition — não alterada sem confirmação).
- **FR-027**: O limiar de remediação obrigatória neste ciclo MUST ser **High +
  Medium**, **salvo** achados individuais marcados `aceite`/`adiado` com
  justificação escrita no registo (FR-022) — p.ex. um MEDIUM cujo controlo vive no
  edge/VPS (recomendação-infra) ou um teto deliberadamente aceite. Os achados
  **Low** MUST ser registados com backlog rastreado e adiados.

### Key Entities

- **Achado de Segurança (Security Finding)**: um problema descoberto — domínio,
  descrição, severidade (Critical/High/Medium/Low), superfície afetada (ficheiro/
  endpoint), estado (`aberto`/`corrigido`/`aceite`/`adiado`), referência da guarda
  de regressão.
- **Invariante Endurecida (baseline)**: um controlo já existente e verificado que a
  revisão apenas confirma que se mantém (ex.: RLS deny-all, HMAC de auditoria, RBAC
  unificado, pin do `bcrypt`).
- **Domínio de Superfície de Ataque**: uma das 9 áreas do levantamento
  (autenticação/sessão, autorização/IDOR, injeção/DAO, upload, segredos/config/CORS,
  SSRF/externos, exposição/logs, frontend/cliente, dependências) — usado para
  organizar o registo e garantir cobertura total.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos endpoints que devolvem ou mutam dados por `id` (nos 34
  módulos) são auditados e confirmados a verificar posse/autorização — 0 endpoints
  sem verificação.
- **SC-002**: Nenhum artefacto confidencial de um sócio (comprovativo financeiro,
  documento pessoal) é obtenível sem autenticação e autorização — verificado por
  tentativa de acesso anónimo e por sócio não autorizado.
- **SC-003**: 0 respostas da API contêm hash de palavra-passe ou qualquer campo
  secreto, em toda a superfície que devolve dados de utilizador/documento.
- **SC-004**: 0 CVEs de dependência de severidade High/Critical alcançáveis por
  código em produção permanecem por remediar ao fechar o ciclo.
- **SC-005**: O limite de ritmo trava demonstravelmente o abuso de login e de
  endpoints dispendiosos mesmo atrás do reverse proxy de produção (o atacante não
  excede o limite pretendido partilhando o IP do proxy).
- **SC-006**: A postura de segurança de produção não pode ser desativada por uma
  única configuração incorreta (cookie seguro, HSTS, docs-off e CORS mantêm-se).
- **SC-007**: O registo de achados enumera 100% dos problemas descobertos com
  severidade e estado; nenhum achado no âmbito de severidade fica sem resolução
  (`corrigido` ou `aceite/adiado` com justificação).
- **SC-008**: Cada problema corrigido tem uma guarda de regressão automática — a
  reintrodução do problema faz falhar uma verificação.
- **SC-009**: A suíte de testes existente mantém-se verde e nenhuma alteração
  funcional visível ao utilizador é introduzida (comportamento preservado exceto
  onde o comportamento era a vulnerabilidade).

## Assumptions

- **Assenta em endurecimento anterior**: os controlos listados em «Fora de âmbito»
  assumem-se corretos; a revisão confirma-os mas não os reconstrói nem re-litiga.
- **Sem mudança funcional**: nenhuma funcionalidade nova; o comportamento observável
  é preservado, exceto quando o comportamento é a própria vulnerabilidade (decisão
  registada no achado).
- **Topologia de produção**: Vercel (SPA) + edge NPM/openresty (`api.controlador.cv`)
  + backend em Docker + Postgres Supabase; correções que toquem infra/prod são STOP
  conditions e exigem confirmação do dono antes de aplicar.
- **Fluxo**: GitFlow (`feature/019-… → develop → release → main`); Conventional
  Commits; deploy do backend pela Via B enquanto o CI está bloqueado por billing.
- **Decisões de âmbito (FR-025/026/027) confirmadas pelo dono (2026-07-05)**:
  remediação em código + guardas de regressão; largura backend + frontend + config
  de deploy versionada (edge do VPS = recomendação com STOP); limiar High+Medium
  neste ciclo, Low registado e adiado.
- **Registo de achados** vive em `specs/019-revisao-seguranca-codigo/` (artefacto da
  spec), não em código de produção.
