---
name: frontend-design
description: Apply ACCTA brand design standards to any UI component or page.
user-invocable: true
---

# ACCTA Design System

## Colors
- Primary/Accent: Carmesim #C7202F (CTAs, alerts, important actions)
- Text Primary: Grafite #3A3A3A
- Background: #FFFFFF (main), #F5F5F5 (secondary surfaces)
- Surfaces: rgba(255,255,255,0.8) with backdrop-blur for glass effects
- Navy: #1e3a5f (headers, navigation depth)
- Success: green-500, Warning: amber-500, Error: red-500

## Typography
- Font Family: Open Sans (body + headings), JetBrains Mono (code/monospace)
- Hero titles: 2.5rem-3rem, font-bold
- Section headings: 1.5rem-2rem, font-semibold
- Body text: 0.875rem-1rem, font-normal
- Letter spacing: tight on headings, normal on body

## Spacing & Layout
- Page padding: 24px-32px
- Card padding: 16px-24px
- Section gaps: 32px-48px
- Border radius: 8px (cards), 6px (buttons), 12px (modals)
- Sidebar: 270px expanded, 72px collapsed

## Components
- Cards: bg-white rounded-lg shadow-sm border border-gray-100 p-6
- Buttons primary: bg-[#C7202F] text-white hover:bg-[#a51b27] rounded-md px-4 py-2
- Buttons secondary: border border-gray-300 text-gray-700 hover:bg-gray-50
- Glass effect: bg-white/80 backdrop-blur-sm border border-white/20
- Elevated cards: shadow-md hover:shadow-lg transition-shadow

## Animations (Framer Motion)
- Page enter: fadeIn + slideUp (y: 20 → 0, opacity: 0 → 1, duration: 0.3s)
- Stagger children: staggerChildren: 0.05
- Hover scale: scale: 1.02, transition: { duration: 0.2 }
- No excessive animations — subtle and professional

## Patterns
- Dashboard: grid of stat cards + charts + activity feed
- List pages: search/filter bar + table or card grid + pagination
- Detail pages: header with actions + tabbed content
- Forms: shadcn/ui form components + Zod validation + toast feedback
- Empty states: centered icon + message + action button

## Do NOT
- Use dark mode (disabled)
- Use flat black backgrounds
- Use colors outside the brand palette
- Build custom UI primitives (use shadcn/ui)
- Use more than 2 font weights per section
