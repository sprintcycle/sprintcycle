"""
PRD 验证器单元测试
"""

import pytest

from sprintcycle.prd.validator import PRDValidator, ValidationResult
from sprintcycle.prd.models import (
    PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode
)


class TestPRDValidator:
    """PRD 验证器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.validator = PRDValidator()
    
    def test_validate_valid_prd(self):
        """测试验证有效 PRD"""
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
            sprints=[
                PRDSprint(
                    name="Sprint 1",
                    goals=["完成开发"],
                    tasks=[
                        PRDTask(task="实现功能", agent="coder", target="src/main.py"),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(prd)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_missing_project_name(self):
        """测试验证缺少项目名"""
        prd = PRD(
            project=PRDProject(name="", path="/root/test"),
            sprints=[
                PRDSprint(
                    name="Sprint 1",
                    tasks=[
                        PRDTask(task="实现功能", agent="coder"),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(prd)
        assert not result.is_valid
        assert any("name" in err.lower() for err in result.errors)
    
    def test_validate_evolution_mode_missing_evolution(self):
        """测试验证自进化模式缺少配置"""
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
            mode=ExecutionMode.EVOLUTION,
            evolution=None,
            sprints=[
                PRDSprint(
                    name="Sprint 1",
                    tasks=[
                        PRDTask(task="进化", agent="evolver"),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(prd)
        assert not result.is_valid
        assert any("evolution" in err.lower() for err in result.errors)
    
    def test_validate_missing_sprints(self):
        """测试验证缺少 sprints"""
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
            sprints=[],
        )
        
        result = self.validator.validate(prd)
        assert not result.is_valid
        assert any("sprint" in err.lower() for err in result.errors)
    
    def test_validate_invalid_agent_type(self):
        """测试验证无效 Agent 类型"""
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
            sprints=[
                PRDSprint(
                    name="Sprint 1",
                    tasks=[
                        PRDTask(task="实现功能", agent="invalid"),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(prd)
        assert not result.is_valid
        assert any("agent" in err.lower() for err in result.errors)
    
    def test_validate_invalid_timeout(self):
        """测试验证无效超时时间"""
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
            sprints=[
                PRDSprint(
                    name="Sprint 1",
                    tasks=[
                        PRDTask(task="实现功能", agent="coder", timeout=0),
                    ]
                ),
            ]
        )
        
        result = self.validator.validate(prd)
        assert not result.is_valid
        assert any("timeout" in err.lower() for err in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
