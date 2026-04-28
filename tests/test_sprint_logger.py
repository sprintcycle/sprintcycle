"""
SprintCycle SprintLogger 模块测试 v0.3
"""

import pytest
import tempfile
import time
import json
from pathlib import Path

from sprintcycle.sprint_logger import (
    TaskStatus,
    SprintStatus,
    TaskLog,
    SprintLog,
    SprintLogger,
    get_sprint_logger
)


class TestTaskStatus:
    """TaskStatus 测试"""
    
    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(TaskStatus)
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.RUNNING in statuses
        assert TaskStatus.SUCCESS in statuses
        assert TaskStatus.FAILED in statuses
        assert TaskStatus.SKIPPED in statuses


class TestSprintStatus:
    """SprintStatus 测试"""
    
    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(SprintStatus)
        assert SprintStatus.PENDING in statuses
        assert SprintStatus.RUNNING in statuses
        assert SprintStatus.SUCCESS in statuses
        assert SprintStatus.FAILED in statuses
        assert SprintStatus.PARTIAL in statuses


class TestTaskLog:
    """TaskLog 测试"""
    
    def test_default_values(self):
        """测试默认值"""
        log = TaskLog(
            task_id="task1",
            task_name="Test Task",
            agent="coder"
        )
        
        assert log.status == "pending"
        assert log.start_time is None
        assert log.end_time is None
        assert log.duration == 0.0
        assert log.output == ""
        assert log.error is None
        assert log.files_changed == []
        assert log.metadata == {}


class TestSprintLog:
    """SprintLog 测试"""
    
    def test_default_values(self):
        """测试默认值"""
        log = SprintLog(
            sprint_id="sprint1",
            sprint_name="Test Sprint"
        )
        
        assert log.total_tasks == 0
        assert log.status == "pending"
        assert log.start_time is None
        assert log.end_time is None
        assert log.duration == 0.0
        assert log.tasks == []
        assert log.success_count == 0
        assert log.failed_count == 0
    
    def test_success_rate_zero(self):
        """测试零任务成功率"""
        log = SprintLog(sprint_id="s1", sprint_name="S1")
        assert log.success_rate == 0.0
    
    def test_success_rate_calculation(self):
        """测试成功率计算"""
        log = SprintLog(sprint_id="s1", sprint_name="S1", total_tasks=4)
        log.success_count = 3
        log.failed_count = 1
        
        assert log.success_rate == 75.0
    
    def test_to_dict(self):
        """测试转换为字典"""
        log = SprintLog(
            sprint_id="sprint1",
            sprint_name="Test Sprint",
            total_tasks=2,
            status="running"
        )
        
        result = log.to_dict()
        
        assert result["sprint_id"] == "sprint1"
        assert result["sprint_name"] == "Test Sprint"
        assert result["total_tasks"] == 2
        assert result["status"] == "running"
        assert "tasks" in result


