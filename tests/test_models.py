"""测试 Pydantic 数据模型"""

import sys
sys.path.insert(0, '/root/sprintcycle')

import pytest
from sprintcycle.models import (
    AgentType, TaskStatus, SprintStatus, Project, Sprint, Task, Report,
    IssueSeverity, IssueType, HealthStatus, Issue, ScanResult, HealthReport
)


class TestEnums:
    """测试枚举类型"""
    
    def test_agent_type_values(self):
        assert AgentType.CODER.value == "coder"
        assert AgentType.REVIEWER.value == "reviewer"
        assert len(AgentType) == 6
    
    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"


class TestTaskModel:
    """测试 Task 模型"""
    
    def test_task_creation(self):
        task = Task(name="Test Task")
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
    
    def test_task_with_agent(self):
        task = Task(name="Review Task", agent=AgentType.REVIEWER)
        assert task.agent == AgentType.REVIEWER


class TestSprintModel:
    """测试 Sprint 模型"""
    
    def test_sprint_creation(self):
        sprint = Sprint(name="Sprint 1")
        assert sprint.name == "Sprint 1"
        assert sprint.status == SprintStatus.PLANNED
    
    def test_sprint_with_tasks(self):
        sprint = Sprint(name="Sprint 1", tasks=[Task(name="Task 1")])
        assert len(sprint.tasks) == 1


class TestProjectModel:
    """测试 Project 模型"""
    
    def test_project_creation(self):
        project = Project(name="Test Project")
        assert project.name == "Test Project"
    
    def test_project_version(self):
        project = Project(name="Test", version="v4.7")
        assert project.version == "v4.7"


class TestReportModel:
    """测试 Report 模型"""
    
    def test_report_creation(self):
        report = Report(project_name="Test Project")
        assert report.project_name == "Test Project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
