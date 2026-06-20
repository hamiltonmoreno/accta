# Home v2 — copy e layout · Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar a spec `docs/superpowers/specs/2026-06-12-home-copy-layout-design.md` em `frontend/src/pages/public/HomePage.js` — 11→10 secções (Stats Bar removida), Hero + "O que é o CTA" + CTA final reescritos para registo sereno e factual, Evento em formato *slim*, sem alterações a APIs ou design tokens.

**Architecture:** Edição de ficheiro único (`HomePage.js`, ~644 linhas). Seis tarefas, cada uma produz **um commit** lógico. Sem novos ficheiros. Sem novos testes — `frontend/src/pages/public/` não tem `__tests__/` (pattern do projecto). Verificação por `eslint`, `yarn build` e *smoke* visual no dev server.

**Tech Stack:** React 19, Tailwind CSS 3, `lucide-react`, `react-router-dom`, `@tanstack/react-query` (uso existente, sem alterações). Test runner é `craco test` (Jest) mas não cobre páginas públicas.

**Branch:** `feature/home-v2-copy-layout` (já criado, com o commit da spec `bce496d`).

---

## File Structure

- **Modify:** `frontend/src/pages/public/HomePage.js` — único ficheiro tocado.
- **No create.** No new tests.

Mudanças concentradas em 5 blocos do ficheiro:

| Bloco | Linhas aprox. | Tarefa |
|---|---|---|
| Imports lucide-react | 8–30 | T2 (remove `Target`) |
| Hero `<section>` | 115–177 | T1 |
| Stats Bar `<section>` | 179–198 | T2 (remove inteiro) |
| Featured Event `<section>` | 200–274 | T3 |
| "What We Do" → "O que é o CTA" | 276–326 | T4 |
| CTA final `<section>` | 609–640 | T5 |

> **Nota sobre linhas:** os números acima são do estado actual; após T2 (remoção de ~20 linhas) os blocos posteriores deslocam-se. As tarefas usam `Edit` com `old_string`/`new_string` exactos — não dependem de números de linha em runtime.

---

## Pre-flight

- [ ] **Step 0.1: Confirmar branch correcto**

```bash
cd "C:/Users/User/Documents/dev-projetos/accta-main/accta"
git branch --show-current
```

Esperado: `feature/home-v2-copy-layout`. Se não for, fazer `git checkout feature/home-v2-copy-layout`.

- [ ] **Step 0.2: Confirmar working tree limpo (excluindo untracked não relacionados)**

```bash
git status --short -- frontend/ backend/ docs/
```

Esperado: vazio (sem entradas modificadas em `frontend/`, `backend/`, `docs/`). Untracked unrelated em `.claude/agent-memory/`, `.understand-anything/`, `backend/venv311/`, `frontend/src/.claude/` são ignorados.

- [ ] **Step 0.3: Confirmar lint baseline passa**

```bash
cd frontend && npx eslint src/pages/public/HomePage.js --max-warnings=60
```

Esperado: exit code 0 (≤60 warnings, sem errors). Se já falhar antes das mudanças, parar e investigar.

---

## Task 1: Reescrever o Hero

**Files:**
- Modify: `frontend/src/pages/public/HomePage.js`

Substitui badge, H1, lead, labels dos CTAs e remove o scroll indicator decorativo. Mantém estrutura DOM, classes Tailwind, `data-testid`s e `animate-fade-up`.

- [ ] **Step 1.1: Substituir o badge do Hero**

`Edit` em `frontend/src/pages/public/HomePage.js`:

`old_string`:
```jsx
              <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-carmesim/20 backdrop-blur-sm border border-carmesim/40 rounded-full mb-6 sm:mb-8">
                <Radio className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-white" />
                <span className="text-white font-sans text-xs sm:text-sm uppercase tracking-wider font-semibold">ACCTA Cabo Verde</span>
              </div>
```

