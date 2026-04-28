"""
SprintCycle 并发调度器
支持多 Sprint 并行执行、任务依赖管理、资源锁机制
"""

import asyncio
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
import uuid


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class Priority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Optional[Callable] = None
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[Exception] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class ResourceLock:
    """资源锁"""
    resource_id: str
    task_id: str
    acquired_at: str = field(default_factory=lambda: datetime.now().isoformat())
    timeout: float = 300.0


class DependencyGraph:
    """任务依赖图"""
    
    def __init__(self):
        self._graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse: Dict[str, Set[str]] = defaultdict(set)
        self._nodes: Set[str] = set()
    
    def add_dependency(self, task_id: str, depends_on: str) -> None:
        self._graph[task_id].add(depends_on)
        self._reverse[depends_on].add(task_id)
        self._nodes.add(task_id)
        self._nodes.add(depends_on)
    
    def get_dependencies(self, task_id: str) -> Set[str]:
        return self._graph.get(task_id, set())
    
    def get_dependents(self, task_id: str) -> Set[str]:
        return self._reverse.get(task_id, set())
    
    def topological_sort(self) -> List[str]:
        """拓扑排序 (Kahn算法)"""
        in_degree = defaultdict(int)
        all_nodes = set()
        
        # 收集所有节点
        for node in self._graph:
            all_nodes.add(node)
            for dep in self._graph[node]:
                all_nodes.add(dep)
        
        # 计算入度
        for node in all_nodes:
            for dep in self._graph.get(node, set()):
                in_degree[node] += 1
        
        # 从入度为0的节点开始
        queue = deque([n for n in all_nodes if in_degree[n] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            for dependent in self._reverse.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        if len(result) != len(all_nodes):
            raise ValueError("Circular dependency detected")
        
        return result
    
    def has_cycle(self) -> bool:
        """检测循环依赖"""
        try:
            self.topological_sort()
            return False
        except ValueError:
            return True
    
    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        """获取可以执行的任务"""
        ready = []
        for task_id in self._nodes:
            if task_id not in completed:
                deps = self._graph.get(task_id, set())
                if deps.issubset(completed):
                    ready.append(task_id)
        return ready


class ResourcePool:
    """资源池"""
    
    def __init__(self):
        self._locks: Dict[str, ResourceLock] = {}
        self._available: Set[str] = set()
        self._lock = threading.RLock()
    
    def add_resource(self, resource_id: str) -> None:
        with self._lock:
            self._available.add(resource_id)
    
    def acquire(self, resource_id: str, task_id: str, timeout: float = 300.0) -> bool:
        with self._lock:
            if resource_id not in self._available:
                if resource_id in self._locks:
                    lock = self._locks[resource_id]
                    acquired_time = datetime.fromisoformat(lock.acquired_at)
                    if (datetime.now() - acquired_time).total_seconds() > lock.timeout:
                        del self._locks[resource_id]
                        self._available.add(resource_id)
                    else:
                        return False
                else:
                    return False
            
            self._available.discard(resource_id)
            self._locks[resource_id] = ResourceLock(resource_id, task_id, timeout=timeout)
            return True
    
    def release(self, resource_id: str, task_id: str) -> bool:
        with self._lock:
            if resource_id in self._locks:
                lock = self._locks[resource_id]
                if lock.task_id == task_id:
                    del self._locks[resource_id]
                    self._available.add(resource_id)
                    return True
            return False
    
    def is_available(self, resource_id: str) -> bool:
        with self._lock:
            return resource_id in self._available


class SprintScheduler:
    """并发调度器"""
    
    def __init__(self, max_concurrency: int = 3):
        self._max_concurrency = max_concurrency
        self._tasks: Dict[str, Task] = {}
        self._running: Set[str] = set()
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._dep_graph = DependencyGraph()
        self._resource_pool = ResourcePool()
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_concurrency)
        self._futures: Dict[str, Future] = {}
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
    
    def add_task(self, task: Task) -> str:
        """添加任务"""
        with self._lock:
            self._tasks[task.id] = task
            for dep_id in task.dependencies:
                self._dep_graph.add_dependency(task.id, dep_id)
            if self._dep_graph.has_cycle():
                self._tasks.pop(task.id)
                raise ValueError(f"Circular dependency detected for task {task.id}")
            return task.id
    
    def add_resource(self, resource_id: str) -> None:
        self._resource_pool.add_resource(resource_id)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)
    
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_tasks": len(self._tasks),
                "running": len(self._running),
                "completed": len(self._completed),
                "failed": len(self._failed),
                "pending": len(self._tasks) - len(self._running) - len(self._completed) - len(self._failed),
                "max_concurrency": self._max_concurrency
            }
    
    async def execute(self, task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        if task_ids is None:
            task_ids = list(self._tasks.keys())
        
        ready_tasks = []
        with self._lock:
            for tid in task_ids:
                task = self._tasks.get(tid)
                if task and task.status == TaskStatus.PENDING:
                    deps = self._dep_graph.get_dependencies(tid)
                    if deps.issubset(self._completed):
                        ready_tasks.append(task)
        
        results = {}
        for task in ready_tasks:
            result = await self._execute_task(task)
            results[task.id] = result
        
        return results
    
    async def _execute_task(self, task: Task) -> Any:
        with self._lock:
            if len(self._running) >= self._max_concurrency:
                task.status = TaskStatus.BLOCKED
                return None
            
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now().isoformat()
            self._running.add(task.id)
        
        try:
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now().isoformat()
            
            with self._lock:
                self._running.discard(task.id)
                self._completed.add(task.id)
            
            for callback in self._callbacks.get(task.id, []):
                callback(task)
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = e
            task.completed_at = datetime.now().isoformat()
            
            with self._lock:
                self._running.discard(task.id)
                self._failed.add(task.id)
            
            raise
    
    def on_complete(self, task_id: str, callback: Callable) -> None:
        self._callbacks[task_id].append(callback)
    
    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._running:
                return False
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.CANCELLED
                return True
            return False
    
    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


def create_parallel_sprints(sprint_count: int = 3) -> SprintScheduler:
    return SprintScheduler(max_concurrency=sprint_count)
