from __future__ import annotations

"""
EvolutionPipeline - 统一进化管道

v0.9.1: 删除空壳 run() 方法，保留 execute() 方法
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from ..config.manager import RuntimeConfig

from .prd_source import PRDSource, EvolutionPRD, ManualPRDSource
from .memory_store import MemoryStore, EvolutionMemory

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"




@dataclass
class SprintExecutionResult:
    sprint_name: str
    success: bool
    task_results: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sprint_name": self.sprint_name,
            "success": self.success,
            "task_results": self.task_results,
            "duration": self.duration,
            "error": self.error,
        }


@dataclass
class PRDExecutionResult:
    prd: EvolutionPRD
    sprint_results: List[SprintExecutionResult] = field(default_factory=list)
    baseline_fitness: float = 0.0
    final_fitness: float = 0.0
    success: bool = False
    improvement: float = 0.0
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def completed_sprints(self) -> int:
        return sum(1 for r in self.sprint_results if r.success)
    
    @property
    def total_sprints(self) -> int:
        return len(self.sprint_results)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prd_name": self.prd.name,
            "prd_version": self.prd.version,
            "completed_sprints": self.completed_sprints,
            "total_sprints": self.total_sprints,
            "baseline_fitness": self.baseline_fitness,
            "final_fitness": self.final_fitness,
            "success": self.success,
            "improvement": self.improvement,
        }


# PipelineResult for backward compatibility
PipelineResult = PRDExecutionResult


class EvolutionPipeline:
    """统一进化管道"""
    
    def __init__(
        self,
        project_path: str = ".",
        config: Optional["RuntimeConfig"] = None,
        memory_store: Optional[MemoryStore] = None,
        prd_source: Optional[PRDSource] = None,
    ):
        """
        初始化进化管道
        
        Args:
            project_path: 项目路径
            config: RuntimeConfig（统一配置）
            memory_store: 记忆存储
            prd_source: PRD 来源
        """
        self.project_path = project_path
        self._config = config
        memory_dir = getattr(config, 'evolution_cache_dir', './evolution_cache/memory') if config else './evolution_cache/memory'
        self._memory_store = memory_store or MemoryStore(storage_path=memory_dir)
        self._prd_source = prd_source or ManualPRDSource()
        self._status = PipelineStatus.IDLE
        self._current_prd: Optional[EvolutionPRD] = None
    
    def execute(self, prd: EvolutionPRD) -> PRDExecutionResult:
        """
        执行单个 PRD
        
        Args:
            prd: EvolutionPRD 对象
            
        Returns:
            PRDExecutionResult
        """
        self._status = PipelineStatus.RUNNING
        self._current_prd = prd
        
        result = PRDExecutionResult(prd=prd)
        
        try:
            for i, sprint in enumerate(prd.sprints):
                sprint_name = sprint.get("name", f"sprint_{i}")
                sprint_result = self._execute_sprint(sprint_name, sprint.get("tasks", []))
                result.sprint_results.append(sprint_result)
                
                if not sprint_result.success and getattr(self._config, "rollback_on_failure", True) if self._config else True:
                    logger.warning(f"Sprint {i} failed, rollback")
                    break
            
            result.success = all(r.success for r in result.sprint_results)
            result.final_fitness = self._calculate_fitness(result)
            result.improvement = result.final_fitness - result.baseline_fitness
            self._status = PipelineStatus.SUCCESS if result.success else PipelineStatus.PARTIAL
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            result.error = str(e)
            self._status = PipelineStatus.FAILED
        
        return result
    
    def _execute_sprint(self, sprint_name: str, tasks: List[Dict[str, Any]]) -> SprintExecutionResult:
        start = datetime.now()
        result = SprintExecutionResult(sprint_name=sprint_name, success=True)
        
        for task in tasks:
            try:
                task_name = task.get("name", "unknown")
                task_result = self._execute_task(task_name)
                result.task_results.append(task_result)
                if not task_result.get("success", False):
                    result.success = False
            except Exception as e:
                logger.error(f"Task {task.get('name', 'unknown')} failed: {e}")
                result.task_results.append({"task": task.get("name", "unknown"), "success": False, "error": str(e)})
                result.success = False
        
        result.duration = (datetime.now() - start).total_seconds()
        return result
    
    def _execute_task(self, task_name: str) -> Dict[str, Any]:
        return {"task": task_name, "success": True}
    
    def _calculate_fitness(self, result: PRDExecutionResult) -> float:
        if not result.sprint_results:
            return 0.0
        success_rate = sum(1 for r in result.sprint_results if r.success) / len(result.sprint_results)
        return success_rate
    
    @property
    def status(self) -> PipelineStatus:
        return self._status
    
    def get_memory(self) -> MemoryStore:
        return self._memory_store
