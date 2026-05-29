"""契约状态机测试 - 覆盖核心生命周期转换逻辑"""

from __future__ import annotations

import pytest

from sprintcycle.domain.core.lifecycle.state_machine import (
    LifecycleStateMachine,
    LIFECYCLE_STAGES,
    STAGE_TRANSITIONS,
    TERMINAL_STAGES,
)
from sprintcycle.domain.core.governance.promotion_policy import PromotionPolicy


class TestLifecycleStateTransitions:
    """测试状态转换的合法性"""

    def test_valid_transition_chain(self):
        """测试完整的合法状态转换链"""
        machine = LifecycleStateMachine()
        contract = {"stage": "new"}

        transitions = [
            ("new", "normalized"),
            ("normalized", "planned"),
            ("planned", "decomposed"),
            ("decomposed", "running"),
            ("running", "observing"),
            ("observing", "delivering"),
            ("delivering", "runtime_linked"),
            ("runtime_linked", "governing"),
            ("governing", "promotion_ready"),
            ("promotion_ready", "promoted"),
        ]

        for from_stage, to_stage in transitions:
            result = machine.transition(contract, to_stage)
            assert result["stage"] == to_stage
            assert result["stage_history"]
            contract = result

    def test_all_valid_transitions(self):
        """验证STAGE_TRANSITIONS中定义的所有转换都是合法的"""
        machine = LifecycleStateMachine()

        for from_stage, allowed_stages in STAGE_TRANSITIONS.items():
            for to_stage in allowed_stages:
                assert machine.can_transition(from_stage, to_stage), \
                    f"Expected {from_stage} -> {to_stage} to be valid"

    def test_terminal_stages_cannot_transition(self):
        """测试终端状态不能转换到其他状态"""
        machine = LifecycleStateMachine()

        for terminal_stage in TERMINAL_STAGES:
            if terminal_stage == "failed":
                continue
            for other_stage in LIFECYCLE_STAGES:
                if other_stage != terminal_stage:
                    assert not machine.can_transition(terminal_stage, other_stage), \
                        f"Terminal stage {terminal_stage} should not transition to {other_stage}"

    def test_failed_can_recover_to_repairing(self):
        """测试失败状态可以转换到修复状态"""
        machine = LifecycleStateMachine()
        assert machine.can_transition("failed", "repairing")

        contract = {"stage": "failed"}
        result = machine.transition(contract, "repairing")
        assert result["stage"] == "repairing"


class TestInvalidTransitions:
    """测试非法状态转换的拒绝"""

    def test_invalid_transition_raises_error(self):
        """测试非法转换应该抛出ValueError"""
        machine = LifecycleStateMachine()
        contract = {"stage": "new"}

        invalid_transitions = [
            ("new", "running"),
            ("normalized", "delivering"),
            ("running", "planned"),
            ("promoted", "governing"),
        ]

        for from_stage, to_stage in invalid_transitions:
            contract["stage"] = from_stage
            with pytest.raises(ValueError, match=f"illegal lifecycle transition"):
                machine.transition(contract, to_stage)

    def test_validate_transition_returns_error_message(self):
        """测试validate_transition方法返回正确的错误消息"""
        machine = LifecycleStateMachine()

        result = machine.validate_transition("new", "running")
        assert result == "illegal lifecycle transition: new -> running"

        result = machine.validate_transition("new", "normalized")
        assert result is None

    def test_empty_stage_validation(self):
        """测试空状态的验证 - 空字符串被规范化为 'new'"""
        machine = LifecycleStateMachine()

        result = machine.validate_transition("", "normalized")
        assert result is None

        result = machine.validate_transition("new", "")
        assert result is None


