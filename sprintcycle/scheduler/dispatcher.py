"""
任务调度器

根据 PRD 创建 Sprint 任务，分配给对应 agent，跟踪执行状态
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

from ..prd.models import PRD, PRDSprint, PRDTask, ExecutionMode
from ..evolution.pipeline import EvolutionPipeline
from ..evolution.prd_source import DiagnosticPRDSource
from ..config.manager import RuntimeConfig
from ..evolution.types import SprintContext

logger = logging.getLogger(__name__)


from ..execution.sprint_types import ExecutionStatus, TaskResult, SprintResult


class TaskDispatcher:
    """
    任务调度器
    
    核心职责：
    1. 解析 PRD 并创建 Sprint 任务
    2. 根据 Agent 类型分配任务
    3. 跟踪执行状态和结果
    4. 支持普通任务和自进化模式
    """
    
    def __init__(
        self,
        config: Optional[RuntimeConfig] = None,
        evolution_pipeline: Optional[EvolutionPipeline] = None,
    ):
        """
        初始化调度器
        
        Args:
            config: 进化引擎配置
            evolution_engine: 进化引擎实例（可选）
        """
        self.config = config or RuntimeConfig()
        self.evolution_pipeline = evolution_pipeline
        self._callbacks: Dict[str, Callable] = {}
        
        # 注册默认回调
        self._callbacks["on_task_start"] = self._default_on_task_start
        self._callbacks["on_task_end"] = self._default_on_task_end
        self._callbacks["on_sprint_start"] = self._default_on_sprint_start
        self._callbacks["on_sprint_end"] = self._default_on_sprint_end
    
    def register_callback(
        self,
        event: str,
        callback: Callable[[Any], None]
    ) -> None:
        """
        注册事件回调
        
        Args:
            event: 事件名称 (on_task_start, on_task_end, on_sprint_start, on_sprint_end)
            callback: 回调函数
        """
        if event in self._callbacks:
            self._callbacks[event] = callback
    
    async def execute_prd(
        self,
        prd: PRD,
        max_concurrent: int = 3,
    ) -> List[SprintResult]:
        """
        执行 PRD
        
        Args:
            prd: PRD 对象
            max_concurrent: 最大并发任务数
            
        Returns:
            Sprint 执行结果列表
        """
        logger.info(f"🚀 开始执行 PRD: {prd.project.name}")
        logger.info(f"   模式: {prd.mode.value}")
        logger.info(f"   Sprint 数量: {len(prd.sprints)}")
        logger.info(f"   总任务数: {prd.total_tasks}")
        
        results: List[SprintResult] = []
        
        # 根据模式选择执行策略
        if prd.is_evolution_mode:
            results = await self._execute_evolution_mode(prd)
        else:
            results = await self._execute_normal_mode(prd, max_concurrent)
        
        # 输出汇总
        total_duration = sum(r.duration for r in results)
        total_success = sum(r.success_count for r in results)
        total_tasks = sum(len(r.task_results) for r in results)
        
        logger.info(f"\n📊 PRD 执行完成:")
        logger.info(f"   总任务: {total_tasks}")
        logger.info(f"   成功: {total_success}")
        logger.info(f"   失败: {total_tasks - total_success}")
        logger.info(f"   总耗时: {total_duration:.2f}s")
        
        return results
    
    async def _execute_normal_mode(
        self,
        prd: PRD,
        max_concurrent: int,
    ) -> List[SprintResult]:
        """普通模式执行"""
        results: List[SprintResult] = []
        
        for sprint in prd.sprints:
            sprint_result = await self._execute_sprint(sprint, prd, max_concurrent)
            results.append(sprint_result)
            
            # 串行执行 Sprint
            if sprint_result.status == ExecutionStatus.FAILED:
                if sprint_result.failed_count > sprint_result.success_count:
                    logger.warning(f"⚠️  Sprint '{sprint.name}' 失败率较高，继续执行下一个 Sprint")
        
        return results
    
    async def _execute_evolution_mode(self, prd: PRD) -> List[SprintResult]:
        """自进化模式执行"""
        results: List[SprintResult] = []
        
        if not prd.evolution:
            logger.error("❌ 自进化模式缺少 evolution 配置")
            return results
        
        # 初始化进化引擎
        if not self.evolution_pipeline:
            self.evolution_pipeline = EvolutionPipeline(".",  prd_source=DiagnosticPRDSource())
        
        # 创建 Sprint 上下文
        context = SprintContext(
            sprint_id=f"evo-{int(time.time())}",
            sprint_number=1,
            goal="; ".join(prd.evolution.goals) if prd.evolution.goals else "优化代码",
            constraints={"dimensions": getattr(self.config, "eval_dimensions", ["correctness", "performance"])},
        )
        
        # 对每个目标执行进化
        for target in prd.evolution.targets:
            sprint = PRDSprint(
                name=f"进化: {target}",
                goals=prd.evolution.goals,
                tasks=[
                    PRDTask(
                        task=f"进化 {target}",
                        agent="evolver",
                        target=target,
                    )
                ],
            )
            
            sprint_result = await self._execute_evolution_task(
                sprint, prd, context, target
            )
            results.append(sprint_result)
        
        return results
    
    async def _execute_sprint(
        self,
        sprint: PRDSprint,
        prd: PRD,
        max_concurrent: int,
    ) -> SprintResult:
        """执行单个 Sprint"""
        start_time = datetime.now()
        self._callbacks["on_sprint_start"](sprint)
        
        logger.info(f"\n📦 开始 Sprint: {sprint.name}")
        if sprint.goals:
            for goal in sprint.goals:
                logger.info(f"   🎯 目标: {goal}")
        
        # 并发执行任务
        processed_results = await self._run_tasks_concurrent(sprint, prd, max_concurrent)
        
        # 计算结果
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        status = self._determine_sprint_status(processed_results)
        
        sprint_result = SprintResult(
            sprint=sprint,
            status=status,
            task_results=processed_results,
            duration=duration,
            start_time=start_time,
            end_time=end_time,
        )
        
        self._callbacks["on_sprint_end"](sprint_result)
        
        logger.info(f"   完成: {sprint_result.success_count}/{len(sprint.tasks)} 成功 ({duration:.2f}s)")
        
        return sprint_result
    
    async def _run_tasks_concurrent(
        self,
        sprint: PRDSprint,
        prd: PRD,
        max_concurrent: int,
    ) -> List[TaskResult]:
        """并发执行任务"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(task: PRDTask) -> TaskResult:
            async with semaphore:
                return await self._execute_task(task, sprint.name, prd)
        
        task_coroutines = [execute_with_semaphore(t) for t in sprint.tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        return self._process_task_results(sprint, task_results)
    
    def _process_task_results(
        self,
        sprint: PRDSprint,
        task_results: List[Any],
    ) -> List[TaskResult]:
        """处理任务结果"""
        processed_results: List[TaskResult] = []
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                processed_results.append(TaskResult(
                    task=sprint.tasks[i],
                    sprint_name=sprint.name,
                    status=ExecutionStatus.FAILED,
                    error=str(result),
                ))
            else:
                processed_results.append(result)  # type: ignore[arg-type]
        return processed_results
    
    def _determine_sprint_status(self, results: List[TaskResult]) -> ExecutionStatus:
        """确定 Sprint 状态"""
        if all(r.status == ExecutionStatus.SUCCESS for r in results):
            return ExecutionStatus.SUCCESS
        if all(r.status in (ExecutionStatus.SKIPPED, ExecutionStatus.SUCCESS) for r in results):
            return ExecutionStatus.SUCCESS
        
        failed = sum(1 for r in results if r.status == ExecutionStatus.FAILED)
        if failed > len(results) / 2:
            return ExecutionStatus.FAILED
        return ExecutionStatus.SUCCESS
    
    async def _execute_evolution_task(
        self,
        sprint: PRDSprint,
        prd: PRD,
        context: SprintContext,
        target: str,
    ) -> SprintResult:
        """执行自进化任务"""
        start_time = datetime.now()
        self._callbacks["on_sprint_start"](sprint)
        
        logger.info(f"\n🧬 开始自进化: {target}")
        
        task_result = TaskResult(
            task=sprint.tasks[0],
            sprint_name=sprint.name,
            status=ExecutionStatus.RUNNING,
            start_time=start_time,
        )
        
        try:
            # 解析目标路径
            target_path = Path(prd.project.path) / target
            if not target_path.exists():
                raise FileNotFoundError(f"目标文件不存在: {target_path}")
            
            # 执行进化
            assert self.evolution_pipeline is not None
            result = self.evolution_pipeline.run(
                max_cycles=self.config.evolution_iterations,
            )
            
            if result.success:
                task_result.status = ExecutionStatus.SUCCESS
                variations: list = getattr(result, "variations", [])
                selected: list = getattr(result, "selected_genes", [])
                task_result.output = f"生成 {len(variations)} 个变异，选择 {len(selected)} 个基因"
            else:
                task_result.status = ExecutionStatus.FAILED
                task_result.error = result.error or "未知错误"
                
        except Exception as e:
            task_result.status = ExecutionStatus.FAILED
            task_result.error = str(e)
            logger.exception(f"进化失败: {target}")
        
        task_result.end_time = datetime.now()
        task_result.duration = ((task_result.end_time or datetime.now()) - (task_result.start_time or datetime.now())).total_seconds()
        
        end_time = datetime.now()
        
        sprint_result = SprintResult(
            sprint=sprint,
            status=task_result.status,
            task_results=[task_result],
            duration=(end_time - start_time).total_seconds(),
            start_time=start_time,
            end_time=end_time,
        )
        
        self._callbacks["on_sprint_end"](sprint_result)
        
        return sprint_result
    
    async def _execute_task(
        self,
        task: PRDTask,
        sprint_name: str,
        prd: PRD,
    ) -> TaskResult:
        """执行单个任务"""
        start_time = datetime.now()
        self._callbacks["on_task_start"](task)
        
        result = TaskResult(
            task=task,
            sprint_name=sprint_name,
            status=ExecutionStatus.RUNNING,
            start_time=start_time,
        )
        
        try:
            logger.info(f"   📋 {task.agent}: {task.task[:60]}...")
            
            # 根据 Agent 类型执行任务
            if task.agent == "evolver":
                result = await self._execute_evolver_task(task, prd, result)
            elif task.agent == "tester":
                result = await self._execute_tester_task(task, prd, result)
            else:
                result = await self._execute_coder_task(task, prd, result)
            
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"任务超时 ({task.timeout}s)"
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            logger.exception(f"任务执行失败")
        
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds() if result.start_time else 0.0
        
        self._callbacks["on_task_end"](result)
        
        return result
    
    async def _execute_coder_task(
        self,
        task: PRDTask,
        prd: PRD,
        result: TaskResult,
    ) -> TaskResult:
        """执行 coder 任务"""
        # TODO: 集成实际的 coder agent
        # 当前模拟执行
        await asyncio.sleep(0.1)
        result.status = ExecutionStatus.SUCCESS
        result.output = f"Coder 任务完成: {task.task[:50]}..."
        return result
    
    async def _execute_evolver_task(
        self,
        task: PRDTask,
        prd: PRD,
        result: TaskResult,
    ) -> TaskResult:
        """执行 evolver 任务"""
        if not task.target:
            result.status = ExecutionStatus.FAILED
            result.error = "evolver 任务必须指定 target"
            return result
        
        # 初始化进化引擎（如果需要）
        if not self.evolution_pipeline:
            
            self.evolution_pipeline = EvolutionPipeline(".", config=self.config, prd_source=DiagnosticPRDSource())
        
        # 创建上下文
        context = SprintContext(
            sprint_id=f"task-{int(time.time())}",
            sprint_number=1,
            goal=task.task,
        )
        
        # 执行进化
        try:
            evo_result = self.evolution_pipeline.run(max_cycles=self.config.evolution_iterations if hasattr(self.config, "evolution_iterations") else 3)
            if evo_result.success:
                result.status = ExecutionStatus.SUCCESS
                evo_variations: list = getattr(result, "variations", [])
                result.output = f"进化成功: {len(evo_variations)} 个变异"
            else:
                result.status = ExecutionStatus.FAILED
                result.error = evo_result.error
                
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
        
        return result
    
    async def _execute_tester_task(
        self,
        task: PRDTask,
        prd: PRD,
        result: TaskResult,
    ) -> TaskResult:
        """执行 tester 任务"""
        # TODO: 集成实际的 tester agent
        # 当前模拟执行
        await asyncio.sleep(0.1)
        result.status = ExecutionStatus.SUCCESS
        result.output = f"Tester 任务完成: {task.task[:50]}..."
        return result
    
    # 默认回调实现
    def _default_on_task_start(self, task: PRDTask) -> None:
        pass
    
    def _default_on_task_end(self, result: TaskResult) -> None:
        if result.status == ExecutionStatus.FAILED:
            logger.error(f"   ❌ 任务失败: {result.error}")
        elif result.status == ExecutionStatus.SUCCESS:
            logger.info(f"   ✅ 任务成功")
    
    def _default_on_sprint_start(self, sprint: PRDSprint) -> None:
        pass
    
    def _default_on_sprint_end(self, result: SprintResult) -> None:
        if result.status == ExecutionStatus.FAILED:
            logger.warning(f"   ⚠️  Sprint 失败率较高")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取调度器状态摘要"""
        return {
            "evolution_pipeline": self.evolution_pipeline is not None,
            "callbacks": list(self._callbacks.keys()),
        }
