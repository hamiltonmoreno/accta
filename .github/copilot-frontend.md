# Frontend Copilot Instructions — ACCTA Portal React App

## Quick Start

Run the frontend development server:
```bash
cd frontend
yarn install  # First time only
yarn start    # Runs on http://localhost:3000
```

---

## Architecture Overview

### Project Structure

```
src/
├── App.js                    # Root component + routing
├── App.css                   # Global styles
├── index.js                  # Entry point
├── index.css                 # Global CSS reset
│
├── components/               # Reusable UI components
│   ├── ACCTALogo.jsx
│   ├── NotificationBell.jsx
│   ├── UserMenu.jsx
│   └── ...
│
├── contexts/                 # React Context (state management)
│   ├── AuthContext.jsx       # Authentication state
│   ├── NotificationContext.jsx
│   └── ThemeContext.jsx
│
├── hooks/                    # Custom React hooks
│   ├── useAuth.js
│   ├── useNotifications.js
│   └── ...
│
├── layouts/                  # Layout wrappers
│   ├── PublicLayout.jsx      # For public pages
│   └── PrivateLayout.jsx     # For authenticated pages
│
├── pages/                    # Page components
│   ├── public/
│   │   ├── HomePage.jsx
│   │   ├── About.jsx
│   │   ├── Profession.jsx
│   │   ├── Transparency.jsx
│   │   ├── Gallery.jsx
│   │   └── WalletValidation.jsx
│   └── private/
│       ├── Dashboard.jsx
│       ├── Finances.jsx
│       ├── Projects.jsx
│       ├── Voting.jsx
│       ├── Events.jsx
│       ├── Profile.jsx
│       ├── Gallery.jsx (member uploads)
│       ├── Wall.jsx (mural)
│       ├── Notifications.jsx
│       ├── Documents.jsx
│       └── Benefits.jsx
│
├── utils/
│   ├── api.js                # ⭐ CENTRALIZED API LAYER (all backend calls)
│   ├── constants.js
│   └── helpers.js
│
└── lib/                      # UI component library (auto-generated)
    └── ...
```

---

## Core Patterns

### 1. API Calls (Always Use `api.js`)

**✅ DO THIS:**
```jsx
// In src/utils/api.js — Define all endpoints once
export const getUsers = () => api.get('/users');
export const getUserById = (id) => api.get(`/users/${id}`);
export const createUser = (data) => api.post('/users', data);
export const updateUser = (id, data) => api.put(`/users/${id}`, data);
export const deleteUser = (id) => api.delete(`/users/${id}`);

// In components — Use the functions
import { getUsers } from '../utils/api';

export function UserList() {
  const [users, setUsers] = useState([]);
  useEffect(() => {
    getUsers().then(res => setUsers(res.data));
  }, []);
  return <div>{users.map(u => <div key={u.id}>{u.name}</div>)}</div>;
}
```

**❌ DON'T DO THIS:**
```jsx
// ❌ Direct axios in components
useEffect(() => {
  axios.get('http://localhost:8001/api/users').then(...);
}, []);
```

### 2. Authentication & Context

**AuthContext Pattern:**
```jsx
// src/contexts/AuthContext.jsx
import { createContext, useState, useEffect } from 'react';
import { loginUser, refreshToken } from '../utils/api';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token is valid
      setUser(JSON.parse(localStorage.getItem('user')));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await loginUser(email, password);
    localStorage.setItem('token', res.data.token);
    localStorage.setItem('user', JSON.stringify(res.data.user));
    setUser(res.data.user);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

**Use in components:**
```jsx
import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

