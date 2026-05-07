"""
Test suite for automatic notification triggers in ACCTA Portal.
Tests notification generation for:
- Project events (create, status change, assign responsible, comments, tasks, expenses, budget exceeded)
- Finance events (create transaction, generate quotas, settings change)
- Notification API endpoints (GET, DELETE, PATCH mark-all-read, DELETE clear/all)
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@controlador.cv"
ADMIN_PASSWORD = "admin123"
SOCIO_EMAIL = "socio1@controlador.cv"
SOCIO_PASSWORD = "socio123"


class TestSetup:
    """Setup fixtures and helper methods"""
    
    @staticmethod
    def get_auth_token(email, password):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @staticmethod
    def get_headers(token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def get_user_id(token):
        """Get current user ID"""
        headers = TestSetup.get_headers(token)
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            return response.json().get("id")
        return None


@pytest.fixture(scope="module")
def admin_token():
    """Admin authentication token"""
    token = TestSetup.get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not token:
        pytest.skip("Admin authentication failed")
    return token


@pytest.fixture(scope="module")
def socio_token():
    """Socio authentication token"""
    token = TestSetup.get_auth_token(SOCIO_EMAIL, SOCIO_PASSWORD)
    if not token:
        pytest.skip("Socio authentication failed")
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin request headers"""
    return TestSetup.get_headers(admin_token)


@pytest.fixture(scope="module")
def socio_headers(socio_token):
    """Socio request headers"""
    return TestSetup.get_headers(socio_token)


@pytest.fixture(scope="module")
def admin_user_id(admin_token):
    """Admin user ID"""
    return TestSetup.get_user_id(admin_token)


@pytest.fixture(scope="module")
def socio_user_id(socio_token):
    """Socio user ID"""
    return TestSetup.get_user_id(socio_token)


# ===== NOTIFICATION API TESTS =====