`new_string`:
```jsx
              <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-carmesim/20 backdrop-blur-sm border border-carmesim/40 rounded-full mb-6 sm:mb-8">
                <span className="w-2 h-2 rounded-full bg-carmesim shrink-0" aria-hidden="true" />
                <span className="text-white font-sans text-xs sm:text-sm uppercase tracking-wider font-semibold">ACCTA · Cabo Verde</span>
              </div>
```

- [ ] **Step 1.2: Substituir o H1 do Hero**

`Edit`:

`old_string`:
```jsx
              <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl xl:text-7xl text-white leading-tight mb-4 sm:mb-6" data-testid="hero-title">
                Os Guardiões{' '}
                <span className="text-white">Invisíveis</span>{' '}
                dos Céus de Cabo Verde
              </h1>
```

`new_string`:
```jsx
              <h1 className="font-bold text-3xl sm:text-5xl lg:text-6xl xl:text-7xl text-white leading-tight mb-4 sm:mb-6" data-testid="hero-title">
                O controlo de tráfego aéreo em Cabo Verde.
              </h1>
```

- [ ] **Step 1.3: Substituir a lead do Hero**

`Edit`:

`old_string`:
```jsx
              <p className="text-base sm:text-xl lg:text-2xl text-white leading-relaxed mb-8 sm:mb-10 max-w-xl" style={{ textShadow: '0 1px 3px rgba(0,0,0,0.4)' }}>
                24 horas por dia, garantimos a segurança, a fluidez e a soberania do espaço aéreo no meio do Atlântico.{' '}
                <span className="text-white font-bold">Nós somos a CTA.</span>
              </p>
```

`new_string`:
```jsx
              <p className="text-base sm:text-xl lg:text-2xl text-white leading-relaxed mb-8 sm:mb-10 max-w-xl" style={{ textShadow: '0 1px 3px rgba(0,0,0,0.4)' }}>
                Somos os controladores de tráfego aéreo que organizam, comunicam e protegem cada voo na FIR Oceânica do Sal — uma das maiores regiões de informação de voo do Atlântico.
              </p>
```

- [ ] **Step 1.4: Actualizar os labels dos CTAs do Hero (imperativo → infinitivo)**

`Edit`:

`old_string`:
```jsx
                  Conheça a Profissão
```

`new_string`:
```jsx
                  Conhecer a profissão
```

`Edit` (segundo CTA):

`old_string`:
```jsx
                  Área do Associado
```

`new_string`:
```jsx
                  Área do associado
```

- [ ] **Step 1.5: Remover o scroll indicator decorativo**

`Edit`:

`old_string`:
```jsx
        <div className="absolute bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2 hidden sm:block animate-fade-up">
          <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center">
            <div className="w-1.5 h-3 bg-carmesim rounded-full mt-2 animate-bounce" />
          </div>
        </div>
```

`new_string`: *(string vazia — remove o bloco; o `</section>` que o segue mantém-se)*

```
```

> **Validação manual:** depois deste `Edit`, abre o ficheiro e verifica visualmente que a tag de fecho `</section>` do Hero (logo a seguir) continua intacta — se acidentalmente apanhares essa tag no `old_string`, o JSX parte.

- [ ] **Step 1.6: Correr lint**

```bash
cd frontend && npx eslint src/pages/public/HomePage.js --max-warnings=60
```

Esperado: exit code 0, sem novos errors. Se `Radio` aparecer como import não usado mas só no Hero, **ignorar** — `Radio` continua usado na secção FIR (linha ~433 do ficheiro original) e nos mapas `CONTROL_ICONS`/`ATS_ICONS`.

- [ ] **Step 1.7: Commit**

```bash
git add frontend/src/pages/public/HomePage.js
git commit -m "feat(home): reescreve hero com tom factual e sereno

- H1 'O controlo de tráfego aéreo em Cabo Verde.' (remove 'Guardiões Invisíveis')
- Lead descreve operação na FIR Oceânica do Sal sem retorica
- Badge passa a span-bullet (sem icone Radio)
- CTAs em infinitivo ('Conhecer a profissão', 'Área do associado')
- Remove scroll indicator decorativo

Spec: docs/superpowers/specs/2026-06-12-home-copy-layout-design.md §5.1"
```

