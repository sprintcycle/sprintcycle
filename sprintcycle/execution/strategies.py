"""
执行策略 - Normal 和 Evolution 两种策略

策略模式实现，所有策略共用 SprintExecutor。
Evolution 作为 Sprint 的增强能力，由 SprintExecutor 内部调用。
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..prd.models import PRD, ExecutionMode
from .sprint_executor import SprintExecutor, SprintResult, ExecutionStatus

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    prd: PRD
    sprint_results: List[SprintResult] = field(default_factory=list)
    duration: float = 0.0
    error: Optional[str] = None
    
    @property
    def completed_sprints(self) -> int:
        return sum(1 for r in self.sprint_results if r.status == ExecutionStatus.SUCCESS)
    
    @property
    def total_sprints(self) -> int:
        return len(self.sprint_results)
    
    @property
    def completed_tasks(self) -> int:
        return sum(r.success_count for r in self.sprint_results)
    
    @property
    def total_tasks(self) -> int:
        return sum(len(r.task_results) for r in self.sprint_results)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "completed_sprints": self.completed_sprints,
            "total_sprints": self.total_sprints,
            "completed_tasks": self.completed_tasks,
            "total_tasks": self.total_tasks,
            "duration": self.duration,
            "error": self.error,
        }


class ExecutionStrategy(ABC):
    """
    执行策略基类
    
    所有策略都必须实现 execute 方法，并共享 SprintExecutor。
    """
    
    def __init__(self, sprint_executor: SprintExecutor):
        """
        初始化策略
        
        Args:
            sprint_executor: 共享的 Sprint 执行器
        """
        self.sprint_executor = sprint_executor
    
    @abstractmethod
    async def execute(self, prd: PRD) -> ExecutionResult:
        """
        执行 PRD
        
        Args:
            prd: PRD 对象
            
        Returns:
            ExecutionResult: 执行结果
        """
        pass


class NormalStrategy(ExecutionStrategy):
    """
    普通任务策略
    
    直接执行 Sprint 迭代，适用于开发其他项目。
    
    流程：
    Sprint 1 → Sprint 2 → Sprint 3 → ... → 完成
    """
    
    async def execute(self, prd: PRD) -> ExecutionResult:
        """执行普通任务"""
        start_time = time.time()
        logger.info(f"📋 Normal 策略执行: {prd.project.name}")
        
        # 直接执行所有 Sprint
        sprint_results = await self.sprint_executor.execute_sprints(prd.sprints)
        
        # 判断整体成功
        success = all(r.status == ExecutionStatus.SUCCESS for r in sprint_results)
        
        duration = time.time() - start_time
        logger.info(f"{'✅' if success else '❌'} Normal 策略完成 ({duration:.2f}s)")
        
        return ExecutionResult(
            success=success,
            prd=prd,
            sprint_results=sprint_results,
            duration=duration,
            error=None if success else "部分 Sprint 失败",
        )


class EvolutionStrategy(ExecutionStrategy):
    """
    自进化策略 - 通过 SprintExecutor 执行
    
    方案 A：Evolution 成为 Sprint 的增强能力，而非独立流程。
    底层复用 SprintExecutor，由其内部调用 EvolutionEngine。
    
    流程：
    Sprint 1 → EvolutionEngine.evolve_sprint() → SprintResult
    Sprint 2 → EvolutionEngine.evolve_sprint() → SprintResult
    ...
    
    关键：EvolutionEngine 通过 SprintExecutor 间接使用
    """
    
    def __init__(
        self, 
        sprint_executor: SprintExecutor,
    ):
        """
        初始化自进化策略
        
        Args:
            sprint_executor: 共享的 Sprint 执行器（已注入 EvolutionEngine）
        """
        super().__init__(sprint_executor)
        # 不再直接持有 evolution_engine，而是通过 SprintExecutor 使用
    
    async def execute(self, prd: PRD) -> ExecutionResult:
        """执行自进化 - 统一走 SprintExecutor"""
        start_time = time.time()
        logger.info(f"🔄 Evolution 策略执行: {prd.project.name}")
        
        # 调用 SprintExecutor 的 evolution 模式
        # EvolutionEngine 已在 SprintExecutor 内部，通过 _execute_evolution_sprints 调用
        sprint_results = await self.sprint_executor.execute_sprints(
            sprints=prd.sprints,
            mode="evolution",
            evolution_config=prd.evolution,
        )
        
        success = all(r.status == ExecutionStatus.SUCCESS for r in sprint_results)
        duration = time.time() - start_time
        
        logger.info(f"{'✅' if success else '❌'} Evolution 策略完成 ({duration:.2f}s)")
        
        return ExecutionResult(
            success=success,
            prd=prd,
            sprint_results=sprint_results,
            duration=duration,
        )


# 策略工厂
def get_strategy(
    mode: ExecutionMode, 
    sprint_executor: SprintExecutor,
) -> ExecutionStrategy:
    """
    根据模式获取对应的策略
    
    方案 A：EvolutionStrategy 不再直接持有 EvolutionEngine，
    而是依赖 SprintExecutor 内部注入的 EvolutionEngine。
    
    Args:
        mode: 执行模式
        sprint_executor: Sprint 执行器（已注入 EvolutionEngine）
        
    Returns:
        ExecutionStrategy: 对应的策略实例
    """
    if mode == ExecutionMode.EVOLUTION:
        return EvolutionStrategy(sprint_executor)
    else:
        return NormalStrategy(sprint_executor)
