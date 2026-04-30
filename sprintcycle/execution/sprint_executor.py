"""
Sprint 执行器 - 统一的 Sprint 迭代执行
支持断点续传（通过 StateStore 集成）。
"""

import asyncio
import logging
import time
import re
import uuid
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..prd.models import PRD, PRDSprint, PRDTask, ExecutionMode, EvolutionConfig
from .state_store import StateStore, ExecutionState, ExecutionStateStatus, get_state_store

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
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
    支持断点续传（通过 StateStore）。
    """
    
    def __init__(
        self, 
        max_parallel: int = 3,
        feedback_loop: Optional[Any] = None,
        prd: Optional[PRD] = None,
        evolution_engine: Optional[Any] = None,
        error_handler: Optional[Any] = None,
        state_store: Optional[StateStore] = None,
    ):
        self._agent_executors: Dict[str, Callable] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._max_parallel = max_parallel
        self._event_bus = None
        self._feedback_loop = feedback_loop
        self._prd = prd
        self._sprint_count = 0
        self._evolution_engine = evolution_engine
        self._error_handler = error_handler
        self._state_store = state_store
        self._execution_id: Optional[str] = None
        self._checkpoint_interval = 1
        self._register_default_executors()
    
    @property
    def state_store(self) -> StateStore:
        if self._state_store is None:
            self._state_store = get_state_store()
        return self._state_store
    
    def set_state_store(self, state_store: StateStore) -> None:
        self._state_store = state_store
        logger.info("StateStore 已注入到 SprintExecutor")
    
    def set_feedback_loop(self, feedback_loop) -> None:
        self._feedback_loop = feedback_loop
    
    def set_prd(self, prd: PRD) -> None:
        self._prd = prd
    
    def set_evolution_engine(self, evolution_engine) -> None:
        self._evolution_engine = evolution_engine
    
    def set_error_handler(self, error_handler) -> None:
        self._error_handler = error_handler
    
    def get_feedback_history(self) -> List[Any]:
        if self._feedback_loop:
            return self._feedback_loop.get_history()
        return []
    
    def _init_execution_state(self, prd: Optional[PRD] = None) -> str:
        if self._execution_id is None:
            self._execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        total_sprints = len(prd.sprints) if prd else (len(self._prd.sprints) if self._prd else 0)
        total_tasks = prd.total_tasks if prd else (self._prd.total_tasks if self._prd else 0)
        
        state = ExecutionState(
            execution_id=self._execution_id,
            prd_name=prd.project.name if prd and prd.project else (self._prd.project.name if self._prd else "unknown"),
            mode="normal",
            status=ExecutionStateStatus.RUNNING,
            total_sprints=total_sprints,
            total_tasks=total_tasks,
        )
        
        self.state_store.save(state)
        logger.info(f"执行状态已初始化: {self._execution_id}")
        return self._execution_id
    
    def _save_checkpoint(
        self, 
        sprint_idx: int, 
        sprint_name: str, 
        sprint_result: SprintResult
    ) -> None:
        if not self._execution_id:
            return
        
        task_results = [r.to_dict() for r in sprint_result.task_results]
        
        success = self.state_store.create_checkpoint(
            execution_id=self._execution_id,
            sprint_idx=sprint_idx,
            sprint_name=sprint_name,
            task_results=task_results,
        )
        
        if success:
            self.state_store.increment_progress(
                execution_id=self._execution_id,
                completed_tasks=sprint_result.success_count,
                completed_sprints=1,
            )
            logger.debug(f"检查点已保存: {sprint_name}")
    
    def can_resume(self, execution_id: str) -> bool:
        return self.state_store.can_resume(execution_id)
    
    def get_resume_point(self, execution_id: str) -> Optional[Dict[str, Any]]:
        return self.state_store.get_resume_point(execution_id)
    
    def load_execution_state(self, execution_id: str) -> Optional[ExecutionState]:
        return self.state_store.load(execution_id)
    
    def pause_execution(self) -> bool:
        if not self._execution_id:
            return False
        return self.state_store.update_status(
            execution_id=self._execution_id,
            status=ExecutionStateStatus.PAUSED,
        )
    
    def resume_execution(self, execution_id: str) -> bool:
        state = self.load_execution_state(execution_id)
        if not state or state.status != ExecutionStateStatus.PAUSED:
            return False
        self._execution_id = execution_id
        return self.state_store.update_status(
            execution_id=execution_id,
            status=ExecutionStateStatus.RUNNING,
        )
    
    def _register_default_executors(self):
        self._agent_executors = {
            "coder": self._execute_coder_task,
            "evolver": self._execute_evolver_task,
            "tester": self._execute_tester_task,
        }
    
    def register_agent_executor(self, agent_type: str, executor: Callable):
        self._agent_executors[agent_type] = executor
    
    TASK_SPLIT_THRESHOLD = 500
    MAX_SUBTASKS = 5
    
    def _should_split_task(self, task: PRDTask) -> bool:
        if len(task.task) >= self.TASK_SPLIT_THRESHOLD:
            return True
        complex_keywords = ["重构", "迁移", "优化", "重写", "implement", "refactor", "migrate", "optimize", "rewrite"]
        task_lower = task.task.lower()
        keyword_count = sum(1 for kw in complex_keywords if kw.lower() in task_lower)
        return keyword_count >= 2
    
    def _split_task(self, task: PRDTask) -> List[PRDTask]:
        subtasks = []
        task_text = task.task
        action_patterns = [
            r"实现[^\s，,。]+", r"添加[^\s，,。]+", r"修改[^\s，,。]+",
            r"修复[^\s，,。]+", r"优化[^\s，,。]+", r"创建[^\s，,。]+",
        ]
        subtask_parts = []
        for pattern in action_patterns:
            matches = re.findall(pattern, task_text, re.IGNORECASE)
            subtask_parts.extend(matches)
        
        if len(subtask_parts) >= 2:
            for i, part in enumerate(subtask_parts[:self.MAX_SUBTASKS]):
                subtask = PRDTask(
                    task=part.strip(),
                    agent=task.agent,
                    target=task.target,
                    constraints=task.constraints.copy(),
                    expected_output=task.expected_output,
                    timeout=task.timeout,
                )
                subtasks.append(subtask)
        else:
            subtask = PRDTask(
                task=task_text[:self.TASK_SPLIT_THRESHOLD] + "..." if len(task_text) > self.TASK_SPLIT_THRESHOLD else task_text,
                agent=task.agent,
                target=task.target,
                constraints=task.constraints.copy(),
                expected_output=task.expected_output,
                timeout=task.timeout,
            )
            subtasks.append(subtask)
        return subtasks
    
    def split_sprint_tasks(self, sprint: PRDSprint) -> PRDSprint:
        new_sprint = PRDSprint(name=sprint.name, goals=sprint.goals.copy(), tasks=[])
        for task in sprint.tasks:
            if self._should_split_task(task):
                subtasks = self._split_task(task)
                new_sprint.tasks.extend(subtasks)
            else:
                new_sprint.tasks.append(task)
        return new_sprint
    
    async def execute_sprint(self, sprint: PRDSprint, context: Dict[str, Any] = None, save_checkpoint: bool = True) -> SprintResult:
        start_time = time.time()
        result = SprintResult(sprint=sprint, status=TaskStatus.RUNNING)
        logger.info(f"开始执行 Sprint: {sprint.name}")
        
        for task in sprint.tasks:
            task_result = await self._execute_task(task, sprint.name, context or {})
            result.task_results.append(task_result)
        
        if all(r.status == TaskStatus.SUCCESS for r in result.task_results):
            result.status = TaskStatus.SUCCESS
        elif any(r.status == TaskStatus.FAILED for r in result.task_results):
            result.status = TaskStatus.FAILED
        else:
            result.status = TaskStatus.SUCCESS
        
        result.duration = time.time() - start_time
        self._collect_feedback(sprint, result)
        
        if save_checkpoint and self._execution_id:
            self._save_checkpoint(0, sprint.name, result)
        
        return result
    
    def _collect_feedback(self, sprint: PRDSprint, result: SprintResult) -> None:
        if self._feedback_loop is None:
            return
        try:
            self._sprint_count += 1
            if self._prd:
                feedback = self._feedback_loop.collect(self._prd, [result])
            else:
                class SimplePRD:
                    def __init__(self):
                        self.id = f"sprint-{self._sprint_count}"
                        self.project = type("obj", (), {"name": sprint.name})()
                feedback = self._feedback_loop.collect(SimplePRD(), [result])
            self._feedback_loop.save(feedback)
        except Exception as e:
            logger.warning(f"收集反馈失败: {e}")
    
    async def execute_sprints(
        self, sprints: List[PRDSprint], mode: str = "normal",
        evolution_config: Optional[EvolutionConfig] = None,
        context: Dict[str, Any] = None,
        execution_id: Optional[str] = None,
        resume: bool = False,
    ) -> List[SprintResult]:
        if resume and execution_id:
            return await self._resume_execution(execution_id, sprints, context)
        self._execution_id = execution_id or self._init_execution_state()
        if mode == "evolution" and self._evolution_engine:
            return await self._execute_evolution_sprints(sprints, evolution_config, context)
        return await self._execute_normal_sprints(sprints, context)
    
    async def _resume_execution(self, execution_id: str, sprints: List[PRDSprint], context: Dict[str, Any] = None) -> List[SprintResult]:
        logger.info(f"从断点恢复执行: {execution_id}")
        state = self.load_execution_state(execution_id)
        if not state:
            return []
        resume_point = self.get_resume_point(execution_id)
        if not resume_point:
            return []
        start_sprint_idx = resume_point.get("current_sprint", 0)
        self._execution_id = execution_id
        self.state_store.update_status(execution_id, ExecutionStateStatus.RUNNING)
        results = []
        for i, sprint in enumerate(sprints):
            if i < start_sprint_idx:
                continue
            result = await self.execute_sprint(sprint, context, save_checkpoint=True)
            results.append(result)
            if result.status == TaskStatus.FAILED:
                break
        return results
    
    async def _execute_normal_sprints(self, sprints: List[PRDSprint], context: Dict[str, Any] = None) -> List[SprintResult]:
        results = []
        for sprint in sprints:
            result = await self.execute_sprint(sprint, context, save_checkpoint=True)
            results.append(result)
            if result.status == TaskStatus.FAILED:
                logger.warning(f"Sprint 失败: {sprint.name}")
        return results
    
    async def _execute_evolution_sprints(self, sprints: List[PRDSprint], evolution_config: Optional[EvolutionConfig], context: Dict[str, Any] = None) -> List[SprintResult]:
        results = []
        max_generations = evolution_config.iterations if evolution_config else 3
        for sprint in sprints:
            result = await self._evolution_engine.evolve_sprint(sprint=sprint, max_generations=max_generations)
            sprint_result = self._convert_evolution_result(sprint, result)
            results.append(sprint_result)
            if self._execution_id:
                self._save_checkpoint(0, sprint.name, sprint_result)
        return results
    
    def _convert_evolution_result(self, sprint: PRDSprint, evo_result: Any) -> SprintResult:
        success = evo_result.success if hasattr(evo_result, "success") else True
        sprint_result = SprintResult(
            sprint=sprint,
            status=TaskStatus.SUCCESS if success else TaskStatus.FAILED,
            duration=evo_result.execution_time if hasattr(evo_result, "execution_time") else 0.0,
        )
        if hasattr(evo_result, "selected_genes") and evo_result.selected_genes:
            for gene in evo_result.selected_genes:
                task = PRDTask(task=f"Evolution Gene: {gene.id[:8]}", agent="evolver")
                task_result = TaskResult(task=task, sprint_name=sprint.name, status=TaskStatus.SUCCESS)
                sprint_result.task_results.append(task_result)
        return sprint_result
    
    def set_event_bus(self, event_bus) -> None:
        self._event_bus = event_bus
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if self._event_bus:
            from .events import Event, EventType
            try:
                event = Event(type=EventType[event_type.upper()], data=data)
                await self._event_bus.emit(event)
            except KeyError:
                pass
    
    async def execute_sprint_parallel(self, sprint: PRDSprint, context: Dict[str, Any] = None, dependency_map: Dict[int, Set[int]] = None, save_checkpoint: bool = True) -> SprintResult:
        start_time = time.time()
        result = SprintResult(sprint=sprint, status=TaskStatus.RUNNING)
        task_count = len(sprint.tasks)
        completed: Set[int] = set()
        task_semaphore = asyncio.Semaphore(self._max_parallel)
        
        async def execute_with_semaphore(task: PRDTask, idx: int) -> TaskResult:
            async with task_semaphore:
                return await self._execute_task_with_event(task, sprint.name, context)
        
        async def run_task(idx: int) -> None:
            task = sprint.tasks[idx]
            task_result = await execute_with_semaphore(task, idx)
            result.task_results.append(task_result)
        
        task_coroutines = [run_task(i) for i in range(task_count)]
        await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        if all(r.status == TaskStatus.SUCCESS for r in result.task_results):
            result.status = TaskStatus.SUCCESS
        elif any(r.status == TaskStatus.FAILED for r in result.task_results):
            result.status = TaskStatus.FAILED
        else:
            result.status = TaskStatus.SUCCESS
        
        result.duration = time.time() - start_time
        
        if save_checkpoint and self._execution_id:
            self._save_checkpoint(0, sprint.name, result)
        
        return result
    
    async def _execute_task_with_event(self, task: PRDTask, sprint_name: str, context: Dict[str, Any]) -> TaskResult:
        result = await self._execute_task(task, sprint_name, context)
        return result
    
    async def _execute_task(self, task: PRDTask, sprint_name: str, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        executor = self._agent_executors.get(task.agent)
        if not executor:
            return TaskResult(task=task, sprint_name=sprint_name, status=TaskStatus.FAILED, error=f"未知的 Agent 类型: {task.agent}")
        try:
            output = await executor(task, context)
            return TaskResult(task=task, sprint_name=sprint_name, status=TaskStatus.SUCCESS, output=output, duration=time.time() - start_time)
        except Exception as e:
            return TaskResult(task=task, sprint_name=sprint_name, status=TaskStatus.FAILED, error=str(e), duration=time.time() - start_time)
    
    async def _execute_coder_task(self, task: PRDTask, context: Dict[str, Any]) -> str:
        await asyncio.sleep(0.1)
        return f"完成: {task.task}"
    
    async def _execute_evolver_task(self, task: PRDTask, context: Dict[str, Any]) -> str:
        await asyncio.sleep(0.1)
        return f"进化完成: {task.task}"
    
    async def _execute_tester_task(self, task: PRDTask, context: Dict[str, Any]) -> str:
        await asyncio.sleep(0.1)
        return f"测试完成: {task.task}"


    def _analyze_dependencies(
        self, 
        tasks: List[PRDTask],
        context: Dict[str, Any] = None
    ) -> Dict[int, Set[int]]:
        """
        分析任务间的依赖关系
        
        Args:
            tasks: 任务列表
            context: 执行上下文
            
        Returns:
            Dict[int, Set[int]]: 任务索引到其依赖任务索引集合的映射
        """
        dependency_map: Dict[int, Set[int]] = {i: set() for i in range(len(tasks))}
        
        # 对每个任务分析依赖
        for i, task in enumerate(tasks):
            self._add_keyword_based_dependencies(tasks, i, task, dependency_map)
            self._add_target_path_dependencies(tasks, i, task, dependency_map)
            self._add_agent_type_dependencies(tasks, i, task, dependency_map)
        
        # 移除自引用
        for idx in dependency_map:
            dependency_map[idx].discard(idx)
        
        return dependency_map

    def _add_keyword_based_dependencies(
        self,
        tasks: List[PRDTask],
        task_idx: int,
        task: PRDTask,
        dep_map: Dict[int, Set[int]]
    ) -> None:
        """基于关键词分析依赖关系"""
        dependency_keywords = [
            ("测试", "实现"), ("test", "implement"),
            ("verify", "build"), ("build", "compile"),
            ("集成", "单元"), ("integration", "unit"),
            ("端到端", "模块"), ("e2e", "module"),
            ("部署", "构建"), ("deploy", "build"),
        ]
        
        task_text = task.task.lower()
        
        for dep_kw, src_kw in dependency_keywords:
            if dep_kw in task_text:
                for j in range(task_idx):
                    prev_text = tasks[j].task.lower()
                    prev_target = (tasks[j].target or "").lower()
                    if src_kw in prev_text or src_kw in prev_target:
                        dep_map[task_idx].add(j)

    def _add_target_path_dependencies(
        self,
        tasks: List[PRDTask],
        task_idx: int,
        task: PRDTask,
        dep_map: Dict[int, Set[int]]
    ) -> None:
        """基于target文件路径分析依赖关系"""
        if not task.target:
            return
        
        task_ext = task.target.lower().split('.')[-1] if '.' in task.target.lower() else ''
        code_extensions = {'py', 'ts', 'js', 'go', 'java'}
        
        if task_ext not in code_extensions:
            return
        
        for j in range(task_idx):
            prev_task = tasks[j]
            if not prev_task.target:
                continue
            
            prev_ext = prev_task.target.lower().split('.')[-1] if '.' in prev_task.target.lower() else ''
            if prev_ext == task_ext:
                dep_map[task_idx].add(j)

    def _add_agent_type_dependencies(
        self,
        tasks: List[PRDTask],
        task_idx: int,
        task: PRDTask,
        dep_map: Dict[int, Set[int]]
    ) -> None:
        """基于任务类型/agent分析依赖关系"""
        task_text = task.task.lower()
        
        # Agent类型依赖: 测试任务依赖实现任务
        if task.agent == "tester":
            for j in range(task_idx):
                if tasks[j].agent in ["coder", "implement"]:
                    dep_map[task_idx].add(j)
        
        # 任务文本依赖规则
        dep_rules = [
            (["build", "编译"], ["compile", "编译"]),
            (["deploy", "部署"], ["build", "构建"]),
        ]
        
        for target_kws, source_kws in dep_rules:
            if any(kw in task_text for kw in target_kws):
                for j in range(task_idx):
                    prev_text = tasks[j].task.lower()
                    if any(kw in prev_text for kw in source_kws):
                        dep_map[task_idx].add(j)


    def _extract_file_paths(self, text: str) -> List[str]:
        """从文本中提取文件路径"""
        import re
        patterns = [
            r'(?:from|import|include|require)\s+["\']([^"\']+)["\']',
            r'[\'"][\./]*([\w/]+\.[\w]+)[\'"]',
            r'path:\s*["\']?([^"\'\s]+)["\']?',
            r'file:\s*["\']?([^"\'\s]+)["\']?',
        ]
        
        paths = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            paths.extend(matches)
        
        return list(set(paths))
    
    def get_execution_order(self, tasks: List[PRDTask]) -> List[List[int]]:
        """
        获取任务的拓扑排序执行顺序
        
        Args:
            tasks: 任务列表
            
        Returns:
            List[List[int]]: 分批执行的任务索引列表
            例如: [[0, 1], [2], [3, 4]] 表示任务分三批执行
        """
        dependency_map = self._analyze_dependencies(tasks)
        
        # 计算每个任务的入度
        in_degree = {i: len(deps) for i, deps in dependency_map.items()}
        remaining = set(range(len(tasks)))
        
        batches: List[List[int]] = []
        
        while remaining:
            # 找到入度为0的任务
            ready = [i for i in remaining if in_degree.get(i, 0) == 0]
            
            if not ready:
                # 存在循环依赖，随机选择一个
                ready = [min(remaining)]
            
            batches.append(ready)
            
            # 更新入度
            for task_idx in ready:
                remaining.discard(task_idx)
                for other_idx, deps in dependency_map.items():
                    if task_idx in deps:
                        in_degree[other_idx] -= 1
        
        return batches
