"""
SprintCycle 错误处理模块测试 v0.3
"""

import pytest
import time
from unittest.mock import Mock, patch

from sprintcycle.error_handlers import (
    ErrorCategory,
    ErrorHandler,
    retry_on_error,
    handle_errors,
    safe_execute,
    get_error_handler
)
from sprintcycle.exceptions import (
    SprintCycleError,
    TaskExecutionError,
    ToolExecutionError,
    TaskTimeoutError,
    ConfigurationError
)


class TestErrorCategory:
    """ErrorCategory 测试"""
    
    def test_all_categories(self):
        """测试所有分类"""
        categories = list(ErrorCategory)
        assert len(categories) > 0
        assert ErrorCategory.TIMEOUT in categories
        assert ErrorCategory.CONFIGURATION in categories
        assert ErrorCategory.UNKNOWN in categories


class TestErrorHandler:
    """ErrorHandler 测试"""
    
    def test_classify_timeout(self):
        """测试超时错误分类"""
        error = TaskTimeoutError("test task", 30)
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.TIMEOUT
    
    def test_classify_timeout_message(self):
        """测试超时错误消息分类"""
        category = ErrorHandler.classify_error("Connection timeout")
        assert category == ErrorCategory.TIMEOUT
    
    def test_classify_configuration(self):
        """测试配置错误分类"""
        error = ConfigurationError("Invalid config", config_key="test")
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.CONFIGURATION
    
    def test_classify_permission(self):
        """测试权限错误分类"""
        category = ErrorHandler.classify_error("Permission denied")
        assert category == ErrorCategory.PERMISSION
    
    def test_classify_network(self):
        """测试网络错误分类"""
        category = ErrorHandler.classify_error("Network connection failed")
        assert category == ErrorCategory.NETWORK
    
    def test_classify_validation(self):
        """测试验证错误分类"""
        category = ErrorHandler.classify_error("Validation error: invalid input")
        assert category == ErrorCategory.VALIDATION
    
    def test_classify_unknown(self):
        """测试未知错误分类"""
        category = ErrorHandler.classify_error("some random error")
        assert category == ErrorCategory.UNKNOWN
    
    def test_get_recovery_suggestions(self):
        """测试获取恢复建议"""
        suggestions = ErrorHandler.get_recovery_suggestions(ErrorCategory.TIMEOUT)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # 检查是否包含超时相关的建议
        assert any("超时" in s or "timeout" in s.lower() for s in suggestions)
    
    def test_record_error(self):
        """测试记录错误"""
        handler = ErrorHandler()
        error = TaskExecutionError("Test error", task="test_task")
        
        record = handler.record_error(error, context={"test": True})
        
        assert record["error_type"] == "TaskExecutionError"
        assert record["category"] == ErrorCategory.UNKNOWN.value
        assert "recovery_suggestions" in record
        assert record["context"]["test"] is True
    
    def test_error_stats(self):
        """测试错误统计"""
        handler = ErrorHandler()
        
        # 记录多个错误
        for _ in range(3):
            handler.record_error(TaskTimeoutError("task1", 30))
        for _ in range(2):
            handler.record_error(TaskExecutionError("task2"))
        
        stats = handler.get_error_stats()
        
        assert stats["total_errors"] == 5
        assert "TaskTimeoutError:timeout" in stats["error_counts"]
        assert stats["error_counts"]["TaskTimeoutError:timeout"] == 3


class TestRetryDecorator:
    """重试装饰器测试"""
    
    def test_successful_execution(self):
        """测试成功执行"""
        @retry_on_error(max_retries=3)
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result == "success"
    
    def test_retry_on_exception(self):
        """测试异常重试"""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        @retry_on_error(max_retries=2, delay=0.01)
        def always_fails():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_fails()
    
    def test_specific_exception_retry(self):
        """测试特定异常重试"""
        call_count = 0
        
        @retry_on_error(max_retries=2, delay=0.01, exceptions=(ValueError,))
        def flaky_value_error():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Specific error")
            return "success"
        
        result = flaky_value_error()
        assert result == "success"
        assert call_count == 3


class TestHandleErrorsDecorator:
    """错误处理装饰器测试"""
    
    def test_successful_execution(self):
        """测试成功执行"""
        @handle_errors(default_return="fallback")
        def func():
            return "success"
        
        result = func()
        assert result == "success"
    
    def test_exception_returns_default(self):
        """测试异常返回默认值"""
        @handle_errors(default_return="fallback", reraise=False)
        def func():
            raise ValueError("Error")
        
        result = func()
        assert result == "fallback"
    
    def test_exception_reraises(self):
        """测试异常重新抛出"""
        @handle_errors(reraise=True)
        def func():
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            func()
    
    def test_sprint_cycle_error_reraises(self):
        """测试业务异常重新抛出"""
        @handle_errors(reraise=False)
        def func():
            raise SprintCycleError("Business error")
        
        # SprintCycleError 应该总是重新抛出
        with pytest.raises(SprintCycleError):
            func()


class TestSafeExecute:
    """安全执行测试"""
    
    def test_successful_execution(self):
        """测试成功执行"""
        def func(a, b):
            return a + b
        
        result = safe_execute(func, 1, 2, default=0)
        assert result == 3
    
    def test_exception_returns_default(self):
        """测试异常返回默认值"""
        def func():
            raise ValueError("Error")
        
        result = safe_execute(func, default="fallback")
        assert result == "fallback"
    
    def test_with_kwargs(self):
        """测试带关键字参数"""
        def func(a, b=10):
            return a * b
        
        result = safe_execute(func, 5, b=3, default=0)
        assert result == 15
    
    def test_on_error_callback(self):
        """测试错误回调"""
        callback_called = []
        
        def on_error(e):
            callback_called.append(str(e))
        
        def func():
            raise ValueError("Test error")
        
        result = safe_execute(func, default="fallback", on_error=on_error)
        
        assert result == "fallback"
        assert len(callback_called) == 1
        assert "Test error" in callback_called[0]


class TestGlobalErrorHandler:
    """全局错误处理器测试"""
    
    def test_get_error_handler(self):
        """测试获取全局错误处理器"""
        handler = get_error_handler()
        assert isinstance(handler, ErrorHandler)
        
        # 应该是同一个实例
        handler2 = get_error_handler()
        assert handler is handler2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
