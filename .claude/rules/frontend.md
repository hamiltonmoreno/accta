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
- Local state (useState) for component-level state
- No Redux/Zustand — Context API is sufficient

## API Integration
- All API calls go through `utils/api.js`
- Use the existing API groups (authAPI, usersAPI, financesAPI, etc.)
- Handle loading/error states in components
- 401 responses trigger automatic logout via interceptor

## Routing
- Protected routes use `<ProtectedRoute>` wrapper
- Specify `allowedRoles` for role-restricted pages
- Public pages under `/pages/public/`, private under `/pages/private/`

## UI Text
- All user-facing text in Portuguese (PT)
- Use Sonner (toast) for success/error feedback
- Loading states use Skeleton components
