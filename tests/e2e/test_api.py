"""
End-to-end tests for the Assignment Assistant Agent API.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import tempfile
import os

# Add backend to path
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    # In a real test, you would create an actual PDF file
    # For now, we'll create a temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Sample assignment content for testing")
        f.flush()
        yield f.name
    os.unlink(f.name)


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "assignment-agent"


class TestAssignmentEndpoints:
    """Test cases for assignment endpoints."""
    
    def test_list_assignments_empty(self, client):
        """Test listing assignments when none exist."""
        response = client.get("/api/assignments/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_upload_assignment(self, client, sample_pdf_file):
        """Test assignment file upload."""
        with open(sample_pdf_file, 'rb') as f:
            files = {"file": ("test_assignment.txt", f, "text/plain")}
            response = client.post("/api/assignments/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test_assignment.txt"
        assert data["file_size"] > 0
        assert data["file_type"] == "txt"
    
    def test_upload_assignment_invalid_type(self, client):
        """Test assignment upload with invalid file type."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
            f.write("This is not a valid assignment file")
            f.flush()
            
            with open(f.name, 'rb') as file:
                files = {"file": ("test.exe", file, "application/octet-stream")}
                response = client.post("/api/assignments/upload", files=files)
        
        os.unlink(f.name)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_upload_assignment_too_large(self, client):
        """Test assignment upload with file too large."""
        # Create a large file (simulate)
        large_content = "x" * (11 * 1024 * 1024)  # 11MB
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            f.flush()
            
            with open(f.name, 'rb') as file:
                files = {"file": ("large_file.txt", file, "text/plain")}
                response = client.post("/api/assignments/upload", files=files)
        
        os.unlink(f.name)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_get_assignment_not_found(self, client):
        """Test getting a non-existent assignment."""
        response = client.get("/api/assignments/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_generate_plan_not_found(self, client):
        """Test generating plan for non-existent assignment."""
        response = client.post("/api/assignments/00000000-0000-0000-0000-000000000000/plan")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


class TestPlanEndpoints:
    """Test cases for plan endpoints."""
    
    def test_list_plans_empty(self, client):
        """Test listing plans when none exist."""
        response = client.get("/api/plans/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_create_plan_invalid_assignment(self, client):
        """Test creating plan with invalid assignment ID."""
        plan_data = {
            "assignment_id": "00000000-0000-0000-0000-000000000000",
            "name": "Test Plan",
            "description": "Test plan description"
        }
        response = client.post("/api/plans/", json=plan_data)
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_get_plan_not_found(self, client):
        """Test getting a non-existent plan."""
        response = client.get("/api/plans/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_execute_plan_not_found(self, client):
        """Test executing a non-existent plan."""
        execution_data = {
            "plan_id": "00000000-0000-0000-0000-000000000000",
            "dry_run": True,
            "parallel_execution": True,
            "max_parallel_tasks": 3
        }
        response = client.post("/api/plans/00000000-0000-0000-0000-000000000000/execute", json=execution_data)
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_get_plan_status_not_found(self, client):
        """Test getting status of non-existent plan."""
        response = client.get("/api/plans/00000000-0000-0000-0000-000000000000/status")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


class TestIntegrationFlow:
    """Integration tests for the complete workflow."""
    
    def test_complete_workflow(self, client, sample_pdf_file):
        """Test the complete assignment workflow."""
        # Step 1: Upload assignment
        with open(sample_pdf_file, 'rb') as f:
            files = {"file": ("integration_test.txt", f, "text/plain")}
            upload_response = client.post("/api/assignments/upload", files=files)
        
        assert upload_response.status_code == 200
        assignment_data = upload_response.json()
        assignment_id = assignment_data["file_id"]
        
        # Step 2: List assignments
        list_response = client.get("/api/assignments/")
        assert list_response.status_code == 200
        assignments = list_response.json()
        assert len(assignments) >= 1
        
        # Step 3: Get specific assignment
        get_response = client.get(f"/api/assignments/{assignment_id}")
        assert get_response.status_code == 200
        assignment = get_response.json()
        assert assignment["id"] == assignment_id
        
        # Step 4: Generate plan
        plan_response = client.post(f"/api/assignments/{assignment_id}/plan")
        assert plan_response.status_code == 200
        plan_data = plan_response.json()
        assert "message" in plan_data
        
        # Step 5: List plans
        plans_response = client.get("/api/plans/")
        assert plans_response.status_code == 200
        plans = plans_response.json()
        # Note: In a real test, you might need to wait for the background task to complete
        
        # Step 6: Update assignment
        update_data = {"title": "Updated Assignment Title"}
        update_response = client.put(f"/api/assignments/{assignment_id}", json=update_data)
        assert update_response.status_code == 200
        updated_assignment = update_response.json()
        assert updated_assignment["title"] == "Updated Assignment Title"


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/plans/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        response = client.post("/api/plans/", json={})
        assert response.status_code == 422
    
    def test_invalid_uuid_format(self, client):
        """Test handling of invalid UUID format."""
        response = client.get("/api/assignments/invalid-uuid")
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test cases for async endpoints."""
    
    async def test_async_health_check(self):
        """Test async health check."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
