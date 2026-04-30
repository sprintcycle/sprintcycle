"""
EvolutionPipeline - 统一进化管道

v0.9.0 核心组件:
- 统一的PRD执行管道
- PRD来源可插拔
- Sprint执行 + Fitness验证 + 记忆存储
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime

from .prd_source import PRDSource, EvolutionPRD, ManualPRDSource
from .types import Gene, GeneType
from .memory_store import MemoryStore, EvolutionMemory, MemoryConfig
from ..prd.models import PRD, PRDSprint, PRDTask

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """管道状态"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # 部分成功


@dataclass
class PipelineConfig:
    memory_dir: str = "./evolution_cache/memory"
    """管道配置"""
    max_cycles: int = 1  # 最大循环次数
    max_tasks_per_sprint: int = 20  # 每个sprint最大任务数
    task_timeout: int = 600  # 任务超时（秒）
    rollback_on_failure: bool = True  # 失败时回滚
    save_genes: bool = True  # 保存基因
    dry_run: bool = False  # 干跑模式


    @classmethod
    def from_runtime_config(cls, rc) -> "PipelineConfig":
        """Construct from RuntimeConfig."""
        return cls(
            memory_dir=getattr(rc, 'evolution_cache_dir', './evolution_cache/memory'),
            max_cycles=getattr(rc, 'evolution_iterations', 3),
            max_tasks_per_sprint=getattr(rc, 'max_tasks_per_sprint', 20),
            task_timeout=getattr(rc, 'diagnostic_timeout', 600),
            rollback_on_failure=True,
            dry_run=getattr(rc, 'dry_run', False),
        )


@dataclass
class SprintExecutionResult:
    """Sprint执行结果"""
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
    """PRD执行结果"""
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
            "sprints": self.sprint_results,
            "baseline_fitness": self.baseline_fitness,
            "final_fitness": self.final_fitness,
            "success": self.success,
            "improvement": self.improvement,
            "error": self.error,
            "completed_sprints": self.completed_sprints,
            "total_sprints": self.total_sprints,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class PipelineResult:
    """管道执行结果"""
    status: PipelineStatus
    cycle_results: List[Dict[str, Any]] = field(default_factory=list)
    total_prds: int = 0
    successful_prds: int = 0
    failed_prds: int = 0
    total_duration: float = 0.0
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def success(self) -> bool:
        return self.status == PipelineStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "cycle_results": self.cycle_results,
            "total_prds": self.total_prds,
            "successful_prds": self.successful_prds,
            "failed_prds": self.failed_prds,
            "total_duration": self.total_duration,
            "error": self.error,
            "success": self.success,
            "created_at": self.created_at.isoformat(),
        }