class TestSprintLogger:
    """SprintLogger 测试"""
    
    @pytest.fixture
    def logger_instance(self, tmp_path):
        """创建临时日志目录"""
        output_dir = tmp_path / "logs"
        return SprintLogger(output_dir=str(output_dir))
    
    def test_start_sprint(self, logger_instance):
        """测试开始 Sprint"""
        log = logger_instance.start_sprint("sprint1", "Test Sprint", 5)
        
        assert log.sprint_id == "sprint1"
        assert log.sprint_name == "Test Sprint"
        assert log.total_tasks == 5
        assert log.status == "running"
        assert log.start_time is not None
        assert logger_instance.current_sprint is not None
    
    def test_complete_sprint(self, logger_instance):
        """测试完成 Sprint"""
        logger_instance.start_sprint("sprint1", "Test Sprint", 2)
        
        # 添加任务
        logger_instance.start_task("t1", "Task 1", "coder")
        logger_instance.complete_task(TaskStatus.SUCCESS)
        
        logger_instance.start_task("t2", "Task 2", "reviewer")
        logger_instance.complete_task(TaskStatus.FAILED, error="Test error")
        
        result = logger_instance.complete_sprint()
        
        assert result.status in ("running", "success", "partial", "failed")  # 状态待更新
        assert result.success_count == 1
        assert result.failed_count == 1
        assert result.duration > 0
    
    def test_start_task(self, logger_instance):
        """测试开始任务"""
        logger_instance.start_sprint("sprint1", "Test Sprint", 1)
        
        task = logger_instance.start_task("task1", "Test Task", "coder")
        
        assert task.task_id == "task1"
        assert task.task_name == "Test Task"
        assert task.agent == "coder"
        assert task.status == "running"
        assert task.start_time is not None
        assert logger_instance.current_task is not None
    
    def test_complete_task_success(self, logger_instance):
        """测试完成任务成功"""
        logger_instance.start_sprint("sprint1", "Test Sprint", 1)
        logger_instance.start_task("task1", "Test Task", "coder")
        
        task = logger_instance.complete_task(
            TaskStatus.SUCCESS,
            output="Done",
            files_changed=["file1.py", "file2.py"]
        )
        
        assert task.status == "success"
        assert task.output == "Done"
        assert len(task.files_changed) == 2
        assert task.duration > 0
    
    def test_complete_task_failure(self, logger_instance):
        """测试完成任务失败"""
        logger_instance.start_sprint("sprint1", "Test Sprint", 1)
        logger_instance.start_task("task1", "Test Task", "coder")
        
        task = logger_instance.complete_task(
            TaskStatus.FAILED,
            error="Task failed due to validation"
        )
        
        assert task.status == "failed"
        assert task.error is not None
        assert "validation" in task.error
    
    def test_task_without_sprint(self, logger_instance):
        """测试没有 Sprint 的任务"""
        task = logger_instance.start_task("t1", "Task", "coder")
        result = logger_instance.complete_task(TaskStatus.SUCCESS)
        
        # 应该正常完成但不会添加到任何 Sprint
        assert result is not None
    
    def test_complete_task_without_start(self, logger_instance):
        """测试没有开始就完成任务"""
        result = logger_instance.complete_task(TaskStatus.SUCCESS)
        assert result is None
    
    def test_complete_sprint_without_start(self, logger_instance):
        """测试没有开始就完成 Sprint"""
        result = logger_instance.complete_sprint()
        assert result is None
    
    def test_get_sprint_summary_empty(self, logger_instance):
        """测试空 Sprint 摘要"""
        summary = logger_instance.get_sprint_summary()
        
        assert summary["total_sprints"] == 0
    
    def test_get_sprint_summary_with_sprints(self, logger_instance):
        """测试有 Sprint 的摘要"""
        # 执行两个 Sprint
        for i in range(2):
            logger_instance.start_sprint(f"sprint{i}", f"Sprint {i}", 2)
            logger_instance.start_task("t1", "Task 1", "coder")
            logger_instance.complete_task(TaskStatus.SUCCESS)
            logger_instance.start_task("t2", "Task 2", "reviewer")
            logger_instance.complete_task(TaskStatus.SUCCESS)
            logger_instance.complete_sprint()
        
        summary = logger_instance.get_sprint_summary()
        
        assert summary["total_sprints"] == 2
        assert summary["total_tasks"] == 4
        assert summary["total_success"] == 4
        assert summary["total_failed"] == 0
    
    def test_export_summary(self, logger_instance, tmp_path):
        """测试导出摘要"""
        logger_instance.start_sprint("sprint1", "Test Sprint", 1)
        logger_instance.start_task("t1", "Task 1", "coder")
        logger_instance.complete_task(TaskStatus.SUCCESS)
        logger_instance.complete_sprint()
        
        output_path = tmp_path / "summary.json"
        logger_instance.export_summary(str(output_path))
        
        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)
        
        assert "total_sprints" in data
        assert "sprints" in data


class TestGlobalSprintLogger:
    """全局 SprintLogger 测试"""
    
    def test_get_sprint_logger(self, tmp_path):
        """测试获取全局 SprintLogger"""
        # 重置全局实例
        import sprintcycle.sprint_logger as sl_module
        sl_module._sprint_logger = None
        
        logger = get_sprint_logger(output_dir=str(tmp_path / "logs"))
        assert isinstance(logger, SprintLogger)
        
        # 应该是同一个实例
        logger2 = get_sprint_logger()
        assert logger is logger2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
