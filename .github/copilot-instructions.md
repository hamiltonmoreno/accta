# GitHub Copilot Instructions — ACCTA Portal

## Overview

**ACCTA Portal** is an institutional website and member management system (SGA) for the Association of Air Traffic Controllers of Cabo Verde. It provides public transparency, private member services, and administrative dashboards with advanced features like digital IDs (QR codes), financial tracking, voting systems, and notifications.

### Key Business Rules

- **No delinquent status**: All member quotas are deducted directly from salary — no pending payments concept
- **Light mode only**: Strict light-mode mandate (dark mode disabled)
- **Photo approval workflow**: Member-submitted photos require admin approval before visibility
- **QR code validation**: Digital wallet and benefits validation via SHA-256 encrypted QR codes
- **RBAC**: Four roles — `admin`, `socio` (member), `financeiro` (financial officer), `moderador` (moderator)

---

## Tech Stack & Architecture

### Frontend
- **Framework**: React 19 with Vite
- **Styling**: Tailwind CSS 3.4 + Shadcn/UI components
- **Routing**: React Router v7
- **Animation**: Framer Motion
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod validation
- **QR**: react-qr-code
- **API Client**: Axios (centralized in `src/utils/api.js`)
- **Package Manager**: Yarn 1.22.22

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: MongoDB (async via Motor)
- **Auth**: JWT + RBAC middleware
- **Async**: Uvicorn + asyncio
- **Rate Limiting**: SlowAPI (200 req/min default)
- **File Uploads**: S3-compatible (boto3) or local filesystem
- **Validation**: Pydantic v2

### Database
**Collections**: `users`, `invoices`, `polls`, `events`, `documents`, `wall_posts`, `notifications`, `projects`, `gallery_albums`, `gallery_photos`

### CI/CD
- **Platform**: GitHub Actions
- **Workflows**: `ci.yml` (lint/test), `deploy.yml` (production)

---

## Project Structure & Key Concepts

### Frontend Layout (`src/`)

```
components/        # Reusable UI components (ACCTALogo, NotificationBell, etc.)
contexts/          # AuthContext, NotificationContext, ThemeContext
hooks/             # Custom React hooks
layouts/           # PublicLayout, PrivateLayout
pages/
  ├── public/      # HomePage, About, Profession, Transparency, Gallery
  └── private/     # Dashboard, Finances, Projects, Voting, Events, etc.
utils/
  ├── api.js       # CENTRALIZED API layer (all backend calls)
  └── ...
```

### Backend Routes (`routes/`)

**Router Structure**: Each route module exports a FastAPI `router` object; all are aggregated in `routes/__init__.py`:

```
auth_routes.py     # /api/auth/* (login, register, token refresh)
users.py           # /api/users/* (CRUD, profile, admin management)
invoices.py        # /api/invoices/* (billing, export PDF/CSV)
polls.py           # /api/polls/* (voting)
posts.py           # /api/posts/* (social posts)
documents.py       # /api/documents/* (institutional docs)
benefits.py        # /api/benefits/* (club benefits + validation)
wall.py            # /api/wall/* (mural de comunicação)
events.py          # /api/events/* (events + calendar)
gallery.py         # /api/gallery/* (photos + albums + approval)
notifications.py   # /api/notifications/* (central + broadcast)
finances.py        # /api/finances/* (DRE, cash flow, charts)
projects.py        # /api/projects/* (CRUD + tasks + milestones)
activity.py        # /api/activity/* (activity feed)
report.py          # /api/report/* (export reports)
stats.py           # /api/stats/* (public transparency stats)
upload.py          # /api/upload/* (file handling)
```

### Core Backend Files

- **models.py**: Pydantic models for all entities (User, Invoice, Poll, Event, etc.)
- **database.py**: MongoDB connection, UPLOAD_DIR, database utilities
- **auth.py**: JWT creation/validation, password hashing (bcrypt)
- **helpers.py**: Shared utilities (email, QR code generation, etc.)
- **server.py**: FastAPI app setup, middleware (CORS, rate limiting), health check

