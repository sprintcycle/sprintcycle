"""
SprintCycle 错误处理工具 v0.3

提供统一的错误处理机制，包括：
- 错误分类与归因
- 错误重试机制
- 降级处理
- 错误恢复建议
"""

import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from functools import wraps
from enum import Enum

from .exceptions import (
    SprintCycleError,
    TaskExecutionError,
    ToolExecutionError,
    TaskTimeoutError,
    ConfigurationError,
)

from loguru import logger

T = TypeVar('T')


class ErrorCategory(Enum):
    """错误分类"""
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    NETWORK = "network"
    RESOURCE = "resource"
    VALIDATION = "validation"
    EXTERNAL = "external"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ErrorHandler:
    """
    统一错误处理器
    
    提供错误分类、重试、恢复建议等功能
    """
    
    # 错误关键词映射
    KEYWORD_CATEGORIES = {
        ErrorCategory.TIMEOUT: [
            "timeout", "timed out", "deadline exceeded",
            "connection timed out", "request timeout"
        ],
        ErrorCategory.CONFIGURATION: [
            "config", "configuration", "setting",
            "not found", "missing required", "invalid value"
        ],
        ErrorCategory.PERMISSION: [
            "permission denied", "access denied", "unauthorized",
            "forbidden", "not allowed"
        ],
        ErrorCategory.NETWORK: [
            "network", "connection", "dns", "socket",
            "connection refused", "no route to host"
        ],
        ErrorCategory.RESOURCE: [
            "memory", "disk", "space", "quota",
            "out of memory", "no space left"
        ],
        ErrorCategory.VALIDATION: [
            "validation", "invalid", "malformed",
            "unexpected", "schema"
        ],
        ErrorCategory.EXTERNAL: [
            "external", "third party", "api error",
            "rate limit", "service unavailable"
        ],
    }
    
    def __init__(self):
        """初始化错误处理器"""
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
    
    @classmethod
    def classify_error(cls, error: Union[Exception, str]) -> ErrorCategory:
        """
        分类错误
        
        Args:
            error: 异常对象或错误消息
            
        Returns:
            错误分类
        """
        error_str = str(error).lower()
        
        for category, keywords in cls.KEYWORD_CATEGORIES.items():
            if any(keyword.lower() in error_str for keyword in keywords):
                return category
        
        return ErrorCategory.UNKNOWN
    
    @classmethod
    def get_recovery_suggestions(cls, category: ErrorCategory) -> List[str]:
        """
        获取错误恢复建议
        
        Args:
            category: 错误分类
            
        Returns:
            恢复建议列表
        """
        suggestions = {
            ErrorCategory.TIMEOUT: [
                "增加超时时间",
                "检查网络连接",
                "优化任务拆分",
                "使用增量执行"
            ],
            ErrorCategory.CONFIGURATION: [
                "检查配置文件",
                "验证环境变量",
                "确认必需参数",
                "查看配置文档"
            ],
            ErrorCategory.PERMISSION: [
                "检查文件权限",
                "验证用户权限",
                "确认访问控制",
                "查看日志详情"
            ],
            ErrorCategory.NETWORK: [
                "检查网络连接",
                "验证防火墙设置",
                "重试请求",
                "检查代理配置"
            ],
            ErrorCategory.RESOURCE: [
                "释放磁盘空间",
                "增加内存限制",
                "清理缓存",
                "优化资源使用"
            ],
            ErrorCategory.VALIDATION: [
                "检查输入格式",
                "验证数据完整性",
                "查看 schema 定义",
                "修复数据源"
            ],
            ErrorCategory.EXTERNAL: [
                "稍后重试",
                "检查服务状态",
                "联系服务提供商",
                "使用备选方案"
            ],
            ErrorCategory.INTERNAL: [
                "查看详细日志",
                "提交 Bug 报告",
                "回滚到稳定版本",
                "联系技术支持"
            ],
            ErrorCategory.UNKNOWN: [
                "查看详细错误信息",
                "检查日志文件",
                "尝试重启服务",
                "联系技术支持"
            ],
        }
        return suggestions.get(category, suggestions[ErrorCategory.UNKNOWN])
    
    def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            
        Returns:
            错误记录字典
        """
        category = self.classify_error(error)
        error_type = type(error).__name__
        
        record = {
            "timestamp": time.time(),
            "error_type": error_type,
            "error_message": str(error),
            "category": category.value,
            "traceback": traceback.format_exc(),
            "context": context or {},
            "recovery_suggestions": self.get_recovery_suggestions(category)
        }
        
        # 更新统计
        key = f"{error_type}:{category.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        self.error_history.append(record)
        
        return record
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        获取错误统计
        
        Returns:
            错误统计字典
        """
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts,
            "category_summary": {
                cat.value: sum(
                    1 for r in self.error_history 
                    if r["category"] == cat.value
                )
                for cat in ErrorCategory
            }
        }


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    错误重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"重试 {func.__name__} (尝试 {attempt + 1}/{max_retries}): {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"重试耗尽 {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def handle_errors(
    default_return: Any = None,
    log_level: str = "ERROR",
    reraise: bool = True,
    context: Optional[Dict[str, Any]] = None
) -> Callable:
    """
    统一错误处理装饰器
    
    Args:
        default_return: 默认返回值
        log_level: 日志级别
        reraise: 是否重新抛出异常
        context: 额外上下文
        
    Returns:
        装饰器函数
    """
    log_func = getattr(logger, log_level.lower(), logger.error)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except SprintCycleError:
                # 已知业务异常，不包装
                raise
            except Exception as e:
                ctx = context or {}
                ctx["function"] = func.__name__
                ctx["args"] = str(args)[:200]
                
                log_func(f"执行 {func.__name__} 时发生错误: {e}", exc_info=True)
                
                if reraise:
                    raise
                return default_return
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable[..., T],
    *args,
    default: T = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    **kwargs
) -> T:
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        default: 默认返回值
        on_error: 错误回调函数
        **kwargs: 关键字参数
        
    Returns:
        函数返回值或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"safe_execute {func.__name__} 失败: {e}")
        if on_error:
            on_error(e)
        return default


# 全局错误处理器实例
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


__all__ = [
    "ErrorCategory",
    "ErrorHandler",
    "retry_on_error",
    "handle_errors",
    "safe_execute",
    "get_error_handler",
]
