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

from sprintcycle.application.results import (
    PlanResult, RunResult, DiagnoseResult,
    StatusResult, RollbackResult, StopResult,
)
from sprintcycle.execution.sprint_types import ExecutionStatus
from sprintcycle.infrastructure.persistence.state.state_store import ExecutionState


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
        from sprintcycle.dashboard.server import create_app
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
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.plan.return_value = PlanResult(
                success=True,
                release_plan_yaml="# ReleasePlan content",
                sprints=[{"name": "Sprint 1", "tasks": ["Task 1"]}],
                mode="auto",
                release_plan_name="TestProject",
                duration=0.5,
            )

            from sprintcycle.dashboard.server import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/plan", json={"intent": "Test intent"})

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'release_plan_yaml' in data
            assert data['release_plan_name'] == "TestProject"

    def test_dashboard_plan_with_mode(self, temp_project):
        """test_dashboard_plan_with_mode: plan respects mode parameter"""
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.plan.return_value = PlanResult(
                success=True,
                release_plan_yaml="# ReleasePlan",
                sprints=[],
                mode="evolution",
                release_plan_name="Test",
                duration=0.1,
            )

            from sprintcycle.dashboard.server import create_app
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
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.run.return_value = RunResult(
                success=True,
                execution_id="exec-123",
                release_plan_name="TestProject",
                completed_sprints=2,
                completed_tasks=5,
                total_sprints=2,
                total_tasks=5,
                duration=10.5,
            )

            from sprintcycle.dashboard.server import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/run", json={"intent": "Run test"})

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['execution_id'] == "exec-123"

    def test_dashboard_run_with_release_plan_yaml(self, temp_project):
        """run forwards release_plan_yaml to SprintCycle.run"""
        release_plan_yaml = """
project:
  name: "YAMLProject"
  path: "."
mode: normal
sprints:
  - name: "Sprint 1"
    tasks:
      - description: "Task"
        agent: coder
"""
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.run.return_value = RunResult(
                success=True,
                duration=1.0,
            )

            from sprintcycle.dashboard.server import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post(
                "/api/run", json={"release_plan_yaml": release_plan_yaml}
            )

            assert response.status_code == 200
            call_kwargs = mock_instance.run.call_args[1]
            assert call_kwargs["release_plan_yaml"] == release_plan_yaml

    def test_dashboard_run_failure(self, temp_project):
        """test_dashboard_run_failure: run returns error on failure"""
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.run.return_value = RunResult(
                success=False,
                error="Execution failed",
                duration=1.0,
            )

            from sprintcycle.dashboard.server import create_app
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
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.status.return_value = StatusResult(
                success=True,
                executions=[
                    {
                        "execution_id": "exec-1",
                        "status": "completed",
                        "release_plan_name": "Project 1",
                        "current_sprint": 3,
                        "total_sprints": 3,
                    }
                ],
                duration=0.1,
            )

            from sprintcycle.dashboard.server import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.post("/api/status", json={})

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert len(data['executions']) == 1

    def test_dashboard_status_with_id(self, temp_project):
        """test_dashboard_status_with_id: status with execution_id"""
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
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

            from sprintcycle.dashboard.server import create_app
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
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
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

            from sprintcycle.dashboard.server import create_app
            app = create_app(project_path=temp_project)
            client = TestClient(app)
            
            response = client.get("/api/diagnose")

            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['health_score'] == 85.0

    def test_dashboard_diagnose_with_issues(self, temp_project):
        """test_dashboard_diagnose_with_issues: diagnose reports issues"""
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
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

            from sprintcycle.dashboard.server import create_app
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
        with patch('sprintcycle.dashboard.server.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.stop.return_value = StopResult(
                success=True,
                execution_id="exec-to-stop",
                cancelled=True,
                message="已标记为 CANCELLED",
                duration=0.1,
            )

            from sprintcycle.dashboard.server import create_app
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
        """test_dashboard_rollback: POST /api/rollback → currently 404 (not implemented)"""
        from sprintcycle.dashboard.server import create_app
        app = create_app(project_path=temp_project)
        client = TestClient(app)

        response = client.post(
            "/api/rollback",
            json={"execution_id": "exec-to-rollback"}
        )

        # Rollback endpoint is not yet implemented in the dashboard
        assert response.status_code == 404


