# Testing Copilot Instructions — ACCTA Portal

## Quick Start

### Backend Testing (Pytest)

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_users.py -v

# Run with coverage report
pytest tests/ --cov --cov-report=html

# Run tests matching a pattern
pytest tests/ -k "auth" -v

# Run with detailed output
pytest tests/ -vv --tb=short
```

### Frontend Testing (Jest + RTL)

```bash
cd frontend

# Run all tests
yarn test --watchAll=false

# Run with coverage
yarn test --coverage --watchAll=false

# Run specific test file
yarn test UserList.test.js --watchAll=false

# Watch mode (re-runs on file changes)
yarn test
```

---

## Test Structure

### Backend Test Layout

```
backend/tests/
├── test_accta_portal.py           # Full system integration tests
├── test_auth_*.py                 # Authentication/JWT tests
├── test_finances.py               # Financial module tests
├── test_gallery*.py               # Gallery & photo approval tests
├── test_wall_mural.py             # Mural de comunicação tests
├── test_notifications_*.py        # Notification system tests
├── test_projects.py               # Project management tests
└── test_*.py                      # Other feature tests
```

### Frontend Test Layout

```
frontend/src/
├── components/
│   └── __tests__/
│       └── ACCTALogo.test.jsx
├── pages/
│   └── __tests__/
│       └── Dashboard.test.jsx
└── utils/
    └── __tests__/
        └── api.test.js
```

---

## Backend Testing Patterns (Pytest)

### 1. Basic Test Setup

```python
import pytest
import uuid
from fastapi.testclient import TestClient
from server import app
from database import db
from datetime import datetime, timezone

client = TestClient(app)

# Setup: Run before each test
@pytest.fixture
async def clear_users():
    await db.users.delete_many({})
    yield
    await db.users.delete_many({})

# Setup: Create sample data
@pytest.fixture
async def sample_user():
    user_data = {
        "id": str(uuid.uuid4()),
        "name": "John Doe",
        "email": "john@accta.cv",
        "password_hash": "hashed_pwd",
        "role": "socio",
        "status": "ativo",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_data)
    yield user_data
    # Cleanup
    await db.users.delete_one({"id": user_data["id"]})

