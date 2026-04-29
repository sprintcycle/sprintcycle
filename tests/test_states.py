"""测试 SprintCycle 状态模块"""
import pytest
from sprintcycle.states import (
    SprintState, SprintStatus,
    TaskState, TaskStatus,
    AgentState, AgentStatus
)


class TestSprintStatus:
    """测试 SprintStatus 枚举"""
    
    def test_sprint_status_values(self):
        """验证所有状态值"""
        assert SprintStatus.PENDING.value == "pending"
        assert SprintStatus.RUNNING.value == "running"
        assert SprintStatus.COMPLETED.value == "completed"
        assert SprintStatus.FAILED.value == "failed"
        assert SprintStatus.CANCELLED.value == "cancelled"
    
    def test_sprint_status_count(self):
        """验证状态数量"""
        assert len(SprintStatus) == 5


class TestSprintState:
    """测试 SprintState 类"""
    
    def test_create_sprint_state(self):
        """创建基础 Sprint 状态"""
        sprint = SprintState(sprint_id="s1", name="Sprint 1")
        assert sprint.sprint_id == "s1"
        assert sprint.name == "Sprint 1"
        assert sprint.status == SprintStatus.PENDING
        assert sprint.progress == 0.0
    
    def test_sprint_progress_with_tasks(self):
        """测试带任务的进度计算"""
        sprint = SprintState(
            sprint_id="s1",
            name="Sprint 1",
            task_ids=["t1", "t2", "t3", "t4"],
            completed_task_ids=["t1", "t2"]
        )
        assert sprint.progress == 0.5  # 2/4 = 0.5
    
    def test_sprint_progress_no_tasks(self):
        """测试无任务时进度为 0"""
        sprint = SprintState(sprint_id="s1", name="Sprint 1")
        assert sprint.progress == 0.0
    
    def test_sprint_is_terminal_pending(self):
        """待处理状态不是终态"""
        sprint = SprintState(sprint_id="s1", name="Sprint 1")
        assert sprint.is_terminal is False
    
    def test_sprint_is_terminal_completed(self):
        """已完成状态是终态"""
        sprint = SprintState(sprint_id="s1", name="Sprint 1", status=SprintStatus.COMPLETED)
        assert sprint.is_terminal is True
    
    def test_sprint_is_terminal_cancelled(self):
        """已取消状态是终态"""
        sprint = SprintState(sprint_id="s1", name="Sprint 1", status=SprintStatus.CANCELLED)
        assert sprint.is_terminal is True


class TestTaskStatus:
    """测试 TaskStatus 枚举"""
    
    def test_task_status_values(self):
        """验证所有状态值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.BLOCKED.value == "blocked"
    
    def test_task_status_count(self):
        """验证状态数量"""
        assert len(TaskStatus) == 6


class TestTaskState:
    """测试 TaskState 类"""
    
    def test_create_task_state(self):
        """创建基础 Task 状态"""
        task = TaskState(task_id="t1", name="Task 1", description="Test task")
        assert task.task_id == "t1"
        assert task.name == "Task 1"
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.created_at is not None
    
    def test_task_with_dependencies(self):
        """测试带依赖的任务"""
        task = TaskState(
            task_id="t1",
            name="Task 1",
            dependencies=["dep1", "dep2"]
        )
        assert len(task.dependencies) == 2
    
    def test_task_is_terminal_completed(self):
        """已完成任务处于终态"""
        task = TaskState(task_id="t1", name="Task 1", status=TaskStatus.COMPLETED)
        assert task.is_terminal is True
    
    def test_task_is_terminal_failed(self):
        """失败任务处于终态"""
        task = TaskState(task_id="t1", name="Task 1", status=TaskStatus.FAILED)
        assert task.is_terminal is True
    
    def test_task_is_terminal_blocked(self):
        """阻塞任务不是终态"""
        task = TaskState(task_id="t1", name="Task 1", status=TaskStatus.BLOCKED)
        assert task.is_terminal is False


class TestAgentStatus:
    """测试 AgentStatus 枚举"""
    
    def test_agent_status_values(self):
        """验证所有状态值"""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.OFFLINE.value == "offline"
    
    def test_agent_status_count(self):
        """验证状态数量"""
        assert len(AgentStatus) == 4


class TestAgentState:
    """测试 AgentState 类"""
    
    def test_create_agent_state(self):
        """创建基础 Agent 状态"""
        agent = AgentState(agent_id="a1", agent_type="coder")
        assert agent.agent_id == "a1"
        assert agent.agent_type == "coder"
        assert agent.status == AgentStatus.IDLE
    
    def test_agent_is_available_idle(self):
        """空闲 Agent 可用"""
        agent = AgentState(agent_id="a1", agent_type="coder", status=AgentStatus.IDLE)
        assert agent.is_available is True
    
    def test_agent_is_available_busy(self):
        """忙碌 Agent 不可用"""
        agent = AgentState(agent_id="a1", agent_type="coder", status=AgentStatus.BUSY)
        assert agent.is_available is False
    
    def test_agent_success_rate_no_tasks(self):
        """无任务时成功率 0"""
        agent = AgentState(agent_id="a1", agent_type="coder")
        assert agent.success_rate == 0.0
    
    def test_agent_success_rate_with_success(self):
        """有成功任务"""
        agent = AgentState(
            agent_id="a1",
            agent_type="coder",
            completed_task_ids=["t1", "t2"],
            failed_task_ids=["t3"]
        )
        assert agent.success_rate == 2/3  # 2 成功 / 3 总任务
    
    def test_agent_success_rate_all_failed(self):
        """全部失败"""
        agent = AgentState(
            agent_id="a1",
            agent_type="coder",
            completed_task_ids=[],
            failed_task_ids=["t1"]
        )
        assert agent.success_rate == 0.0
