"""SprintCycle 核心模块测试"""
import sys
import pytest
from pathlib import Path
sys.path.insert(0, "/root/sprintcycle")


def test_models():
    """测试数据模型"""
    from sprintcycle.models import (
        Sprint, SprintStatus, 
        Task, TaskStatus,
        Project, Report
    )
    
    # Sprint 模型
    sprint = Sprint(index=0, name="Test", goals=["g1"])
    assert sprint.status == SprintStatus.PLANNED
    assert sprint.name == "Test"
    print("✅ Sprint模型")
    
    # Task 模型
    task = Task(id="t1", name="Test Task")
    assert task.status == TaskStatus.PENDING
    assert task.name == "Test Task"
    print("✅ Task模型")
    
    # Project 模型
    project = Project(name="Test Project")
    assert project.name == "Test Project"
    print("✅ Project模型")


def test_enums():
    """测试枚举定义"""
    from sprintcycle.models import (
        AgentType, TaskStatus, SprintStatus,
        ReviewSeverity, IssueSeverity, IssueType, HealthStatus
    )
    
    # AgentType
    assert AgentType.CODER.value == "coder"
    assert AgentType.REVIEWER.value == "reviewer"
    
    # TaskStatus
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    
    # SprintStatus
    assert SprintStatus.PLANNED.value == "planned"
    assert SprintStatus.IN_PROGRESS.value == "in_progress"
    
    print("✅ 枚举定义")


def test_knowledge_base():
    """测试知识库功能"""
    from sprintcycle.chorus import KnowledgeBase
    
    kb = KnowledgeBase("/tmp/test_kb.json")
    stats = kb.get_stats()
    assert stats["total"] == 0
    print("✅ KnowledgeBase初始化")


def test_execution_layer():
    """测试执行层"""
    from sprintcycle.chorus import ExecutionLayer
    
    layer = ExecutionLayer()
    available = layer.list_available()
    assert isinstance(available, dict)
    assert "aider" in available
    print("✅ ExecutionLayer功能")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
