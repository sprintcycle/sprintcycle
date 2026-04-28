"""
SprintCycle Sprint 日志模块 v0.3

提供 Sprint 执行期间的日志记录，支持：
- Sprint/Task 级别日志
- 性能统计
- 错误追踪
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from loguru import logger
from utils.logger import set_log_context, clear_log_context


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SprintStatus(Enum):
    """Sprint 状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class TaskLog:
    """任务日志"""
    task_id: str
    task_name: str
    agent: str
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: float = 0.0
    output: str = ""
    error: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SprintLog:
    """Sprint 日志"""
    sprint_id: str
    sprint_name: str
    total_tasks: int = 0
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: float = 0.0
    tasks: List[TaskLog] = field(default_factory=list)
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_tasks == 0:
            return 0.0
        return self.success_count / self.total_tasks * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sprint_id": self.sprint_id,
            "sprint_name": self.sprint_name,
            "total_tasks": self.total_tasks,
            "status": self.status,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "success_rate": f"{self.success_rate:.1f}%",
            "tasks": [
                {
                    "task_id": t.task_id,
                    "task_name": t.task_name,
                    "agent": t.agent,
                    "status": t.status,
                    "duration": t.duration,
                    "files_changed": len(t.files_changed),
                    "error": t.error[:100] if t.error else None
                }
                for t in self.tasks
            ]
        }


