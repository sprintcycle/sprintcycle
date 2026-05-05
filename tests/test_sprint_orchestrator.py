"""
调度器单元测试
"""

import pytest
import asyncio

from sprintcycle.config import RuntimeConfig
from sprintcycle.orchestration.sprint_orchestrator import (
    ExecutionStatus,
    SprintOrchestrator,
    SprintResult,
    TaskResult,
)
from sprintcycle.release_plan.models import (
    PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode
)


class TestSprintOrchestrator:
    """Sprint 编排器测试"""
    
    def setup_method(self):
        """测试前准备（dry_run 避免真实 LLM / Aider 调用）"""
        self.orchestrator = SprintOrchestrator(config=RuntimeConfig(dry_run=True, quality_level="L1"))
    
    def test_orchestrator_initialization(self):
        """测试编排器初始化"""
        assert self.orchestrator is not None
        assert self.orchestrator.evolution_pipeline is None
    
    def test_execute_normal_prd(self):
        """测试执行普通 PRD"""
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
            mode=ExecutionMode.NORMAL,
            sprints=[
                PRDSprint(
                    name="Sprint 1",
                    goals=["完成开发"],
                    tasks=[
                        PRDTask(description="实现功能 A", agent="coder"),
                        PRDTask(description="实现功能 B", agent="coder"),
                    ]
                ),
            ]
        )
        
        # 同步运行
        results = asyncio.run(self.orchestrator.execute_release_plan(prd))
        
        assert len(results) == 1
        assert results[0].sprint.name == "Sprint 1"
        assert len(results[0].task_results) == 2
    
    def test_execute_multiple_sprints(self):
        """测试执行多个 Sprint"""
        prd = PRD(
            project=PRDProject(name="test", path="/root/test"),
            mode=ExecutionMode.NORMAL,
            sprints=[
                PRDSprint(
                    name="Sprint 1",
                    tasks=[
                        PRDTask(description="任务 1", agent="coder"),
                    ]
                ),
                PRDSprint(
                    name="Sprint 2",
                    tasks=[
                        PRDTask(description="任务 2", agent="coder"),
                    ]
                ),
            ]
        )
        
        results = asyncio.run(self.orchestrator.execute_release_plan(prd))
        
        assert len(results) == 2
        assert results[0].sprint.name == "Sprint 1"
        assert results[1].sprint.name == "Sprint 2"
    
    def test_get_summary(self):
        """测试获取摘要"""
        summary = self.orchestrator.get_summary()
        
        assert "evolution_pipeline" in summary
        assert "callbacks" in summary
        assert isinstance(summary["callbacks"], list)


class TestTaskResult:
    """任务结果测试"""
    
    def test_task_result_creation(self):
        """测试创建任务结果"""
        task = PRDTask(description="测试任务", agent="coder")
        result = TaskResult(
            work_item=task,
            sprint_name="Sprint 1",
            status=ExecutionStatus.SUCCESS,
            output="完成",
            duration=10.5,
        )
        
        assert result.work_item.description == "测试任务"
        assert result.status == ExecutionStatus.SUCCESS
        assert result.duration == 10.5
    
    def test_task_result_to_dict(self):
        """测试任务结果序列化"""
        task = PRDTask(description="测试任务", agent="coder", target="src/main.py")
        result = TaskResult(
            work_item=task,
            sprint_name="Sprint 1",
            status=ExecutionStatus.SUCCESS,
        )
        
        result_dict = result.to_dict()
        
        assert "description" in result_dict
        assert "agent" in result_dict
        assert result_dict["status"] == "success"


class TestSprintResult:
    """Sprint 结果测试"""
    
    def test_sprint_result_calculations(self):
        """测试 Sprint 结果计算"""
        sprint = PRDSprint(
            name="Sprint 1",
            tasks=[
                PRDTask(description="任务1", agent="coder"),
                PRDTask(description="任务2", agent="coder"),
                PRDTask(description="任务3", agent="coder"),
            ]
        )
        
        results = [
            TaskResult(
                work_item=sprint.tasks[0],
                sprint_name="Sprint 1",
                status=ExecutionStatus.SUCCESS,
            ),
            TaskResult(
                work_item=sprint.tasks[1],
                sprint_name="Sprint 1",
                status=ExecutionStatus.SUCCESS,
            ),
            TaskResult(
                work_item=sprint.tasks[2],
                sprint_name="Sprint 1",
                status=ExecutionStatus.FAILED,
            ),
        ]
        
        sprint_result = SprintResult(
            sprint=sprint,
            status=ExecutionStatus.SUCCESS,
            task_results=results,
            duration=30.0,
        )
        
        assert sprint_result.success_count == 2
        assert sprint_result.failed_count == 1
        assert sprint_result.success_rate == pytest.approx(2/3)
    
    def test_sprint_result_empty(self):
        """测试空 Sprint 结果"""
        sprint = PRDSprint(name="Sprint 1", tasks=[])
        sprint_result = SprintResult(
            sprint=sprint,
            status=ExecutionStatus.SKIPPED,
            task_results=[],
        )
        
        assert sprint_result.success_count == 0
        assert sprint_result.success_rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