class TestPromotionPolicy:
    """测试promotion policy触发条件"""

    def test_promotion_passes_with_all_requirements_met(self):
        """测试所有条件满足时promotion通过"""
        policy = PromotionPolicy(min_score=70)

        contract = {
            "evaluation_refs": {"score_card": {"total": 85}},
            "validation_refs": {"final_snapshot": True},
            "evidence": {"stages": {"repair": {"closed_loop": True}}},
        }
        runtime = {"healthy": True}
        governance = {"approved": True}
        evidence = {"contract": {"normalized": True}}

        result = policy.evaluate(contract, runtime=runtime, governance=governance, evidence=evidence)

        assert result["allowed"] is True
        assert result["passed"] is True
        assert result["status"] == "promotable"
        assert result["score"] == 85
        assert len(result["reasons"]) == 0

    def test_promotion_fails_with_insufficient_score(self):
        """测试分数不足时promotion失败"""
        policy = PromotionPolicy(min_score=70)

        contract = {
            "evaluation_refs": {"score_card": {"total": 65}},
            "validation_refs": {"final_snapshot": True},
            "evidence": {"stages": {"repair": {"closed_loop": True}}},
        }
        runtime = {"healthy": True}
        governance = {"approved": True}
        evidence = {"contract": {"normalized": True}}

        result = policy.evaluate(contract, runtime=runtime, governance=governance, evidence=evidence)

        assert result["allowed"] is False
        assert result["passed"] is False
        assert result["status"] == "blocked"
        assert "insufficient_score" in result["reasons"]

    def test_promotion_fails_with_unhealthy_runtime(self):
        """测试运行时不健康时promotion失败"""
        policy = PromotionPolicy(min_score=70)

        contract = {
            "evaluation_refs": {"score_card": {"total": 80}},
            "validation_refs": {"final_snapshot": True},
            "evidence": {"stages": {"repair": {"closed_loop": True}}},
        }
        runtime = {"healthy": False}
        governance = {"approved": True}
        evidence = {"contract": {"normalized": True}}

        result = policy.evaluate(contract, runtime=runtime, governance=governance, evidence=evidence)

        assert result["allowed"] is False
        assert "runtime_not_healthy" in result["reasons"]

    def test_promotion_fails_with_unapproved_governance(self):
        """测试治理未批准时promotion失败"""
        policy = PromotionPolicy(min_score=70)

        contract = {
            "evaluation_refs": {"score_card": {"total": 80}},
            "validation_refs": {"final_snapshot": True},
            "evidence": {"stages": {"repair": {"closed_loop": True}}},
        }
        runtime = {"healthy": True}
        governance = {"approved": False}
        evidence = {"contract": {"normalized": True}}

        result = policy.evaluate(contract, runtime=runtime, governance=governance, evidence=evidence)

        assert result["allowed"] is False
        assert "governance_not_approved" in result["reasons"]

    def test_promotion_missing_final_snapshot_records_reason(self):
        """测试缺少最终快照时记录原因但不影响通过"""
        policy = PromotionPolicy(min_score=70)

        contract = {
            "evaluation_refs": {"score_card": {"total": 80}},
            "validation_refs": {},
            "evidence": {"stages": {"repair": {"closed_loop": True}}},
        }
        runtime = {"healthy": True}
        governance = {"approved": True}
        evidence = {"contract": {"normalized": True}}

        result = policy.evaluate(contract, runtime=runtime, governance=governance, evidence=evidence)

        assert result["allowed"] is True
        assert "missing_final_snapshot" in result["reasons"]

    def test_promotion_missing_stage_history_records_reason(self):
        """测试缺少阶段历史时记录原因但不影响通过"""
        policy = PromotionPolicy(min_score=70)

        contract = {
            "evaluation_refs": {"score_card": {"total": 80}},
            "validation_refs": {"final_snapshot": True},
            "evidence": {"stages": {}},
        }
        runtime = {"healthy": True}
        governance = {"approved": True}
        evidence = {"contract": {"normalized": True}}

        result = policy.evaluate(contract, runtime=runtime, governance=governance, evidence=evidence)

        assert result["allowed"] is True
        assert "missing_stage_history" in result["reasons"]

    def test_promotion_with_completion_score_fallback(self):
        """测试使用completion_score作为备选分数"""
        policy = PromotionPolicy(min_score=70)

        contract = {
            "completion_score": 75,
            "validation_refs": {"final_snapshot": True},
            "evidence": {"stages": {"repair": {"closed_loop": True}}},
        }
        runtime = {"healthy": True}
        governance = {"approved": True}
        evidence = {"contract": {"normalized": True}}

        result = policy.evaluate(contract, runtime=runtime, governance=governance, evidence=evidence)

        assert result["allowed"] is True
        assert result["score"] == 75


class TestStateMachineHelpers:
    """测试状态机辅助方法"""

    def test_normalize_stage(self):
        """测试阶段名称规范化"""
        machine = LifecycleStateMachine()

        assert machine.normalize_stage("NEW") == "new"
        assert machine.normalize_stage("Running") == "running"
        assert machine.normalize_stage("  OBSERVING  ") == "observing"
        assert machine.normalize_stage("unknown") == "new"
        assert machine.normalize_stage(None) == "new"

    def test_next_stages(self):
        """测试获取下一阶段列表"""
        machine = LifecycleStateMachine()

        assert machine.next_stages("new") == ("normalized", "failed", "cancelled")
        assert machine.next_stages("promoted") == ()

    def test_stage_index(self):
        """测试阶段索引获取 - unknown被规范化为new"""
        machine = LifecycleStateMachine()

        assert machine.stage_index("new") == 0
        assert machine.stage_index("running") == 4
        assert machine.stage_index("promoted") == 13
        assert machine.stage_index("unknown") == 0

    def test_is_terminal(self):
        """测试终端状态判断"""
        machine = LifecycleStateMachine()

        assert machine.is_terminal("promoted") is True
        assert machine.is_terminal("failed") is True
        assert machine.is_terminal("aborted") is True
        assert machine.is_terminal("cancelled") is True
        assert machine.is_terminal("running") is False
        assert machine.is_terminal("governing") is False

    def test_failure_to_recovery_target(self):
        """测试失败状态到恢复目标的映射"""
        machine = LifecycleStateMachine()

        assert machine.get_recovery_target("running") == "repairing"
        assert machine.get_recovery_target("observing") == "repairing"
        assert machine.get_recovery_target("diagnosed") == "repairing"
        assert machine.get_recovery_target("delivering") == "repairing"
        assert machine.get_recovery_target("promoted") == "repairing"
