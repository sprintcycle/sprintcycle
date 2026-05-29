"""LifecycleStateMachineService 测试 - 覆盖状态机服务的核心方法"""

from __future__ import annotations

import pytest

from sprintcycle.domain.core.lifecycle.state_machine import (
    LifecycleStateMachine,
    get_lifecycle_state_machine,
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
    LifecycleStatus,
    create_lifecycle,
)
from sprintcycle.domain.core.lifecycle.state_machine import LifecycleSubstage
from sprintcycle.domain.core.lifecycle.values import CorrelationContext


class TestLifecycleStateMachineBasic:
    """测试状态机的基本方法"""

    def test_machine_initialization(self):
        """测试状态机初始化"""
        machine = LifecycleStateMachine()
        
        assert machine is not None
        assert machine.STAGES == LIFECYCLE_STAGES
        assert machine.TERMINAL_STAGES == TERMINAL_STAGES
        assert machine.TRANSITIONS == STAGE_TRANSITIONS
        assert machine.RECOVERY_TARGETS == RECOVERY_TARGETS

    def test_singleton_machine(self):
        """测试单例状态机"""
        machine1 = get_lifecycle_state_machine()
        machine2 = get_lifecycle_state_machine()
        
        assert machine1 is machine2

    def test_normalize_stage(self):
        """测试阶段规范化"""
        machine = LifecycleStateMachine()

        assert machine.normalize_stage("NEW") == "new"
        assert machine.normalize_stage("Running") == "running"
        assert machine.normalize_stage("  OBSERVING  ") == "observing"
        assert machine.normalize_stage(LifecycleSubstage.NEW) == "new"
        assert machine.normalize_stage(LifecycleSubstage.RUNNING) == "running"
        assert machine.normalize_stage("unknown") == "new"
        assert machine.normalize_stage(None) == "new"
        assert machine.normalize_stage("") == "new"

    def test_can_transition(self):
        """测试转换检查"""
        machine = LifecycleStateMachine()

        assert machine.can_transition("new", "normalized") is True
        assert machine.can_transition("new", "running") is False
        assert machine.can_transition("running", "observing") is True
        assert machine.can_transition("promoted", "governing") is False
        assert machine.can_transition("failed", "repairing") is True
        assert machine.can_transition("repairing", "verifying") is True

    def test_can_transition_same_stage(self):
        """测试相同阶段转换（noop）"""
        machine = LifecycleStateMachine()

        assert machine.can_transition("new", "new") is True
        assert machine.can_transition("running", "running") is True

    def test_validate_transition(self):
        """测试转换验证 - 空字符串被规范化为new"""
        machine = LifecycleStateMachine()

        assert machine.validate_transition("new", "normalized") is None
        assert machine.validate_transition("new", "running") == "illegal lifecycle transition: new -> running"
        assert machine.validate_transition("", "normalized") is None  # empty normalized to new
        assert machine.validate_transition("new", "") is None  # empty normalized to new

    def test_next_stages(self):
        """测试获取下一阶段"""
        machine = LifecycleStateMachine()

        assert machine.next_stages("new") == ("normalized", "failed", "cancelled")
        assert machine.next_stages("running") == ("observing", "diagnosed", "repairing", "failed", "cancelled")
        assert machine.next_stages("promoted") == ()
        assert machine.next_stages(LifecycleSubstage.NEW) == ("normalized", "failed", "cancelled")

    def test_stage_index(self):
        """测试阶段索引"""
        machine = LifecycleStateMachine()

        assert machine.stage_index("new") == 0
        assert machine.stage_index("running") == 4
        assert machine.stage_index("promoted") == 13
        assert machine.stage_index("unknown") == 0  # unknown is normalized to new
        assert machine.stage_index(LifecycleSubstage.RUNNING) == 4

    def test_is_terminal(self):
        """测试终端状态判断"""
        machine = LifecycleStateMachine()

        assert machine.is_terminal("promoted") is True
        assert machine.is_terminal("failed") is True
        assert machine.is_terminal("aborted") is True
        assert machine.is_terminal("cancelled") is True
        assert machine.is_terminal("running") is False
        assert machine.is_terminal("governing") is False
        assert machine.is_terminal(LifecycleSubstage.PROMOTED) is True

    def test_is_failure(self):
        """测试失败状态判断"""
        machine = LifecycleStateMachine()

        assert machine.is_failure("failed") is True
        assert machine.is_failure("aborted") is True
        assert machine.is_failure("cancelled") is True
        assert machine.is_failure("running") is False
        assert machine.is_failure("repairing") is False

    def test_is_recovery(self):
        """测试恢复状态判断"""
        machine = LifecycleStateMachine()

        assert machine.is_recovery("repairing") is True
        assert machine.is_recovery("verifying") is True
        assert machine.is_recovery("running") is False
        assert machine.is_recovery("observing") is False

    def test_get_recovery_target(self):
        """测试获取恢复目标"""
        machine = LifecycleStateMachine()

        assert machine.get_recovery_target("running") == "repairing"
        assert machine.get_recovery_target("observing") == "repairing"
        assert machine.get_recovery_target("diagnosed") == "repairing"
        assert machine.get_recovery_target("repairing") == "verifying"
        assert machine.get_recovery_target("verifying") == "observing"
        assert machine.get_recovery_target("failed") == "repairing"
        assert machine.get_recovery_target("unknown") == "repairing"  # default
        assert machine.get_recovery_target(LifecycleSubstage.RUNNING) == "repairing"

    def test_get_failure_kind(self):
        """测试获取失败类型"""
        machine = LifecycleStateMachine()

        assert machine.get_failure_kind("running") == "execution_error"
        assert machine.get_failure_kind("observing") == "observation_error"
        assert machine.get_failure_kind("diagnosed") == "diagnosis_error"
        assert machine.get_failure_kind("repairing") == "repair_error"
        assert machine.get_failure_kind("verifying") == "verification_error"
        assert machine.get_failure_kind("delivering") == "delivery_error"
        assert machine.get_failure_kind("new") == ""
        assert machine.get_failure_kind("promoted") == ""
        assert machine.get_failure_kind(LifecycleSubstage.RUNNING) == "execution_error"

    def test_get_allowed_next_stages(self):
        """测试获取允许的下一阶段（排除失败状态）"""
        machine = LifecycleStateMachine()

        assert machine.get_allowed_next_stages("new") == ["normalized"]
        assert machine.get_allowed_next_stages("running") == ["observing", "diagnosed", "repairing"]
        assert machine.get_allowed_next_stages("promoted") == []