---

## Task 2: Remover a Stats Bar e o import `Target`

**Files:**
- Modify: `frontend/src/pages/public/HomePage.js`

A Stats Bar autónoma exibia stats fluff ("1 Missão") e dados sem fonte oficial. Removida inteira. O único ícone que fica órfão é `Target` (era o ícone da "1 Missão").

- [ ] **Step 2.1: Remover o bloco `<section>` da Stats Bar**

`Edit`:

`old_string`:
```jsx
      {/* Stats Bar */}
      <section className="bg-grafite py-6 sm:py-8 border-y border-carmesim/20">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5 sm:gap-8">
            {[
              { icon: Globe, value: 'FIR', label: 'Oceânica do Sal' },
              { icon: Clock, value: '24/7', label: 'Operação Ininterrupta' },
              { icon: MapPin, value: '4', label: 'Aeroportos Internacionais' },
              { icon: Target, value: '1', label: 'Missão: Segurança Total' },
            ].map((stat, index) => (
              <div key={index}
                className="text-center animate-fade-up">
                <stat.icon className="w-6 sm:w-8 h-6 sm:h-8 text-white mx-auto mb-2 sm:mb-3" />
                <div className="font-bold text-2xl sm:text-3xl lg:text-4xl text-white mb-0.5">{stat.value}</div>
                <div className="text-xs text-white/80 tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

```

`new_string`: *(string vazia — remove o bloco e a linha em branco a seguir)*

```
```

- [ ] **Step 2.2: Remover `Target` do import `lucide-react`**

`Edit`:

`old_string`:
```jsx
  Target,
```

`new_string`: *(string vazia)*

```
```

> **Nota:** `Globe`, `Clock`, `MapPin` mantêm-se no import — continuam usados em FIR (Globe), Event (Clock, MapPin).

- [ ] **Step 2.3: Correr lint**

```bash
cd frontend && npx eslint src/pages/public/HomePage.js --max-warnings=60
```

Esperado: exit code 0, sem warning de "Target is defined but never used".

- [ ] **Step 2.4: Commit**

```bash
git add frontend/src/pages/public/HomePage.js
git commit -m "feat(home): remove Stats Bar autonoma

Os 4 stats ('FIR', '24/7', '4 aeroportos', '1 Missão: Seguranca Total')
misturavam factos com fluff. Sem fontes oficiais para km² da FIR ou
voos/ano (per deep-research-report); a 'escala' da operacao ja é
transmitida pelos cards de TWR/APP/ACC, FIR e 4 entidades.

Remove tambem o import 'Target' (orfao).

Spec: §4, §5 (Stats Bar nao consta no novo esqueleto)"
```

---

## Task 3: Encolher a secção de Evento em destaque (*slim*)

**Files:**
- Modify: `frontend/src/pages/public/HomePage.js`

Render condicional e estrutura DOM mantidos. Reduz paddings, encolhe countdown boxes, remove decorações de fundo (dots pattern + blur orb), corrige acento de "Proximo".

- [ ] **Step 3.1: Reduzir o padding da `<section>` exterior**

`Edit`:

`old_string`:
```jsx
        <section className="py-12 sm:py-16 bg-white border-b border-gray-100" data-testid="featured-event-section">
```

`new_string`:
```jsx
        <section className="py-8 sm:py-10 bg-white border-b border-gray-100" data-testid="featured-event-section">
```

- [ ] **Step 3.2: Reduzir o padding do card grafite interior**

`Edit`:

`old_string`:
```jsx
            <div className="relative overflow-hidden rounded-2xl bg-grafite p-6 sm:p-10 lg:p-12">
```

`new_string`:
```jsx
            <div className="relative overflow-hidden rounded-2xl bg-grafite p-5 sm:p-7 lg:p-8">
```

- [ ] **Step 3.3: Remover o background pattern (dots) e o blur orb decorativo**