class EvolutionPipeline:
    """
    统一进化管道
    
    唯一入口，统一执行:
    1. PRD来源可插拔
    2. SprintChain执行
    3. Fitness验证
    4. 基因池存储
    
    使用方式:
    ```python
    # 方式1: 诊断驱动
    pipeline = EvolutionPipeline(prd_source=DiagnosticPRDSource())
    result = pipeline.run()
    
    # 方式2: 手动PRD
    pipeline = EvolutionPipeline(prd_source=ManualPRDSource("prd"))
    result = pipeline.run()
    ```
    """
    
    def __init__(
        self,
        project_path: str = ".",
        prd_source: Optional[PRDSource] = None,
        config: Optional[PipelineConfig] = None,
        runtime_config=None,
        # Mock组件（用于测试）
        executor: Optional[Any] = None,
        fitness_func: Optional[Callable[[str], float]] = None,
        rollback_func: Optional[Callable[[str], None]] = None,
    ):
        """
        初始化进化管道
        
        Args:
            project_path: 项目路径
            prd_source: PRD来源
            config: 管道配置
            executor: Sprint执行器（可mock）
            fitness_func: Fitness评估函数（可mock）
            rollback_func: 回滚函数（可mock）
        """
        self.project_path = project_path
        self._prd_source = prd_source
        if config is None and runtime_config is not None:
            config = PipelineConfig.from_runtime_config(runtime_config)
        self._config = config or PipelineConfig()
        
        # Mock或真实组件
        self._executor = executor
        self._fitness_func = fitness_func
        self._rollback_func = rollback_func
        
        # 内部状态
        self._genes: List[Gene] = []
        self._history: List[PRDExecutionResult] = []
    
    def run(self, max_cycles: Optional[int] = None) -> PipelineResult:
        """
        执行进化管道
        
        Args:
            max_cycles: 最大循环次数（覆盖配置）
            
        Returns:
            PipelineResult
        """
        import time
        start_time = time.time()
        
        max_cycles = max_cycles or self._config.max_cycles
        logger.info(f"启动进化管道: project={self.project_path}, cycles={max_cycles}")
        
        try:
            # 1. 获取PRD列表
            prds = self._get_prds()
            if not prds:
                logger.warning("没有可执行的PRD")
                return PipelineResult(
                    status=PipelineStatus.IDLE,
                    total_prds=0,
                    total_duration=time.time() - start_time,
                )
            
            # 2. 执行PRD循环
            all_results = []
            successful_count = 0
            failed_count = 0
            
            for i in range(max_cycles):
                logger.info(f"开始第 {i+1}/{max_cycles} 轮循环")
                
                for prd in prds:
                    result = self._execute_prd(prd)
                    all_results.append(result.to_dict())
                    
                    if result.success:
                        successful_count += 1
                    else:
                        failed_count += 1
                    
                    # 保存基因
                    if self._config.save_genes:
                        self._save_gene(result)
                    
                    self._history.append(result)
            
            # 3. 构建结果
            status = PipelineStatus.SUCCESS
            if failed_count > 0:
                status = PipelineStatus.PARTIAL if successful_count > 0 else PipelineStatus.FAILED
            
            return PipelineResult(
                status=status,
                cycle_results=all_results,
                total_prds=len(prds),
                successful_prds=successful_count,
                failed_prds=failed_count,
                total_duration=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"管道执行失败: {e}")
            return PipelineResult(
                status=PipelineStatus.FAILED,
                error=str(e),
                total_duration=time.time() - start_time,
            )
    
    def _get_prds(self) -> List[EvolutionPRD]:
        """获取PRD列表"""
        if self._prd_source:
            return self._prd_source.generate(self.project_path)
        
        # 默认使用ManualPRDSource
        source = ManualPRDSource()
        return source.generate(self.project_path)
    
    def _execute_prd(self, prd: EvolutionPRD) -> PRDExecutionResult:
        """
        执行单个PRD
        
        Args:
            prd: EvolutionPRD
            
        Returns:
            PRDExecutionResult
        """
        import time
        start_time = time.time()
        
        logger.info(f"执行PRD: {prd.name}")
        
        # 1. 记录基线fitness
        baseline = self._measure_fitness()
        
        # 2. 拆解并执行Sprint
        sprint_results = []
        
        for sprint_data in prd.sprints:
            result = self._execute_sprint(sprint_data, prd)
            sprint_results.append(result)
            
            # 如果Sprint失败且配置回滚
            if not result.success and self._config.rollback_on_failure:
                logger.warning(f"Sprint失败，执行回滚: {result.sprint_name}")
                self._rollback()
                break
        
        # 3. 测量最终fitness
        final = self._measure_fitness()
        
        # 4. 判断成功
        success = all(r.success for r in sprint_results)
        improvement = final - baseline
        
        logger.info(
            f"PRD执行完成: {prd.name}, "
            f"success={success}, "
            f"fitness: {baseline:.2f} -> {final:.2f} ({improvement:+.2f})"
        )
        
        return PRDExecutionResult(
            prd=prd,
            sprint_results=sprint_results,
            baseline_fitness=baseline,
            final_fitness=final,
            success=success,
            improvement=improvement,
        )
    
    def _execute_sprint(
        self, sprint_data: Dict[str, Any], prd: EvolutionPRD
    ) -> SprintExecutionResult:
        """
        执行单个Sprint
        
        Args:
            sprint_data: Sprint数据
            prd: 所属PRD
            
        Returns:
            SprintExecutionResult
        """
        import time
        start_time = time.time()
        
        sprint_name = sprint_data.get("name", "Unnamed Sprint")
        tasks = sprint_data.get("tasks", [])
        
        logger.info(f"执行Sprint: {sprint_name}, 任务数={len(tasks)}")
        
        # 限制任务数
        tasks = tasks[:self._config.max_tasks_per_sprint]
        
        task_results = []
        
        for task_data in tasks:
            task_result = self._execute_task(task_data, sprint_name)
            task_results.append(task_result)
            
            # 如果任务失败，停止Sprint
            if not task_result.get("success", True):
                logger.warning(f"任务失败: {task_result.get('task', 'unknown')}")
                if self._config.rollback_on_failure:
                    self._rollback()
                break
        
        success = all(r.get("success", True) for r in task_results)
        
        return SprintExecutionResult(
            sprint_name=sprint_name,
            success=success,
            task_results=task_results,
            duration=time.time() - start_time,
        )
    
    def _execute_task(
        self, task_data: Dict[str, Any], sprint_name: str
    ) -> Dict[str, Any]:
        """
        执行单个任务
        
        Args:
            task_data: 任务数据
            sprint_name: Sprint名称
            
        Returns:
            任务结果字典
        """
        import time
        start_time = time.time()
        
        task_desc = task_data.get("task", "Unknown task")
        agent = task_data.get("agent", "coder")
        constraints = task_data.get("constraints", [])
        
        logger.debug(f"执行任务: {task_desc[:50]}...")
        
        # 如果配置了executor，使用executor
        if self._executor:
            try:
                result = self._executor.execute(task_data)
                return {
                    "task": task_desc,
                    "agent": agent,
                    "success": result.get("success", False),
                    "output": result.get("output", ""),
                    "error": result.get("error"),
                    "duration": time.time() - start_time,
                }
            except Exception as e:
                return {
                    "task": task_desc,
                    "agent": agent,
                    "success": False,
                    "error": str(e),
                    "duration": time.time() - start_time,
                }
        
        # 否则模拟执行（干跑模式）
        if self._config.dry_run:
            return {
                "task": task_desc,
                "agent": agent,
                "success": True,
                "dry_run": True,
                "duration": time.time() - start_time,
            }
        
        # 默认返回失败（需要配置executor）
        return {
            "task": task_desc,
            "agent": agent,
            "success": False,
            "error": "No executor configured",
            "duration": time.time() - start_time,
        }
    
    def _measure_fitness(self) -> float:
        """
        测量Fitness
        
        Returns:
            Fitness评分
        """
        if self._fitness_func:
            return self._fitness_func(self.project_path)
        
        # 简单模拟
        return 0.5
    
    def _rollback(self) -> None:
        """执行回滚"""
        if self._rollback_func:
            self._rollback_func(self.project_path)
    
    def _save_gene(self, result: PRDExecutionResult) -> None:
        """保存基因到基因池"""
        import json
        gene = Gene(
            id=f"gene_{len(self._genes) + 1}",
            type=GeneType.CODE,
            content=json.dumps(result.prd.to_dict()),
            metadata={
                "prd_name": result.prd.name,
                "improvement": result.improvement,
                "success": result.success,
            },
            fitness_scores={"overall": result.final_fitness},
        )
        self._genes.append(gene)
        logger.debug(f"保存基因: {gene.id}")
    
    @property
    def genes(self) -> List[Gene]:
        """获取基因列表"""
        return self._genes
    
    @property
    def history(self) -> List[PRDExecutionResult]:
        """获取执行历史"""
        return self._history
