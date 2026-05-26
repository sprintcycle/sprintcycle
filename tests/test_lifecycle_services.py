"""LifecycleStateMachineService 测试 - 覆盖状态机服务的核心方法"""

from __future__ import annotations

import pytest

from sprintcycle.domain.core.lifecycle.services import (
    LifecycleStateMachineService,
    get_lifecycle_state_machine_service,
    LIFECYCLE_STAGES,
    TERMINAL_STAGES,
    FAILURE_STAGES,
    RECOVERY_STAGES,
    STAGE_TRANSITIONS,
    RECOVERY_TARGETS,
    FAILURE_KIND_BY_STAGE,
)
from sprintcycle.domain.core.lifecycle.lifecycle_root import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
)
from sprintcycle.domain.core.lifecycle.values import CorrelationContext


class TestLifecycleStateMachineServiceBasic:
    """测试状态机服务的基本方法"""

    def test_service_initialization(self):
        """测试服务初始化"""
        service = LifecycleStateMachineService()
        
        assert service is not None
        assert service.STAGES == LIFECYCLE_STAGES
        assert service.TERMINAL_STAGES == TERMINAL_STAGES
        assert service.TRANSITIONS == STAGE_TRANSITIONS
        assert service.RECOVERY_TARGETS == RECOVERY_TARGETS

    def test_singleton_service(self):
        """测试单例服务"""
        service1 = get_lifecycle_state_machine_service()
        service2 = get_lifecycle_state_machine_service()
        
        assert service1 is service2

    def test_normalize_stage(self):
        """测试阶段规范化"""
        service = LifecycleStateMachineService()

        assert service.normalize_stage("NEW") == "new"
        assert service.normalize_stage("Executing") == "executing"
        assert service.normalize_stage("  OBSERVING  ") == "observing"
        assert service.normalize_stage(LifecycleStage.NEW) == "new"
        assert service.normalize_stage(LifecycleStage.EXECUTING) == "executing"
        assert service.normalize_stage("unknown") == "new"
        assert service.normalize_stage(None) == "new"
        assert service.normalize_stage("") == "new"

    def test_can_transition(self):
        """测试转换检查"""
        service = LifecycleStateMachineService()

        assert service.can_transition("new", "normalized") is True
        assert service.can_transition("new", "executing") is False
        assert service.can_transition("executing", "observing") is True
        assert service.can_transition("promoted", "governing") is False
        assert service.can_transition("failed", "repairing") is True
        assert service.can_transition("repairing", "verifying") is True

    def test_can_transition_same_stage(self):
        """测试相同阶段转换（noop）"""
        service = LifecycleStateMachineService()

        assert service.can_transition("new", "new") is True
        assert service.can_transition("executing", "executing") is True

    def test_validate_transition(self):
        """测试转换验证 - 空字符串被规范化为new"""
        service = LifecycleStateMachineService()

        assert service.validate_transition("new", "normalized") is None
        assert service.validate_transition("new", "executing") == "illegal lifecycle transition: new -> executing"
        assert service.validate_transition("", "normalized") is None  # empty normalized to new
        assert service.validate_transition("new", "") is None  # empty normalized to new

    def test_next_stages(self):
        """测试获取下一阶段"""
        service = LifecycleStateMachineService()

        assert service.next_stages("new") == ("normalized", "failed", "cancelled")
        assert service.next_stages("executing") == ("observing", "diagnosed", "delivering", "failed", "cancelled")
        assert service.next_stages("promoted") == ()
        assert service.next_stages(LifecycleStage.NEW) == ("normalized", "failed", "cancelled")

    def test_stage_index(self):
        """测试阶段索引"""
        service = LifecycleStateMachineService()

        assert service.stage_index("new") == 0
        assert service.stage_index("executing") == 5
        assert service.stage_index("promoted") == 14
        assert service.stage_index("unknown") == 0  # unknown is normalized to new
        assert service.stage_index(LifecycleStage.EXECUTING) == 5

    def test_is_terminal(self):
        """测试终端状态判断"""
        service = LifecycleStateMachineService()

        assert service.is_terminal("promoted") is True
        assert service.is_terminal("failed") is True
        assert service.is_terminal("aborted") is True
        assert service.is_terminal("cancelled") is True
        assert service.is_terminal("executing") is False
        assert service.is_terminal("governing") is False
        assert service.is_terminal(LifecycleStage.PROMOTED) is True

    def test_is_failure(self):
        """测试失败状态判断"""
        service = LifecycleStateMachineService()

        assert service.is_failure("failed") is True
        assert service.is_failure("aborted") is True
        assert service.is_failure("cancelled") is True
        assert service.is_failure("executing") is False
        assert service.is_failure("repairing") is False

    def test_is_recovery(self):
        """测试恢复状态判断"""
        service = LifecycleStateMachineService()

        assert service.is_recovery("repairing") is True
        assert service.is_recovery("verifying") is True
        assert service.is_recovery("executing") is False
        assert service.is_recovery("observing") is False

    def test_get_recovery_target(self):
        """测试获取恢复目标"""
        service = LifecycleStateMachineService()

        assert service.get_recovery_target("executing") == "repairing"
        assert service.get_recovery_target("observing") == "repairing"
        assert service.get_recovery_target("diagnosed") == "repairing"
        assert service.get_recovery_target("repairing") == "verifying"
        assert service.get_recovery_target("verifying") == "observing"
        assert service.get_recovery_target("failed") == "repairing"
        assert service.get_recovery_target("unknown") == "repairing"  # default
        assert service.get_recovery_target(LifecycleStage.EXECUTING) == "repairing"

    def test_get_failure_kind(self):
        """测试获取失败类型"""
        service = LifecycleStateMachineService()

        assert service.get_failure_kind("executing") == "execution_error"
        assert service.get_failure_kind("observing") == "observation_error"
        assert service.get_failure_kind("diagnosed") == "diagnosis_error"
        assert service.get_failure_kind("repairing") == "repair_error"
        assert service.get_failure_kind("verifying") == "verification_error"
        assert service.get_failure_kind("delivering") == "delivery_error"
        assert service.get_failure_kind("new") == ""
        assert service.get_failure_kind("promoted") == ""
        assert service.get_failure_kind(LifecycleStage.EXECUTING) == "execution_error"

    def test_get_allowed_next_stages(self):
        """测试获取允许的下一阶段（排除失败状态）"""
        service = LifecycleStateMachineService()

        assert service.get_allowed_next_stages("new") == ["normalized"]
        assert service.get_allowed_next_stages("executing") == ["observing", "diagnosed", "delivering"]
        assert service.get_allowed_next_stages("promoted") == []