class SprintLogger:
    """
    Sprint 日志记录器
    
    提供结构化的 Sprint 执行日志记录
    """
    
    def __init__(self, output_dir: str = "./logs"):
        """
        初始化 Sprint 日志记录器
        
        Args:
            output_dir: 日志输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前 Sprint 状态
        self.current_sprint: Optional[SprintLog] = None
        self.current_task: Optional[TaskLog] = None
        self.sprint_history: List[SprintLog] = []
        
        # 性能统计
        self._task_timings: Dict[str, float] = {}
    
    def start_sprint(self, sprint_id: str, sprint_name: str, total_tasks: int) -> SprintLog:
        """
        开始 Sprint
        
        Args:
            sprint_id: Sprint ID
            sprint_name: Sprint 名称
            total_tasks: 任务总数
            
        Returns:
            SprintLog 实例
        """
        self.current_sprint = SprintLog(
            sprint_id=sprint_id,
            sprint_name=sprint_name,
            total_tasks=total_tasks,
            status="running",
            start_time=time.time()
        )
        
        set_log_context(
            sprint_id=sprint_id,
            sprint_name=sprint_name,
            total_tasks=total_tasks
        )
        
        logger.info(
            f"🚀 Sprint 开始: {sprint_name} "
            f"(ID: {sprint_id}, 任务数: {total_tasks})"
        )
        
        return self.current_sprint
    
    def complete_sprint(self, status: SprintStatus = SprintStatus.SUCCESS) -> SprintLog:
        """
        完成 Sprint
        
        Args:
            status: Sprint 状态
            
        Returns:
            SprintLog 实例
        """
        if self.current_sprint is None:
            logger.warning("没有正在执行的 Sprint")
            return None
        
        self.current_sprint.end_time = time.time()
        self.current_sprint.duration = self.current_sprint.end_time - self.current_sprint.start_time
        self.current_sprint.status = status.value
        
        # 统计结果
        self.current_sprint.success_count = sum(
            1 for t in self.current_sprint.tasks if t.status == "success"
        )
        self.current_sprint.failed_count = sum(
            1 for t in self.current_sprint.tasks if t.status == "failed"
        )
        self.current_sprint.skipped_count = sum(
            1 for t in self.current_sprint.tasks if t.status == "skipped"
        )
        
        # 记录日志
        status_emoji = {
            "success": "✅",
            "failed": "❌",
            "partial": "⚠️",
            "running": "🔄"
        }
        emoji = status_emoji.get(status.value, "📋")
        
        logger.info(
            f"{emoji} Sprint 完成: {self.current_sprint.sprint_name} "
            f"(成功: {self.current_sprint.success_count}/{self.current_sprint.total_tasks}, "
            f"失败: {self.current_sprint.failed_count}, "
            f"耗时: {self.current_sprint.duration:.1f}秒)"
        )
        
        # 保存日志
        self._save_sprint_log()
        
        # 添加到历史
        self.sprint_history.append(self.current_sprint)
        result = self.current_sprint
        self.current_sprint = None
        
        clear_log_context()
        return result
    
    def start_task(
        self,
        task_id: str,
        task_name: str,
        agent: str
    ) -> TaskLog:
        """
        开始任务
        
        Args:
            task_id: 任务 ID
            task_name: 任务名称
            agent: Agent 类型
            
        Returns:
            TaskLog 实例
        """
        self.current_task = TaskLog(
            task_id=task_id,
            task_name=task_name,
            agent=agent,
            status="running",
            start_time=time.time()
        )
        
        set_log_context(task_id=task_id, task_name=task_name)
        
        logger.debug(f"📋 开始任务: {task_name} (Agent: {agent})")
        
        return self.current_task
    
    def complete_task(
        self,
        status: TaskStatus = TaskStatus.SUCCESS,
        output: str = "",
        error: Optional[str] = None,
        files_changed: Optional[List[str]] = None
    ) -> TaskLog:
        """
        完成任务
        
        Args:
            status: 任务状态
            output: 执行输出
            error: 错误信息
            files_changed: 变更的文件列表
            
        Returns:
            TaskLog 实例
        """
        if self.current_task is None:
            logger.warning("没有正在执行的任务")
            return None
        
        self.current_task.end_time = time.time()
        self.current_task.duration = self.current_task.end_time - self.current_task.start_time
        self.current_task.status = status.value
        self.current_task.output = output
        self.current_task.error = error
        
        if files_changed:
            self.current_task.files_changed = files_changed
        
        # 记录日志
        if status == TaskStatus.SUCCESS:
            logger.info(
                f"✅ 任务完成: {self.current_task.task_name} "
                f"(耗时: {self.current_task.duration:.2f}秒, "
                f"文件: {len(self.current_task.files_changed)})"
            )
        else:
            logger.error(
                f"❌ 任务失败: {self.current_task.task_name} "
                f"(耗时: {self.current_task.duration:.2f}秒)"
            )
        
        # 添加到 Sprint
        if self.current_sprint:
            self.current_sprint.tasks.append(self.current_task)
        
        clear_log_context()
        result = self.current_task
        self.current_task = None
        return result
    
    def _save_sprint_log(self) -> None:
        """保存 Sprint 日志"""
        if self.current_sprint is None:
            return
        
        log_file = self.output_dir / f"sprint_{self.current_sprint.sprint_id}_{int(time.time())}.json"
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_sprint.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug(f"📝 Sprint 日志已保存: {log_file}")
        except Exception as e:
            logger.warning(f"保存 Sprint 日志失败: {e}")
    
    def get_sprint_summary(self) -> Dict[str, Any]:
        """
        获取 Sprint 执行摘要
        
        Returns:
            Sprint 摘要字典
        """
        if not self.sprint_history:
            return {"total_sprints": 0}
        
        total_tasks = sum(s.total_tasks for s in self.sprint_history)
        total_success = sum(s.success_count for s in self.sprint_history)
        total_failed = sum(s.failed_count for s in self.sprint_history)
        total_duration = sum(s.duration for s in self.sprint_history)
        
        return {
            "total_sprints": len(self.sprint_history),
            "total_tasks": total_tasks,
            "total_success": total_success,
            "total_failed": total_failed,
            "total_duration_seconds": total_duration,
            "overall_success_rate": f"{total_success / total_tasks * 100:.1f}%" if total_tasks > 0 else "0%",
            "average_duration_seconds": total_duration / len(self.sprint_history) if self.sprint_history else 0,
        }
    
    def export_summary(self, output_path: str) -> None:
        """
        导出执行摘要
        
        Args:
            output_path: 输出文件路径
        """
        summary = self.get_sprint_summary()
        summary["sprints"] = [s.to_dict() for s in self.sprint_history]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Sprint 执行摘要已导出: {output_path}")


# 全局 Sprint 日志记录器实例
_sprint_logger: Optional[SprintLogger] = None


def get_sprint_logger(output_dir: str = "./logs") -> SprintLogger:
    """
    获取全局 Sprint 日志记录器
    
    Args:
        output_dir: 日志输出目录
        
    Returns:
        SprintLogger 实例
    """
    global _sprint_logger
    if _sprint_logger is None:
        _sprint_logger = SprintLogger(output_dir)
    return _sprint_logger


__all__ = [
    "TaskStatus",
    "SprintStatus",
    "TaskLog",
    "SprintLog",
    "SprintLogger",
    "get_sprint_logger",
]
