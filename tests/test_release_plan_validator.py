"""
ReleasePlan 验证器单元测试
"""

import pytest

from sprintcycle.release_plan.validator import ReleasePlanValidator, ValidationResult
from sprintcycle.release_plan.models import (
    ReleasePlan,
    ProductAnchor,
    SprintDefinition,
    SprintBacklogItem,
    ExecutionMode,
    EvolutionParams,
)


class TestReleasePlanValidator:
    """ReleasePlan 验证器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.validator = ReleasePlanValidator()
    
    def test_validate_valid_release_plan(self):
        """测试验证有效 ReleasePlan"""
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    goals=["完成开发"],
                    tasks=[
                        SprintBacklogItem(description="实现功能", agent="coder", target="src/main.py"),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(plan)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_missing_project_name(self):
        """测试验证缺少项目名"""
        plan = ReleasePlan(
            project=ProductAnchor(name="", path="/root/test"),
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    tasks=[
                        SprintBacklogItem(description="实现功能", agent="coder"),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(plan)
        assert not result.is_valid
        assert any("name" in err.lower() for err in result.errors)
    
    def test_validate_evolution_mode_missing_evolution(self):
        """测试验证自进化模式缺少配置"""
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            mode=ExecutionMode.EVOLUTION,
            evolution=None,
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    tasks=[
                        SprintBacklogItem(description="进化相关编码任务", agent="coder"),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(plan)
        assert not result.is_valid
        assert any("evolution" in err.lower() for err in result.errors)
    
    def test_validate_missing_sprints(self):
        """测试验证缺少 sprints"""
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            sprints=[],
        )
        
        result = self.validator.validate(plan)
        assert not result.is_valid
        assert any("sprint" in err.lower() for err in result.errors)
    
    def test_validate_invalid_agent_type(self):
        """测试验证无效 Agent 类型"""
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    tasks=[
                        SprintBacklogItem(description="实现功能", agent="invalid"),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(plan)
        assert not result.is_valid
        assert any("agent" in err.lower() for err in result.errors)
    
    def test_validate_invalid_timeout(self):
        """测试验证无效超时时间"""
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    tasks=[
                        SprintBacklogItem(description="实现功能", agent="coder", timeout=0),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(plan)
        assert not result.is_valid
        assert any("timeout" in err.lower() for err in result.errors)

    def test_evolution_mode_empty_sprints_with_targets_valid(self):
        """自进化 + targets 时允许 sprints 为空（执行前展开）。"""
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            mode=ExecutionMode.EVOLUTION,
            evolution=EvolutionParams(targets=["src/a.py"], goals=["优化"]),
            sprints=[],
        )
        result = self.validator.validate(plan)
        assert result.is_valid
        assert any("展开" in w for w in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
