"""LifecycleRoot 核心测试 - 覆盖聚合根的关键方法"""

from __future__ import annotations

import pytest

from sprintcycle.domain.core.lifecycle.lifecycle_root import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
)
from sprintcycle.domain.core.lifecycle.values import (
    StageEvidence,
    GovernanceRef,
    EvolutionRef,
    RuntimeRef,
    CorrelationContext,
)


class TestLifecycleRootCreation:
    """测试生命周期根的创建"""

    def test_create_lifecycle_factory(self):
        """测试工厂函数创建生命周期"""
        lifecycle = create_lifecycle(
            execution_id="test-exec-1",
            task_id="test-task-1",
            project_path="/test/project",
            task_type="project_optimization",
            intent="test intent",
            metadata={"author": "test"},
        )

        assert lifecycle.execution_id == "test-exec-1"
        assert lifecycle.task_id == "test-task-1"
        assert lifecycle.project_path == "/test/project"
        assert lifecycle.task_type == "project_optimization"
        assert lifecycle.intent == "test intent"
        assert lifecycle.metadata == {"author": "test"}
        assert lifecycle.stage == LifecycleStage.NEW
        assert lifecycle.status == LifecycleStatus.PENDING
        assert lifecycle.contract_id.startswith("lifecycle-")
        assert lifecycle.correlation.execution_id == "test-exec-1"
        assert lifecycle.allowed_next_stages == ("normalized", "failed", "cancelled")

    def test_lifecycle_root_identity_properties(self):
        """测试标识属性"""
        lifecycle = create_lifecycle(
            execution_id="test-exec-2",
            task_id="test-task-2",
            project_path="/test/project",
        )

        assert lifecycle.is_terminal is False
        assert lifecycle.is_running is False
        assert lifecycle.contract_id_or_default == lifecycle.contract_id

    def test_lifecycle_root_terminal_check(self):
        """测试终端状态检查"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
        lifecycle = lifecycle.transition_to(LifecycleStage.PLANNED)
        lifecycle = lifecycle.transition_to(LifecycleStage.PREPARED)
        lifecycle = lifecycle.transition_to(LifecycleStage.DECOMPOSED)
        lifecycle = lifecycle.transition_to(LifecycleStage.EXECUTING)
        lifecycle = lifecycle.transition_to(LifecycleStage.OBSERVING)
        lifecycle = lifecycle.transition_to(LifecycleStage.DELIVERING)
        lifecycle = lifecycle.transition_to(LifecycleStage.RUNTIME_LINKED)
        lifecycle = lifecycle.transition_to(LifecycleStage.GOVERNING)
        lifecycle = lifecycle.transition_to(LifecycleStage.PROMOTION_READY)
        lifecycle = lifecycle.transition_to(LifecycleStage.PROMOTED)

        assert lifecycle.is_terminal is True
        assert lifecycle.status == LifecycleStatus.PROMOTED


class TestStageTransitions:
    """测试阶段转换"""

    def test_transition_to_valid_stage(self):
        """测试有效状态转换"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED, reason="normalized")

        assert lifecycle.stage == LifecycleStage.NORMALIZED
        assert lifecycle.status == LifecycleStatus.RUNNING
        assert lifecycle.transition_reason == "normalized"
        assert len(lifecycle.stage_history) == 1
        assert lifecycle.stage_history[0].from_stage == "new"
        assert lifecycle.stage_history[0].to_stage == "normalized"

    def test_transition_to_invalid_stage(self):
        """测试无效状态转换"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        with pytest.raises(ValueError, match="illegal lifecycle transition"):
            lifecycle.transition_to(LifecycleStage.EXECUTING)

    def test_transition_from_terminal_stage(self):
        """测试从终端状态转换"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
        lifecycle = lifecycle.transition_to(LifecycleStage.PLANNED)
        lifecycle = lifecycle.transition_to(LifecycleStage.PREPARED)
        lifecycle = lifecycle.transition_to(LifecycleStage.DECOMPOSED)
        lifecycle = lifecycle.transition_to(LifecycleStage.EXECUTING)
        lifecycle = lifecycle.transition_to(LifecycleStage.OBSERVING)
        lifecycle = lifecycle.transition_to(LifecycleStage.DELIVERING)
        lifecycle = lifecycle.transition_to(LifecycleStage.RUNTIME_LINKED)
        lifecycle = lifecycle.transition_to(LifecycleStage.GOVERNING)
        lifecycle = lifecycle.transition_to(LifecycleStage.PROMOTION_READY)
        lifecycle = lifecycle.transition_to(LifecycleStage.PROMOTED)

        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            lifecycle.transition_to(LifecycleStage.NORMALIZED)

    def test_transition_with_explicit_status(self):
        """测试带显式状态的转换"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        lifecycle = lifecycle.transition_to(
            LifecycleStage.NORMALIZED,
            reason="test",
            new_status=LifecycleStatus.RUNNING,
        )

        assert lifecycle.status == LifecycleStatus.RUNNING

    def test_can_advance_to(self):
        """测试can_advance_to方法"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        assert lifecycle.can_advance_to(LifecycleStage.NORMALIZED) is True
        assert lifecycle.can_advance_to(LifecycleStage.EXECUTING) is False

    def test_get_next_stage(self):
        """测试获取下一阶段"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        next_stage = lifecycle.get_next_stage()
        assert next_stage == LifecycleStage.NORMALIZED

        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
        next_stage = lifecycle.get_next_stage()
        assert next_stage == LifecycleStage.PLANNED


class TestRecoveryFlow:
    """测试恢复流程"""

    def test_trigger_recovery_from_failed(self):
        """测试从失败状态触发恢复"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.transition_to(LifecycleStage.FAILED)

        lifecycle = lifecycle.trigger_recovery(
            failure_kind="test_error",
            reason="test recovery",
        )

        assert lifecycle.stage == LifecycleStage.REPAIRING
        assert lifecycle.status == LifecycleStatus.RUNNING
        assert lifecycle.failure_kind == "test_error"
        assert "Recovery" in lifecycle.transition_reason

    def test_trigger_recovery_default_failure_kind(self):
        """测试恢复时使用默认失败类型 - FAILED状态的默认失败类型为空"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.transition_to(LifecycleStage.FAILED)

        lifecycle = lifecycle.trigger_recovery(reason="test")

        assert lifecycle.failure_kind == ""


class TestCrossSubdomainReferences:
    """测试跨子域引用"""

    def test_attach_governance(self):
        """测试附加治理引用"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        lifecycle = lifecycle.attach_governance(
            governance_session_id="gov-sess-1",
            gate="review",
            approved=True,
        )

        assert lifecycle.governance_ref is not None
        assert lifecycle.governance_ref.governance_session_id == "gov-sess-1"
        assert lifecycle.governance_ref.gate == "review"
        assert lifecycle.governance_ref.approved is True

    def test_attach_evolution(self):
        """测试附加演化引用"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        lifecycle = lifecycle.attach_evolution(
            evolution_request_id="evo-req-1",
            version_id="v1.0.0",
        )

        assert lifecycle.evolution_ref is not None
        assert lifecycle.evolution_ref.evolution_request_id == "evo-req-1"
        assert lifecycle.evolution_ref.version_id == "v1.0.0"

    def test_attach_runtime(self):
        """测试附加运行时引用"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        lifecycle = lifecycle.attach_runtime(
            runtime_id="runtime-1",
            linked=True,
            healthy=True,
        )

        assert lifecycle.runtime_ref is not None
        assert lifecycle.runtime_ref.runtime_id == "runtime-1"
        assert lifecycle.runtime_ref.linked is True
        assert lifecycle.runtime_ref.healthy is True

    def test_attach_all_references(self):
        """测试附加所有引用"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        lifecycle = (
            lifecycle.attach_governance("gov-1", "review", True)
            .attach_evolution("evo-1", "v1")
            .attach_runtime("rt-1", True, True)
        )

        assert lifecycle.governance_ref is not None
        assert lifecycle.evolution_ref is not None
        assert lifecycle.runtime_ref is not None


class TestStageEvidence:
    """测试阶段证据"""

    def test_add_stage_evidence(self):
        """测试添加阶段证据"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        evidence = StageEvidence(
            stage="normalized",
            present=True,
            evidence={"key": "value"},
        )

        lifecycle = lifecycle.add_stage_evidence(evidence)

        assert "normalized" in lifecycle.evidence.stages
        assert lifecycle.evidence.stages["normalized"].present is True
        assert lifecycle.evidence.stages["normalized"].evidence == {"key": "value"}

    def test_add_multiple_evidences(self):
        """测试添加多个阶段证据"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        evidence1 = StageEvidence(stage="normalized", present=True)
        evidence2 = StageEvidence(stage="planned", present=True)

        lifecycle = lifecycle.add_stage_evidence(evidence1)
        lifecycle = lifecycle.add_stage_evidence(evidence2)

        assert len(lifecycle.evidence.stages) == 2
        assert "normalized" in lifecycle.evidence.stages
        assert "planned" in lifecycle.evidence.stages


class TestValidation:
    """测试验证方法"""

    def test_validate_valid_lifecycle(self):
        """测试验证有效生命周期"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        errors = lifecycle.validate()

        assert len(errors) == 0
        assert lifecycle.is_valid is True

    def test_validate_missing_required_fields(self):
        """测试验证缺少必需字段"""
        lifecycle = LifecycleRoot(
            contract_id="",
            execution_id="",
            task_id="",
            project_path="",
        )

        errors = lifecycle.validate()

        assert len(errors) > 0
        assert "execution_id is required" in errors
        assert "task_id is required" in errors
        assert "project_path is required" in errors
        assert lifecycle.is_valid is False

    def test_validate_invalid_status(self):
        """测试验证无效状态"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle.status = LifecycleStatus.RUNNING

        errors = lifecycle.validate()

        assert len(errors) == 0

    def test_validate_terminal_status_non_terminal_stage(self):
        """测试终端状态与非终端阶段的一致性"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle.status = LifecycleStatus.SUCCESS
        lifecycle.stage = LifecycleStage.EXECUTING

        errors = lifecycle.validate()

        assert any("terminal status requires terminal stage" in error for error in errors)


