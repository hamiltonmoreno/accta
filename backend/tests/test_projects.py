"""
Test suite for Projects module - ACCTA Portal
Tests: Project CRUD, Tasks, Comments, Expenses, Milestones
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"email": "admin@controlador.cv", "password": "admin123"}
SOCIO_CREDS = {"email": "socio1@controlador.cv", "password": "socio123"}


class TestProjectsAuth:
    """Authentication setup for project tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def socio_token(self):
        """Get socio authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SOCIO_CREDS)
        assert response.status_code == 200, f"Socio login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def socio_headers(self, socio_token):
        return {"Authorization": f"Bearer {socio_token}", "Content-Type": "application/json"}


class TestProjectCRUD(TestProjectsAuth):
    """Test Project CRUD operations"""
    
    def test_admin_creates_project_with_aprovado_status(self, admin_headers):
        """Admin creates project - should have status 'aprovado'"""
        payload = {
            "title": "TEST_Admin Project",
            "description": "Project created by admin for testing",
            "visibility": "publico",
            "category": "Testing",
            "budget": 50000.0,
            "start_date": "2026-01-15",
            "end_date": "2026-06-30"
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create project failed: {response.text}"
        
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["status"] == "aprovado", "Admin-created project should have status 'aprovado'"
        assert data["visibility"] == "publico"
        assert data["budget"] == 50000.0
        assert "id" in data
        
        # Store for cleanup
        self.__class__.admin_project_id = data["id"]
        print(f"Admin created project with ID: {data['id']}, status: {data['status']}")
    
    def test_socio_creates_project_with_proposta_status(self, socio_headers):
        """Socio creates project - should have status 'proposta'"""
        payload = {
            "title": "TEST_Socio Project Proposal",
            "description": "Project proposed by socio for testing",
            "visibility": "publico",
            "category": "Social",
            "budget": 25000.0
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=socio_headers)
        assert response.status_code == 200, f"Create project failed: {response.text}"
        
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["status"] == "proposta", "Socio-created project should have status 'proposta'"
        assert "id" in data
        
        self.__class__.socio_project_id = data["id"]
        print(f"Socio created project with ID: {data['id']}, status: {data['status']}")
    
    def test_list_projects_with_pagination(self, admin_headers):
        """GET /api/projects - lists projects with pagination {items, total}"""
        response = requests.get(f"{BASE_URL}/api/projects", headers=admin_headers)
        assert response.status_code == 200, f"List projects failed: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' field"
        assert "total" in data, "Response should have 'total' field"
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert data["total"] >= 0
        
        print(f"Listed {len(data['items'])} projects, total: {data['total']}")
    
    def test_list_projects_with_status_filter(self, admin_headers):
        """GET /api/projects?status=proposta - filter by status"""
        response = requests.get(f"{BASE_URL}/api/projects?status=proposta", headers=admin_headers)
        assert response.status_code == 200, f"Filter projects failed: {response.text}"
        
        data = response.json()
        for project in data["items"]:
            assert project["status"] == "proposta", f"Project {project['id']} has wrong status"
        
        print(f"Found {len(data['items'])} projects with status 'proposta'")
    
    def test_get_project_detail_with_enriched_data(self, admin_headers):
        """GET /api/projects/{id} - returns full project with tasks, comments, expenses, milestones"""
        project_id = getattr(self.__class__, 'admin_project_id', None)
        if not project_id:
            pytest.skip("No project ID available")
        
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        assert response.status_code == 200, f"Get project failed: {response.text}"
        
        data = response.json()
        assert data["id"] == project_id
        assert "tasks" in data, "Project should have 'tasks' field"
        assert "comments" in data, "Project should have 'comments' field"
        assert "expenses" in data, "Project should have 'expenses' field"
        assert "milestones" in data, "Project should have 'milestones' field"
        assert "spent" in data, "Project should have 'spent' field"
        
        print(f"Project detail: tasks={len(data['tasks'])}, comments={len(data['comments'])}, expenses={len(data['expenses'])}, milestones={len(data['milestones'])}")
    
    def test_update_project_status_and_progress(self, admin_headers):
        """PATCH /api/projects/{id} - update project status, progress"""
        project_id = getattr(self.__class__, 'admin_project_id', None)
        if not project_id:
            pytest.skip("No project ID available")
        
        payload = {"status": "em_curso", "progress": 25}
        response = requests.patch(f"{BASE_URL}/api/projects/{project_id}", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Update project failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "em_curso"
        assert data["progress"] == 25
        
        print("Updated project status to 'em_curso', progress to 25%")
    
    def test_admin_approves_proposal(self, admin_headers):
        """PATCH /api/projects/{id}/approve - admin can approve proposals"""
        project_id = getattr(self.__class__, 'socio_project_id', None)
        if not project_id:
            pytest.skip("No socio project ID available")
        
        response = requests.patch(f"{BASE_URL}/api/projects/{project_id}/approve", headers=admin_headers)
        assert response.status_code == 200, f"Approve project failed: {response.text}"
        
        # Verify status changed
        get_response = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "aprovado"
        
        print(f"Admin approved project {project_id}")
    
    def test_socio_cannot_approve_project(self, socio_headers, admin_headers):
        """Socio cannot approve projects - should get 403"""
        # Create a new proposal first
        payload = {"title": "TEST_Another Proposal", "visibility": "publico"}
        create_resp = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=socio_headers)
        assert create_resp.status_code == 200
        project_id = create_resp.json()["id"]
        
        # Try to approve as socio
        response = requests.patch(f"{BASE_URL}/api/projects/{project_id}/approve", headers=socio_headers)
        assert response.status_code == 403, "Socio should not be able to approve projects"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        print("Verified socio cannot approve projects (403)")


class TestProjectTasks(TestProjectsAuth):
    """Test Project Tasks CRUD"""
    
    @pytest.fixture(scope="class")
    def test_project(self, admin_headers):
        """Create a test project for task tests"""
        payload = {"title": "TEST_Task Project", "visibility": "publico", "budget": 10000}
        response = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=admin_headers)
        assert response.status_code == 200
        project = response.json()
        yield project
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{project['id']}", headers=admin_headers)
    
    def test_create_task_with_assignee_and_priority(self, admin_headers, test_project):
        """POST /api/projects/{id}/tasks - create task with assignee and priority"""
        project_id = test_project["id"]
        
        # Get members for assignee
        members_resp = requests.get(f"{BASE_URL}/api/projects/meta/members", headers=admin_headers)
        assert members_resp.status_code == 200
        members = members_resp.json()
        assignee_id = members[0]["id"] if members else None
        
        payload = {
            "title": "TEST_Task 1",
            "description": "Test task description",
            "assignee_id": assignee_id,
            "priority": "alta",
            "due_date": "2026-02-15"
        }
        response = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Create task failed: {response.text}"
        
        data = response.json()
        assert data["title"] == "TEST_Task 1"
        assert data["priority"] == "alta"
        assert data["status"] == "pendente"
        assert "id" in data
        
        self.__class__.task_id = data["id"]
        print(f"Created task with ID: {data['id']}, priority: {data['priority']}")
    
    def test_update_task_status_sets_completed_at(self, admin_headers, test_project):
        """PATCH /api/projects/{id}/tasks/{tid} - update task status (concluido sets completed_at)"""
        project_id = test_project["id"]
        task_id = getattr(self.__class__, 'task_id', None)
        if not task_id:
            pytest.skip("No task ID available")
        
        # Update to concluido
        payload = {"status": "concluido"}
        response = requests.patch(f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Update task failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "concluido"
        assert data.get("completed_at") is not None, "completed_at should be set when status is concluido"
        
        print(f"Task marked as concluido, completed_at: {data['completed_at']}")
    
    def test_delete_task(self, admin_headers, test_project):
        """DELETE /api/projects/{id}/tasks/{tid}"""
        project_id = test_project["id"]
        
        # Create a task to delete
        payload = {"title": "TEST_Task to Delete", "priority": "baixa"}
        create_resp = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", json=payload, headers=admin_headers)
        assert create_resp.status_code == 200
        task_id = create_resp.json()["id"]
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}", headers=admin_headers)
        assert response.status_code == 200
        
        print(f"Deleted task {task_id}")


class TestProjectComments(TestProjectsAuth):
    """Test Project Comments"""
    
    @pytest.fixture(scope="class")
    def test_project(self, admin_headers):
        """Create a test project for comment tests"""
        payload = {"title": "TEST_Comment Project", "visibility": "publico"}
        response = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=admin_headers)
        assert response.status_code == 200
        project = response.json()
        yield project
        requests.delete(f"{BASE_URL}/api/projects/{project['id']}", headers=admin_headers)
    
    def test_add_comment(self, admin_headers, test_project):
        """POST /api/projects/{id}/comments - add comment"""
        project_id = test_project["id"]
        
        payload = {"content": "This is a test comment for the project"}
        response = requests.post(f"{BASE_URL}/api/projects/{project_id}/comments", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Add comment failed: {response.text}"
        
        data = response.json()
        assert data["content"] == payload["content"]
        assert "user_name" in data
        assert "id" in data
        
        self.__class__.comment_id = data["id"]
        print(f"Added comment with ID: {data['id']}")
    
    def test_comment_appears_in_project_detail(self, admin_headers, test_project):
        """Verify comment appears in project detail"""
        project_id = test_project["id"]
        
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["comments"]) > 0, "Project should have comments"
        
        print(f"Project has {len(data['comments'])} comment(s)")
    
    def test_delete_comment(self, admin_headers, test_project):
        """DELETE /api/projects/{id}/comments/{cid}"""
        project_id = test_project["id"]
        comment_id = getattr(self.__class__, 'comment_id', None)
        if not comment_id:
            pytest.skip("No comment ID available")
        
        response = requests.delete(f"{BASE_URL}/api/projects/{project_id}/comments/{comment_id}", headers=admin_headers)
        assert response.status_code == 200
        
        print(f"Deleted comment {comment_id}")


class TestProjectExpenses(TestProjectsAuth):
    """Test Project Expenses and Budget Tracking"""
    
    @pytest.fixture(scope="class")
    def test_project(self, admin_headers):
        """Create a test project for expense tests"""
        payload = {"title": "TEST_Expense Project", "visibility": "publico", "budget": 100000}
        response = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=admin_headers)
        assert response.status_code == 200
        project = response.json()
        yield project
        requests.delete(f"{BASE_URL}/api/projects/{project['id']}", headers=admin_headers)
    
    def test_add_expense_updates_project_spent(self, admin_headers, test_project):
        """POST /api/projects/{id}/expenses - add expense, auto-updates project spent"""
        project_id = test_project["id"]
        
        payload = {
            "description": "TEST_Expense 1 - Catering",
            "amount": 15000,
            "date": "2026-01-20"
        }
        response = requests.post(f"{BASE_URL}/api/projects/{project_id}/expenses", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Add expense failed: {response.text}"
        
        data = response.json()
        assert data["description"] == payload["description"]
        assert data["amount"] == 15000
        
        self.__class__.expense_id = data["id"]
        
        # Verify project spent was updated
        project_resp = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        assert project_resp.status_code == 200
        project_data = project_resp.json()
        assert project_data["spent"] == 15000, f"Project spent should be 15000, got {project_data['spent']}"
        
        print(f"Added expense {data['id']}, project spent updated to {project_data['spent']}")
    
    def test_add_second_expense_accumulates_spent(self, admin_headers, test_project):
        """Adding another expense should accumulate spent"""
        project_id = test_project["id"]
        
        payload = {
            "description": "TEST_Expense 2 - Decorations",
            "amount": 5000,
            "date": "2026-01-21"
        }
        response = requests.post(f"{BASE_URL}/api/projects/{project_id}/expenses", json=payload, headers=admin_headers)
        assert response.status_code == 200
        
        # Verify accumulated spent
        project_resp = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        project_data = project_resp.json()
        assert project_data["spent"] == 20000, f"Project spent should be 20000, got {project_data['spent']}"
        
        print(f"Total spent after second expense: {project_data['spent']}")
    
    def test_delete_expense_updates_spent(self, admin_headers, test_project):
        """DELETE /api/projects/{id}/expenses/{eid} - should update spent"""
        project_id = test_project["id"]
        expense_id = getattr(self.__class__, 'expense_id', None)
        if not expense_id:
            pytest.skip("No expense ID available")
        
        response = requests.delete(f"{BASE_URL}/api/projects/{project_id}/expenses/{expense_id}", headers=admin_headers)
        assert response.status_code == 200
        
        # Verify spent was updated
        project_resp = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        project_data = project_resp.json()
        assert project_data["spent"] == 5000, f"Project spent should be 5000 after deletion, got {project_data['spent']}"
        
        print(f"Deleted expense, spent updated to {project_data['spent']}")


class TestProjectMilestones(TestProjectsAuth):
    """Test Project Milestones"""
    
    @pytest.fixture(scope="class")
    def test_project(self, admin_headers):
        """Create a test project for milestone tests"""
        payload = {"title": "TEST_Milestone Project", "visibility": "publico"}
        response = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=admin_headers)
        assert response.status_code == 200
        project = response.json()
        yield project
        requests.delete(f"{BASE_URL}/api/projects/{project['id']}", headers=admin_headers)
    
    def test_add_milestone(self, admin_headers, test_project):
        """POST /api/projects/{id}/milestones - add milestone"""
        project_id = test_project["id"]
        
        payload = {
            "title": "TEST_Milestone 1 - Planning Complete",
            "date": "2026-02-01"
        }
        response = requests.post(f"{BASE_URL}/api/projects/{project_id}/milestones", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Add milestone failed: {response.text}"
        
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["date"] == payload["date"]
        assert data["completed"] == False
        
        self.__class__.milestone_id = data["id"]
        print(f"Added milestone with ID: {data['id']}")
    
    def test_toggle_milestone_completed(self, admin_headers, test_project):
        """PATCH /api/projects/{id}/milestones/{mid} - toggle completed"""
        project_id = test_project["id"]
        milestone_id = getattr(self.__class__, 'milestone_id', None)
        if not milestone_id:
            pytest.skip("No milestone ID available")
        
        # Toggle to completed
        payload = {"completed": True}
        response = requests.patch(f"{BASE_URL}/api/projects/{project_id}/milestones/{milestone_id}", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Update milestone failed: {response.text}"
        
        data = response.json()
        assert data["completed"] == True
        
        # Toggle back
        payload = {"completed": False}
        response = requests.patch(f"{BASE_URL}/api/projects/{project_id}/milestones/{milestone_id}", json=payload, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["completed"] == False
        
        print("Toggled milestone completed status")
    
    def test_delete_milestone(self, admin_headers, test_project):
        """DELETE /api/projects/{id}/milestones/{mid}"""
        project_id = test_project["id"]
        milestone_id = getattr(self.__class__, 'milestone_id', None)
        if not milestone_id:
            pytest.skip("No milestone ID available")
        
        response = requests.delete(f"{BASE_URL}/api/projects/{project_id}/milestones/{milestone_id}", headers=admin_headers)
        assert response.status_code == 200
        
        print(f"Deleted milestone {milestone_id}")


class TestPrivateProjects(TestProjectsAuth):
    """Test Private Project Visibility"""
    
    def test_private_project_not_visible_to_non_admin_non_creator(self, admin_headers, socio_headers):
        """Private projects not visible to non-admin/non-creator"""
        # Admin creates private project
        payload = {
            "title": "TEST_Private Board Project",
            "description": "Confidential board discussion",
            "visibility": "privado"
        }
        create_resp = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=admin_headers)
        assert create_resp.status_code == 200
        project_id = create_resp.json()["id"]
        
        # Socio tries to access
        get_resp = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=socio_headers)
        assert get_resp.status_code == 403, "Socio should not be able to access private project"
        
        # Socio lists projects - private project should not appear
        list_resp = requests.get(f"{BASE_URL}/api/projects", headers=socio_headers)
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        project_ids = [p["id"] for p in items]
        assert project_id not in project_ids, "Private project should not appear in socio's list"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        print("Verified private project visibility restrictions")


class TestProjectDelete(TestProjectsAuth):
    """Test Project Deletion with Cascade"""
    
    def test_admin_delete_project_cascades_related_data(self, admin_headers):
        """DELETE /api/projects/{id} - admin only, cascade deletes related data"""
        # Create project with tasks, comments, expenses, milestones
        project_payload = {"title": "TEST_Delete Cascade Project", "visibility": "publico", "budget": 50000}
        project_resp = requests.post(f"{BASE_URL}/api/projects", json=project_payload, headers=admin_headers)
        assert project_resp.status_code == 200
        project_id = project_resp.json()["id"]
        
        # Add task
        task_resp = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", 
                                  json={"title": "Task to cascade delete"}, headers=admin_headers)
        assert task_resp.status_code == 200
        
        # Add comment
        comment_resp = requests.post(f"{BASE_URL}/api/projects/{project_id}/comments",
                                     json={"content": "Comment to cascade delete"}, headers=admin_headers)
        assert comment_resp.status_code == 200
        
        # Add expense
        expense_resp = requests.post(f"{BASE_URL}/api/projects/{project_id}/expenses",
                                     json={"description": "Expense to cascade", "amount": 1000, "date": "2026-01-20"}, headers=admin_headers)
        assert expense_resp.status_code == 200
        
        # Add milestone
        milestone_resp = requests.post(f"{BASE_URL}/api/projects/{project_id}/milestones",
                                       json={"title": "Milestone to cascade", "date": "2026-02-01"}, headers=admin_headers)
        assert milestone_resp.status_code == 200
        
        # Delete project
        delete_resp = requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        assert delete_resp.status_code == 200
        
        # Verify project is gone
        get_resp = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        assert get_resp.status_code == 404
        
        print(f"Deleted project {project_id} with cascade delete of related data")
    
    def test_socio_cannot_delete_project(self, admin_headers, socio_headers):
        """Socio cannot delete projects - should get 403"""
        # Create project as admin
        payload = {"title": "TEST_Socio Cannot Delete", "visibility": "publico"}
        create_resp = requests.post(f"{BASE_URL}/api/projects", json=payload, headers=admin_headers)
        assert create_resp.status_code == 200
        project_id = create_resp.json()["id"]
        
        # Socio tries to delete
        delete_resp = requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=socio_headers)
        assert delete_resp.status_code == 403, "Socio should not be able to delete projects"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
        print("Verified socio cannot delete projects (403)")


class TestMetaEndpoints(TestProjectsAuth):
    """Test Meta Endpoints"""
    
    def test_get_members_list(self, admin_headers):
        """GET /api/projects/meta/members - returns list of active members"""
        response = requests.get(f"{BASE_URL}/api/projects/meta/members", headers=admin_headers)
        assert response.status_code == 200, f"Get members failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "name" in data[0]
        
        print(f"Got {len(data)} active members")


# Cleanup test data
class TestCleanup(TestProjectsAuth):
    """Cleanup any remaining test data"""
    
    def test_cleanup_test_projects(self, admin_headers):
        """Remove any TEST_ prefixed projects"""
        response = requests.get(f"{BASE_URL}/api/projects?limit=100", headers=admin_headers)
        if response.status_code == 200:
            items = response.json().get("items", [])
            for project in items:
                if project["title"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/projects/{project['id']}", headers=admin_headers)
                    print(f"Cleaned up test project: {project['title']}")
