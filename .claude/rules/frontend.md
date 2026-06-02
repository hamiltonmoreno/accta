---
paths:
  - "frontend/src/components/**/*.js"
  - "frontend/src/components/**/*.jsx"
  - "frontend/src/pages/**/*.js"
  - "frontend/src/layouts/**/*.js"
---

# Frontend Rules — ACCTA Portal

## Components
- Functional components + hooks only
- shadcn/ui (New York style) for UI primitives — never build from scratch
- Lucide React for all icons
- Framer Motion for animations
- cn() from lib/utils.js for conditional classes

## Styling
> Canonical design system: the **`/frontend-design` skill**
> (`.claude/skills/frontend-design/SKILL.md`). It wins on any conflict.
- Tailwind CSS exclusively — no inline styles, no CSS modules
- **Neutral-led**: white `#FFFFFF` / `#F5F5F5` surfaces, Grafite `#3A3A3A` text,
  muted never lighter than `#6B7280`. Neutral carries ~90% of the UI.
- **Action color is semantic**: the ONE primary positive button per view is
  **Floresta `#166534`** (hover `#14532D`; Guardar/Confirmar/Criar/Aprovar/
  Entrar/Votar). **Carmesim `#C7202F`** (hover `#A51B27`) is brand identity +
  destructive: active nav, links on white, focus ring, logo — and destructive
  actions as **outline by default** (`bg-white border-[#C7202F] text-[#C7202F]
  hover:bg-[#FBEAEC]`), solid carmesim only inside an irreversible confirm
  dialog. Default every other control to neutral (Secondary = `border-[#D1D5DB]`).
- ❌ **Never Carmesim/red text on dark, Navy or colored backgrounds** — the
  legibility bug. ❌ Never make every button red (red = destructive only).
  ❌ Never Carmesim as a positive primary (that is Floresta).
- Every text/bg pair must reach ≥4.5:1; status = icon + text (never color alone)
- Focus: `focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 ring-offset-2`
- Font: Open Sans (body + headings), JetBrains Mono (code) — max 2 weights/section
- No dark mode — disabled by design decision; no flat black
- Glass effects: use `.glass-effect` utility class

## State Management
- AuthContext for auth state (login, logout, roles)
- NotificationContext for real-time notifications
- TanStack Query (`@tanstack/react-query`) for server state
  (fetching, caching, mutations) — see API Integration below
- Local state (useState) for UI-only state (modals, form drafts, filters)
- No Redux/Zustand — Context API + TanStack Query are sufficient

## API Integration
- All API calls go through `utils/api.js` (keep using axios groups)
- Read patterns: `useQuery({ queryKey: queryKeys.X.Y(), queryFn })`
  - Use `queryKeys` from `lib/queryClient.js` — never hand-roll keys
  - Default `staleTime: 30s` is fine for most lists; override for
    rapidly-changing data (lower) or read-only/static (higher)
- Write patterns: `useMutation({ mutationFn, onSuccess, onError })`
  - On success, `qc.invalidateQueries({ queryKey })` to auto-refetch
  - Surface errors via `toast.error(error.response?.data?.detail)`
- DO NOT mix patterns: pages already migrated to useQuery/useMutation
  must not re-introduce `useState + useEffect + axios`
- 401 responses trigger automatic logout via interceptor (utils/api.js)
- Avoid `console.error` for API failures — TanStack DevTools logs and
  the user already gets toast/UI feedback

## Routing
- Protected routes use `<ProtectedRoute>` wrapper
- Specify `allowedRoles` for role-restricted pages
- Public pages under `/pages/public/`, private under `/pages/private/`

## UI Text
- All user-facing text in Portuguese (PT)
- Use Sonner (toast) for success/error feedback
- Loading states use Skeleton components
