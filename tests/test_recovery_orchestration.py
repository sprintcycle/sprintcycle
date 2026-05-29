"""恢复流程测试 - 覆盖recovery orchestration逻辑和失败重试机制"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from sprintcycle.application.services.governance.repair_orchestration_service import (
    RepairOrchestrationService,
)
from sprintcycle.application.services.execution.phase_workflow import (
    DiagnoseArtifact,
    RepairArtifact,
    ObserveArtifact,
    build_diagnose_artifact,
    build_repair_artifact,
    build_observe_artifact,
)


class MockObservabilityFacade:
    """Mock observability facade for testing"""

    def __init__(self, trace_payload=None):
        self._trace_payload = trace_payload or {}

    def to_trace_payload(self, execution_id: str):
        return self._trace_payload


class TestRepairOrchestrationService:
    """测试恢复流程编排服务"""

    def test_diagnose_with_failure_events(self):
        """测试诊断方法 - 当有失败事件时"""
        trace_payload = {
            "execution_id": "test-exec-1",
            "events": [
                {
                    "kind": "task_failed",
                    "root_cause": "dependency_missing",
                    "failure_kind": "missing_dependency",
                },
                {
                    "kind": "task_failed",
                    "root_cause": "syntax_error",
                    "failure_kind": "code_error",
                },
                {
                    "kind": "task_completed",
                    "status": "success",
                },
            ],
        }

        observability = MockObservabilityFacade(trace_payload)
        service = RepairOrchestrationService(observability=observability)

        result = service.diagnose("test-exec-1")

        assert result["success"] is True
        data = result["data"]
        assert data["execution_id"] == "test-exec-1"
        assert data["failure_count"] == 2
        assert "dependency_missing" in data["root_causes"]
        assert "syntax_error" in data["root_causes"]
        assert data["repair_ready"] is True
        assert data["diagnose_artifact"] is not None

    def test_diagnose_with_no_failure_events(self):
        """测试诊断方法 - 当没有失败事件时"""
        trace_payload = {
            "execution_id": "test-exec-2",
            "events": [
                {"kind": "task_completed", "status": "success"},
                {"kind": "stage_completed", "status": "success"},
            ],
        }

        observability = MockObservabilityFacade(trace_payload)
        service = RepairOrchestrationService(observability=observability)

        result = service.diagnose("test-exec-2")

        assert result["success"] is True
        data = result["data"]
        assert data["failure_count"] == 0
        assert len(data["root_causes"]) == 0
        assert data["repair_ready"] is False
        assert data["diagnose_artifact"] is not None

    def test_diagnose_with_empty_trace(self):
        """测试诊断方法 - 空trace"""
        observability = MockObservabilityFacade({})
        service = RepairOrchestrationService(observability=observability)

        result = service.diagnose("test-exec-3")

        assert result["success"] is True
        data = result["data"]
        assert data["failure_count"] == 0
        assert data["repair_ready"] is False

    def test_repair_requires_failed_state(self):
        """测试修复方法需要从failed状态开始"""
        from sprintcycle.domain.core.lifecycle import LifecycleSubstage
        from sprintcycle.domain.core.lifecycle.state_machine import LifecycleStateMachine
        
        machine = LifecycleStateMachine()
        
        assert machine.can_transition("failed", "repairing") is True
        assert machine.can_transition("new", "repairing") is False

    def test_recover_with_not_repair_ready(self):
        """测试恢复方法 - 当repair_ready为False时"""
        trace_payload = {
            "execution_id": "test-exec-7",
            "events": [
                {"kind": "task_completed", "status": "success"},
            ],
        }

        observability = MockObservabilityFacade(trace_payload)
        service = RepairOrchestrationService(observability=observability)

        result = service.recover("test-exec-7")

        assert result["success"] is True
        data = result["data"]
        assert data["execution_id"] == "test-exec-7"
        assert data["recovery"]["mode"] == "observe_only"
        assert data["recovery"]["repair_ready"] is False
        assert data["closed_loop"] is False
        assert "observe_artifact" in data


class TestRecoveryArtifacts:
    """测试恢复相关的artifact构建"""

    def test_build_diagnose_artifact(self):
        """测试构建诊断artifact"""
        contract_payload = {
            "execution_id": "test-exec-9",
            "task_id": "test-task-9",
            "project_path": "/test/project",
        }

        result = build_diagnose_artifact(
            contract_payload,
            root_causes=["error_1", "error_2"],
            repair_ready=True,
            confidence=0.85,
            recommendations=["fix_error_1", "fix_error_2"],
        )

        assert "lifecycle_contract" in result
        assert "diagnose" in result
        diagnose = result["diagnose"]
        assert diagnose["execution_id"] == "test-exec-9"
        assert diagnose["root_causes"] == ["error_1", "error_2"]
        assert diagnose["repair_ready"] is True
        assert diagnose["confidence"] == 0.85
        assert diagnose["recommendations"] == ["fix_error_1", "fix_error_2"]

    def test_build_repair_artifact(self):
        """测试构建修复artifact"""
        contract_payload = {
            "execution_id": "test-exec-10",
            "task_id": "test-task-10",
            "project_path": "/test/project",
        }

        verify_result = {"status": "success", "verified": True}

        result = build_repair_artifact(
            contract_payload,
            closed_loop=True,
            verify_result=verify_result,
        )

        assert "lifecycle_contract" in result
        assert "repair" in result
        repair = result["repair"]
        assert repair["execution_id"] == "test-exec-10"
        assert repair["attempted"] is True
        assert repair["closed_loop"] is True
        assert repair["verify_result"] == verify_result

    def test_build_observe_artifact(self):
        """测试构建观察artifact"""
        contract_payload = {
            "execution_id": "test-exec-11",
            "task_id": "test-task-11",
            "project_path": "/test/project",
        }

        trace = {"events": [], "metrics": {}}
        diagnostics = {"health": "good", "performance": "optimal"}

        result = build_observe_artifact(
            contract_payload,
            trace=trace,
            diagnostics=diagnostics,
        )

        assert "lifecycle_contract" in result
        assert "observe" in result
        observe = result["observe"]
        assert observe["execution_id"] == "test-exec-11"
        assert observe["trace"] == trace
        assert observe["diagnostics"] == diagnostics


class TestRecoveryLifecycleTransitions:
    """测试恢复流程中的生命周期转换"""

    def test_failed_state_can_recover_to_repairing(self):
        """测试failed状态可以通过trigger_recovery转换到repairing"""
        from sprintcycle.domain.core.lifecycle import LifecycleSubstage, create_lifecycle
        from sprintcycle.domain.core.lifecycle.state_machine import LifecycleStateMachine
        
        machine = LifecycleStateMachine()
        
        assert machine.can_transition("failed", "repairing") is True
        
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.FAILED)
        
        assert lifecycle.substage == LifecycleSubstage.FAILED
        
        lifecycle = lifecycle.trigger_recovery(failure_kind="test_error", reason="test recovery")
        
        assert lifecycle.substage == LifecycleSubstage.REPAIRING

    def test_recovery_flow_completes(self):
        """测试完整的恢复流程：failed -> repairing -> verifying -> observing"""
        from sprintcycle.domain.core.lifecycle import LifecycleSubstage, create_lifecycle
        
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.FAILED)
        
        lifecycle = lifecycle.trigger_recovery(failure_kind="test_error")
        
        assert lifecycle.substage == LifecycleSubstage.REPAIRING
        
        lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.VERIFYING)
        
        assert lifecycle.substage == LifecycleSubstage.VERIFYING
        
        lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.OBSERVING)
        
        assert lifecycle.substage == LifecycleSubstage.OBSERVING

    def test_recovery_transition_reason_recorded(self):
        """测试恢复转换原因被正确记录"""
        from sprintcycle.domain.core.lifecycle import LifecycleSubstage, create_lifecycle
        
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.FAILED)
        
        lifecycle = lifecycle.trigger_recovery(failure_kind="network_error", reason="network timeout")
        
        assert "Recovery" in lifecycle.transition_reason
        assert "network timeout" in lifecycle.transition_reason