class TestSerialization:
    """测试序列化和反序列化"""

    def test_to_dict(self):
        """测试转换为字典"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.attach_governance("gov-1", "review", True)
        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED, reason="test")

        result = lifecycle.to_dict()

        assert result["execution_id"] == "test-exec"
        assert result["task_id"] == "test-task"
        assert result["stage"] == "normalized"
        assert result["status"] == "running"
        assert result["governance_ref"]["governance_session_id"] == "gov-1"
        assert len(result["stage_history"]) == 1
        assert result["is_terminal"] is False
        assert result["is_valid"] is True

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "contract_id": "test-contract",
            "execution_id": "test-exec",
            "task_id": "test-task",
            "project_path": "/test/project",
            "stage": "normalized",
            "status": "running",
            "governance_ref": {
                "governance_session_id": "gov-1",
                "gate": "review",
                "approved": True,
            },
            "stage_history": [
                {"from": "new", "to": "normalized", "reason": "test"},
            ],
        }

        lifecycle = LifecycleRoot.from_dict(data)

        assert lifecycle.contract_id == "test-contract"
        assert lifecycle.execution_id == "test-exec"
        assert lifecycle.stage == LifecycleStage.NORMALIZED
        assert lifecycle.status == LifecycleStatus.RUNNING
        assert lifecycle.governance_ref.governance_session_id == "gov-1"
        assert len(lifecycle.stage_history) == 1

    def test_serialization_roundtrip(self):
        """测试序列化往返"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")
        lifecycle = lifecycle.attach_governance("gov-1")
        lifecycle = lifecycle.attach_evolution("evo-1", "v1")
        lifecycle = lifecycle.attach_runtime("rt-1", True, True)
        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)

        data = lifecycle.to_dict()
        lifecycle2 = LifecycleRoot.from_dict(data)

        assert lifecycle.execution_id == lifecycle2.execution_id
        assert lifecycle.stage == lifecycle2.stage
        assert lifecycle.status == lifecycle2.status
        assert lifecycle.governance_ref.governance_session_id == lifecycle2.governance_ref.governance_session_id
        assert lifecycle.evolution_ref.evolution_request_id == lifecycle2.evolution_ref.evolution_request_id
        assert lifecycle.runtime_ref.runtime_id == lifecycle2.runtime_ref.runtime_id