export function Dashboard() {
  const { user, logout } = useContext(AuthContext);
  return <div>Welcome {user.name} <button onClick={logout}>Logout</button></div>;
}
```

### 3. Component Pattern

**Functional Component with Hooks:**
```jsx
import { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { getItems, createItem } from '../utils/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function ItemList() {
  const { user } = useContext(AuthContext);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newItemName, setNewItemName] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const res = await getItems();
        setItems(res.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleAdd = async () => {
    try {
      const res = await createItem({ name: newItemName });
      setItems([...items, res.data]);
      setNewItemName('');
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-600">Error: {error}</div>;

  return (
    <div className="p-6 bg-white rounded-lg">
      <h2 className="text-2xl font-semibold mb-4">Items</h2>
      {items.map(item => (
        <div key={item.id} className="p-4 border-b">{item.name}</div>
      ))}
      <div className="mt-4 flex gap-2">
        <Input 
          value={newItemName} 
          onChange={(e) => setNewItemName(e.target.value)}
          placeholder="Item name"
        />
        <Button onClick={handleAdd}>Add</Button>
      </div>
    </div>
  );
}
```

---

## Styling Rules & Anti-Patterns

### Design System (Tailwind CSS)

**Color system** (canonical: `.claude/skills/frontend-design/SKILL.md` — the skill wins on any conflict). **Neutral-led: Carmesim is the single restrained accent, not the default.**
```js
// Neutral foundation (~90% of the UI)
Grafite (text primary):  #3A3A3A   // body/headings (~9:1 on white)
Text muted:              #6B7280   // never use text lighter than this
Surface:                 #FFFFFF / #F5F5F5
Border:                  #E5E7EB / #D1D5DB

// Single accent — sparingly
Carmesim:                #C7202F (hover #A51B27)
// ONLY: 1 primary button/view, active nav, links-on-white, destructive, focus ring
// NEVER: body text, every button, or text on dark/colored backgrounds

Navy (restricted):       #1e3a5f   // marketing hero only, white text
Semantic text/solid:     Success #15803D/#16A34A · Warn #B45309/#D97706
                         Error #B91C1C/#C7202F · Info #1D4ED8/#2563EB
```

**Typography Classes:**
```jsx
// Headings: Open Sans, semibold
<h1 className="text-5xl md:text-6xl tracking-tight font-semibold">Main Title</h1>

// Body text: Open Sans, always legible
<p className="text-base md:text-lg leading-relaxed text-slate-600">Description</p>

// Data/codes: JetBrains Mono
<span className="font-mono text-sm text-slate-700">ACCTA-2026-001</span>
```

**Button taxonomy** (≤1 Primary per view — default to Secondary):
```jsx
// Primary — the ONE main action per view
<button className="bg-[#C7202F] text-white hover:bg-[#A51B27] rounded-md px-4 py-2 font-semibold">Salvar</button>

// Secondary — neutral, the default for most actions
<button className="bg-white border border-[#D1D5DB] text-[#3A3A3A] hover:bg-[#F5F5F5] rounded-md px-4 py-2">Cancelar</button>

// Tertiary / ghost — low emphasis
<button className="text-[#3A3A3A] hover:bg-[#F5F5F5] rounded-md px-4 py-2">Voltar</button>
```

**Surface Patterns:**
```jsx
// Glass effect for overlays/cards
<div className="bg-white/80 backdrop-blur-sm border border-white/30 shadow-sm rounded-lg">
  Glass effect content
</div>

// Active menu item (Carmesim only as the indicator)
<div className="bg-[#F5F5F5] border-l-4 border-[#C7202F]">
  Active item
</div>

// Focus state (CRITICAL — every interactive element)
<button className="focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 rounded-md">
  Focused button
</button>

// Card
<div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6 hover:shadow-md transition-shadow">
  Card
</div>
```

### ❌ Anti-Patterns (NEVER DO)

```jsx
// ❌ Dark mode - FORBIDDEN
<div className="dark:bg-gray-900">...</div>

// ❌ Red/Carmesim text on dark or colored background — the legibility bug
<div className="bg-[#1e3a5f]"><p className="text-[#C7202F]">Texto</p></div>

// ❌ Every button red — Primary is rare; the rest are neutral
<button className="bg-[#C7202F] text-white">Cancelar</button>

// ❌ Accent on large surfaces / state by color alone
<section className="bg-[#C7202F]">...</section>

// ❌ Muted text lighter than #6B7280, or a font other than Open Sans
<p className="text-gray-400 font-serif">...</p>

// ❌ Non-brand CTAs — Primary is Carmesim #C7202F only (no purple/teal/green)
<button className="bg-purple-600">Action</button>
```

---

## React Router Setup

**Example routing in App.js:**
```jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PublicLayout from './layouts/PublicLayout';
import PrivateLayout from './layouts/PrivateLayout';
import HomePage from './pages/public/HomePage';
import Dashboard from './pages/private/Dashboard';
import { AuthProvider } from './contexts/AuthContext';

function ProtectedRoute({ children }) {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div>Loading...</div>;
  return user ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<About />} />
          </Route>

          {/* Private routes */}
          <Route element={
            <ProtectedRoute>
              <PrivateLayout />
            </ProtectedRoute>
          }>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/finances" element={<Finances />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}
```

---

## Form Handling (React Hook Form + Zod)

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1, 'Name required'),
  email: z.string().email('Invalid email'),
  role: z.enum(['admin', 'socio', 'financeiro', 'moderador']),
});

export function UserForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data) => {
    try {
      await createUser(data);
      // Success
    } catch (err) {
      // Error
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Input {...register('name')} placeholder="Name" />
        {errors.name && <span className="text-red-600">{errors.name.message}</span>}
      </div>
      <div>
        <Input {...register('email')} type="email" placeholder="Email" />
        {errors.email && <span className="text-red-600">{errors.email.message}</span>}
      </div>
      <Button type="submit">Submit</Button>
    </form>
  );
}
```

---

## Common Tasks

### Display Notification
```jsx
import { useContext } from 'react';
import { NotificationContext } from '../contexts/NotificationContext';

export function MyComponent() {
  const { addNotification } = useContext(NotificationContext);
  
  const handleSuccess = () => {
    addNotification({ type: 'success', message: 'Item created!' });
  };

  return <button onClick={handleSuccess}>Create</button>;
}
```

### Handle Loading & Errors
```jsx
if (loading) return <div className="flex justify-center p-8">Loading...</div>;
if (error) return <div className="p-4 bg-red-50 text-red-700 rounded">{error}</div>;
```

### Upload File
```jsx
const handleFileUpload = async (e) => {
  const file = e.target.files[0];
  const formData = new FormData();
  formData.append('file', file);
  const res = await uploadFile(formData);
  return res.data.url;
};
```

---

## Environment Variables

**`frontend/.env`**:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```
(`api.js` appends `/api` to this base.)

**Access in code:**
```jsx
const apiBase = `${process.env.REACT_APP_BACKEND_URL}/api`;
```

---

## Testing (Jest + React Testing Library)

**Pattern:**
```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { UserList } from './UserList';
import * as api from '../utils/api';

jest.mock('../utils/api');

test('displays users', async () => {
  api.getUsers.mockResolvedValue({
    data: [{ id: 1, name: 'John' }],
  });

  render(<UserList />);
  expect(await screen.findByText('John')).toBeInTheDocument();
});
```

---

## Debugging Tips

1. **API not responding?** Check `REACT_APP_BACKEND_URL` in `.env` and backend on port 8001
2. **Styles not applying?** Ensure Tailwind CSS is built (`yarn start` rebuilds)
3. **Context not working?** Verify `AuthProvider` wraps entire app in `App.js`
4. **Auth token expired?** Implement token refresh in `AuthContext`
5. **Console errors?** Check browser DevTools → Network tab for failed API calls

---

## Recommended Copilot Prompts

- "Add a new form field to the user profile page"
- "Create a modal component for confirming deletions"
- "Fix the styling on the stats cards to match the design system"
- "Add loading skeleton screens for the dashboard"
- "Update the API layer to include pagination for the members list"

---

**Last Updated**: May 19, 2026 (design system reworked: neutral-led, single restrained Carmesim accent, button taxonomy, no red-on-dark — mirrors the `frontend-design` skill)  
**Version**: 1.1