---

## Development Workflow

### Local Setup

**Prerequisites**: Python 3.10+, Node.js 18+, MongoDB (local or Atlas)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
yarn install
yarn start

# Seed test data
cd scripts && python seed_data.py
```

### Test Credentials

| Profile | Email | Password |
|---------|-------|----------|
| Admin | admin@accta.cv | admin123 |
| Financial Officer | financeiro@accta.cv | fin123 |
| Member | socio1@accta.cv | socio123 |

### Key Commands

| Task | Command |
|------|---------|
| Run backend (dev) | `cd backend && uvicorn server:app --reload` |
| Run frontend (dev) | `cd frontend && yarn start` |
| Run backend tests | `cd backend && pytest tests/` |
| Build frontend | `cd frontend && yarn build` |
| Seed database | `cd scripts && python seed_data.py` |
| Linting (backend) | `cd backend && black . && isort .` |

### Environment Variables

**Backend** (`backend/.env`):
```
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/accta
JWT_SECRET=your-secret-key
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
UPLOAD_DIR=./uploads
S3_BUCKET=accta-uploads
S3_REGION=us-east-1
```

**Frontend** (`frontend/.env`):
```
REACT_APP_API_URL=http://localhost:8001/api
REACT_APP_TIMEOUT=30000
```

---

## Design System Reference

See [design_guidelines.json](design_guidelines.json) for exhaustive styling rules.

### Typography (Open Sans, Outfit on headings)

- **Display**: `text-6xl md:text-8xl tracking-tight font-bold`
- **H1**: `text-5xl md:text-6xl tracking-tight font-semibold`
- **Body**: `text-base md:text-lg leading-relaxed text-slate-600`

### Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Primary (Navy) | #0A1F44 | Sidebar, footer, headings |
| Secondary (Cloud) | #F4F6F8 | App background, panels |
| Accent (Radar Green) | #00FF9C | Active states, success, CTAs |
| Alert (Cockpit Red) | #FF4C4C | Errors, destructive actions |

### Component Patterns

- **Glass effect**: `bg-white/70 backdrop-blur-xl border border-white/40 shadow-sm`
- **Active item**: `bg-slate-100 border-l-4 border-[#00FF9C]`
- **Focus ring**: `ring-2 ring-[#0A1F44] ring-offset-2`

### Anti-Patterns ❌

- No dark mode
- No generic 'Inter' font everywhere
- No centered boring text blocks
- No gradients without texture/noise
- No purple/teal CTAs (use Navy or Green)

---

## Code Conventions

### Backend (FastAPI + Pydantic)

**Model Pattern**:
```python
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timezone
import uuid

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Route Pattern**:
```python
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
async def list_items(current_user: dict = Depends(get_current_user)):
    # Your code
    pass

@router.post("/", status_code=201)
async def create_item(item: ItemCreate, current_user: dict = Depends(get_current_user)):
    # Validation + DB insert
    pass
```

**Database Pattern**:
```python
from database import db
from bson import ObjectId

async def get_item(item_id: str):
    return await db.items.find_one({"_id": ObjectId(item_id)})
```

### Frontend (React + Hooks)

**Component Pattern**:
```jsx
import { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { Button } from '@/components/ui/button';

export function MyComponent() {
  const { user } = useContext(AuthContext);
  const [state, setState] = useState(null);

  return (
    <div className="p-6 bg-white rounded-lg">
      {/* Component content */}
    </div>
  );
}
```

**API Call Pattern** (use `src/utils/api.js`):
```javascript
// In src/utils/api.js
export const getItems = () => api.get('/items');
export const createItem = (data) => api.post('/items', data);

// In component
import { getItems } from '../utils/api';
const [items, setItems] = useState([]);
useEffect(() => {
  getItems().then(res => setItems(res.data));
}, []);
```

### Testing

- **Backend**: pytest in `backend/tests/` (see `test_*.py` for patterns)
- **Frontend**: Jest + React Testing Library in `__tests__/` directories
- **Test reports**: Stored in `test_reports/` as JSON + XML

---

## Debugging & Common Pitfalls

### Backend Issues

1. **MongoDB Connection**: Verify `MONGODB_URI` in `.env` — check credentials & IP whitelist (Atlas)
2. **CORS Errors**: Update `CORS_ORIGINS` in `.env` and restart server
3. **JWT Expiry**: Token TTL defaults to 24h; check `auth.py` for custom logic
4. **Rate Limiting**: SlowAPI limit is 200 req/min; adjust in `server.py` if needed
5. **File Uploads**: Ensure `UPLOAD_DIR` is writable or S3 credentials are valid

### Frontend Issues

1. **API Timeout**: Update `REACT_APP_TIMEOUT` if backend is slow
2. **Route Not Found**: Check React Router config in `App.js` + Layout structure
3. **Styling Conflicts**: Verify Tailwind CSS build in `craco.config.js` and no competing CSS
4. **Auth Context Missing**: Ensure `AuthContext` wraps entire app tree in `App.js`

### General Checks

- [ ] Is `.env` file created with all required vars?
- [ ] Are frontend & backend ports correct (3000 vs 8001)?
- [ ] Is MongoDB running / accessible?
- [ ] Are dependencies installed (`pip install`, `yarn install`)?

---

## Documentation & References

- **[PROJETO_ACCTA.md](PROJETO_ACCTA.md)**: Detailed feature overview & URLs
- **[DEPLOY.md](DEPLOY.md)**: Production deployment guide
- **[SSH_SETUP.md](SSH_SETUP.md)**: SSH key configuration
- **[SISTEMA_NOTIFICACOES.md](SISTEMA_NOTIFICACOES.md)**: Notification system architecture
- **[ANALISE_MELHORIAS.md](ANALISE_MELHORIAS.md)**: Improvement analysis & roadmap
- **[design_guidelines.json](design_guidelines.json)**: Exhaustive design system reference

---

## Recommended Copilot Workflows

### New Feature Development

```
1. Define data model in backend/models.py (Pydantic)
2. Create FastAPI route in routes/{feature}.py
3. Seed test data in scripts/seed_{feature}.py
4. Write backend tests in tests/test_{feature}.py
5. Build React page/component in frontend/src/pages/private
6. Wire API calls via frontend/src/utils/api.js
7. Run full system test with `pytest backend/tests/`
```

### Bug Fix Workflow

```
1. Identify component (backend route vs frontend page)
2. Check logs: backend test failure → check models/routes; frontend → browser console
3. Review test_reports/ for failure patterns
4. Write failing test first, then fix code
5. Run full test suite to prevent regressions
```

---

## Prompt Examples for Copilot

- **"Add a new field `department` to User model and update the admin form"** → Touches models.py, routes/users.py, frontend component
- **"Create a notification broadcast endpoint for admins"** → Add route to routes/notifications.py, create FastAPI endpoint with admin auth check
- **"Why are photos not appearing in the gallery?"** → Check gallery.py route logic, image URL generation, frontend image component rendering
- **"Fix the CORS error on login"** → Check CORS_ORIGINS env var, restart backend, verify frontend API_URL

---

## Quick Reference: RBAC Privileges

| Role | Privileges |
|------|-----------|
| `admin` | All privileges: manage users, finances, events, documents, content moderation, benefits, audit logs |
| `financeiro` | `manage_finances`, `view_audit_logs` |
| `moderador` | `moderate_content` |
| `socio` | Read-only access to public areas; limited write to own profile, wall posts, event registration |

---

## File Naming & Organization

- **Python files**: `snake_case.py`
- **React files**: `PascalCase.jsx` (components), `camelCase.js` (utilities)
- **Routes**: Organized by feature (not HTTP method) — e.g., `routes/invoices.py` contains GET, POST, PUT, DELETE for invoices
- **Tests**: `test_{feature}.py` mirroring route structure

---

**Last Updated**: April 2, 2026  
**Version**: 1.0