class TestTransitionMethods:
    """测试转换相关方法"""

    def test_build_transition_event(self):
        """测试构建转换事件"""
        service = LifecycleStateMachineService()

        event = service.build_transition_event(
            from_stage="executing",
            to_stage="observing",
            reason="test transition",
            correlation={"request_id": "req-1"},
            source="api",
        )

        assert event["from"] == "executing"
        assert event["to"] == "observing"
        assert event["reason"] == "test transition"
        assert event["source"] == "api"
        assert event["correlation"] == {"request_id": "req-1"}
        assert "at" in event

    def test_build_default_correlation(self):
        """测试构建默认关联上下文"""
        service = LifecycleStateMachineService()

        payload = {
            "execution_id": "exec-1",
            "task_id": "task-1",
            "metadata": {"author": "test"},
        }

        correlation = service.build_default_correlation(payload)

        assert correlation["execution_id"] == "exec-1"
        assert correlation["task_id"] == "task-1"
        assert correlation["metadata"]["author"] == "test"
        assert "trace_id" in correlation

    def test_attach_correlation(self):
        """测试附加关联信息"""
        service = LifecycleStateMachineService()

        contract = {"stage": "new", "metadata": {"existing": "value"}}
        correlation = {
            "execution_id": "exec-1",
            "task_id": "task-1",
            "request_id": "req-1",
            "other_field": "ignored",
        }

        result = service.attach_correlation(contract, correlation)

        assert result["correlation"] == correlation
        assert result["metadata"]["existing"] == "value"
        assert result["metadata"]["execution_id"] == "exec-1"
        assert result["metadata"]["task_id"] == "task-1"
        assert result["metadata"]["request_id"] == "req-1"
        assert "other_field" not in result["metadata"]

    def test_transition_success(self):
        """测试成功转换"""
        service = LifecycleStateMachineService()

        contract = {"stage": "new", "execution_id": "exec-1"}

        result = service.transition(contract, "normalized", reason="test")

        assert result["stage"] == "normalized"
        assert result["execution_id"] == "exec-1"
        assert len(result["stage_history"]) == 1
        assert result["stage_history"][0]["from"] == "new"
        assert result["stage_history"][0]["to"] == "normalized"
        assert result["stage_history"][0]["reason"] == "test"
        assert result["is_terminal"] is False
        assert result["stage_index"] == 1

    def test_transition_invalid(self):
        """测试无效转换"""
        service = LifecycleStateMachineService()

        contract = {"stage": "new"}

        with pytest.raises(ValueError, match="illegal lifecycle transition"):
            service.transition(contract, "executing")

    def test_transition_with_status(self):
        """测试带状态的转换"""
        service = LifecycleStateMachineService()

        contract = {"stage": "new"}

        result = service.transition(contract, "normalized", status="running")

        assert result["status"] == "running"

    def test_transition_to_failure(self):
        """测试转换到失败状态"""
        service = LifecycleStateMachineService()

        contract = {"stage": "executing"}

        result = service.transition(contract, "failed")

        assert result["stage"] == "failed"
        assert result["status"] == "failed"
        assert result["failure_kind"] == "execution_error"
        assert result["is_terminal"] is True

    def test_transition_to_terminal(self):
        """测试转换到终端状态"""
        service = LifecycleStateMachineService()

        contract = {"stage": "promotion_ready"}

        result = service.transition(contract, "promoted")

        assert result["stage"] == "promoted"
        assert result["status"] == "success"
        assert result["is_terminal"] is True