`Edit`:

`old_string`:
```jsx
              {/* Background pattern */}
              <div className="absolute inset-0 opacity-[0.04]" style={{
                backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
                backgroundSize: '24px 24px'
              }} />
              <div className="absolute top-0 right-0 w-64 h-64 bg-carmesim/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />

```

`new_string`: *(string vazia)*

```
```

- [ ] **Step 3.4: Corrigir acento "Proximo" → "Próximo"**

`Edit`:

`old_string`:
```jsx
                    <span className="text-xs text-white font-semibold uppercase tracking-wider">Proximo Evento</span>
```

`new_string`:
```jsx
                    <span className="text-xs text-white font-semibold uppercase tracking-wider">Próximo evento</span>
```

- [ ] **Step 3.5: Encolher os countdown boxes (w-16 → w-12; w-20 → w-14)**

`Edit`:

`old_string`:
```jsx
                        <div className="w-16 h-16 sm:w-20 sm:h-20 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl flex items-center justify-center mb-2">
                          <span className="font-bold text-2xl sm:text-3xl text-white font-mono" data-testid={`countdown-${unit.label.toLowerCase()}`}>
```

`new_string`:
```jsx
                        <div className="w-12 h-12 sm:w-14 sm:h-14 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl flex items-center justify-center mb-2">
                          <span className="font-bold text-xl sm:text-2xl text-white font-mono" data-testid={`countdown-${unit.label.toLowerCase()}`}>
```

- [ ] **Step 3.6: Correr lint**

```bash
cd frontend && npx eslint src/pages/public/HomePage.js --max-warnings=60
```

Esperado: exit code 0.

- [ ] **Step 3.7: Commit**

```bash
git add frontend/src/pages/public/HomePage.js
git commit -m "feat(home): aplica formato slim ao evento em destaque

- py-12 sm:py-16 -> py-8 sm:py-10
- Card padding p-6 sm:p-10 lg:p-12 -> p-5 sm:p-7 lg:p-8
- Countdown boxes 16/20 -> 12/14; digits text-2xl/3xl -> text-xl/2xl
- Remove pattern de dots e blur orb decorativos
- Corrige acento 'Proximo' -> 'Próximo'

Mantem render condicional, data-testids e todos os campos exibidos.

Spec: §5.2"
```

---

## Task 4: Reescrever a secção "O que é o CTA"

**Files:**
- Modify: `frontend/src/pages/public/HomePage.js`

Mantém o `<section>`, o grid 2-colunas e os 4 cards (Vigilância 24h / Comunicação / Segurança / Coordenação). Reescreve badge, body §1 e body §2. H2 e link inferior **mantêm-se** (já funcionam).

- [ ] **Step 4.1: Substituir o pill badge "O que fazemos" → "O que é o CTA"**

`Edit`:

`old_string`:
```jsx
              <span className="inline-block px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
                O que fazemos
              </span>
```

`new_string`:
```jsx
              <span className="inline-block px-3 py-1.5 bg-carmesim/10 text-carmesim rounded-full text-xs uppercase tracking-wider font-semibold mb-4 sm:mb-6">
                O que é o CTA
              </span>
```

- [ ] **Step 4.2: Reescrever o §1 do body (remover "equipa de elite em terra")**

`Edit`:

`old_string`:
```jsx
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-4 sm:mb-6">
                Quando embarca num avião, vê o piloto e a tripulação. Mas existe uma{' '}
                <strong className="text-grafite">equipa de elite em terra</strong>, monitorizando cada metro do seu voo.
              </p>
```

`new_string`:
```jsx
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-4 sm:mb-6">
                Quando embarca num avião, vê o piloto e a tripulação. Em terra, há também uma{' '}
                <strong className="text-grafite">equipa que acompanha cada fase do voo</strong> — da partida à chegada.
              </p>
```

- [ ] **Step 4.3: Reescrever o §2 do body (remover "evitar colisões", "complexas rotas")**

`Edit`:

