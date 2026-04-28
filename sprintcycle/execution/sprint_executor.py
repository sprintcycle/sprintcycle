"""
Sprint 执行器 - 统一的 Sprint 迭代执行

所有策略共用这个执行器来执行 Sprint 任务。
支持串行和并行两种执行模式。
支持 Normal 和 Evolution 两种执行模式。
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..prd.models import PRD, PRDSprint, PRDTask, ExecutionMode, EvolutionConfig

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """任务执行结果"""
    task: PRDTask
    sprint_name: str
    status: TaskStatus
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task.task[:100],
            "agent": self.task.agent,
            "status": self.status.value,
            "error": self.error,
            "duration": self.duration,
        }


@dataclass
class SprintResult:
    """Sprint 执行结果"""
    sprint: PRDSprint
    status: TaskStatus
    task_results: List[TaskResult] = field(default_factory=list)
    duration: float = 0.0
    
    @property
    def success_count(self) -> int:
        return sum(1 for r in self.task_results if r.status == TaskStatus.SUCCESS)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.task_results if r.status == TaskStatus.FAILED)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sprint_name": self.sprint.name,
            "status": self.status.value,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "duration": self.duration,
        }


class SprintExecutor:
    """
    Sprint 执行器
    
    统一执行 Sprint 迭代，被 NormalStrategy 和 EvolutionStrategy 共用。
    支持串行和并行两种执行模式。
    支持 Normal 和 Evolution 两种执行模式。
    
    职责：
    1. 解析 Sprint 任务
    2. 分配给对应 Agent 执行
    3. 跟踪执行状态
    4. 收集执行反馈（通过 FeedbackLoop）
    5. 返回执行结果
    6. 支持并行执行独立任务
    7. 支持 Evolution 模式（通过内部调用 EvolutionEngine）
    """
    
    def __init__(
        self, 
        max_parallel: int = 3,
        feedback_loop: Optional[Any] = None,
        prd: Optional[PRD] = None,
        evolution_engine: Optional[Any] = None,
    ):
        """
        初始化执行器
        
        Args:
            max_parallel: 最大并行任务数
            feedback_loop: 反馈循环实例（可选，用于收集执行反馈）
            prd: PRD 实例（可选，用于反馈关联）
            evolution_engine: 进化引擎实例（可选，用于 Evolution 模式）
        """
        self._agent_executors: Dict[str, Callable] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._max_parallel = max_parallel
        self._event_bus = None  # 延迟导入避免循环依赖
        self._feedback_loop = feedback_loop
        self._prd = prd
        self._sprint_count = 0  # 跟踪执行的 Sprint 数量
        self._evolution_engine = evolution_engine  # 进化引擎（Evolution 模式用）
        self._register_default_executors()
    
    def set_feedback_loop(self, feedback_loop) -> None:
        """设置反馈循环"""
        self._feedback_loop = feedback_loop
    
    def set_prd(self, prd: PRD) -> None:
        """设置 PRD（用于反馈关联）"""
        self._prd = prd
    
    def set_evolution_engine(self, evolution_engine) -> None:
        """设置进化引擎（用于 Evolution 模式）"""
        self._evolution_engine = evolution_engine
        logger.info("✅ EvolutionEngine 已注入到 SprintExecutor")
    
    def get_feedback_history(self) -> List[Any]:
        """
        获取反馈历史
        
        Returns:
            List: 反馈历史列表
        """
        if self._feedback_loop:
            return self._feedback_loop.get_history()
        return []
    
    def _register_default_executors(self):
        """注册默认的 Agent 执行器"""
        self._agent_executors = {
            "coder": self._execute_coder_task,
            "evolver": self._execute_evolver_task,
            "tester": self._execute_tester_task,
        }
    
    def register_agent_executor(self, agent_type: str, executor: Callable):
        """注册自定义 Agent 执行器"""
        self._agent_executors[agent_type] = executor
    
    async def execute_sprint(self, sprint: PRDSprint, context: Dict[str, Any] = None) -> SprintResult:
        """
        执行单个 Sprint
        
        Args:
            sprint: Sprint 定义
            context: 执行上下文
            
        Returns:
            SprintResult: 执行结果
        """
        start_time = time.time()
        result = SprintResult(sprint=sprint, status=TaskStatus.RUNNING)
        
        logger.info(f"🚀 开始执行 Sprint: {sprint.name}")
        
        for task in sprint.tasks:
            task_result = await self._execute_task(task, sprint.name, context or {})
            result.task_results.append(task_result)
        
        # 确定 Sprint 状态
        if all(r.status == TaskStatus.SUCCESS for r in result.task_results):
            result.status = TaskStatus.SUCCESS
        elif any(r.status == TaskStatus.FAILED for r in result.task_results):
            result.status = TaskStatus.FAILED
        else:
            result.status = TaskStatus.SUCCESS
        
        result.duration = time.time() - start_time
        logger.info(f"✅ Sprint 完成: {sprint.name} ({result.duration:.2f}s)")
        
        # 收集反馈（通过 FeedbackLoop）
        self._collect_feedback(sprint, result)
        
        return result
    
    def _collect_feedback(self, sprint: PRDSprint, result: SprintResult) -> None:
        """
        收集执行反馈
        
        Args:
            sprint: Sprint 定义
            result: 执行结果
        """
        if self._feedback_loop is None:
            return
        
        try:
            self._sprint_count += 1
            
            # 准备反馈数据
            feedback_data = {
                "sprint_name": sprint.name,
                "sprint_index": self._sprint_count,
                "task_results": result.task_results,
                "duration": result.duration,
            }
            
            # 如果有 PRD，使用它
            if self._prd:
                feedback = self._feedback_loop.collect(self._prd, [result])
            else:
                # 创建一个简单的 PRD 对象用于反馈
                class SimplePRD:
                    def __init__(self):
                        self.id = f"sprint-{self._sprint_count}"
                        self.project = type("obj", (), {"name": sprint.name})()
                
                feedback = self._feedback_loop.collect(SimplePRD(), [result])
            
            logger.debug(f"📝 反馈已收集: {sprint.name}, 成功率: {feedback.success_rate}%")
            
        except Exception as e:
            logger.warning(f"⚠️ 收集反馈失败: {e}")
    
    async def execute_sprints(
        self, 
        sprints: List[PRDSprint], 
        mode: str = "normal",
        evolution_config: Optional[EvolutionConfig] = None,
        context: Dict[str, Any] = None
    ) -> List[SprintResult]:
        """
        统一执行入口 - 支持 Normal 和 Evolution 两种模式
        
        Args:
            sprints: Sprint 列表
            mode: 执行模式，"normal" 或 "evolution"
            evolution_config: 进化配置（Evolution 模式用）
            context: 执行上下文
            
        Returns:
            List[SprintResult]: 执行结果列表
        """
        if mode == "evolution" and self._evolution_engine:
            return await self._execute_evolution_sprints(sprints, evolution_config, context)
        else:
            return await self._execute_normal_sprints(sprints, context)
    
    async def _execute_normal_sprints(
        self, 
        sprints: List[PRDSprint], 
        context: Dict[str, Any] = None
    ) -> List[SprintResult]:
        """
        Normal 模式执行 - 原有逻辑
        
        Args:
            sprints: Sprint 列表
            context: 执行上下文
            
        Returns:
            List[SprintResult]: 执行结果列表
        """
        logger.info(f"📋 Normal 模式执行 {len(sprints)} 个 Sprint")
        results = []
        for sprint in sprints:
            result = await self.execute_sprint(sprint, context)
            results.append(result)
            # 如果 Sprint 失败，可以选择停止后续执行
            if result.status == TaskStatus.FAILED:
                logger.warning(f"⚠️ Sprint 失败: {sprint.name}")
        return results
    
    async def _execute_evolution_sprints(
        self, 
        sprints: List[PRDSprint],
        evolution_config: Optional[EvolutionConfig],
        context: Dict[str, Any] = None
    ) -> List[SprintResult]:
        """
        Evolution 模式执行 - 通过 EvolutionEngine 增强
        
        Args:
            sprints: Sprint 列表
            evolution_config: 进化配置
            context: 执行上下文
            
        Returns:
            List[SprintResult]: 执行结果列表
        """
        logger.info(f"🔄 Evolution 模式执行 {len(sprints)} 个 Sprint")
        results = []
        
        # 获取进化参数
        max_generations = evolution_config.iterations if evolution_config else 3
        
        for sprint in sprints:
            logger.info(f"🔍 开始 Evolution 增强: {sprint.name}")
            
            # 调用 EvolutionEngine 对 Sprint 进行进化
            result = await self._evolution_engine.evolve_sprint(
                sprint=sprint,
                max_generations=max_generations,
            )
            
            # EvolutionEngine.evolve_sprint 返回 EvolutionResult，
            # 需要转换为 SprintResult 格式
            sprint_result = self._convert_evolution_result(sprint, result)
            results.append(sprint_result)
            
            # 收集反馈
            self._collect_feedback(sprint, sprint_result)
        
        logger.info(f"✅ Evolution 模式完成: {len(results)} 个 Sprint")
        return results
    
    def _convert_evolution_result(self, sprint: PRDSprint, evo_result: Any) -> SprintResult:
        """
        将 EvolutionResult 转换为 SprintResult
        
        Args:
            sprint: 原始 Sprint
            evo_result: EvolutionResult
            
        Returns:
            SprintResult: 转换后的 Sprint 结果
        """
        # 判断成功与否
        success = evo_result.success if hasattr(evo_result, 'success') else True
        
        # 创建 SprintResult
        sprint_result = SprintResult(
            sprint=sprint,
            status=TaskStatus.SUCCESS if success else TaskStatus.FAILED,
            duration=evo_result.execution_time if hasattr(evo_result, 'execution_time') else 0.0,
        )
        
        # 如果有任务结果，添加到 SprintResult
        if hasattr(evo_result, 'selected_genes') and evo_result.selected_genes:
            for gene in evo_result.selected_genes:
                # 将进化的基因作为任务结果
                task = PRDTask(
                    task=f"Evolution Gene: {gene.id[:8]}",
                    agent="evolver",
                    target=gene.metadata.get("file") if hasattr(gene, 'metadata') else None,
                )
                task_result = TaskResult(
                    task=task,
                    sprint_name=sprint.name,
                    status=TaskStatus.SUCCESS,
                    output=gene.content[:500] if hasattr(gene, 'content') else "",
                )
                sprint_result.task_results.append(task_result)
        
        return sprint_result
    
    def set_event_bus(self, event_bus) -> None:
        """设置事件总线"""
        self._event_bus = event_bus
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """发送事件"""
        if self._event_bus:
            from .events import Event, EventType
            try:
                event = Event(type=EventType[event_type.upper()], data=data)
                await self._event_bus.emit(event)
            except KeyError:
                logger.warning(f"Unknown event type: {event_type}")
    
    async def execute_sprint_parallel(
        self, 
        sprint: PRDSprint, 
        context: Dict[str, Any] = None,
        dependency_map: Dict[int, Set[int]] = None
    ) -> SprintResult:
        """
        并行执行 Sprint（同一 Sprint 内的独立任务并行）
        
        Args:
            sprint: Sprint 定义
            context: 执行上下文
            dependency_map: 任务依赖关系，格式 {task_idx: {dependent_task_indices}}
                            任务只在所有依赖完成后才执行
            
        Returns:
            SprintResult: 执行结果
        """
        from .events import EventType
        
        start_time = time.time()
        result = SprintResult(sprint=sprint, status=TaskStatus.RUNNING)
        
        logger.info(f"🚀 开始并行执行 Sprint: {sprint.name} (max_parallel={self._max_parallel})")
        
        # 发送 Sprint 开始事件
        await self._emit_event("sprint_start", {
            "sprint_name": sprint.name,
            "task_count": len(sprint.tasks),
        })
        
        # 任务状态跟踪
        task_count = len(sprint.tasks)
        completed: Set[int] = set()
        running: Set[int] = set()
        task_semaphore = asyncio.Semaphore(self._max_parallel)
        
        async def execute_with_semaphore(task: PRDTask, idx: int) -> TaskResult:
            """带并发限制的任务执行"""
            async with task_semaphore:
                running.add(idx)
                try:
                    return await self._execute_task_with_event(task, sprint.name, context)
                finally:
                    running.discard(idx)
                    completed.add(idx)
        
        async def wait_for_dependencies(idx: int) -> bool:
            """检查依赖是否满足"""
            if dependency_map and idx in dependency_map:
                deps = dependency_map[idx]
                while not deps.issubset(completed):
                    await asyncio.sleep(0.1)
                    # 检查依赖任务是否失败
                    for dep_idx in deps:
                        if dep_idx < idx and result.task_results[dep_idx].status == TaskStatus.FAILED:
                            return False
                return True
            return True
        
        # 创建任务协程
        async def run_task(idx: int) -> None:
            task = sprint.tasks[idx]
            # 等待依赖满足
            if not await wait_for_dependencies(idx):
                result.task_results.append(TaskResult(
                    task=task,
                    sprint_name=sprint.name,
                    status=TaskStatus.SKIPPED,
                    error="依赖任务失败",
                ))
                return
            # 执行任务
            task_result = await execute_with_semaphore(task, idx)
            result.task_results.append(task_result)
        
        # 创建所有任务协程
        task_coroutines = [run_task(i) for i in range(task_count)]
        
        # 并发执行所有任务
        await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # 确定 Sprint 状态
        if all(r.status == TaskStatus.SUCCESS for r in result.task_results):
            result.status = TaskStatus.SUCCESS
        elif any(r.status == TaskStatus.FAILED for r in result.task_results):
            result.status = TaskStatus.FAILED
        else:
            result.status = TaskStatus.SUCCESS
        
        result.duration = time.time() - start_time
        
        # 发送 Sprint 完成事件
        await self._emit_event("sprint_complete", {
            "sprint_name": sprint.name,
            "status": result.status.value,
            "success_count": result.success_count,
            "failed_count": result.failed_count,
            "duration": result.duration,
        })
        
        logger.info(f"✅ Sprint 完成: {sprint.name} ({result.duration:.2f}s, "
                   f"成功:{result.success_count}, 失败:{result.failed_count})")
        
        return result
    
    async def _execute_task_with_event(
        self, 
        task: PRDTask, 
        sprint_name: str, 
        context: Dict[str, Any]
    ) -> TaskResult:
        """执行单个任务并发送事件"""
        from .events import EventType
        
        # 发送任务开始事件
        await self._emit_event("task_start", {
            "task": task.task[:100],
            "agent": task.agent,
            "target": task.target,
            "sprint_name": sprint_name,
        })
        
        # 执行任务
        result = await self._execute_task(task, sprint_name, context)
        
        # 发送任务完成/失败事件
        if result.status == TaskStatus.SUCCESS:
            await self._emit_event("task_complete", result.to_dict())
        else:
            await self._emit_event("task_failed", result.to_dict())
        
        return result
    
    async def _execute_task(self, task: PRDTask, sprint_name: str, context: Dict[str, Any]) -> TaskResult:
        """执行单个任务"""
        start_time = time.time()
        
        # 获取对应的执行器
        executor = self._agent_executors.get(task.agent)
        if not executor:
            return TaskResult(
                task=task,
                sprint_name=sprint_name,
                status=TaskStatus.FAILED,
                error=f"未知的 Agent 类型: {task.agent}",
            )
        
        try:
            # 执行任务
            output = await executor(task, context)
            duration = time.time() - start_time
            
            return TaskResult(
                task=task,
                sprint_name=sprint_name,
                status=TaskStatus.SUCCESS,
                output=output,
                duration=duration,
            )
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            return TaskResult(
                task=task,
                sprint_name=sprint_name,
                status=TaskStatus.FAILED,
                error=str(e),
                duration=time.time() - start_time,
            )
    
    async def _execute_coder_task(self, task: PRDTask, context: Dict[str, Any]) -> str:
        """
        执行编码任务
        
        这是一个占位实现，实际使用时应该被真实的 Agent 执行器替换。
        """
        logger.info(f"🤖 执行编码任务: {task.task[:50]}...")
        await asyncio.sleep(0.1)  # 模拟执行
        return f"完成: {task.task}"
    
    async def _execute_evolver_task(self, task: PRDTask, context: Dict[str, Any]) -> str:
        """
        执行进化任务
        
        这是一个占位实现，实际使用时应该被真实的 Agent 执行器替换。
        """
        logger.info(f"🧬 执行进化任务: {task.task[:50]}...")
        await asyncio.sleep(0.1)  # 模拟执行
        return f"进化完成: {task.task}"
    
    async def _execute_tester_task(self, task: PRDTask, context: Dict[str, Any]) -> str:
        """
        执行测试任务
        
        这是一个占位实现，实际使用时应该被真实的 Agent 执行器替换。
        """
        logger.info(f"🧪 执行测试任务: {task.task[:50]}...")
        await asyncio.sleep(0.1)  # 模拟执行
        return f"测试完成: {task.task}"