class TestTransitionMethods:
    """测试转换相关方法"""

    def test_build_transition_event(self):
        """测试构建转换事件"""
        machine = LifecycleStateMachine()

        event = machine.build_transition_event(
            from_stage="running",
            to_stage="observing",
            reason="test transition",
            correlation={"request_id": "req-1"},
            source="api",
        )

        assert event["from"] == "running"
        assert event["to"] == "observing"
        assert event["reason"] == "test transition"
        assert event["source"] == "api"
        assert event["correlation"] == {"request_id": "req-1"}
        assert "at" in event

    def test_build_default_correlation(self):
        """测试构建默认关联上下文"""
        machine = LifecycleStateMachine()

        payload = {
            "execution_id": "exec-1",
            "task_id": "task-1",
            "metadata": {"author": "test"},
        }

        correlation = machine.build_default_correlation(payload)

        assert correlation["execution_id"] == "exec-1"
        assert correlation["task_id"] == "task-1"
        assert correlation["metadata"]["author"] == "test"
        assert "trace_id" in correlation

    def test_attach_correlation(self):
        """测试附加关联信息"""
        machine = LifecycleStateMachine()
    
        contract = {"stage": "new", "metadata": {"existing": "value"}}
        correlation = {
            "execution_id": "exec-1",
            "task_id": "task-1",
            "request_id": "req-1",
            "other_field": "ignored",
        }
    
        result = machine.attach_correlation(contract, correlation)
    
        assert result["correlation"]["execution_id"] == "exec-1"
        assert result["correlation"]["task_id"] == "task-1"
        assert result["correlation"]["request_id"] == "req-1"
        assert result["metadata"]["existing"] == "value"
        assert result["metadata"]["execution_id"] == "exec-1"
        assert result["metadata"]["task_id"] == "task-1"
        assert result["metadata"]["request_id"] == "req-1"
        assert "other_field" not in result["metadata"]

    def test_transition_success(self):
        """测试成功转换"""
        machine = LifecycleStateMachine()

        contract = {"stage": "new", "execution_id": "exec-1"}

        result = machine.transition(contract, "normalized", reason="test")

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
        machine = LifecycleStateMachine()

        contract = {"stage": "new"}

        with pytest.raises(ValueError, match="illegal lifecycle transition"):
            machine.transition(contract, "running")

    def test_transition_with_status(self):
        """测试带状态的转换"""
        machine = LifecycleStateMachine()

        contract = {"stage": "new"}

        result = machine.transition(contract, "normalized", status="running")

        assert result["status"] == "running"

    def test_transition_to_failure(self):
        """测试转换到失败状态"""
        machine = LifecycleStateMachine()

        contract = {"stage": "running"}

        result = machine.transition(contract, "failed")

        assert result["stage"] == "failed"
        assert result["status"] == "failed"
        assert result["failure_kind"] == "execution_error"
        assert result["is_terminal"] is True

    def test_transition_to_terminal(self):
        """测试转换到终端状态"""
        machine = LifecycleStateMachine()

        contract = {"stage": "promotion_ready"}

        result = machine.transition(contract, "promoted")

        assert result["stage"] == "promoted"
        assert result["status"] == "success"
        assert result["is_terminal"] is True


