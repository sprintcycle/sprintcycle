"""
Tests for SprintCycle Integrations Module - 集成模块测试
"""

import pytest
from unittest.mock import MagicMock, patch
from sprintcycle.integrations import (
    SprintEvolutionIntegration,
    EvolutionTrigger,
)


class TestEvolutionTrigger:
    """EvolutionTrigger 测试"""

    def test_trigger_construction(self):
        """测试触发器构造"""
        trigger = EvolutionTrigger(
            name="test_trigger",
            condition="metric > threshold",
        )
        assert trigger.name == "test_trigger"
        assert trigger.condition == "metric > threshold"
        assert trigger.enabled is True

    def test_trigger_with_threshold(self):
        """测试带阈值的触发器"""
        trigger = EvolutionTrigger(
            name="coverage_trigger",
            condition="coverage < 80",
            threshold={"coverage": 80},
        )
        assert trigger.threshold["coverage"] == 80

    def test_evaluate_empty_condition(self):
        """测试空条件评估"""
        trigger = EvolutionTrigger(name="empty", condition="")
        assert trigger.evaluate({}) is False

    def test_evaluate_with_metrics(self):
        """测试带指标的评估"""
        trigger = EvolutionTrigger(name="test", condition="value > 0")
        result = trigger.evaluate({"value": 10})
        assert isinstance(result, bool)


class TestSprintEvolutionIntegration:
    """SprintEvolutionIntegration 测试"""

    def test_integration_init(self):
        """测试集成器初始化"""
        integration = SprintEvolutionIntegration()
        assert integration.config is not None
        assert integration.evolution_history == []

    def test_integration_init_with_config(self):
        """测试带配置的初始化"""
        from sprintcycle.config.runtime_config import RuntimeConfig
        config = RuntimeConfig(max_sprints=5)
        integration = SprintEvolutionIntegration(config=config)
        assert integration.config.max_sprints == 5

    def test_get_evolution_status(self):
        """测试获取进化状态"""
        integration = SprintEvolutionIntegration()
        status = integration.get_evolution_status()
        assert "history_count" in status
        assert status["history_count"] == 0

    def test_trigger_after_sprint(self):
        """测试Sprint后触发"""
        integration = SprintEvolutionIntegration()
        metrics = {"sprint_number": 1, "success_rate": 0.8}
        result = integration.trigger_after_sprint(metrics, targets=[])
        assert "evolved" in result
        assert "history_count" in result

    def test_multiple_triggers(self):
        """测试多次触发"""
        integration = SprintEvolutionIntegration()
        metrics = {"sprint_number": 1}
        integration.trigger_after_sprint(metrics, targets=[])
        integration.trigger_after_sprint(metrics, targets=[])
        assert integration.get_evolution_status()["history_count"] == 0

    def test_repr(self):
        """测试字符串表示"""
        integration = SprintEvolutionIntegration()
        assert "SprintEvolutionIntegration" in repr(integration)