class TestLifecycleStageEnum:
    """测试生命周期阶段枚举"""

    def test_stage_from_string(self):
        """测试从字符串创建阶段"""
        assert LifecycleStage.from_string("NEW") == LifecycleStage.NEW
        assert LifecycleStage.from_string("normalized") == LifecycleStage.NORMALIZED
        assert LifecycleStage.from_string("  EXECUTING  ") == LifecycleStage.EXECUTING
        assert LifecycleStage.from_string("unknown") == LifecycleStage.NEW

    def test_stage_is_terminal(self):
        """测试终端阶段判断"""
        assert LifecycleStage.PROMOTED.is_terminal() is True
        assert LifecycleStage.FAILED.is_terminal() is True
        assert LifecycleStage.CANCELLED.is_terminal() is True
        assert LifecycleStage.EXECUTING.is_terminal() is False

    def test_get_failure_kind(self):
        """测试获取失败类型"""
        assert LifecycleStage.FAILED.get_failure_kind() == ""
        assert LifecycleStage.ABORTED.get_failure_kind() == ""
        assert LifecycleStage.EXECUTING.get_failure_kind() == "execution_error"


class TestStatusDerivation:
    """测试状态推导"""

    def test_status_derivation(self):
        """测试状态从阶段推导"""
        lifecycle = create_lifecycle("test-exec", "test-task", "/test/project")

        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
        assert lifecycle.status == LifecycleStatus.RUNNING

        lifecycle = lifecycle.transition_to(LifecycleStage.FAILED)
        assert lifecycle.status == LifecycleStatus.FAILED

        lifecycle2 = create_lifecycle("test-exec2", "test-task2", "/test/project")
        lifecycle2 = lifecycle2.transition_to(LifecycleStage.CANCELLED)
        assert lifecycle2.status == LifecycleStatus.CANCELLED

        lifecycle3 = create_lifecycle("test-exec3", "test-task3", "/test/project")
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.NORMALIZED)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.PLANNED)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.PREPARED)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.DECOMPOSED)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.EXECUTING)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.OBSERVING)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.DELIVERING)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.RUNTIME_LINKED)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.GOVERNING)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.PROMOTION_READY)
        lifecycle3 = lifecycle3.transition_to(LifecycleStage.PROMOTED)
        assert lifecycle3.status == LifecycleStatus.PROMOTED
