---
name: ui-ux-pro-max
description: "UI/UX design intelligence ADAPTED TO THE ACCTA BRAND. 67 styles, 96 palettes, 57 font pairings, 25 charts, 13 stacks (React, Next.js, Vue, Svelte, Tailwind, shadcn/ui). Actions: plan, build, create, design, implement, review, fix, improve, optimize, refactor, check UI/UX code. Projects: ACCTA Portal pages/components, dashboard, admin panel, landing, forms, tables, charts. Elements: button, modal, navbar, sidebar, card, table, form, chart. Topics: color palette, accessibility, animation, layout, typography, spacing, hover, shadow. Output is HARD-LOCKED to the ACCTA brand (Carmesim #C7202F / Grafite #3A3A3A / Navy #1e3a5f, Open Sans, light mode only, shadcn/ui)."
user-invocable: true
---

# UI/UX Pro Max — ACCTA Edition

> Project-local copy of `ui-ux-pro-max`, **adapted to the ACCTA brand**. It overrides
> the generic global skill of the same name (project skills win by precedence).
> The CSV/BM25 engine still works, but its color / typography / dark-mode output
> is **advisory only** — the Brand Lock below and the **`/frontend-design`** skill
> are authoritative.

---

## 🔒 ACCTA BRAND LOCK (read first — non-negotiable)

Per `CLAUDE.md` and `.claude/rules/frontend.md`, **`/frontend-design` is the
single source of truth** for ACCTA design. This skill provides the *engine*
(pattern/UX/layout/chart intelligence); it must never emit off-brand tokens.

**Neutral-led system — Carmesim is the single accent, not the default.**
Full spec in `/frontend-design` (canonical); summary — discard any engine
suggestion that conflicts:

| Token | Value | Use |
|-------|-------|-----|
| Carmesim (brand accent) | `#C7202F` · hover `#A51B27` | ONLY: the one primary button per view · active nav · links on white · destructive · focus ring. Never body text, never on dark. |
| Text primary (Grafite) | `#3A3A3A` | body + headings (≈9:1 on white) |
| Text muted | `#6B7280` | never use text lighter than this |
| Surface | `#FFFFFF` main · `#F5F5F5` sunken | neutral foundation (~90% of UI) |
| Border | `#E5E7EB` default · `#D1D5DB` strong/divider | — |
| Navy (restricted) | `#1e3a5f` | public/marketing hero depth only, white text — not portal chrome, not a 2nd accent |
| Glass | `rgba(255,255,255,0.8)` + `backdrop-blur-sm` + `border-white/30` | — |
| Semantic (text/tint/solid) | Success `#15803D`/`#F0FDF4`/`#16A34A` · Warn `#B45309`/`#FFFBEB`/`#D97706` · Error `#B91C1C`/`#FEF2F2`/`#C7202F` · Info `#1D4ED8`/`#EFF6FF`/`#2563EB` | icon + text, never color alone |
| Fonts | **Open Sans** (headings+body), **JetBrains Mono** (code) | max 2 weights/section |
| Radius / Shadow | `8px` card · `6px` btn · `12px` modal · `shadow-sm`→`md/lg` hover | — |
| Motion (Framer) | enter fadeIn+slideUp (y:20→0, 0.3s) · stagger 0.05 · hover scale 1.02 (0.2s) | subtle |
| Focus (CRITICAL) | `focus-visible:ring-2 ring-[#C7202F]/40 ring-offset-2` | every interactive el |

**Button taxonomy:** Primary = `bg-[#C7202F] text-white` (**≤1 per view**);
Secondary = `bg-white border-[#D1D5DB] text-[#3A3A3A]`; Tertiary = ghost;
Destructive = brand red + confirm dialog. Default to Secondary.

**Hard NOs (treat as CRITICAL anti-patterns):**

- ❌ **Dark mode** — disabled by design decision. Never add it. Never "test both modes".
- ❌ **Carmesim/red text on dark, Navy, colored or photo backgrounds** — the legibility bug to never repeat.
- ❌ **Every button red** — Primary is rare; everything else is neutral.
- ❌ Flat black backgrounds; any color outside the system above; accent on large surfaces.
- ❌ Text lighter than `#6B7280`; state conveyed by color alone (pair with icon/text).
- ❌ Removing focus outline without a visible replacement.
- ❌ Custom UI primitives — use **shadcn/ui** (New York style).
- ❌ More than 2 font weights per section; any font other than Open Sans / JetBrains Mono.
- ❌ An `inadimplente` status — member statuses are only `ativo` / `inativo` / `pendente_convite`.
- ❌ Inline styles — Tailwind only. All user-facing text in **Portuguese (PT)**.

