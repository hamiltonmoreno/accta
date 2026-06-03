# Frontend Consistency 7.3 — Resíduos pós-spec principal

_Spec curto que ataca os 6 resíduos sinalizados ao fechar a
`frontend-consistency-spec.md` (Fases 0–7.2). Mesmo branch
(`fix/frontend-consistency`), nada para `main` sem OK explícito._

---

## Contexto

A `frontend-consistency-spec.md` foi executada em 16 commits e ficou
QA-green (eslint 0/43, build exit 0, todos os acceptance greps passam).
Durante a execução foram sinalizados 6 resíduos heterogéneos: uns
mecânicos, outros decisões de design, um bug funcional. Esta spec
fecha-os, sem alargar escopo para além desses 6.

## Princípios

- **Mesma branch `fix/frontend-consistency`**, mesmo padrão (1 commit
  por fase, `craco build` + `npx eslint --max-warnings=60` exit 0 antes
  de cada commit, heredoc para mensagens).
- **Não tocar SKILL.md**, `.claude/rules/*`, `design_guidelines.json`
  (lição L8). Code-side wins, doc fica para owner.
- **Não tocar `.claude/settings.json` / `.claude/settings.local.json`**
  (mudanças do utilizador, pré-existentes ao trabalho).
- **PARAR antes da Fase 4** (mudança root no `index.css` afeta cada
  `.btn-secondary` da app; requer OK explícito do owner).
- Sem migração de dados, sem backend, sem auth, sem novo endpoint.

---

## Sequenciamento (risco crescente)

```
0 ─► 1 ─► 2 ─► 3 ─► [STOP p/ OK] ─► 4
```

| Fase | Conteúdo | Risco | Ficheiros |
|---|---|---|---|
| 0 | 5 ternários inline-color + 1 multi-prop split via `cn()` | Muito baixo | 5 |
| 1 | `<div animate={{ width }}>` inválido → CSS transition | Baixo | 1 (DocumentosPage) |
| 2 | Bug `deleteMutation.onSuccess` não limpa `editingUser` | Baixo | 1 (AdminUsuariosPage) |
| 3 | Botões destrutivos red-{500..700} → paleta SKILL error | Médio (visual) | 2 (AdminUsuariosPage + 1) |
| 4 | `.btn-secondary` `bg-grafite` → SKILL Secondary (white+borda) | **Mais alto** (root) | 1 (`index.css`) |

---

## Fase 0 — Ternários inline-color + split multi-prop (V11)

Substitui os 6 sobreviventes do regex `{{` da aceitação da Fase 7.1.

- [ ] **5 ternários** `style={cond ? { color: 'var(--text-X)' } : undefined}`
      → `className={cn(..., cond && 'text-X-auto')}`.
      Adicionar `import { cn } from '../../lib/utils'` ou `'@/lib/utils'`
      conforme o estilo do ficheiro (`@/` alias é configurado pelo Craco).
  - `src/layouts/PrivateLayout.js` L219 (`!isActive ? secondary : undefined`)
  - `src/layouts/PrivateLayout.js` L228 (`!isActive ? muted : undefined`)
  - `src/pages/private/financeiro/DRETab.js` L71
    (`dre.resultado_liquido >= 0 ? primary : undefined`)
  - `src/pages/private/FinanceiroPage.js` L16 (`!active ? muted : undefined`)
  - `src/pages/private/MuralPage.js` L540 (`!isLiked ? muted : undefined`)
- [ ] **1 multi-prop split** em `src/pages/private/MuralPage.js` L103:
      `style={{ backgroundColor: 'var(--surface-border)', color: 'var(--text-primary)' }}`
      → remover `color` (vai para `className text-grafite-auto`);
      manter `backgroundColor` inline (alvo de futura migração de
      `var(--surface-*)`, fora deste escopo).

**Aceitação:**
```
grep -rn --include="*.js" --include="*.jsx" "color: 'var(--text" frontend/src
→ 0 hits
```

(O regex deixa de ter exceções — tanto `{{` como ternários cobertos.)

---

## Fase 1 — Cleanup `<div animate={{ width }}>` inválido (V12)

- [ ] `frontend/src/pages/private/DocumentosPage.js` L372
      (ou linha equivalente após Fase 6.4):

  ```jsx
  <div animate={{ width: `${uploadProgress}%` }}
    className="h-full bg-carmesim rounded-full animate-fade-up" />
  ```

  `animate` é resto de framer-motion num `<div>` simples (atributo DOM
  inválido). Mudança: remover `animate={...}` e mover a largura para
  `style={{ width: ... }}` inline ou usar `motion.div` corretamente.
  **Decisão simples (preferida):** trocar `animate={...}` por
  `style={{ width: \`${uploadProgress}%\` }}` — o `transition-all`
  ancestor já dá interpolação CSS.

**Aceitação:**
```
grep -nE '\banimate=\{' frontend/src/pages/private/DocumentosPage.js
→ 0 hits
```

Build sem warnings de React sobre props desconhecidas em `<div>`
(verificar com `npm test` ou abrir browser e ver consola — não
bloqueante; o build não captura warnings runtime).

---

## Fase 2 — Bug `deleteMutation.onSuccess` não limpa `editingUser` (V13)