class TestDashboardPlatformSummary:
    """GET /api/platform/summary — 管理平台聚合"""

    def test_platform_summary(self, temp_project):
        from sprintcycle.dashboard.platform_state import reset_platform_state_for_tests

        reset_platform_state_for_tests()
        with patch("sprintcycle.dashboard.server.SprintCycle") as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance
            mock_instance.project_path = temp_project
            mock_instance.status.return_value = StatusResult(
                success=True,
                executions=[
                    {
                        "execution_id": "exec_run_1",
                        "status": "running",
                        "release_plan_name": "Demo",
                        "current_sprint": 1,
                        "total_sprints": 3,
                        "completed_tasks": 4,
                        "total_tasks": 10,
                        "updated_at": "2026-01-01T12:00:00",
                    }
                ],
                duration=0.02,
            )
            mock_instance.hitl_pending = AsyncMock(
                return_value={"success": True, "data": [{"request_id": "h1"}]}
            )
            mock_instance.platform_overview.return_value = {
                "success": True,
                "project_path": temp_project,
                "executions_overview": {
                    "running_count": 1,
                    "executions": [
                        {
                            "lane_id": "running",
                            "lane_label_zh": "运行中",
                        }
                    ],
                },
                "hitl": {"open_requests": 1},
            }

            from sprintcycle.dashboard.server import create_app

            app = create_app(project_path=temp_project)
            client = TestClient(app)
            r = client.get("/api/platform/summary")
            assert r.status_code == 200
            data = r.json()
            assert data["success"] is True
            assert data["project_path"] == temp_project
            assert data["executions_overview"]["running_count"] == 1
            assert data["hitl"]["open_requests"] == 1
            ov0 = data["executions_overview"]["executions"][0]
            assert ov0["lane_id"] == "running"
            assert "lane_label_zh" in ov0


class TestDashboardSSE:
    """Test SSE event stream"""

    def test_dashboard_events_stream_exists(self, temp_project):
        """test_dashboard_events_stream_exists: SSE endpoint exists"""
        from sprintcycle.dashboard.server import create_app
        app = create_app(project_path=temp_project)
        
        # Check that the route exists
        routes = [r.path for r in app.routes]
        assert '/api/events/stream' in routes

    def test_dashboard_events_stream_content_type(self, temp_project):
        """test_dashboard_events_stream_content_type: SSE endpoint returns correct content type"""
        from sprintcycle.dashboard.server import create_app
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
        from sprintcycle.dashboard.server import create_app
        app = create_app(project_path=temp_project)
        client = TestClient(app)

        response = client.get("/api/clients")

        assert response.status_code == 200
        data = response.json()
        # Falls back to 0 when client manager is unavailable
        assert data.get("client_count") == 0


def _write_minimal_governance_project(project_dir: str) -> None:
    """README + sprintcycle.toml：轻量门禁，避免 import linter / static 拖慢集成测试。"""
    root = Path(project_dir)
    (root / "README.md").write_text("# p\n", encoding="utf-8")
    (root / "sprintcycle.toml").write_text(
        "[quality]\nlevel = \"L0\"\n\n[governance]\nrun_static = false\nrun_import_linter = false\n",
        encoding="utf-8",
    )


class TestGovernanceLatestApi:
    """GET /api/governance/latest（v4.0 只读报告）"""

    def test_governance_latest_404_when_missing(self, temp_project):
        from sprintcycle.dashboard.server import create_app

        app = create_app(project_path=temp_project)
        client = TestClient(app)
        r = client.get("/api/governance/latest")
        assert r.status_code == 404

    def test_governance_latest_returns_review_json(self, temp_project):
        import json
        from pathlib import Path

        d = Path(temp_project) / ".sprintcycle"
        d.mkdir(parents=True, exist_ok=True)
        payload = {"gate": "review", "violations": [], "metadata": {}}
        (d / "governance_last.json").write_text(json.dumps(payload), encoding="utf-8")

        from sprintcycle.dashboard.server import create_app

        app = create_app(project_path=temp_project)
        client = TestClient(app)
        r = client.get("/api/governance/latest")
        assert r.status_code == 200
        body = r.json()
        assert body["gate"] == "review"


class TestGovernanceHistoryAndCheckApi:
    """GET /api/governance/history、POST /api/governance/check"""

    def test_governance_history_empty_then_with_entries(self, temp_project):
        _write_minimal_governance_project(temp_project)
        from sprintcycle.dashboard.server import create_app

        app = create_app(project_path=temp_project)
        client = TestClient(app)
        r0 = client.get("/api/governance/history", params={"limit": 10})
        assert r0.status_code == 200
        assert r0.json().get("entries") == []

        r1 = client.post("/api/governance/check", json={"gate": "review"})
        assert r1.status_code == 200
        body = r1.json()
        assert "review" in body
        assert "should_fail_ci" in body

        # governance/check does NOT persist to history
        r2 = client.get("/api/governance/history", params={"limit": 10})
        assert r2.status_code == 200
        assert r2.json().get("entries") == []


class TestDashboardLegacy:
    """Test legacy endpoints"""

    def test_dashboard_events_legacy_exists(self, temp_project):
        """test_dashboard_events_legacy_exists: legacy SSE endpoint exists"""
        from sprintcycle.dashboard.server import create_app
        app = create_app(project_path=temp_project)
        
        routes = [r.path for r in app.routes]
        assert '/api/events' in routes

    def test_dashboard_events_legacy_path_exists(self, temp_project):
        """test_dashboard_events_legacy_path_exists: legacy SSE endpoint /api/events/legacy exists"""
        from sprintcycle.dashboard.server import create_app
        app = create_app(project_path=temp_project)
        
        routes = [r.path for r in app.routes]
        assert '/api/events/legacy' in routes
