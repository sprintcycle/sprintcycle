"""
SprintCycle Integration Tests

Tests for HTTPServices and SprintOrchestrator covering: plan, run, diagnose, status, rollback, stop
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from sprintcycle.application.factories.http import HTTPServices
from sprintcycle.application.orchestration.sprint_orchestrator import SprintOrchestrator
from sprintcycle.application.dto.results import (
    PlanResult, RunResult, DiagnoseResult,
    StatusResult, RollbackResult, StopResult,
)
from sprintcycle.execution.sprint_types import ExecutionStatus
from sprintcycle.infrastructure.adapters.core.execution.state_store.state_store import StateStore, ExecutionState


class TestHTTPServicesDiagnose:
    """Test diagnose operation"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_diagnose_returns_health(self):
        """diagnose → returns health information"""
        services = HTTPServices(project_path=self.temp_dir)
        result = services.diagnose()
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "health_score" in result
        assert "issues" in result


class TestHTTPServicesStatus:
    """Test status operation"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_status_returns_overview(self):
        """status → returns console overview when no execution_id provided"""
        services = HTTPServices(project_path=self.temp_dir)
        result = services.status()
        
        assert isinstance(result, dict)
        assert "success" in result


class TestHTTPServicesStop:
    """Test stop operation"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_stop_returns_result(self):
        """stop returns StopResult-like dict"""
        services = HTTPServices(project_path=self.temp_dir)
        result = services.stop(execution_id="test-exec")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "execution_id" in result


class TestHTTPServicesRollback:
    """Test rollback operation"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_rollback_returns_result(self):
        """rollback returns RollbackResult-like dict"""
        services = HTTPServices(project_path=self.temp_dir)
        result = services.rollback(execution_id="test-exec")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "execution_id" in result


class TestSprintOrchestratorPlan:
    """Test plan operation via SprintOrchestrator"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_plan_returns_plan_result(self):
        """plan → returns PlanResult"""
        from sprintcycle.infrastructure.adapters.generic.config import RuntimeConfig
        
        cfg = RuntimeConfig(dry_run=True)
        orch = SprintOrchestrator(config=cfg, project_path=self.temp_dir)
        
        with patch('sprintcycle.application.sprint_orchestrator.UserIntentEvolutionLoop'):
            result = orch.plan(intent="Test intent")
            
            assert isinstance(result, PlanResult)
            assert hasattr(result, 'success')
            assert hasattr(result, 'release_plan_yaml')


class TestSprintOrchestratorRun:
    """Test run operation via SprintOrchestrator"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / ".sprintcycle" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_returns_run_result(self):
        """run → returns RunResult"""
        from sprintcycle.infrastructure.adapters.generic.config import RuntimeConfig
        
        cfg = RuntimeConfig(dry_run=True)
        orch = SprintOrchestrator(config=cfg, project_path=self.temp_dir)
        
        with patch('sprintcycle.application.sprint_orchestrator.UserIntentEvolutionLoop'), \
             patch('sprintcycle.application.sprint_orchestrator.get_execution_event_backend'):
            result = orch.run(intent="Run test")
            
            assert isinstance(result, RunResult)
            assert hasattr(result, 'success')
            assert hasattr(result, 'execution_id')