- [ ] `frontend/src/pages/private/AdminUsuariosPage.js` L87-93
      (mutation de delete):

  ```js
  const deleteMutation = useMutation({
    mutationFn: (userId) => usersAPI.delete(userId),
    onSuccess: () => {
      toast.success('Utilizador removido');
      setDeleteConfirm(null);
      setEditingUser(null);   // ← NOVO: fechar tambem o edit-modal
      invalidateUsers();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao remover'),
  });
  ```

  Razão: o "Remover" é disparado a partir do rodapé do edit-modal; sem
  esta linha o modal de edição fica aberto a mostrar o utilizador que
  acabou de ser apagado (UX bug pré-existente identificado na Fase 6.8).

**Aceitação:** revisão manual do diff (1 linha); fluxo:
edit → Remover → AlertDialog → Sim, remover → ambos os dialogs fecham
e a lista atualiza.

---

## Fase 3 — Botões destrutivos red-{500..700} → paleta SKILL error (V14)

SKILL §4 error: `text=#B91C1C`, `bg-light=#FEF2F2`, `solid=#C7202F`.
A paleta `red-500..700` do Tailwind (`#EF4444 / #DC2626 / #B91C1C`)
está visualmente próxima mas não é a paleta canónica.

- [ ] **"Sim, remover"** em `AdminUsuariosPage.js` (delete-confirm,
      `AlertDialogAction`):
  - Antes: `className="bg-red-600 text-white hover:bg-red-700"`
  - Depois: `className="bg-[#C7202F] text-white hover:bg-[#B91C1C]"`

- [ ] **"Remover"** em `AdminUsuariosPage.js` (rodapé do edit-modal):
  - Antes: `className="... text-red-500 hover:text-red-700 ..."`
  - Depois: `className="... text-[#B91C1C] hover:text-[#991B1B] ..."`

- [ ] **Apanhar outros usos legados `text-red-*` / `bg-red-*`** (audit
      curto):
  ```
  grep -rnE 'text-red-(500|600|700)|bg-red-(500|600|700)' frontend/src/
  ```
  - Decidir por **cada** match se é (i) destrutivo (→ SKILL error),
    (ii) decorativo (não devia ser red — caso a caso), ou (iii) parte
    de um indicador de status (já cobertos pela Fase 4 via
    `statusConfig`). Não fazer global replace — `text-red-X` não é
    automaticamente o mesmo que SKILL error (lição L7).

**Aceitação:**
- Botões destrutivos do AdminUsuariosPage usam `#C7202F`/`#B91C1C`.
- Outros matches `text-red-*` / `bg-red-*` classificados explicitamente
  (sem global replace).

---

## Fase 4 — `.btn-secondary` `bg-grafite` → SKILL Secondary (V15)

> **STOP — pedir OK explícito antes desta fase.** É uma mudança no
> root `index.css` que reflete em cada `.btn-secondary` da app (algumas
> dezenas de utilizações). Risco visual sistémico, decisão de design.

SKILL Secondary: branco com borda neutra (sem fundo de marca).
Atualmente `.btn-secondary` em `index.css` L145-147 usa
`bg-grafite text-white hover:bg-grafite-dark` — o que faz com que o
"botão secundário" pareça outro botão primário escuro.

**Mudança proposta:**

```css
.btn-secondary {
    @apply h-10 sm:h-11 px-5 sm:px-6 rounded-lg font-semibold text-sm transition-colors;
    background-color: var(--surface-card);     /* white */
    color: var(--text-primary);                /* grafite */
    border: 1px solid #D1D5DB;                 /* SKILL border */
}
.btn-secondary:hover {
    background-color: var(--surface-card-hover);  /* #f9fafb */
}
```

- [ ] Editar `frontend/src/index.css` L145-147 conforme acima.
- [ ] Audit visual: rodar dev server, ver páginas com `.btn-secondary`
      em diversas localizações (formulários, modais, ações de tabela).
      `grep -rln 'btn-secondary' frontend/src/` para enumerar.
- [ ] Se algum ecrã ficar com 0 botões primários por contraste perdido
      (i.e. **só** botões neutros), sinalizar — pode ser que esse ecrã
      use `.btn-secondary` para o que devia ser `.btn-primary`.

**Aceitação:**
- `.btn-secondary` em index.css é branco-com-borda, NÃO grafite-sólido.
- Audit visual confirma SKILL §Buttons (≤1 primário Carmesim por view;
  outros neutros).

---

## Fase 5 — Verificação final & relatório (V16)

- [ ] `cd frontend && npx eslint src/ --ext .js,.jsx --max-warnings=60` limpo.
- [ ] `cd frontend && CI=true npx craco build` exit 0.
- [ ] `grep "color: 'var(--text"` em `frontend/src/` retorna 0 (Fase 0).
- [ ] `grep "animate=\{"` em `DocumentosPage.js` retorna 0 (Fase 1).
- [ ] Relatório consolidado (commits, mudanças por categoria,
      qualquer resíduo novo).
- [ ] `tasks/lessons.md`: adicionar lições novas se surgirem.

---

## Fora de escopo (7.3)

- Reescrever paleta destrutiva system-wide (`text-red-*` continua em
  status-error de algumas tags semânticas — alvo da Fase 4 do spec
  principal já feita).
- Refactor de `var(--surface-*)` inline → classes (mais ampla,
  out-of-spec; alvo eventual de spec futura).
- Public pages (mesmo escopo do spec principal: privado-first).
- `tasks/todo.md` (gerido por outro processo).

---

_Spec gerada após execução da `frontend-consistency-spec.md` (16
commits, c0e2bac..750fa86). Branch `fix/frontend-consistency`,
nada em `main`. ESLint 0/43, build exit 0._