@pytest.fixture
async def admin_user():
    user_data = {
        "id": str(uuid.uuid4()),
        "name": "Admin",
        "email": "admin@accta.cv",
        "password_hash": "hashed_pwd",
        "role": "admin",
        "status": "ativo",
        "privileges": ["manage_users", "manage_finances"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_data)
    yield user_data
    await db.users.delete_one({"id": user_data["id"]})
```

### 2. Testing GET Endpoints

```python
@pytest.mark.asyncio
async def test_list_users(sample_user):
    response = client.get("/api/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.asyncio
async def test_get_user_by_id(sample_user):
    user_id = sample_user["id"]
    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "john@accta.cv"

@pytest.mark.asyncio
async def test_get_nonexistent_user():
    response = client.get("/api/users/nonexistent-id")
    assert response.status_code == 404
```

### 3. Testing POST Endpoints

```python
@pytest.mark.asyncio
async def test_create_user():
    response = client.post("/api/users/", json={
        "name": "Jane Doe",
        "email": "jane@accta.cv",
        "password": "secret123",
        "role": "socio"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@accta.cv"
    assert data["role"] == "socio"

@pytest.mark.asyncio
async def test_create_user_duplicate_email():
    client.post("/api/users/", json={
        "name": "John",
        "email": "john@accta.cv",
        "password": "secret123",
        "role": "socio"
    })
    response = client.post("/api/users/", json={
        "name": "another John",
        "email": "john@accta.cv",
        "password": "secret123",
        "role": "socio"
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_create_user_invalid_email():
    response = client.post("/api/users/", json={
        "name": "John",
        "email": "invalid-email",
        "password": "secret123",
        "role": "socio"
    })
    assert response.status_code == 422  # Validation error
```

### 4. Testing PUT/PATCH Endpoints

```python
@pytest.mark.asyncio
async def test_update_user(sample_user, admin_token):
    user_id = sample_user["id"]
    response = client.put(
        f"/api/users/{user_id}",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

@pytest.mark.asyncio
async def test_update_nonexistent_user(admin_token):
    response = client.put(
        "/api/users/nonexistent-id",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
```

### 5. Testing DELETE Endpoints

```python
@pytest.mark.asyncio
async def test_delete_user(sample_user, admin_token):
    user_id = sample_user["id"]
    response = client.delete(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 404
```

### 6. Testing Authentication & Authorization

```python
@pytest.fixture
def admin_token():
    # Generate valid JWT token for admin
    from auth import create_token
    return create_token({"user_id": "admin-1", "role": "admin"})

@pytest.fixture
def member_token():
    from auth import create_token
    return create_token({"user_id": "member-1", "role": "socio"})

@pytest.mark.asyncio
async def test_admin_only_endpoint_requires_auth():
    response = client.post("/api/users/", json={
        "name": "John",
        "email": "john@accta.cv",
        "password": "secret123"
    })
    assert response.status_code == 401  # Unauthorized

@pytest.mark.asyncio
async def test_admin_only_endpoint_denies_member(member_token):
    response = client.post(
        "/api/users/",
        json={"name": "John", "email": "john@accta.cv", "password": "secret123"},
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert response.status_code == 403  # Forbidden

@pytest.mark.asyncio
async def test_admin_endpoint_allows_admin(admin_token):
    response = client.post(
        "/api/users/",
        json={"name": "John", "email": "john@accta.cv", "password": "secret123"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
```

### 7. Testing Business Logic

```python
@pytest.mark.asyncio
async def test_invoice_status_calculation():
    """Test invoice is marked 'paid' if amount equals sum of payments"""
    invoice_data = {
        "id": str(uuid.uuid4()),
        "member_id": "123",
        "amount": 100.0,
        "payments": [50.0, 50.0],
        "status": "pending"
    }
    await db.invoices.insert_one(invoice_data)
    
    # Trigger status update
    response = client.post(f"/api/invoices/{invoice_data['id']}/update-status")
    assert response.status_code == 200
    assert response.json()["status"] == "paid"

@pytest.mark.asyncio
async def test_photo_approval_workflow():
    """Test photo transitions from pending to approved"""
    photo_data = {
        "id": str(uuid.uuid4()),
        "member_id": "123",
        "url": "photo.jpg",
        "status": "pending_approval"
    }
    await db.gallery_photos.insert_one(photo_data)
    
    # Approve photo
    response = client.post(
        f"/api/gallery/photos/{photo_data['id']}/approve",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
```

---

## Frontend Testing Patterns (Jest + React Testing Library)

### 1. Basic Component Test

```jsx
import { render, screen } from '@testing-library/react';
import { UserProfile } from './UserProfile';

describe('UserProfile', () => {
  test('renders user name', () => {
    const mockUser = { id: '1', name: 'John Doe' };
    render(<UserProfile user={mockUser} />);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

### 2. Testing with User Interactions

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginForm } from './LoginForm';

test('submits form with correct data', async () => {
  const mockSubmit = jest.fn();
  render(<LoginForm onSubmit={mockSubmit} />);
  
  fireEvent.change(screen.getByPlaceholderText('Email'), {
    target: { value: 'john@accta.cv' }
  });
  fireEvent.change(screen.getByPlaceholderText('Password'), {
    target: { value: 'secret123' }
  });
  fireEvent.click(screen.getByRole('button', { name: /login/i }));
  
  expect(mockSubmit).toHaveBeenCalledWith({
    email: 'john@accta.cv',
    password: 'secret123'
  });
});
```

### 3. Testing Async Operations

```jsx
import { render, screen, waitFor } from '@testing-library/react';
import { UserList } from './UserList';
import * as api from '../utils/api';

jest.mock('../utils/api');

test('displays users after loading', async () => {
  api.getUsers.mockResolvedValue({
    data: [{ id: '1', name: 'John' }]
  });
  
  render(<UserList />);
  
  await waitFor(() => {
    expect(screen.getByText('John')).toBeInTheDocument();
  });
});
```

### 4. Testing Context Usage

```jsx
import { render, screen } from '@testing-library/react';
import { Dashboard } from './Dashboard';
import { AuthContext } from '../contexts/AuthContext';

test('displays user name from context', () => {
  const mockAuth = {
    user: { name: 'John Doe' }
  };
  
  render(
    <AuthContext.Provider value={mockAuth}>
      <Dashboard />
    </AuthContext.Provider>
  );
  
  expect(screen.getByText('Welcome, John Doe')).toBeInTheDocument();
});
```

### 5. Testing Error Handling

```jsx
import { render, screen, waitFor } from '@testing-library/react';
import { UserList } from './UserList';
import * as api from '../utils/api';

jest.mock('../utils/api');

test('displays error message on API failure', async () => {
  api.getUsers.mockRejectedValue(new Error('API Error'));
  
  render(<UserList />);
  
  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

---

## Common Test Fixtures & Mocks

### Mock API Calls

```python
# backend/tests/conftest.py
import pytest
from unittest.mock import patch, AsyncMock

@pytest.fixture
def mock_send_email():
    with patch('helpers.send_email', new_callable=AsyncMock) as mock:
        yield mock
```

### Mock Database

```python
@pytest.fixture
async def clean_db():
    # Isolate each test by clearing collections via the Mongo-compatible DAO
    # (PostgreSQL/Supabase, configured through DATABASE_URL)
    from database import db
    yield db
    # Cleanup
    await db.users.delete_many({})
    await db.gallery_photos.delete_many({})
    await db.invoices.delete_many({})
```

### Mock Authentication

```python
@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
```

---

## Test Coverage Goals

| Module | Target Coverage |
|--------|-----------------|
| Auth routes | 95% |
| User management | 90% |
| Financial tracking | 85% |
| Gallery workflow | 80% |
| Notifications | 75% |

**Generate coverage report:**
```bash
cd backend
pytest tests/ --cov=routes --cov=models --cov=auth --cov-report=html
open htmlcov/index.html
```

---

## Performance Testing

### Load Testing with Apache Bench

```bash
# Test 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:8001/api/users/

# Write results to file
ab -n 1000 -c 10 -g results.tsv http://localhost:8001/api/users/
```

### Stress Testing with Locust

```python
# locustfile.py
from locust import HttpUser, between, task

class ACCTAUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def list_users(self):
        self.client.get("/api/users/")
    
    @task
    def get_dashboard(self):
        self.client.get("/api/dashboard/")
```

```bash
locust -f locustfile.py --host=http://localhost:8001
```

---

## Debugging Failed Tests

```bash
# Show print statements
pytest tests/test_users.py -v -s

# Drop into pdb on failure
pytest tests/test_users.py --pdb

# Capture all output
pytest tests/test_users.py -vv --tb=long

# Run last failed test
pytest --lf

# Run failed tests first
pytest --ff
```

---

## CI/CD Test Integration

**GitHub Actions** (`.github/workflows/ci.yml`):
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest tests/ --cov
      - run: cd frontend && yarn install && yarn test
```

---

## Recommended Test Prompts

- "Create a test for the user authentication flow"
- "Add tests for the invoice export functionality"
- "Write tests for the gallery photo approval workflow"
- "Create integration tests for the notification system"
- "Add performance tests for the dashboard loading"

---

**Last Updated**: April 2, 2026  
**Version**: 1.0