class TestLifecycleToDict:
    """测试生命周期转换为字典"""

    def test_lifecycle_to_dict_basic(self):
        """测试基本转换"""
        lifecycle = create_lifecycle("exec-1", "task-1", "/test/project")

        result = lifecycle.to_dict()

        assert result["contract_id"] == lifecycle.contract_id
        assert result["execution_id"] == "exec-1"
        assert result["task_id"] == "task-1"
        assert result["substage"] == "new"
        assert result["phase"] == "initializing"
        assert result["status"] == "pending"
        assert result["is_terminal"] is False
        assert result["stage_index"] == 0

    def test_lifecycle_to_dict_with_history(self):
        """测试带历史记录的转换"""
        lifecycle = create_lifecycle("exec-1", "task-1", "/test/project")
        lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.NORMALIZED, reason="test")

        result = lifecycle.to_dict()

        assert len(result["stage_history"]) == 1
        assert result["stage_history"][0]["from"] == "new"
        assert result["stage_history"][0]["to"] == "normalized"
        assert result["stage_history"][0]["reason"] == "test"

    def test_lifecycle_to_dict_with_correlation(self):
        """测试带关联信息的转换"""
        lifecycle = create_lifecycle("exec-1", "task-1", "/test/project")

        result = lifecycle.to_dict()

        assert "correlation" in result
        assert result["correlation"]["execution_id"] == "exec-1"
        assert result["correlation"]["task_id"] == "task-1"

class TestConstants:
    """测试常量定义"""

    def test_lifecycle_stages_order(self):
        """测试生命周期阶段顺序"""
        stages = list(LIFECYCLE_STAGES)
        
        assert stages.index("new") == 0
        assert stages.index("running") == 4
        assert stages.index("promoted") == 13

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
            "running", "observing", "diagnosed", "repairing", "verifying",
            "delivering", "runtime_linked", "governing", "promotion_ready", "failed"
        }
        for stage in covered_stages:
            assert stage in RECOVERY_TARGETS, f"Missing recovery target for stage: {stage}"

    def test_failure_kind_by_stage(self):
        """测试失败类型定义"""
        assert FAILURE_KIND_BY_STAGE["running"] == "execution_error"
        assert FAILURE_KIND_BY_STAGE["verifying"] == "verification_error"
        assert FAILURE_KIND_BY_STAGE["new"] == ""
        assert FAILURE_KIND_BY_STAGE["promoted"] == ""
