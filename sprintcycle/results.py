"""
SprintCycle 统一返回值类型

所有操作（plan/run/diagnose/status/rollback/stop）返回统一的 Result 对象，
支持 to_dict() 序列化，确保 CLI / MCP / Dashboard 输出一致。
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ResultBase:
    """所有 Result 的基类"""
    success: bool
    error: Optional[str] = None
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # 移除值为 None 的字段，保持输出干净
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class PlanResult(ResultBase):
    """plan() 返回 — 意图→PRD 计划（不执行）"""
    prd_yaml: str = ""
    sprints: List[Dict[str, Any]] = field(default_factory=list)
    mode: str = ""
    prd_name: str = ""


@dataclass
class RunResult(ResultBase):
    """run() 返回 — 执行结果"""
    execution_id: str = ""
    prd_name: str = ""
    completed_sprints: int = 0
    completed_tasks: int = 0
    total_sprints: int = 0
    total_tasks: int = 0
    sprint_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DiagnoseResult(ResultBase):
    """diagnose() 返回 — 项目体检"""
    health_score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    coverage: float = 0.0
    complexity: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatusResult(ResultBase):
    """status() 返回 — 执行状态/历史"""
    execution_id: str = ""
    status: str = ""
    current_sprint: int = 0
    total_sprints: int = 0
    sprint_history: List[Dict[str, Any]] = field(default_factory=list)
    executions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RollbackResult(ResultBase):
    """rollback() 返回 — 回滚结果"""
    execution_id: str = ""
    rollback_point: str = ""
    files_restored: List[str] = field(default_factory=list)


@dataclass
class StopResult(ResultBase):
    """stop() 返回 — 停止结果"""
    execution_id: str = ""
    cancelled: bool = False
    current_sprint: int = 0
    message: str = ""


__all__ = [
    "ResultBase",
    "PlanResult",
    "RunResult",
    "DiagnoseResult",
    "StatusResult",
    "RollbackResult",
    "StopResult",
]
