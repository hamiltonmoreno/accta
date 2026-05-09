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
- Tailwind CSS exclusively — no inline styles, no CSS modules
- Brand colors: Carmesim (#C7202F) for accents/CTAs, Grafite (#3A3A3A) for text
- Font: Open Sans (body), JetBrains Mono (code)
- No dark mode — disabled by design decision
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
