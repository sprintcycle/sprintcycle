"""
ConcurrentExecutor - 任务并发执行器

功能:
- 使用 asyncio.Semaphore 控制并发数量
- 实现优先级队列
- 支持任务依赖管理
- 提供实时进度回调
"""

import asyncio
import heapq
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Awaitable
from enum import IntEnum
from datetime import datetime
from collections import defaultdict
from loguru import logger
import uuid


class TaskPriority(IntEnum):
    """任务优先级（数值越小优先级越高）"""
    CRITICAL = 0   # 关键路径任务
    HIGH = 1       # 高优先级
    NORMAL = 2     # 普通任务
    LOW = 3        # 低优先级
    BACKGROUND = 4 # 后台任务


@dataclass
class PriorityTask:
    """
    优先级任务
    
    支持:
    - 优先级排序
    - 依赖管理
    - 状态追踪
    - 重试机制
    """
    id: str
    task: Callable[[], Awaitable[Any]]  # 异步任务函数
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    max_retries: int = 2
    timeout: float = 300  # 超时时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 运行时状态
    status: str = "pending"  # pending, running, completed, failed, cancelled
    retry_count: int = 0
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def __lt__(self, other: "PriorityTask") -> bool:
        """用于堆排序 - 优先级高的先执行"""
        return self.priority < other.priority
    
    @property
    def duration(self) -> float:
        """执行时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0
    
    @property
    def is_completed(self) -> bool:
        return self.status in ("completed", "failed", "cancelled")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "priority": self.priority.name,
            "status": self.status,
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "duration": self.duration,
            "metadata": self.metadata
        }


class PriorityQueue:
    """
    优先级队列
    
    基于堆实现，支持:
    - O(log n) 入队和出队
    - 按优先级排序
    - 任务状态追踪
    """
    
    def __init__(self):
        self._heap: List[PriorityTask] = []
        self._tasks: Dict[str, PriorityTask] = {}
        self._completed: set = set()
    
    def enqueue(self, task: PriorityTask) -> None:
        """入队"""
        heapq.heappush(self._heap, task)
        self._tasks[task.id] = task
        logger.debug(f"任务入队: {task.id} (优先级: {task.priority.name})")
    
    def dequeue(self) -> Optional[PriorityTask]:
        """出队 - 返回最高优先级且依赖已满足的任务"""
        while self._heap:
            task = heapq.heappop(self._heap)
            
            # 检查任务是否已被取消或完成
            if task.status in ("cancelled", "completed", "failed"):
                continue
            
            # 检查依赖是否满足
            if self._check_dependencies(task):
                return task
            else:
                # 依赖未满足，放回队列末尾
                heapq.heappush(self._heap, task)
                break
        
        return None
    
    def _check_dependencies(self, task: PriorityTask) -> bool:
        """检查依赖是否已满足"""
        for dep_id in task.dependencies:
            if dep_id not in self._completed:
                dep = self._tasks.get(dep_id)
                if dep and dep.status != "completed":
                    return False
        return True
    
    def mark_completed(self, task_id: str) -> None:
        """标记任务完成"""
        self._completed.add(task_id)
    
    def get_task(self, task_id: str) -> Optional[PriorityTask]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def __len__(self) -> int:
        return len(self._heap)
    
    def is_empty(self) -> bool:
        return len(self._heap) == 0


@dataclass
class ExecutionStats:
    """执行统计"""
    total_tasks: int = 0
    completed: int = 0
    failed: int = 0
    running: int = 0
    pending: int = 0
    total_duration: float = 0
    avg_duration: float = 0
    throughput: float = 0  # tasks/sec
    
    def update(self, task: PriorityTask):
        """更新统计"""
        self.total_tasks = len([t for t in task.metadata.values() if hasattr(t, 'status')])
        self.completed = sum(1 for t in self._get_all_tasks() if t.status == "completed")
        self.failed = sum(1 for t in self._get_all_tasks() if t.status == "failed")
        self.running = sum(1 for t in self._get_all_tasks() if t.status == "running")
        self.pending = self.total_tasks - self.completed - self.failed - self.running
    
    def _get_all_tasks(self) -> List[PriorityTask]:
        return list(task.metadata.values()) if hasattr(task.metadata, 'values') else []


class ConcurrentExecutor:
    """
    并发执行器
    
    特性:
    - Semaphore 控制最大并发数
    - 优先级队列调度
    - 依赖管理
    - 实时进度回调
    - 超时和重试机制
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        max_retries: int = 2,
        default_timeout: float = 300,
        on_progress: Callable[[str, str, int], None] = None,
        on_complete: Callable[[str, Any], None] = None,
        on_error: Callable[[str, Exception], None] = None
    ):
        """
        初始化执行器
        
        Args:
            max_concurrent: 最大并发数
            max_retries: 默认最大重试次数
            default_timeout: 默认超时时间（秒）
            on_progress: 进度回调 (task_id, status, progress)
            on_complete: 完成回调 (task_id, result)
            on_error: 错误回调 (task_id, error)
        """
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.default_timeout = default_timeout
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._queue = PriorityQueue()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._start_time: Optional[datetime] = None
        self._is_shutdown = False
        
        logger.info(f"ConcurrentExecutor 初始化完成 (max_concurrent={max_concurrent})")
    
    @property
    def stats(self) -> ExecutionStats:
        """获取执行统计"""
        all_tasks = list(self._queue._tasks.values())
        completed = [t for t in all_tasks if t.status == "completed"]
        failed = [t for t in all_tasks if t.status == "failed"]
        running = [t for t in all_tasks if t.status == "running"]
        
        total_duration = sum(t.duration for t in completed) if completed else 0
        
        return ExecutionStats(
            total_tasks=len(all_tasks),
            completed=len(completed),
            failed=len(failed),
            running=len(running),
            pending=len(all_tasks) - len(completed) - len(failed) - len(running),
            total_duration=total_duration,
            avg_duration=total_duration / len(completed) if completed else 0
        )
    
    def create_task(
        self,
        task_fn: Callable[[], Awaitable[Any]],
        task_id: str = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[str] = None,
        max_retries: int = None,
        timeout: float = None,
        **metadata
    ) -> PriorityTask:
        """
        创建任务
        
        Args:
            task_fn: 异步任务函数
            task_id: 任务ID（自动生成）
            priority: 优先级
            dependencies: 依赖的任务ID
            max_retries: 最大重试次数
            timeout: 超时时间
            **metadata: 额外元数据
            
        Returns:
            PriorityTask
        """
        task_id = task_id or str(uuid.uuid4())[:8]
        
        task = PriorityTask(
            id=task_id,
            task=task_fn,
            priority=priority,
            dependencies=dependencies or [],
            max_retries=max_retries or self.max_retries,
            timeout=timeout or self.default_timeout,
            metadata=metadata
        )
        
        return task
    
    async def submit(self, task: PriorityTask) -> str:
        """提交任务到队列"""
        async with self._lock:
            self._queue.enqueue(task)
            logger.debug(f"任务已提交: {task.id}")
        
        # 尝试调度
        asyncio.create_task(self._schedule())
        
        return task.id
    
    async def submit_batch(self, tasks: List[PriorityTask]) -> List[str]:
        """批量提交任务"""
        task_ids = []
        async with self._lock:
            for task in tasks:
                self._queue.enqueue(task)
                task_ids.append(task.id)
        
        # 启动调度
        asyncio.create_task(self._schedule())
        
        logger.info(f"批量提交 {len(tasks)} 个任务")
        return task_ids
    
    async def _schedule(self):
        """调度任务执行"""
        if self._is_shutdown:
            return
        
        # 初始化信号量
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 获取可执行的任务
        while not self._queue.is_empty():
            # 检查并发限制
            async with self._lock:
                if len(self._running_tasks) >= self.max_concurrent:
                    break
            
            task = self._queue.dequeue()
            if task is None:
                break
            
            # 创建执行任务
            asyncio.create_task(self._execute_task(task))
    
    async def _execute_task(self, task: PriorityTask):
        """执行单个任务"""
        task_id = task.id
        task.status = "running"
        task.start_time = datetime.now()
        
        async with self._lock:
            self._running_tasks[task_id] = asyncio.current_task()
        
        if self.on_progress:
            self.on_progress(task_id, "running", 0)
        
        logger.info(f"开始执行任务: {task_id}")
        
        try:
            # 使用信号量控制并发
            async with self._semaphore:
                # 使用超时包装
                result = await asyncio.wait_for(
                    task.task(),
                    timeout=task.timeout
                )
            
            # 任务成功
            task.status = "completed"
            task.result = result
            task.end_time = datetime.now()
            
            async with self._lock:
                self._results[task_id] = result
                self._queue.mark_completed(task_id)
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]
            
            if self.on_progress:
                self.on_progress(task_id, "completed", 100)
            if self.on_complete:
                self.on_complete(task_id, result)
            
            logger.info(f"任务完成: {task_id} (耗时: {task.duration:.2f}s)")
            
        except asyncio.TimeoutError:
            await self._handle_task_failure(task, f"任务超时 ({task.timeout}s)")
            
        except Exception as e:
            await self._handle_task_failure(task, str(e))
        
        # 继续调度其他任务
        asyncio.create_task(self._schedule())
    
    async def _handle_task_failure(self, task: PriorityTask, error: str):
        """处理任务失败"""
        task.retry_count += 1
        task.error = error
        
        if task.retry_count < task.max_retries:
            # 重试
            task.status = "pending"
            task.end_time = datetime.now()
            async with self._lock:
                self._queue.enqueue(task)
            logger.warning(f"任务 {task.id} 失败，将在 {task.retry_count + 1} 次重试")
        else:
            # 最终失败
            task.status = "failed"
            task.end_time = datetime.now()
            
            async with self._lock:
                self._errors[task_id] = error
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]
            
            if self.on_progress:
                self.on_progress(task_id, "failed", 0)
            if self.on_error:
                self.on_error(task_id, Exception(error))
            
            logger.error(f"任务 {task.id} 最终失败: {error}")
    
    async def wait_all(self, timeout: float = None) -> Dict[str, Any]:
        """等待所有任务完成"""
        start = datetime.now()
        
        while True:
            async with self._lock:
                all_done = (
                    self._queue.is_empty() and 
                    len(self._running_tasks) == 0
                )
            
            if all_done:
                break
            
            if timeout and (datetime.now() - start).total_seconds() > timeout:
                raise asyncio.TimeoutError("等待所有任务完成超时")
            
            await asyncio.sleep(0.1)
        
        return {
            "results": self._results.copy(),
            "errors": self._errors.copy(),
            "stats": self.stats.__dict__
        }
    
    async def get_result(self, task_id: str, timeout: float = 60) -> Any:
        """获取单个任务结果"""
        start = datetime.now()
        
        while True:
            async with self._lock:
                if task_id in self._results:
                    return self._results[task_id]
                if task_id in self._errors:
                    raise Exception(self._errors[task_id])
            
            if (datetime.now() - start).total_seconds() > timeout:
                raise asyncio.TimeoutError(f"获取任务 {task_id} 结果超时")
            
            await asyncio.sleep(0.1)
    
    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        task = self._queue.get_task(task_id)
        if task and task.status == "pending":
            task.status = "cancelled"
            logger.info(f"任务已取消: {task_id}")
            return True
        return False
    
    async def shutdown(self):
        """关闭执行器"""
        self._is_shutdown = True
        
        # 取消所有运行中的任务
        async with self._lock:
            for task_id, running_task in self._running_tasks.items():
                running_task.cancel()
                task = self._queue.get_task(task_id)
                if task:
                    task.status = "cancelled"
            self._running_tasks.clear()
        
        logger.info("ConcurrentExecutor 已关闭")


# ============ 便捷函数 ============

def create_executor(
    max_concurrent: int = 5,
    **kwargs
) -> ConcurrentExecutor:
    """创建并发执行器"""
    return ConcurrentExecutor(max_concurrent=max_concurrent, **kwargs)


async def run_tasks_parallel(
    tasks: List[Callable[[], Awaitable[Any]]],
    max_concurrent: int = 5,
    priority: TaskPriority = TaskPriority.NORMAL
) -> List[Any]:
    """
    并行运行多个任务
    
    Args:
        tasks: 异步任务函数列表
        max_concurrent: 最大并发数
        priority: 任务优先级
        
    Returns:
        任务结果列表
    """
    executor = ConcurrentExecutor(max_concurrent=max_concurrent)
    
    # 提交所有任务
    priority_tasks = [
        executor.create_task(task, priority=priority)
        for task in tasks
    ]
    await executor.submit_batch(priority_tasks)
    
    # 等待完成
    results = await executor.wait_all()
    
    # 按顺序返回结果
    return [results["results"].get(t.id) for t in priority_tasks]
