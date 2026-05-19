---
name: frontend-design
description: Apply ACCTA brand design standards to any UI component or page.
user-invocable: true
---

# ACCTA Design System

> **Canonical source of truth** for ACCTA visual design. The `ui-ux-pro-max`
> skill provides pattern/UX/chart intelligence but defers to this file for every
> color, type, spacing and component decision.

## Design Philosophy

Professional, accessible, **neutral-led**. The interface is built on a calm
neutral foundation; **Carmesim `#C7202F` is the brand logo color and the single
accent — used sparingly, never as the default for every control.** Inspired by
Swiss Modernism: strict hierarchy, one accent, high contrast, no decoration for
its own sake. **Light mode only.** WCAG 2.1 AA is a hard floor (AAA for body
text where achievable).

The most common past mistake — and the rule that overrides instinct:
**most buttons and surfaces are neutral; red is an event, not a background.**

---

## Color System

### 1. Brand accent (use sparingly — ≤1 prominent instance per view)

| Token | Hex | Where it is ALLOWED |
|-------|-----|---------------------|
| Carmesim | `#C7202F` | The single primary button per view · active/selected nav indicator · links on white (underlined) · destructive primary button · focus ring tint · logo |
| Carmesim hover/active | `#A51B27` | Hover/pressed state of the above |
| Carmesim tint surface | `#FBEAEC` | Selected row / subtle highlight — **only** with Grafite text on top |

**Carmesim is FORBIDDEN as:** body text · the fill of secondary/every button ·
text on any dark/colored/photographic surface · large background areas · borders
of non-active elements.

### 2. Neutral foundation (carries ~90% of the UI)

| Role | Hex | Notes |
|------|-----|-------|
| Text primary (Grafite) | `#3A3A3A` | ~9:1 on white (AAA) |
| Text secondary / muted | `#6B7280` | ~4.8:1 on white (AA) — **never use text lighter than this** |
| Text on accent/dark | `#FFFFFF` | white on `#C7202F` ≈ 5.7:1 (AA) |
| Decorative disabled | `#9CA3AF` | non-text only (icons/dividers) |
| Surface base | `#FFFFFF` | main background |
| Surface sunken | `#F5F5F5` | secondary surfaces, page sections |
| Border default | `#E5E7EB` | cards, inputs |
| Border strong / divider | `#D1D5DB` | secondary buttons, separators |
| Glass | `rgba(255,255,255,0.8)` | + `backdrop-blur-sm` + `border-white/30` |

### 3. Structural deep accent (restricted)

`#1e3a5f` (Navy) — **only** for public/marketing hero depth or a deliberate dark
band, **always with white text** (never red text on it). Not used in the member
portal chrome (sidebar/header are light). Not a second accent.

### 4. Semantic status (always icon + text — never color alone)

| State | Text/Icon | Tint background | Solid (button/badge fill) |
|-------|-----------|-----------------|---------------------------|
| Success | `#15803D` | `#F0FDF4` | `#16A34A` |
| Warning | `#B45309` | `#FFFBEB` | `#D97706` |
| Error | `#B91C1C` | `#FEF2F2` | `#C7202F` (brand) hover `#A51B27` |
| Info | `#1D4ED8` | `#EFF6FF` | `#2563EB` |

Error **message text** uses the accessible `#B91C1C`; a destructive **button
fill** uses brand `#C7202F`. All -700 text shades clear 4.5:1 on white and on
their own tint.

### 5. Allowed contrast pairs (the rule that kills red-on-dark)

Only these foreground/background combinations are permitted for text:

- Grafite `#3A3A3A` **on** white / `#F5F5F5` / `#FBEAEC` — primary text
- `#6B7280` **on** white / `#F5F5F5` — secondary text
- White `#FFFFFF` **on** `#C7202F` / `#A51B27` / `#1e3a5f` / semantic solids
- Carmesim `#C7202F` **on** white only — links/emphasis (underline links)
- Semantic -700 **on** its matching tint or white

Anything else (esp. **red text on dark/Navy/photo**) is a defect. Verify every
text/bg pair reaches **4.5:1** (3:1 for ≥24px or ≥18.66px bold).

---

## Typography

- Family: **Open Sans** (headings + body), **JetBrains Mono** (code only)
- Hero titles: 2.5–3rem, font-bold (700)
- Section headings: 1.5–2rem, font-semibold (600)
- Body: 0.875–1rem, font-normal (400); min 16px on mobile
- Muted/caption: 0.875rem, color `#6B7280`
- Line-height 1.5–1.7 body; line-length 65–75ch
- **Max 2 font weights per section.** Letter-spacing tight on headings only.

