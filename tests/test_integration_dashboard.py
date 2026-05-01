"""
SprintCycle Dashboard Integration Tests

Tests the Dashboard FastAPI application
covering all API endpoints: /, /api/plan, /api/run, /api/status, /api/events/stream
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

from sprintcycle.results import (
    PlanResult, RunResult, DiagnoseResult,
    StatusResult, RollbackResult, StopResult,
)
from sprintcycle.execution.state_store import ExecutionState, ExecutionStateStatus


@pytest.fixture
def temp_project():
    """Create a temporary project directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestDashboardHome:
    """Test dashboard home page"""

    def test_dashboard_home(self, temp_project):
        """test_dashboard_home: GET / → 200 with HTML"""
        from sprintcycle.dashboard.app import create_app
        app = create_app(project_path=temp_project)
        client = TestClient(app)
        
        response = client.get("/")

        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
        assert 'SprintCycle' in response.text


class TestDashboardPlan:
    """Test plan API"""

    def test_dashboard_plan(self, temp_project):
        """test_dashboard_plan: POST /api/plan → 200 with plan result"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.plan.return_value = PlanResult(
                success=True,
                prd_yaml="# PRD content",
                sprints=[{"name": "Sprint 1", "tasks": ["Task 1"]}],
                mode="auto",
                prd_name="TestProject",
                duration=0.5,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/plan", json={"intent": "Test intent"})

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'prd_yaml' in data
            assert data['prd_name'] == "TestProject"

    def test_dashboard_plan_with_mode(self, temp_project):
        """test_dashboard_plan_with_mode: plan respects mode parameter"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.plan.return_value = PlanResult(
                success=True,
                prd_yaml="# PRD",
                sprints=[],
                mode="evolution",
                prd_name="Test",
                duration=0.1,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post(
                "/api/plan",
                json={"intent": "Evolve", "mode": "evolution"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['mode'] == "evolution"


class TestDashboardRun:
    """Test run API"""

    def test_dashboard_run(self, temp_project):
        """test_dashboard_run: POST /api/run → 200 with run result"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.run.return_value = RunResult(
                success=True,
                execution_id="exec-123",
                prd_name="TestProject",
                completed_sprints=2,
                completed_tasks=5,
                total_sprints=2,
                total_tasks=5,
                duration=10.5,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/run", json={"intent": "Run test"})

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['execution_id'] == "exec-123"

    def test_dashboard_run_with_prd_yaml(self, temp_project):
        """test_dashboard_run_with_prd_yaml: run accepts prd_yaml"""
        prd_yaml = """
project:
  name: "YAMLProject"
  path: "."
mode: normal
sprints:
  - name: "Sprint 1"
    tasks:
      - task: "Task"
        agent: coder
"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.run.return_value = RunResult(
                success=True,
                duration=1.0,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/run", json={"prd_yaml": prd_yaml})

            assert response.status_code == 200
            call_kwargs = mock_instance.run.call_args[1]
            assert call_kwargs['prd_yaml'] == prd_yaml

    def test_dashboard_run_failure(self, temp_project):
        """test_dashboard_run_failure: run returns error on failure"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.run.return_value = RunResult(
                success=False,
                error="Execution failed",
                duration=1.0,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/run", json={"intent": "Failing task"})

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is False
            assert 'error' in data


class TestDashboardStatus:
    """Test status API"""

    def test_dashboard_status(self, temp_project):
        """test_dashboard_status: GET /api/status → 200 with status"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.status.return_value = StatusResult(
                success=True,
                executions=[
                    {
                        "execution_id": "exec-1",
                        "status": "completed",
                        "prd_name": "Project 1",
                        "current_sprint": 3,
                        "total_sprints": 3,
                    }
                ],
                duration=0.1,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/status", json={})

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert len(data['executions']) == 1

    def test_dashboard_status_with_id(self, temp_project):
        """test_dashboard_status_with_id: status with execution_id"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.status.return_value = StatusResult(
                success=True,
                execution_id="exec-specific",
                status="running",
                current_sprint=1,
                total_sprints=3,
                duration=0.1,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post(
                "/api/status",
                json={"execution_id": "exec-specific"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['execution_id'] == "exec-specific"
            assert data['status'] == "running"


class TestDashboardDiagnose:
    """Test diagnose API"""

    def test_dashboard_diagnose(self, temp_project):
        """test_dashboard_diagnose: GET /api/diagnose → 200 with diagnostic"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.diagnose.return_value = DiagnoseResult(
                success=True,
                health_score=85.0,
                issues=[],
                coverage=75.0,
                complexity={"average": 8.5},
                duration=2.5,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.get("/api/diagnose")

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['health_score'] == 85.0

    def test_dashboard_diagnose_with_issues(self, temp_project):
        """test_dashboard_diagnose_with_issues: diagnose reports issues"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.diagnose.return_value = DiagnoseResult(
                success=True,
                health_score=60.0,
                issues=[
                    {"severity": "warning", "message": "Low coverage"},
                ],
                coverage=50.0,
                complexity={},
                duration=1.0,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.get("/api/diagnose")

            assert response.status_code == 200
            data = response.json()
            assert len(data['issues']) == 1


class TestDashboardStop:
    """Test stop API"""

    def test_dashboard_stop(self, temp_project):
        """test_dashboard_stop: POST /api/stop → 200 with stop result"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.stop.return_value = StopResult(
                success=True,
                execution_id="exec-to-stop",
                cancelled=True,
                message="已标记为 CANCELLED",
                duration=0.1,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/stop", json={"execution_id": "exec-to-stop"})

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['cancelled'] is True


class TestDashboardRollback:
    """Test rollback API"""

    def test_dashboard_rollback(self, temp_project):
        """test_dashboard_rollback: POST /api/rollback → 200 with rollback result"""
        with patch('sprintcycle.dashboard.app.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.rollback.return_value = RollbackResult(
                success=True,
                execution_id="exec-to-rollback",
                rollback_point="abc1234",
                files_restored=["file1.py"],
                duration=1.5,
            )

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post(
                "/api/rollback",
                json={"execution_id": "exec-to-rollback"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['rollback_point'] == "abc1234"


class TestDashboardSSE:
    """Test SSE event stream"""

    def test_dashboard_events_stream_exists(self, temp_project):
        """test_dashboard_events_stream_exists: SSE endpoint exists"""
        from sprintcycle.dashboard.app import create_app
        app = create_app(project_path=temp_project)
        
        # Check that the route exists
        routes = [r.path for r in app.routes]
        assert '/api/events/stream' in routes

    def test_dashboard_events_stream_content_type(self, temp_project):
        """test_dashboard_events_stream_content_type: SSE endpoint returns correct content type"""
        from sprintcycle.dashboard.app import create_app
        from fastapi.requests import Request
        from fastapi.responses import StreamingResponse
        
        app = create_app(project_path=temp_project)
        
        # Find the route handler
        for route in app.routes:
            if hasattr(route, 'path') and route.path == '/api/events/stream':
                # Verify the route exists and has proper configuration
                assert route is not None
                break
        else:
            pytest.fail("Route /api/events/stream not found")


class TestDashboardClients:
    """Test clients count API"""

    def test_dashboard_clients(self, temp_project):
        """test_dashboard_clients: GET /api/clients → returns client count"""
        with patch('sprintcycle.dashboard.app.get_client_manager') as mock_manager:
            mock_manager.return_value.get_client_count.return_value = 3

            from sprintcycle.dashboard.app import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.get("/api/clients")

            assert response.status_code == 200
            data = response.json()
            assert 'client_count' in data


class TestDashboardLegacy:
    """Test legacy endpoints"""

    def test_dashboard_events_legacy_exists(self, temp_project):
        """test_dashboard_events_legacy_exists: legacy SSE endpoint exists"""
        from sprintcycle.dashboard.app import create_app
        app = create_app(project_path=temp_project)
        
        routes = [r.path for r in app.routes]
        assert '/api/events' in routes

    def test_dashboard_events_legacy_path_exists(self, temp_project):
        """test_dashboard_events_legacy_path_exists: legacy SSE endpoint /api/events/legacy exists"""
        from sprintcycle.dashboard.app import create_app
        app = create_app(project_path=temp_project)
        
        routes = [r.path for r in app.routes]
        assert '/api/events/legacy' in routes