**Query convention (makes the engine return ACCTA, not generic):** the dataset
contains ACCTA-locked rows whose unique token is `accta`. **Every query you run
through the engine MUST contain the literal word `accta`**, and you MUST pass
`-p "ACCTA Portal"`. The high IDF of `accta` ranks the ACCTA rows #1 across the
product / color / typography / landing / reasoning domains.

If engine output and this Brand Lock ever disagree, the Brand Lock and
`/frontend-design` win — no exceptions.

---

## When to Apply

Reference these guidelines when:
- Designing/building ACCTA Portal components or pages
- Choosing layout patterns, charts, animations, UX details
- Reviewing ACCTA UI code for UX / accessibility issues

For **color, typography, and brand tokens**, the Brand Lock above is final —
the engine is consulted for *pattern/UX/chart/layout* intelligence only.

## Rule Categories by Priority

| Priority | Category | Impact | Domain |
|----------|----------|--------|--------|
| 1 | Accessibility | CRITICAL | `ux` |
| 2 | Touch & Interaction | CRITICAL | `ux` |
| 3 | Performance | HIGH | `ux`, `react` |
| 4 | Layout & Responsive | HIGH | `ux` |
| 5 | Typography & Color | LOCKED | Brand Lock (not engine) |
| 6 | Animation | MEDIUM | `ux` |
| 7 | Style Selection | MEDIUM | `style`, `product` |
| 8 | Charts & Data | LOW | `chart` |

## Quick Reference

### 1. Accessibility (CRITICAL)
- `color-contrast` — min 4.5:1 (Grafite `#3A3A3A` on white passes; verify Carmesim usage)
- `focus-states` — visible focus rings on interactive elements
- `alt-text` — descriptive alt text for meaningful images
- `aria-labels` — `aria-label` for icon-only buttons
- `keyboard-nav` — tab order matches visual order
- `form-labels` — `<label for>`; pair with shadcn/ui form + Zod + toast feedback

### 2. Touch & Interaction (CRITICAL)
- `touch-target-size` — min 44×44px
- `loading-buttons` — disable button during async; spinner
- `error-feedback` — clear PT message near the problem (toast)
- `cursor-pointer` — on every clickable element

### 3. Performance (HIGH)
- `image-optimization` — WebP, srcset, lazy loading
- `reduced-motion` — respect `prefers-reduced-motion`
- `content-jumping` — reserve space for async content (skeletons)

### 4. Layout & Responsive (HIGH)
- `readable-font-size` — min 16px body on mobile
- `breakpoints` — verify at 375 / 768 / 1024 / 1440px
- Sidebar: 270px expanded, 72px collapsed (ACCTA `PrivateLayout`)
- `z-index-management` — defined scale (10, 20, 30, 50)

### 5. Animation (MEDIUM)
- Use the Framer Motion specs from the Brand Lock; nothing flashy

### 6. Style Selection (MEDIUM)
- ACCTA style priority: **Glassmorphism + Flat Design + Minimalism**
- Same style across all pages; SVG icons only (no emoji icons)

### 7. Charts & Data (LOW)
- Recharts (project standard); accessible palette anchored on brand tokens
- Provide a table alternative for accessibility

---

## Prerequisites

```bash
python --version    # or: python3 --version   (3.11+ in this project)
```

## How to Use This Skill

### Step 1: Analyze the request
- ACCTA Portal area: dashboard, financeiro, projetos, mural, eventos, votação, admin…
- Page type: dashboard / list / detail / form / empty state / public marketing
- Stack: this project = **React 19 + Tailwind + shadcn/ui** → use `--stack shadcn`
  (or `--stack react`); never default to `html-tailwind` here.

### Step 2: Generate the design system (REQUIRED — note the `accta` token)

```bash
python .claude/skills/ui-ux-pro-max/scripts/search.py "accta portal <area> <page type>" --design-system -p "ACCTA Portal"
```

Example:

```bash
python .claude/skills/ui-ux-pro-max/scripts/search.py "accta portal financeiro dashboard" --design-system -p "ACCTA Portal"
```

