"""扩展超时处理测试 - 针对 timeout.py 低覆盖率模块"""
import pytest
import time
from sprintcycle.timeout import (
    TimeoutResult,
    TimeoutHandler,
)


class TestTimeoutResult:
    """超时结果数据类测试"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = TimeoutResult(success=True, result={"data": "value"}, duration=1.5)
        assert result.success is True
        assert result.result == {"data": "value"}
        assert result.duration == 1.5
        assert result.timed_out is False
    
    def test_failure_result(self):
        """测试失败结果"""
        result = TimeoutResult(success=False, error="Task failed", timed_out=True)
        assert result.success is False
        assert result.error == "Task failed"
        assert result.timed_out is True
    
    def test_default_values(self):
        """测试默认值"""
        result = TimeoutResult(success=True)
        assert result.result is None
        assert result.error is None
        assert result.duration == 0
        assert result.timed_out is False


class TestTimeoutHandler:
    """超时处理类测试"""
    
    def test_handler_initialization(self):
        """测试处理器初始化"""
        handler = TimeoutHandler(default_timeout=60, max_retries=5)
        assert handler.default_timeout == 60
        assert handler.max_retries == 5
        assert handler.backoff_multiplier == 1.5
    
    def test_handler_default_values(self):
        """测试处理器默认值"""
        handler = TimeoutHandler()
        assert handler.default_timeout == 120
        assert handler.max_retries == 3
    
    def test_execute_with_timeout_success(self):
        """测试超时执行成功"""
        handler = TimeoutHandler(default_timeout=10)
        
        def quick_func():
            return 42
        
        result = handler.execute_with_timeout(quick_func, 10)
        assert result.success is True
        assert result.result == 42
        assert result.error is None
    
    def test_execute_with_timeout_with_args(self):
        """测试带参数超时执行"""
        handler = TimeoutHandler(default_timeout=10)
        
        def add(a, b):
            return a + b
        
        result = handler.execute_with_timeout(add, 10, 6, 7)
        assert result.success is True
        assert result.result == 13
    
    def test_execute_with_timeout_timeout(self):
        """测试超时"""
        handler = TimeoutHandler(default_timeout=1)
        
        def slow_func():
            time.sleep(5)
            return "done"
        
        result = handler.execute_with_timeout(slow_func, 1)
        assert result.success is False
        assert result.timed_out is True
    
    def test_with_timeout_decorator(self):
        """测试超时装饰器"""
        handler = TimeoutHandler(default_timeout=10)
        
        @handler.with_timeout(task_name="test_task")
        def quick_func():
            return "done"
        
        result = quick_func()
        assert result.success is True
        assert result.result == "done"
    
    def test_with_timeout_decorator_custom(self):
        """测试自定义超时装饰器"""
        handler = TimeoutHandler(default_timeout=100)
        
        @handler.with_timeout(timeout=1, task_name="slow_task")
        def slow_func():
            time.sleep(5)
            return "done"
        
        result = slow_func()
        assert result.success is False
        assert result.timed_out is True
    
    def test_execute_with_timeout_kwargs(self):
        """测试带关键字参数的超时执行"""
        handler = TimeoutHandler(default_timeout=10)
        
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        result = handler.execute_with_timeout(greet, 10, name="World", greeting="Hi")
        assert result.success is True
        assert result.result == "Hi, World!"
    
    def test_multiple_handlers(self):
        """测试多个处理器实例"""
        handler1 = TimeoutHandler(default_timeout=10)
        handler2 = TimeoutHandler(default_timeout=20)
        
        assert handler1.default_timeout == 10
        assert handler2.default_timeout == 20
    
    def test_active_timers_initially_empty(self):
        """测试活跃计时器初始为空"""
        handler = TimeoutHandler()
        assert len(handler._active_timers) == 0
    
    def test_handler_with_max_backoff(self):
        """测试处理器最大退避值"""
        handler = TimeoutHandler(max_backoff=600)
        assert handler.max_backoff == 600