`old_string`:
```jsx
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-6 sm:mb-8">
                O Controlador de Tráfego Aéreo (CTA) é o responsável por evitar colisões, organizar descolagens e aterragens 
                e guiar aeronaves em segurança através das complexas rotas do Atlântico.
              </p>
```

`new_string`:
```jsx
              <p className="text-sm sm:text-lg text-gray-600 leading-relaxed mb-6 sm:mb-8">
                O Controlador de Tráfego Aéreo (CTA) organiza descolagens e aterragens, mantém a separação entre aeronaves e guia os voos pelas rotas do Atlântico médio.
              </p>
```

- [ ] **Step 4.4: Correr lint**

```bash
cd frontend && npx eslint src/pages/public/HomePage.js --max-warnings=60
```

Esperado: exit code 0.

- [ ] **Step 4.5: Commit**

```bash
git add frontend/src/pages/public/HomePage.js
git commit -m "feat(home): reescreve copy da seccao 'O que é o CTA'

- Pill badge: 'O que fazemos' -> 'O que é o CTA' (registo educativo)
- §1: remove 'equipa de elite em terra', 'monitorizando cada metro'
- §2: remove 'evitar colisões', 'complexas rotas do Atlantico';
       substitui por descricao funcional (separacao, rotas do
       Atlantico medio)

Mantem H2 ('Muito alem da Torre de Controlo'), os 4 cards e o link
inferior para /profissao.

Spec: §5.3"
```

---

## Task 5: Reescrever o CTA final

**Files:**
- Modify: `frontend/src/pages/public/HomePage.js`

Resolve a ambiguidade do título actual ("Junte-se aos profissionais" lê-se como recrutamento, não convite à associação). Mantém `<section>` grafite com grid pattern, container central e 2 botões.

- [ ] **Step 5.1: Substituir o H2**

`Edit`:

`old_string`:
```jsx
          <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-white mb-4 sm:mb-6">
            Junte-se aos profissionais que garantem a{' '}
            <span className="text-white">segurança dos céus</span>
          </h2>
```

`new_string`:
```jsx
          <h2 className="font-bold text-2xl sm:text-4xl lg:text-5xl text-white mb-4 sm:mb-6">
            A ACCTA representa os controladores de tráfego aéreo de Cabo Verde.
          </h2>
```

- [ ] **Step 5.2: Substituir a lead**

`Edit`:

`old_string`:
```jsx
          <p className="text-base sm:text-xl text-white/80 mb-8 sm:mb-10">
            A ACCTA representa e valoriza os controladores de tráfego aéreo de Cabo Verde
          </p>
```

`new_string`:
```jsx
          <p className="text-base sm:text-xl text-white/80 mb-8 sm:mb-10">
            Conheça quem somos, o que defendemos e como participamos no setor da navegação aérea.
          </p>
```

- [ ] **Step 5.3: Actualizar labels dos CTAs finais (imperativo → infinitivo)**

`Edit`:

`old_string`:
```jsx
              Conheça a Associação
```

`new_string`:
```jsx
              Conhecer a associação
```

`Edit` (segundo CTA):

`old_string`:
```jsx
              Entre em Contacto
```

`new_string`:
```jsx
              Entrar em contacto
```

- [ ] **Step 5.4: Correr lint**

```bash
cd frontend && npx eslint src/pages/public/HomePage.js --max-warnings=60
```

Esperado: exit code 0.

- [ ] **Step 5.5: Commit**

```bash
git add frontend/src/pages/public/HomePage.js
git commit -m "feat(home): reescreve CTA final como convite institucional

- H2: 'Junte-se aos profissionais...' -> 'A ACCTA representa os
  controladores de trafego aereo de Cabo Verde.' (sem ambiguidade
  recrutar-vs-associar)
- Lead descreve o que se vai encontrar em /sobre
- CTAs em infinitivo: 'Conhecer a associação', 'Entrar em contacto'

Spec: §5.10"
```

---

## Task 6: Verificação final

**Files:**
- Read-only.

Lint completo, build de produção, smoke test visual no dev server.

