"""SprintScheduler 单元测试"""

import pytest
import asyncio
import time
from sprintcycle.scheduler import (
    SprintScheduler, DependencyGraph, ResourcePool
)
from sprintcycle.scheduler import Task as SchedTask, TaskStatus as SchedTaskStatus, Priority


class TestDependencyGraph:
    """依赖图测试"""
    
    def test_add_dependency(self):
        """测试添加依赖"""
        graph = DependencyGraph()
        graph.add_dependency("task1", "task0")
        assert "task0" in graph.get_dependencies("task1")
    
    def test_topological_sort(self):
        """测试拓扑排序"""
        graph = DependencyGraph()
        graph.add_dependency("task1", "task0")
        graph.add_dependency("task2", "task1")
        sorted_tasks = graph.topological_sort()
        assert sorted_tasks.index("task0") < sorted_tasks.index("task1")
        assert sorted_tasks.index("task1") < sorted_tasks.index("task2")
    
    def test_cycle_detection(self):
        """测试循环检测"""
        graph = DependencyGraph()
        graph.add_dependency("task1", "task0")
        graph.add_dependency("task2", "task1")
        graph.add_dependency("task0", "task2")
        assert graph.has_cycle() is True


class TestResourcePool:
    """资源池测试"""
    
    def test_acquire_release(self):
        """测试资源获取和释放"""
        pool = ResourcePool()
        pool.add_resource("resource1")
        assert pool.acquire("resource1", "task1") is True
        assert pool.is_available("resource1") is False
        assert pool.release("resource1", "task1") is True
        assert pool.is_available("resource1") is True
    
    def test_lock_contention(self):
        """测试锁竞争"""
        pool = ResourcePool()
        pool.add_resource("resource1")
        assert pool.acquire("resource1", "task1") is True
        assert pool.acquire("resource1", "task2") is False


class TestSprintScheduler:
    """调度器测试"""
    
    def setup_method(self):
        self.scheduler = SprintScheduler(max_concurrency=2)
    
    def teardown_method(self):
        self.scheduler.shutdown()
    
    def test_add_task(self):
        """测试添加任务"""
        task = SchedTask(name="test_task", func=lambda: 42)
        task_id = self.scheduler.add_task(task)
        assert task_id is not None
    
    def test_execute_simple(self):
        """测试简单执行"""
        results = []
        def simple_func():
            results.append(1)
            return 1
        task = SchedTask(name="simple", func=simple_func)
        self.scheduler.add_task(task)
        asyncio.run(self.scheduler.execute())
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_execute_async(self):
        """测试异步执行"""
        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"
        task = SchedTask(name="async_task", func=async_func)
        self.scheduler.add_task(task)
        results = await self.scheduler.execute()
        assert len(results) == 1