class TestLifecycleToDict:
    """测试生命周期转换为字典"""

    def test_lifecycle_to_dict_basic(self):
        """测试基本转换"""
        service = LifecycleStateMachineService()
        lifecycle = create_lifecycle("exec-1", "task-1", "/test/project")

        result = service.lifecycle_to_dict(lifecycle)

        assert result["contract_id"] == lifecycle.contract_id
        assert result["execution_id"] == "exec-1"
        assert result["task_id"] == "task-1"
        assert result["stage"] == "new"
        assert result["status"] == "pending"
        assert result["is_terminal"] is False
        assert result["stage_index"] == 0

    def test_lifecycle_to_dict_with_history(self):
        """测试带历史记录的转换"""
        service = LifecycleStateMachineService()
        lifecycle = create_lifecycle("exec-1", "task-1", "/test/project")
        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED, reason="test")

        result = service.lifecycle_to_dict(lifecycle)

        assert len(result["stage_history"]) == 1
        assert result["stage_history"][0]["from"] == "new"
        assert result["stage_history"][0]["to"] == "normalized"
        assert result["stage_history"][0]["reason"] == "test"

    def test_lifecycle_to_dict_with_correlation(self):
        """测试带关联信息的转换"""
        service = LifecycleStateMachineService()
        lifecycle = create_lifecycle("exec-1", "task-1", "/test/project")

        result = service.lifecycle_to_dict(lifecycle)

        assert "correlation" in result
        assert result["correlation"]["execution_id"] == "exec-1"
        assert result["correlation"]["task_id"] == "task-1"

    def test_lifecycle_to_dict_with_non_lifecycle_root(self):
        """测试非LifecycleRoot输入"""
        service = LifecycleStateMachineService()

        result = service.lifecycle_to_dict({"stage": "new", "execution_id": "exec-1"})

        assert result["stage"] == "new"
        assert result["execution_id"] == "exec-1"


class TestConstants:
    """测试常量定义"""

    def test_lifecycle_stages_order(self):
        """测试生命周期阶段顺序"""
        stages = list(LIFECYCLE_STAGES)
        
        assert stages.index("new") == 0
        assert stages.index("executing") == 5
        assert stages.index("promoted") == 14

    def test_terminal_stages(self):
        """测试终端阶段"""
        assert "promoted" in TERMINAL_STAGES
        assert "failed" in TERMINAL_STAGES
        assert "aborted" in TERMINAL_STAGES
        assert "cancelled" in TERMINAL_STAGES

    def test_failure_stages(self):
        """测试失败阶段"""
        assert "failed" in FAILURE_STAGES
        assert "aborted" in FAILURE_STAGES
        assert "cancelled" in FAILURE_STAGES

    def test_recovery_stages(self):
        """测试恢复阶段"""
        assert "repairing" in RECOVERY_STAGES
        assert "verifying" in RECOVERY_STAGES

    def test_stage_transitions_coverage(self):
        """测试阶段转换覆盖所有阶段"""
        for stage in LIFECYCLE_STAGES:
            assert stage in STAGE_TRANSITIONS, f"Missing transitions for stage: {stage}"

    def test_recovery_targets_coverage(self):
        """测试恢复目标覆盖 - 部分阶段不在恢复目标中"""
        covered_stages = {
            "executing", "observing", "diagnosed", "repairing", "verifying",
            "delivering", "runtime_linked", "governing", "promotion_ready", "failed"
        }
        for stage in covered_stages:
            assert stage in RECOVERY_TARGETS, f"Missing recovery target for stage: {stage}"

    def test_failure_kind_by_stage(self):
        """测试失败类型定义"""
        assert FAILURE_KIND_BY_STAGE["executing"] == "execution_error"
        assert FAILURE_KIND_BY_STAGE["verifying"] == "verification_error"
        assert FAILURE_KIND_BY_STAGE["new"] == ""
        assert FAILURE_KIND_BY_STAGE["promoted"] == ""
