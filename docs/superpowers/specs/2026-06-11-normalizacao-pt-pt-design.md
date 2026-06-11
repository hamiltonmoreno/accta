# Spec — Normalização PT-PT (sub-projeto A)

**Data:** 2026-06-11
**Estado:** desenho aprovado (glossário + atualização de testes confirmados pelo dono)
**Âmbito:** sub-projeto A de um conjunto de 4 (A: PT-PT · B: verificação factual ·
C: hiperligações institucionais · D: imagem do FIR). B/C/D ficam para a 2ª ronda,
com specs próprias.

---

## 1. Objetivo

Normalizar **todo o texto visível ao utilizador** para **português de Portugal**,
eliminando brasileirismos (vindos sobretudo da base de conhecimento que alimenta
o site público), para o produto soar adequado aos utilizadores cabo-verdianos
habituados ao PT-PT.

**Sucesso:** nenhum brasileirismo do glossário (abaixo) permanece em texto visível
nas superfícies em âmbito; identificadores e estruturas técnicas intactos; testes
verdes; build OK.

## 2. Âmbito (aprovado)

Normalizar:
- **Site público** — `frontend/src/pages/public/*`
- **App privada** — `frontend/src/pages/private/*`, `frontend/src/components/*`,
  `frontend/src/layouts/*`
- **Backend (strings ao utilizador)** — `HTTPException(detail=…)`, templates de
  email (`email_service.py`), notificações/audit (`helpers.py`, `routes/*`)
- **Relatório-fonte** — `memory/deep-research-report.md` (corrigir a origem para
  não reimportar brasileirismos)

Fora de âmbito: B/C/D (factual, links, FIR).

## 3. Glossário aprovado (PT-BR → PT-PT, só texto visível)

| PT-BR | PT-PT |
|-------|-------|
| usuário(s) | utilizador(es) — **só rótulos visíveis** |
| registro | registo |
| arquivo(s) | ficheiro(s) |
| conosco | connosco |
| você / "você pode" | impessoal / "pode" (PT-PT evita "você") |
| tela | ecrã |
| contato | contacto |
| senha | palavra-passe |
| equipe | equipa |
| esporte | desporto |
| planejamento | planeamento |
| gerenciar | gerir |
| gerência | gestão |
| acessar | aceder |
| deletar | eliminar / apagar |
| aplicativo | aplicação |
| celular | telemóvel |
| gerúndio ("está fazendo") | "a" + infinitivo ("está a fazer") |

A leitura é **cuidada e contextual** (não find-replace cego): apanha também
construções subtis (gerúndio, colocação pronominal) e vocabulário do mesmo
registo que não esteja na tabela mas seja claramente brasileiro.

## 4. Guardrails — NUNCA tocar

Regra de identidade do `CLAUDE.md` (identificadores ligados a rotas/API/jsonb/
frontend — não renomear em massa):
- **Rotas/URLs**: `/admin/usuarios`, `/notificacoes`, etc.
- **Nomes** de componentes/ficheiros/variáveis/funções: `AdminUsuariosPage`,
  `usuario` como variável, etc.
- **`data-testid`** (ex.: `sidebar-...`, `menu-...`, `header-...`).
- **Chaves jsonb / campos da API**.
- **Inglês técnico**: `time`, `date`, `update`, `status` — os `time`/`tela`
  detetados são quase todos falsos positivos (datas, `team_members`,
  substrings); **cada ocorrência é revista em contexto** antes de tocar.
- **Termos de domínio PT corretos**: `joia`, `quota`, `socio`, `exercicio`,
  `assembleia`, `deliberacao`, `sancao`, etc.

## 5. Verificação

- **Frontend**: `eslint` limpo nas páginas tocadas; testes via `craco test`
  verdes. Atualizar testes que afirmem a string antiga (ex.: um teste que
  espere "Arquivo" passa a esperar "Ficheiro").
- **Backend**: `pytest` nas rotas tocadas; atualizar asserts sobre `detail`
  exato (ex.: "Arquivo inválido" → "Ficheiro inválido").
- **Emails**: só se altera o **template** — nada é enviado (não é STOP
  condition).
- **Manual**: carregar páginas-chave (Login, Recuperação, Sobre, Contactos,
  Documentos) e confirmar o texto.

## 6. Entrega (GitFlow)

- Branch `feature/normalizacao-pt-pt` → PR para `develop`.
- Commits agrupados por superfície (público / privado / backend / relatório)
  para revisão fácil.
- É frontend+backend de strings: chega a produção no próximo release a `main`
  (frontend via Vercel; backend via deploy manual Via B se/quando houver release
  de backend — mas estas mudanças de string não exigem deploy urgente).

## 7. Riscos / notas

- **Falsos positivos** (`time`, `tela`): rever em contexto; não tocar inglês.
- **`você` no backend** (`polls.py`) e em páginas privadas: reformular para
  impessoal sem alterar o sentido nem a chave/identificador.
- **Strings em testes**: alteração coordenada código+teste no mesmo commit para
  manter o histórico bissetável.
- **Acordo Ortográfico**: a maioria da ortografia já convergiu; o foco é
  **vocabulário e sintaxe**, não re-grafar palavras que já estão corretas.