- [ ] **Step 6.1: Lint completo da pasta `src/`**

```bash
cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60
```

Esperado: exit code 0. Se houver novos warnings/errors fora de `HomePage.js`, parar — não devíamos ter tocado nada mais.

- [ ] **Step 6.2: Build de produção**

```bash
cd frontend && yarn build
```

Esperado: build conclui sem errors. JSX inválido faz isto falhar — é a primeira defesa real contra um `</section>` orfão.

- [ ] **Step 6.3: Smoke test visual no dev server**

Em terminal separado:
```bash
cd frontend && yarn start
```

Abrir `http://localhost:3000/` no browser e verificar manualmente:

1. **Hero:** Badge "● ACCTA · Cabo Verde"; H1 "O controlo de tráfego aéreo em Cabo Verde."; 2 botões "Conhecer a profissão" (verde Floresta) e "Área do associado" (ghost branco). Sem scroll indicator (a bolinha no fundo do hero).
2. **Stats Bar:** **ausente** — logo abaixo do hero vem o Evento (se houver featured event) ou directamente "O que é o CTA".
3. **Evento (se houver):** card grafite mais compacto, badge "Próximo evento" (com acento), countdown de digits mais pequenos.
4. **O que é o CTA:** badge "O que é o CTA", H2 "Muito além da Torre de Controlo" (mantido), 4 cards intactos.
5. **TWR/APP/ACC, 4 entidades, FIR, Caminho, FAQ, Notícias:** todos intactos.
6. **CTA final:** H2 começa com "A ACCTA representa...", botões "Conhecer a associação" / "Entrar em contacto".
7. **Mobile breakpoint** (DevTools, ≤640px): hero responde, evento slim cabe em mobile com countdown legível, sem horizontal scroll.

- [ ] **Step 6.4: (Opcional) Commit de polimento**

Se o smoke revelar algo pequeno (e.g. um espaçamento esquisito numa secção tocada), corrigir e:

```bash
git add frontend/src/pages/public/HomePage.js
git commit -m "fix(home): ajustes de polimento pós-smoke

[descrever]"
```

Se não houver polimentos, **não criar commit vazio**.

- [ ] **Step 6.5: Listar commits da feature**

```bash
git log --oneline develop..feature/home-v2-copy-layout
```

Esperado: 6–7 commits (1 spec + 5 features + 0/1 polimento).

---

## Riscos e mitigação durante a implementação

| Risco | Mitigação |
|---|---|
| `Edit` falha por `old_string` não-único (por exemplo dois CTAs com "Conheça") | Os steps T1.4 e T5.3 usam `Edit` separado por CTA — strings distintas garantidas pelo contexto envolvente |
| `</section>` órfão depois de remover Stats Bar | Step 2.1 inclui a comment-marker `{/* Stats Bar */}` no `old_string` para garantir corte limpo; Step 6.2 (`yarn build`) detecta JSX inválido |
| Import `Target` deixado órfão se Step 2.2 falhar | Lint do Step 2.3 apanha o "no-unused-vars" |
| Build quebrar por outra razão | Step 6.2 corre antes de qualquer push; reverter com `git reset --soft HEAD~N` se necessário |
| Evento slim ilegível em mobile | Step 6.3 inclui smoke mobile explícito; countdown de `w-12 h-12` (48px) continua tappable (>44px Apple HIG) |

## Critério de aceitação (espelha §9 da spec)

- [ ] 10 secções na ordem da §4 da spec
- [ ] Hero conforme §5.1; scroll indicator removido
- [ ] Stats Bar removida; `Target` removido dos imports
- [ ] Evento slim conforme §5.2; conditional render mantido
- [ ] "O que é o CTA" com badge, §1 e §2 reescritos; 4 cards intactos
- [ ] CTA final reescrito conforme §5.10
- [ ] `yarn eslint` passa com ≤60 warnings
- [ ] `yarn build` passa
- [ ] Smoke visual em desktop + mobile sem regressões nas secções intocadas