---

## Spacing & Layout

- Page padding: 24–32px · Card padding: 16–24px · Section gaps: 32–48px
- Border radius: 8px cards · 6px buttons/inputs · 12px modals
- Sidebar: 270px expanded / 72px collapsed (`PrivateLayout`)
- Containers: consistent `max-w-7xl`; 8px base spacing unit
- z-index scale: 10 / 20 / 30 / 50

---

## Buttons (taxonomy — the fix for "everything is red")

**Never more than one Primary (Carmesim-filled) button visible in the same
view/section.** Default to Secondary; promote to Primary only the single main
action.

| Tier | Use for | Spec |
|------|---------|------|
| **Primary** | The ONE main action (Salvar, Confirmar) | `bg-[#C7202F] text-white hover:bg-[#A51B27] rounded-md px-4 py-2 font-semibold` |
| **Secondary** | Neutral / alternative (Cancelar, Voltar) | `bg-white border border-[#D1D5DB] text-[#3A3A3A] hover:bg-[#F5F5F5] rounded-md px-4 py-2` |
| **Tertiary / Ghost** | Low-emphasis, toolbars, inline | no bg/border, `text-[#3A3A3A] hover:bg-[#F5F5F5]`; link-style = Carmesim underline |
| **Destructive** | Irreversible (Excluir) | primary: `bg-[#C7202F] text-white`; secondary destructive: `border border-[#B91C1C] text-[#B91C1C]`; **always** a confirm dialog |
| **Disabled** | — | `opacity-50 cursor-not-allowed`, no hover |

All clickable elements: `cursor-pointer`. All interactive elements:
`focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2`
(focus visibility is CRITICAL — never `outline-none` without a replacement).

---

## Components

- Cards: `bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6` · hover `shadow-md`
- Elevated/modal: `shadow-lg` / `shadow-xl`, radius 12–16px
- Glass: `bg-white/80 backdrop-blur-sm border border-white/30`
- Inputs: `border border-[#E5E7EB] rounded-md px-3 py-2`; focus ring as above; use shadcn/ui
- Forms: shadcn/ui + Zod validation + toast feedback (PT)
- Tables: zebra optional with `#F5F5F5`; row hover `#F5F5F5`; selected row `#FBEAEC`
- Build on **shadcn/ui** primitives (New York) — do not hand-roll inputs/dialogs

## Animations (Framer Motion)

- Page enter: fadeIn + slideUp (y: 20 → 0, opacity 0 → 1, 0.3s)
- Stagger children: 0.05 · Hover scale: 1.02 (0.2s)
- Transitions 150–300ms; respect `prefers-reduced-motion`
- Subtle and professional — no layout-shifting hovers, no flashy motion

## Patterns

- Dashboard: stat-card grid + charts (Recharts) + activity feed
- List pages: filter bar + table/card grid + pagination
- Detail pages: header with actions + tabbed content
- Empty states: centered SVG icon + message + single primary action
- Status: badge = icon + label + semantic color (never color alone)

---

## Do NOT

- ❌ Dark mode (disabled by design) · flat black backgrounds
- ❌ Carmesim as text on dark/colored/photo backgrounds — **the legibility bug**
- ❌ Make every button red — Primary is rare; the rest are neutral
- ❌ Any color outside this system; accent on large surfaces
- ❌ Text lighter than `#6B7280`; more than 2 font weights per section
- ❌ Convey state by color alone (always pair with icon/text)
- ❌ Remove focus outline without a visible replacement
- ❌ Custom UI primitives (use shadcn/ui) · inline styles (Tailwind only)
- ❌ Non-PT user-facing text · an `inadimplente` member status

## Acceptance checklist (verify before delivering UI)

- [ ] ≤1 Primary/Carmesim button per view; others neutral
- [ ] Every text/bg pair is an allowed contrast pair and ≥4.5:1 (3:1 large)
- [ ] No red text on dark/Navy/photo anywhere
- [ ] Visible `focus-visible` ring on all interactive elements
- [ ] Status uses icon + text + semantic color
- [ ] Open Sans, ≤2 weights/section; muted text ≥ `#6B7280`
- [ ] shadcn/ui primitives; Tailwind only; all copy in PT
- [ ] Responsive 375 / 768 / 1024 / 1440px; `prefers-reduced-motion` respected
