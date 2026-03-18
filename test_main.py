"""
Pytest test suite for FastAPI REST API
"""

import pytest
from fastapi.testclient import TestClient
from main import app, db, TaskStatus, UserRole
import os


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db():
    """Cleanup database before and after tests"""
    # Remove test database if it exists
    if os.path.exists("tasks.db"):
        os.remove("tasks.db")
    
    yield
    
    # Cleanup after tests
    if os.path.exists("tasks.db"):
        os.remove("tasks.db")


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test API health"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Task Management API"


class TestUserEndpoints:
    """Test user management endpoints"""
    
    def test_create_user(self, client):
        """Test user creation"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123",
            "full_name": "Test User"
        }
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 201
        assert response.json()["username"] == "testuser"
    
    def test_create_user_duplicate_username(self, client):
        """Test duplicate username prevention"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123"
        }
        
        # Create first user
        client.post("/api/v1/users", json=user_data)
        
        # Try to create user with same username
        user_data["email"] = "another@example.com"
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 400
    
    def test_list_users(self, client):
        """Test listing users"""
        # Create a user first
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123"
        }
        client.post("/api/v1/users", json=user_data)
        
        # List users
        response = client.get("/api/v1/users")
        assert response.status_code == 200
        assert "users" in response.json()
        assert response.json()["total"] >= 1
    
    def test_get_user(self, client):
        """Test getting specific user"""
        # Create a user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass123"
        }
        create_response = client.post("/api/v1/users", json=user_data)
        user_id = create_response.json()["id"]
        
        # Get user
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"
    
    def test_get_nonexistent_user(self, client):
        """Test getting non-existent user"""
        response = client.get("/api/v1/users/99999")
        assert response.status_code == 404


class TestTaskEndpoints:
    """Test task management endpoints"""
    
    @pytest.fixture
    def user_id(self, client):
        """Create a user and return ID"""
        user_data = {
            "username": "taskuser",
            "email": "task@example.com",
            "password": "securepass123"
        }
        response = client.post("/api/v1/users", json=user_data)
        return response.json()["id"]
    
    def test_create_task(self, client, user_id):
        """Test task creation"""
        task_data = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": 2
        }
        response = client.post(f"/api/v1/tasks?user_id={user_id}", json=task_data)
        assert response.status_code == 201
        assert response.json()["title"] == "Test Task"
    
    def test_create_task_invalid_title(self, client, user_id):
        """Test task creation with invalid title"""
        task_data = {
            "title": "a",  # Too short
            "priority": 1
        }
        response = client.post(f"/api/v1/tasks?user_id={user_id}", json=task_data)
        assert response.status_code == 422
    
    def test_list_tasks(self, client, user_id):
        """Test listing tasks"""
        # Create a task
        task_data = {
            "title": "Test Task",
            "priority": 1
        }
        client.post(f"/api/v1/tasks?user_id={user_id}", json=task_data)
        
        # List tasks
        response = client.get(f"/api/v1/tasks?user_id={user_id}")
        assert response.status_code == 200
        assert "tasks" in response.json()
    
    def test_list_tasks_with_filter(self, client, user_id):
        """Test listing tasks with status filter"""
        # Create a task
        task_data = {
            "title": "Test Task",
            "priority": 1
        }
        client.post(f"/api/v1/tasks?user_id={user_id}", json=task_data)
        
        # List with filter
        response = client.get(
            f"/api/v1/tasks?user_id={user_id}&status=pending"
        )
        assert response.status_code == 200
    
    def test_get_task(self, client, user_id):
        """Test getting specific task"""
        # Create a task
        task_data = {
            "title": "Test Task",
            "priority": 1
        }
        create_response = client.post(
            f"/api/v1/tasks?user_id={user_id}",
            json=task_data
        )
        task_id = create_response.json()["id"]
        
        # Get task
        response = client.get(f"/api/v1/tasks/{task_id}?user_id={user_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test Task"
    
    def test_update_task(self, client, user_id):
        """Test updating task"""
        # Create a task
        task_data = {
            "title": "Test Task",
            "priority": 1
        }
        create_response = client.post(
            f"/api/v1/tasks?user_id={user_id}",
            json=task_data
        )
        task_id = create_response.json()["id"]
        
        # Update task
        update_data = {
            "title": "Updated Task",
            "status": "in_progress"
        }
        response = client.put(
            f"/api/v1/tasks/{task_id}?user_id={user_id}",
            json=update_data
        )
        assert response.status_code == 200
    
    def test_delete_task(self, client, user_id):
        """Test deleting task"""
        # Create a task
        task_data = {
            "title": "Test Task",
            "priority": 1
        }
        create_response = client.post(
            f"/api/v1/tasks?user_id={user_id}",
            json=task_data
        )
        task_id = create_response.json()["id"]
        
        # Delete task
        response = client.delete(f"/api/v1/tasks/{task_id}?user_id={user_id}")
        assert response.status_code == 200


class TestStatisticsEndpoint:
    """Test statistics endpoint"""
    
    def test_get_statistics(self, client):
        """Test getting statistics"""
        # Create user
        user_data = {
            "username": "statsuser",
            "email": "stats@example.com",
            "password": "securepass123"
        }
        user_response = client.post("/api/v1/users", json=user_data)
        user_id = user_response.json()["id"]
        
        # Create task
        task_data = {"title": "Task 1", "priority": 1}
        client.post(f"/api/v1/tasks?user_id={user_id}", json=task_data)
        
        # Get statistics
        response = client.get(f"/api/v1/stats?user_id={user_id}")
        assert response.status_code == 200
        assert "by_status" in response.json()
        assert "by_priority" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