This resolves to the ACCTA-locked rows: Carmesim/Grafite/Navy palette, Open Sans,
ACCTA Portal pattern, `CRITICAL` anti-patterns including **dark mode**. If the
output ever shows non-brand hexes or a non-Open-Sans font, the query was missing
the `accta` token or `-p "ACCTA Portal"` — fix it and re-run; the Brand Lock
still overrides regardless.

### Step 3: Supplement with detailed searches (pattern/UX/chart only)

```bash
python .claude/skills/ui-ux-pro-max/scripts/search.py "accta <keyword>" --domain ux  -n 5
python .claude/skills/ui-ux-pro-max/scripts/search.py "accta <keyword>" --domain chart
python .claude/skills/ui-ux-pro-max/scripts/search.py "accta <keyword>" --domain landing
```

Do **not** use `--domain color` / `--domain typography` to *decide* brand tokens —
those are fixed by the Brand Lock. (You may run them to confirm the ACCTA row wins.)

### Step 4: Stack guidelines (ACCTA = shadcn/React)

```bash
python .claude/skills/ui-ux-pro-max/scripts/search.py "accta <keyword>" --stack shadcn
python .claude/skills/ui-ux-pro-max/scripts/search.py "accta <keyword>" --stack react
```

### Step 5: Persisting a design system (optional)

`--persist` writes to `design-system/accta-portal/` in the **current working
directory**. If you use it, run from a scratch dir or delete the output after —
do not commit generated `design-system/` folders into the repo.

---

## Search Reference

| Domain | Use for (ACCTA) |
|--------|-----------------|
| `product` | resolves category → "ACCTA Portal" |
| `style` | layout/effect style (Glass/Flat/Minimal) |
| `landing` | public marketing page structure |
| `chart` | Recharts chart-type selection |
| `ux` | accessibility, a11y, loading, z-index |
| `react` | React 19 performance (memo, suspense, rerender) |
| `web` | aria, focus, semantic, virtualize |
| `color` / `typography` | **confirmation only** — tokens are Brand-Locked |

Stacks available: `shadcn` (preferred), `react`, `nextjs`, `vue`, `svelte`,
`html-tailwind`, `swiftui`, `react-native`, `flutter`, `jetpack-compose`.

---

## Common Rules for Professional UI (ACCTA)

| Rule | Do | Don't |
|------|----|-------|
| Icons | SVG (Lucide / Heroicons) | emojis as UI icons |
| Hover | color/opacity/shadow transition 150–300ms | scale transforms that shift layout |
| Primitives | shadcn/ui (New York) | hand-rolled inputs/dialogs |
| Cursor | `cursor-pointer` on clickables | default cursor on interactive cards |
| Glass card | `bg-white/80 backdrop-blur-sm border border-white/20` | `bg-white/10` (too transparent) |
| Text contrast | Grafite `#3A3A3A` body, muted no lighter than `#475569` | gray-400 or lighter body text |
| Container | consistent `max-w-7xl`; page padding 24–32px | mixed container widths |

---

## Pre-Delivery Checklist (ACCTA)

### Brand (LOCKED)
- [ ] Only brand tokens used (Carmesim `#C7202F`, Grafite `#3A3A3A`, Navy `#1e3a5f`, white/`#F5F5F5`)
- [ ] **No dark mode**, no flat black, no off-brand colors
- [ ] Open Sans (≤2 weights/section); JetBrains Mono only for code
- [ ] shadcn/ui primitives; Tailwind only (no inline styles)
- [ ] All user-facing text in Portuguese (PT)
- [ ] No `inadimplente` status anywhere

### Visual / Interaction
- [ ] SVG icons only (Lucide/Heroicons), consistent set & sizing
- [ ] `cursor-pointer` on all clickables; hover feedback without layout shift
- [ ] Transitions 150–300ms; Framer Motion enter/stagger per Brand Lock
- [ ] Focus states visible for keyboard nav

### Layout / A11y
- [ ] Responsive at 375 / 768 / 1024 / 1440px; no horizontal scroll on mobile
- [ ] Content not hidden behind fixed navbar/sidebar
- [ ] Images have alt text; form inputs have labels (shadcn/ui + Zod + toast)
- [ ] Color is not the only indicator; `prefers-reduced-motion` respected

---

## Relationship to `/frontend-design`

`/frontend-design` = **canonical brand spec** (what the tokens are).
This skill = **design intelligence engine** (which pattern/UX/chart/layout to use),
constrained to those tokens. When in doubt about a color, font, radius, spacing or
animation value, defer to `/frontend-design`. Engine guidance that contradicts it
is wrong by definition.
