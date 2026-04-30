"""
SprintCycle Integrations 模块测试
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any, Optional

from sprintcycle.integrations import (
    SprintEvolutionIntegration,
    EvolutionTrigger,
)


class TestEvolutionTrigger:
    """EvolutionTrigger 数据类测试"""

    def test_construction_basic(self):
        """测试基本构造"""
        trigger = EvolutionTrigger(
            name="low_success_rate",
            condition="success_rate < 0.5",
        )
        assert trigger.name == "low_success_rate"
        assert trigger.condition == "success_rate < 0.5"
        assert trigger.threshold is None

    def test_construction_with_threshold(self):
        """测试带阈值的构造"""
        threshold = {"success_rate": 0.5, "avg_duration": 60}
        trigger = EvolutionTrigger(
            name="performance_degradation",
            condition="avg_duration > threshold",
            threshold=threshold,
        )
        assert trigger.threshold == threshold
        assert trigger.threshold["success_rate"] == 0.5

    def test_construction_empty_condition(self):
        """测试空条件"""
        trigger = EvolutionTrigger(
            name="always_trigger",
            condition="",
        )
        assert trigger.condition == ""


class TestSprintEvolutionIntegration:
    """SprintEvolutionIntegration 测试"""

    @pytest.fixture
    def integration(self):
        """创建测试集成实例"""
        return SprintEvolutionIntegration()

    def test_init_default(self):
        """测试默认初始化"""
        integration = SprintEvolutionIntegration()
        assert integration.config is not None
        assert integration.evolution_history == []

    def test_init_with_config(self):
        """测试带配置的初始化"""
        from sprintcycle.config import RuntimeConfig
        
        config = RuntimeConfig(max_sprints=5)
        integration = SprintEvolutionIntegration(config=config)
        
        assert integration.config == config
        assert integration.config.max_sprints == 5

    def test_default_targets(self):
        """测试默认目标路径"""
        assert SprintEvolutionIntegration.DEFAULT_TARGETS is not None
        assert len(SprintEvolutionIntegration.DEFAULT_TARGETS) == 2
        assert "sprintcycle/config/" in SprintEvolutionIntegration.DEFAULT_TARGETS
        assert "sprintcycle/evolution/" in SprintEvolutionIntegration.DEFAULT_TARGETS

    def test_get_evolution_status_empty(self, integration):
        """测试空状态获取"""
        status = integration.get_evolution_status()
        
        assert "history_count" in status
        assert status["history_count"] == 0

    def test_get_evolution_status_with_history(self, integration):
        """测试有历史记录的状态获取"""
        # 添加一些模拟历史记录
        integration.evolution_history = [
            {"target": "module1", "success": True, "sprint_number": 1},
            {"target": "module2", "success": False, "sprint_number": 2},
        ]
        
        status = integration.get_evolution_status()
        assert status["history_count"] == 2

    def test_trigger_after_sprint_empty_targets(self, integration):
        """测试不存在的目标路径"""
        metrics = {"sprint_number": 1}
        result = integration.trigger_after_sprint(
            sprint_metrics=metrics,
            targets=["non_existent_path"],
        )
        
        assert result["evolved"] == 0
        assert result["history_count"] == 0

    def test_trigger_after_sprint_with_valid_targets(self, integration):
        """测试有效的目标路径"""
        # 使用存在的路径
        metrics = {"sprint_number": 1}
        result = integration.trigger_after_sprint(
            sprint_metrics=metrics,
            targets=["sprintcycle/config/", "sprintcycle/evolution/"],
        )
        
        # 应该尝试进化这些路径
        assert "evolved" in result
        assert "history_count" in result

    def test_trigger_after_sprint_sprint_number(self, integration):
        """测试sprint编号传递"""
        metrics = {"sprint_number": 5}
        result = integration.trigger_after_sprint(
            sprint_metrics=metrics,
            targets=[],  # 空目标，不实际执行
        )
        
        assert result["history_count"] == 0

    def test_evolution_history_structure(self, integration):
        """测试历史记录结构"""
        # 添加一条模拟历史
        integration.evolution_history.append({
            "target": "test_module",
            "success": True,
            "sprint_number": 1,
            "timestamp": "2024-01-01T00:00:00",
        })
        
        record = integration.evolution_history[0]
        assert "target" in record
        assert "success" in record
        assert "sprint_number" in record
        assert "timestamp" in record

    def test_multiple_triggers_accumulate_history(self, integration):
        """测试多次触发累积历史"""
        metrics1 = {"sprint_number": 1}
        metrics2 = {"sprint_number": 2}
        
        # 第一次触发
        integration.trigger_after_sprint(metrics1, targets=[])
        assert len(integration.evolution_history) == 0
        
        # 第二次触发
        integration.trigger_after_sprint(metrics2, targets=[])
        assert len(integration.evolution_history) == 0

    def test_config_attribute_access(self, integration):
        """测试配置属性访问"""
        # RuntimeConfig 有默认属性
        assert hasattr(integration.config, "max_sprints")
        assert hasattr(integration.config, "evolution_enabled")

    def test_evolution_integration_repr(self, integration):
        """测试集成对象字符串表示"""
        repr_str = repr(integration)
        assert "SprintEvolutionIntegration" in repr_str

    def test_history_count_after_empty_triggers(self, integration):
        """测试空触发后历史计数"""
        # 触发但没有有效目标
        integration.trigger_after_sprint(
            {"sprint_number": 1},
            targets=["definitely_does_not_exist_12345"],
        )
        
        assert integration.get_evolution_status()["history_count"] == 0

    def test_sprint_metrics_empty_dict(self, integration):
        """测试空sprint_metrics"""
        # 不提供sprint_number时应该使用默认值
        result = integration.trigger_after_sprint(sprint_metrics={})
        assert "evolved" in result

    def test_integration_with_custom_targets(self, integration):
        """测试自定义目标列表"""
        custom_targets = ["sprintcycle/config/"]
        result = integration.trigger_after_sprint(
            {"sprint_number": 10},
            targets=custom_targets,
        )
        
        assert "evolved" in result
        assert isinstance(result["evolved"], int)
