"""
SprintCycle Integration Tests

Tests for ExecutionHandler and SprintOrchestrator covering: plan, run, diagnose, status, rollback, stop
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from sprintcycle.interfaces.http.handlers.execution import ExecutionHandler
from sprintcycle.interfaces.http.handlers.services import create_service_aggregator
from sprintcycle.application.orchestration.sprint_orchestrator import SprintOrchestrator
from sprintcycle.application.dto.results import (
    PlanResult, RunResult, DiagnoseResult,
    StatusResult, RollbackResult, StopResult,
)
from sprintcycle.domain.generic.interfaces.types import ExecutionStatus


class TestExecutionHandlerDiagnose:
    """Test diagnose operation"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_diagnose_returns_health(self):
        """diagnose → returns health information"""
        from sprintcycle.application.composition import initialize_http_infrastructure
        initialize_http_infrastructure(self.temp_dir)
        
        services = create_service_aggregator(self.temp_dir)
        handler = ExecutionHandler(services)
        result = handler.diagnose()
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "health_score" in result
        assert "issues" in result


class TestExecutionHandlerStatus:
    """Test status operation"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_status_returns_overview(self):
        """status → returns console overview when no execution_id provided"""
        from sprintcycle.application.composition import initialize_http_infrastructure
        initialize_http_infrastructure(self.temp_dir)
        
        services = create_service_aggregator(self.temp_dir)
        handler = ExecutionHandler(services)
        result = handler.status()
        
        assert isinstance(result, dict)
        assert "success" in result


class TestExecutionHandlerStop:
    """Test stop operation"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_stop_returns_result(self):
        """stop returns StopResult-like dict"""
        from sprintcycle.application.composition import initialize_http_infrastructure
        initialize_http_infrastructure(self.temp_dir)
        
        services = create_service_aggregator(self.temp_dir)
        handler = ExecutionHandler(services)
        result = handler.stop_execution(execution_id="test-exec")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "execution_id" in result


class TestExecutionHandlerRollback:
    """Test rollback operation"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_rollback_returns_result(self):
        """rollback returns RollbackResult-like dict"""
        from sprintcycle.application.composition import initialize_http_infrastructure
        initialize_http_infrastructure(self.temp_dir)
        
        services = create_service_aggregator(self.temp_dir)
        handler = ExecutionHandler(services)
        result = handler.rollback(execution_id="test-exec")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "execution_id" in result