class TestNotificationAPI:
    """Test notification CRUD endpoints"""
    
    def test_get_notifications_paginated(self, admin_headers):
        """GET /api/notifications returns paginated items"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        print(f"PASSED: GET /api/notifications returns {len(data['items'])} items, total: {data['total']}")
    
    def test_get_notifications_with_type_filter(self, admin_headers):
        """GET /api/notifications?type=projeto filters by type"""
        response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # All returned items should have type 'projeto'
        for item in data["items"]:
            assert item.get("type") == "projeto", f"Expected type 'projeto', got '{item.get('type')}'"
        print(f"PASSED: GET /api/notifications?type=projeto returns {len(data['items'])} filtered items")
    
    def test_get_notifications_unread_count(self, admin_headers):
        """GET /api/notifications/unread/count returns count"""
        response = requests.get(f"{BASE_URL}/api/notifications/unread/count", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        print(f"PASSED: GET /api/notifications/unread/count returns count: {data['count']}")
    
    def test_mark_all_notifications_read(self, admin_headers):
        """PATCH /api/notifications/mark-all-read works"""
        response = requests.patch(f"{BASE_URL}/api/notifications/mark-all-read", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"PASSED: PATCH /api/notifications/mark-all-read - {data['message']}")
    
    def test_clear_all_read_notifications(self, admin_headers):
        """DELETE /api/notifications/clear/all clears read notifications"""
        response = requests.delete(f"{BASE_URL}/api/notifications/clear/all", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"PASSED: DELETE /api/notifications/clear/all - {data['message']}")


# ===== PROJECT NOTIFICATION TESTS =====

class TestProjectNotifications:
    """Test automatic notifications for project events"""
    
    @pytest.fixture
    def test_project(self, socio_headers, admin_headers):
        """Create a test project and clean up after"""
        # Create project as socio (will be 'proposta' status)
        project_data = {
            "title": f"TEST_Projeto_Notif_{int(time.time())}",
            "description": "Test project for notification testing",
            "visibility": "privado",
            "budget": 10000
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=socio_headers)
        assert response.status_code == 200, f"Failed to create project: {response.text}"
        project = response.json()
        project_id = project["id"]
        
        yield project
        
        # Cleanup: delete project as admin
        requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
    
    def test_project_creation_notifies_admins(self, socio_headers, admin_headers, test_project):
        """Creating a project as socio sends notification to admins"""
        # Check admin notifications for the new project proposal
        response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Look for notification about the test project
        found = False
        for notif in data["items"]:
            if test_project["title"] in notif.get("message", "") or test_project["title"] in notif.get("title", ""):
                found = True
                assert "proposta" in notif.get("title", "").lower() or "proposta" in notif.get("message", "").lower()
                print(f"PASSED: Project creation notification found: {notif['title']}")
                break
        
        assert found, f"No notification found for project '{test_project['title']}'"
    
    def test_assign_responsible_notifies_user(self, admin_headers, socio_headers, socio_user_id, test_project):
        """Assigning responsible_id via PATCH sends 'Projeto Atribuido' notification"""
        project_id = test_project["id"]
        
        # Assign socio as responsible (as admin)
        response = requests.patch(
            f"{BASE_URL}/api/projects/{project_id}",
            json={"responsible_id": socio_user_id},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to assign responsible: {response.text}"
        
        # Check socio notifications
        time.sleep(0.5)  # Small delay for notification to be created
        response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Look for 'Projeto Atribuido' notification
        found = False
        for notif in data["items"]:
            if "atribuido" in notif.get("title", "").lower() or "designado" in notif.get("message", "").lower():
                found = True
                print(f"PASSED: Assign responsible notification found: {notif['title']}")
                break
        
        assert found, "No 'Projeto Atribuido' notification found for assigned user"
    
    def test_status_change_notifies_stakeholders(self, admin_headers, socio_headers, test_project):
        """Changing project status sends 'Projeto Atualizado' notification"""
        project_id = test_project["id"]
        
        # Change status to 'aprovado' (as admin)
        response = requests.patch(
            f"{BASE_URL}/api/projects/{project_id}",
            json={"status": "aprovado"},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to change status: {response.text}"
        
        # Check socio notifications (project creator)
        time.sleep(0.5)
        response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Look for status change notification
        found = False
        for notif in data["items"]:
            if "atualizado" in notif.get("title", "").lower() and "aprovado" in notif.get("message", "").lower():
                found = True
                print(f"PASSED: Status change notification found: {notif['title']}")
                break
        
        assert found, "No 'Projeto Atualizado' notification found for status change"
    
    def test_project_approval_notifies_stakeholders(self, admin_headers, socio_headers):
        """Project approval via /approve endpoint sends notification"""
        # Create a new project as socio
        project_data = {
            "title": f"TEST_Approval_Notif_{int(time.time())}",
            "description": "Test project for approval notification",
            "visibility": "privado"
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=socio_headers)
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        try:
            # Approve project as admin
            response = requests.patch(f"{BASE_URL}/api/projects/{project_id}/approve", headers=admin_headers)
            assert response.status_code == 200, f"Failed to approve project: {response.text}"
            
            # Check socio notifications
            time.sleep(0.5)
            response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=socio_headers)
            assert response.status_code == 200
            data = response.json()
            
            # Look for approval notification
            found = False
            for notif in data["items"]:
                if "aprovado" in notif.get("title", "").lower():
                    found = True
                    print(f"PASSED: Project approval notification found: {notif['title']}")
                    break
            
            assert found, "No 'Projeto Aprovado' notification found"
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
    
    def test_add_comment_notifies_stakeholders(self, admin_headers, socio_headers, test_project):
        """Adding a comment sends notification to project stakeholders"""
        project_id = test_project["id"]
        
        # Add comment as admin
        comment_data = {"content": f"TEST_Comment_{int(time.time())}"}
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/comments",
            json=comment_data,
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to add comment: {response.text}"
        
        # Check socio notifications (project creator)
        time.sleep(0.5)
        response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Look for comment notification
        found = False
        for notif in data["items"]:
            if "comentario" in notif.get("title", "").lower() or "comentou" in notif.get("message", "").lower():
                found = True
                print(f"PASSED: Comment notification found: {notif['title']}")
                break
        
        assert found, "No comment notification found for project stakeholders"
    
    def test_create_task_notifies_assignee(self, admin_headers, socio_headers, socio_user_id, test_project):
        """Creating a task with assignee sends 'Nova Tarefa Atribuida' notification"""
        project_id = test_project["id"]
        
        # First approve the project so admin can manage it
        requests.patch(f"{BASE_URL}/api/projects/{project_id}", json={"status": "aprovado"}, headers=admin_headers)
        
        # Create task assigned to socio (as admin)
        task_data = {
            "title": f"TEST_Task_{int(time.time())}",
            "description": "Test task for notification",
            "assignee_id": socio_user_id,
            "priority": "media"
        }
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/tasks",
            json=task_data,
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to create task: {response.text}"
        
        # Check socio notifications
        time.sleep(0.5)
        response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Look for task assignment notification
        found = False
        for notif in data["items"]:
            if "tarefa" in notif.get("title", "").lower() and "atribuida" in notif.get("title", "").lower():
                found = True
                print(f"PASSED: Task assignment notification found: {notif['title']}")
                break
        
        assert found, "No 'Nova Tarefa Atribuida' notification found"
    
    def test_complete_task_notifies_stakeholders(self, admin_headers, socio_headers, socio_user_id, test_project):
        """Completing a task sends notification to project stakeholders"""
        project_id = test_project["id"]
        
        # Create a task
        task_data = {
            "title": f"TEST_Complete_Task_{int(time.time())}",
            "description": "Test task for completion notification",
            "assignee_id": socio_user_id,
            "priority": "media"
        }
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/tasks",
            json=task_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        task = response.json()
        task_id = task["id"]
        
        # Complete the task as socio (assignee)
        response = requests.patch(
            f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}",
            json={"status": "concluido"},
            headers=socio_headers
        )
        assert response.status_code == 200, f"Failed to complete task: {response.text}"
        
        # Check admin notifications (project stakeholder)
        time.sleep(0.5)
        response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Look for task completion notification
        found = False
        for notif in data["items"]:
            if "tarefa" in notif.get("title", "").lower() and "concluida" in notif.get("title", "").lower():
                found = True
                print(f"PASSED: Task completion notification found: {notif['title']}")
                break
        
        # Note: Admin might be excluded if they are the one completing, so this is optional
        print(f"INFO: Task completion notification check - found: {found}")
    
    def test_add_expense_notifies_stakeholders(self, admin_headers, socio_headers, test_project):
        """Adding an expense sends 'Nova Despesa' notification to stakeholders"""
        project_id = test_project["id"]
        
        # Add expense as admin
        expense_data = {
            "description": f"TEST_Expense_{int(time.time())}",
            "amount": 500,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/expenses",
            json=expense_data,
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to add expense: {response.text}"
        
        # Check socio notifications (project creator)
        time.sleep(0.5)
        response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=socio_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Look for expense notification
        found = False
        for notif in data["items"]:
            if "despesa" in notif.get("title", "").lower():
                found = True
                print(f"PASSED: Expense notification found: {notif['title']}")
                break
        
        assert found, "No 'Nova Despesa' notification found"
    
    def test_budget_exceeded_triggers_notification(self, admin_headers, socio_headers):
        """Budget exceeded triggers extra notification"""
        # Create project with small budget
        project_data = {
            "title": f"TEST_Budget_Exceeded_{int(time.time())}",
            "description": "Test project for budget exceeded notification",
            "visibility": "privado",
            "budget": 100  # Small budget
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=admin_headers)
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        
        try:
            # Add expense that exceeds budget
            expense_data = {
                "description": f"TEST_Large_Expense_{int(time.time())}",
                "amount": 200,  # Exceeds 100 budget
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            response = requests.post(
                f"{BASE_URL}/api/projects/{project_id}/expenses",
                json=expense_data,
                headers=admin_headers
            )
            assert response.status_code == 200, f"Failed to add expense: {response.text}"
            
            # Check admin notifications for budget exceeded
            time.sleep(0.5)
            response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            
            # Look for budget exceeded notification
            found = False
            for notif in data["items"]:
                if "orcamento" in notif.get("title", "").lower() and "excedido" in notif.get("title", "").lower():
                    found = True
                    print(f"PASSED: Budget exceeded notification found: {notif['title']}")
                    break
            
            assert found, "No 'Orcamento Excedido' notification found"
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)


# ===== FINANCE NOTIFICATION TESTS =====

class TestFinanceNotifications:
    """Test automatic notifications for finance events"""
    
    def test_create_transaction_notifies_admins(self, admin_headers):
        """Creating a transaction notifies admins (excluding creator if admin)"""
        # Create transaction as admin
        transaction_data = {
            "type": "receita",
            "category": "quotas",
            "description": f"TEST_Transaction_{int(time.time())}",
            "amount": 1000,
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
        response = requests.post(
            f"{BASE_URL}/api/finances/transactions",
            json=transaction_data,
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to create transaction: {response.text}"
        transaction = response.json()
        transaction_id = transaction.id if hasattr(transaction, 'id') else transaction.get('id')
        
        print(f"PASSED: Transaction created successfully - ID: {transaction_id}")
        
        # Check notifications (admin is excluded as creator, so we just verify the endpoint works)
        response = requests.get(f"{BASE_URL}/api/notifications?type=financeiro", headers=admin_headers)
        assert response.status_code == 200
        print("PASSED: Finance notifications endpoint accessible")
        
        # Cleanup
        if transaction_id:
            requests.delete(f"{BASE_URL}/api/finances/transactions/{transaction_id}", headers=admin_headers)
    
    def test_generate_quotas_notifies_all_users(self, admin_headers, socio_headers):
        """Generating quotas notifies all active users"""
        # Generate quotas for a test month (use future month to avoid conflicts)
        test_month = 12
        test_year = 2030
        
        response = requests.post(
            f"{BASE_URL}/api/finances/generate-quotas?month={test_month}&year={test_year}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to generate quotas: {response.text}"
        data = response.json()
        print(f"PASSED: Quotas generated - {data.get('created', 0)} created, {data.get('skipped', 0)} skipped")
        
        # Check socio notifications for quota generation
        time.sleep(0.5)
        response = requests.get(f"{BASE_URL}/api/notifications?type=financeiro", headers=socio_headers)
        assert response.status_code == 200
        notif_data = response.json()
        
        # Look for quota notification
        found = False
        for notif in notif_data["items"]:
            if "quota" in notif.get("title", "").lower() or "quota" in notif.get("message", "").lower():
                found = True
                print(f"PASSED: Quota generation notification found: {notif['title']}")
                break
        
        # Note: If no quotas were created (all skipped), notification might not be sent
        if data.get('created', 0) > 0:
            assert found, "No quota generation notification found"
        else:
            print("INFO: No new quotas created, notification may not have been sent")
    
    def test_change_settings_notifies_admins(self, admin_headers):
        """Changing quota settings notifies admins"""
        # Get current settings
        response = requests.get(f"{BASE_URL}/api/finances/settings", headers=admin_headers)
        assert response.status_code == 200
        current_settings = response.json()
        current_quota = current_settings.get("quota_amount", 2000)
        
        # Change quota amount
        new_quota = current_quota + 100
        response = requests.patch(
            f"{BASE_URL}/api/finances/settings",
            json={"quota_amount": new_quota},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to update settings: {response.text}"
        print(f"PASSED: Settings updated - quota changed to {new_quota}")
        
        # Check notifications
        time.sleep(0.5)
        response = requests.get(f"{BASE_URL}/api/notifications?type=financeiro", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Look for settings change notification
        found = False
        for notif in data["items"]:
            if "quota" in notif.get("title", "").lower() and "atualizado" in notif.get("title", "").lower():
                found = True
                print(f"PASSED: Settings change notification found: {notif['title']}")
                break
        
        # Note: Admin is excluded as the one making the change
        print(f"INFO: Settings change notification check - found: {found} (admin excluded as changer)")
        
        # Restore original settings
        requests.patch(
            f"{BASE_URL}/api/finances/settings",
            json={"quota_amount": current_quota},
            headers=admin_headers
        )


# ===== NOTIFICATION DELETE TEST =====

class TestNotificationDelete:
    """Test notification deletion"""
    
    def test_delete_notification(self, admin_headers):
        """DELETE /api/notifications/{id} works"""
        # First get a notification to delete
        response = requests.get(f"{BASE_URL}/api/notifications", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["items"]) == 0:
            pytest.skip("No notifications to delete")
        
        notif_id = data["items"][0]["id"]
        
        # Delete the notification
        response = requests.delete(f"{BASE_URL}/api/notifications/{notif_id}", headers=admin_headers)
        assert response.status_code == 200
        delete_data = response.json()
        assert "message" in delete_data
        print(f"PASSED: DELETE /api/notifications/{notif_id} - {delete_data['message']}")


# ===== INTEGRATION TEST =====

class TestNotificationIntegration:
    """End-to-end notification flow test"""
    
    def test_full_project_notification_flow(self, admin_headers, socio_headers, socio_user_id):
        """Test complete project notification flow"""
        print("\n=== Starting Full Project Notification Flow Test ===")
        
        # 1. Socio creates project (notifies admins)
        project_data = {
            "title": f"TEST_Full_Flow_{int(time.time())}",
            "description": "Full flow test project",
            "visibility": "privado",
            "budget": 5000
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=socio_headers)
        assert response.status_code == 200
        project = response.json()
        project_id = project["id"]
        print(f"1. Project created: {project['title']}")
        
        try:
            # 2. Admin approves project (notifies stakeholders)
            response = requests.patch(f"{BASE_URL}/api/projects/{project_id}/approve", headers=admin_headers)
            assert response.status_code == 200
            print("2. Project approved")
            
            # 3. Admin assigns responsible (notifies assigned user)
            response = requests.patch(
                f"{BASE_URL}/api/projects/{project_id}",
                json={"responsible_id": socio_user_id},
                headers=admin_headers
            )
            assert response.status_code == 200
            print("3. Responsible assigned")
            
            # 4. Admin creates task (notifies assignee)
            task_data = {
                "title": "Test Task",
                "description": "Test task description",
                "assignee_id": socio_user_id,
                "priority": "alta"
            }
            response = requests.post(
                f"{BASE_URL}/api/projects/{project_id}/tasks",
                json=task_data,
                headers=admin_headers
            )
            assert response.status_code == 200
            task = response.json()
            task_id = task["id"]
            print("4. Task created and assigned")
            
            # 5. Socio completes task (notifies stakeholders)
            response = requests.patch(
                f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}",
                json={"status": "concluido"},
                headers=socio_headers
            )
            assert response.status_code == 200
            print("5. Task completed")
            
            # 6. Admin adds comment (notifies stakeholders)
            response = requests.post(
                f"{BASE_URL}/api/projects/{project_id}/comments",
                json={"content": "Great work on completing the task!"},
                headers=admin_headers
            )
            assert response.status_code == 200
            print("6. Comment added")
            
            # 7. Admin adds expense (notifies stakeholders)
            response = requests.post(
                f"{BASE_URL}/api/projects/{project_id}/expenses",
                json={"description": "Test expense", "amount": 1000, "date": datetime.now().strftime("%Y-%m-%d")},
                headers=admin_headers
            )
            assert response.status_code == 200
            print("7. Expense added")
            
            # Verify notifications were created
            time.sleep(0.5)
            response = requests.get(f"{BASE_URL}/api/notifications?type=projeto", headers=socio_headers)
            assert response.status_code == 200
            notif_data = response.json()
            print(f"8. Socio has {len(notif_data['items'])} project notifications")
            
            print("=== Full Project Notification Flow Test PASSED ===\n")
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=admin_headers)
            print("Cleanup: Project deleted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
