"""
Application Layer Protocols - 核心接口定义

定义应用服务层的抽象接口，确保层间解耦和可测试性。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sprintcycle.domain.generic.models import ReleasePlan
from sprintcycle.domain.generic.interfaces import TaskResult, ExecutionStatus

if TYPE_CHECKING:
    pass


class OrchestrationProtocol(ABC):
    """Sprint 编排协议"""

    @abstractmethod
    def execute_release_plan(
        self,
        release_plan: ReleasePlan,
        *,
        resume_from_sprint: Optional[int] = None,
    ) -> Dict[str, Any]:
        """执行发布计划"""
        ...

    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        ...


class LifecycleProtocol(ABC):
    """生命周期管理协议"""

    @abstractmethod
    def can_promote(self, stage: str) -> bool:
        """检查是否可以晋升到指定阶段"""
        ...

    @abstractmethod
    def promote(self, stage: str) -> Dict[str, Any]:
        """执行晋升"""
        ...


class EvolutionProtocol(ABC):
    """演进管理协议"""

    @abstractmethod
    def evolve(
        self,
        intent: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行意图演进"""
        ...

    @abstractmethod
    def rollback(self, version: str) -> bool:
        """回滚到指定版本"""
        ...


class FeedbackProtocol(ABC):
    """反馈循环协议"""

    @abstractmethod
    def process_feedback(
        self,
        task_result: TaskResult,
    ) -> List[Dict[str, Any]]:
        """处理任务反馈，生成改进建议"""
        ...


# =============================================================================
# Infrastructure Protocol - 基础设施层接口
# =============================================================================
# Application 层通过这些协议依赖 Infrastructure 层实现
# =============================================================================


class ExecutionStateProtocol(ABC):
    """执行状态协议"""

    @abstractmethod
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        ...

    @abstractmethod
    def save_execution(self, state: Dict[str, Any]) -> None:
        """保存执行状态"""
        ...

    @abstractmethod
    def list_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """列出执行记录"""
        ...

    @abstractmethod
    def update_status(self, execution_id: str, status: ExecutionStatus, error: Optional[str] = None) -> bool:
        """更新执行状态"""
        ...


class GraphCompilerProtocol(ABC):
    """LangGraph 编译器协议"""

    @abstractmethod
    def compile_intent_graph(self, **kwargs: Any) -> Any:
        """编译意图图"""
        ...

    @abstractmethod
    def compile_sprint_graph(self, **kwargs: Any) -> Any:
        """编译 Sprint 图"""
        ...





# --- Protocol Exports ---
__all__ = [
    # Orchestration
    "OrchestrationProtocol",
    "LifecycleProtocol",
    "EvolutionProtocol",
    "FeedbackProtocol",
    # Infrastructure
    "ExecutionStateProtocol",
    "GraphCompilerProtocol",
]
