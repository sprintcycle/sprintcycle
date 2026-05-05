"""
Sprint 执行类型 — 与 Scrum **Sprint / Sprint Backlog Item 结果 / Increment 证据** 对齐

- ``TaskResult``：单条 Sprint Backlog Item 的执行结果（非完整 Product Backlog Item 生命周期）。
- ``SprintResult``：一个 **Sprint** 结束后的聚合状态；与 **Increment** 的关系为：Increment 由代码库 +
  质量门/DoD 体现，本对象承载该 Sprint 内工作项结果与时长等**可检视证据**。

v0.9.1: TaskResult/SprintResult 并入本模块；执行状态统一为 ``ExecutionStatus``。

**``ExecutionStatus`` 与对外协议（CLI JSON / MCP）**

- **建议在集成层当作稳定契约依赖的取值**（单条 Sprint Backlog Item 或单个 Sprint 聚合的
  ``status`` 字段，见 ``TaskResult.to_dict`` / ``SprintResult`` 及 ``RunResult.sprint_results``）：
  ``pending``、``running``、``success``、``failed``、``skipped``、``timeout``、``cancelled``。
  新前端/自动化只应对以上分支做完备处理即可。

- **执行会话轴**（``StateStore`` / ``ExecutionState``、``SprintCycle.status`` 返回的**整条执行**
  状态，与上列「任务级」字符串同枚举但语义不同）：常见 ``running``、``completed``、
  ``failed``、``cancelled``、``paused``。勿与单任务 JSON 的 ``status`` 混用同一套 UI 映射。

- **内部或次要场景**：``idle``、``partial``（如进化管道聚合态）；``completed`` 与 ``success``
  并存属历史合并遗留，会话级完成优先用 ``completed``，Sprint/任务成败用 ``success``。
  新增对外字段时**不要**再引入新的字符串；若必须扩展，先改文档与本段说明再落地。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

from ..release_plan.models import PRDTask, PRDSprint


class ExecutionStatus(Enum):
    """统一执行状态枚举（v0.9.2: 合并 ExecutionStateStatus + PipelineStatus）。

    取值分轴见**本模块文件顶部说明**。摘要：任务/Sprint 结果 JSON 优先依赖
    ``pending`` … ``cancelled``；整条执行记录另看 ``running`` / ``completed`` / ``paused`` 等。
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    # 从 ExecutionStateStatus 合并
    COMPLETED = "completed"
    PAUSED = "paused"
    # 从 PipelineStatus 合并
    IDLE = "idle"
    PARTIAL = "partial"


@dataclass
class TaskResult:
    """单条 Sprint Backlog Item 的执行结果（``work_item`` 为 ``PRDTask`` 工作项定义）。"""
    work_item: PRDTask
    sprint_name: str
    status: ExecutionStatus
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        desc = self.work_item.description
        return {
            "description": desc[:100] + "..." if len(desc) > 100 else desc,
            "agent": self.work_item.agent,
            "target": self.work_item.target,
            "status": self.status.value,
            "output": self.output[:500] if self.output else "",
            "error": self.error,
            "duration": self.duration,
        }


@dataclass
class SprintResult:
    """单个 Sprint 结束后的聚合结果（检视 Increment 时的输入之一：工作项成败与耗时）。"""
    sprint: PRDSprint
    status: ExecutionStatus
    task_results: List[TaskResult] = field(default_factory=list)
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_count(self) -> int:
        return sum(1 for r in self.task_results if r.status == ExecutionStatus.SUCCESS)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.task_results if r.status == ExecutionStatus.FAILED)
    
    @property
    def success_rate(self) -> float:
        if not self.task_results:
            return 0.0
        return self.success_count / len(self.task_results)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sprint_name": self.sprint.name,
            "status": self.status.value,
            "total_tasks": len(self.task_results),
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": self.success_rate,
            "duration": self.duration,
            "task_results": [r.to_dict() for r in self.task_results],
        }
