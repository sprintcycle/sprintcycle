"""
SprintCycle 异常类体系

提供统一的异常处理机制，包含：
- 基础异常类
- 配置相关异常
- 任务执行异常
- 知识库异常
- 工具执行异常
"""

from typing import Optional, Any, Dict


class SprintCycleError(Exception):
    """SprintCycle 基础异常类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\n详情: {self.details}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ConfigurationError(SprintCycleError):
    """配置相关错误"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.config_key = config_key
        if config_key:
            self.details["config_key"] = config_key


class ConfigFileNotFoundError(ConfigurationError):
    """配置文件未找到"""
    
    def __init__(self, config_path: str):
        super().__init__(
            f"配置文件未找到: {config_path}",
            config_key=config_path
        )
        self.config_path = config_path


class ConfigValidationError(ConfigurationError):
    """配置验证失败"""
    
    def __init__(self, message: str, config_key: str, expected: Any, actual: Any):
        details = {"expected": expected, "actual": actual}
        super().__init__(message, config_key, details)
        self.expected = expected
        self.actual = actual


class TaskExecutionError(SprintCycleError):
    """任务执行错误"""
    
    def __init__(
        self, 
        message: str, 
        task: Optional[str] = None,
        agent: Optional[str] = None,
        tool: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.task = task
        self.agent = agent
        self.tool = tool
        if task:
            self.details["task"] = task
        if agent:
            self.details["agent"] = agent
        if tool:
            self.details["tool"] = tool


class TaskTimeoutError(TaskExecutionError):
    """任务执行超时"""
    
    def __init__(self, task: str, timeout_seconds: int):
        super().__init__(
            f"任务执行超时: {task[:50]}... (超时: {timeout_seconds}秒)",
            task=task
        )
        self.timeout_seconds = timeout_seconds
        self.details["timeout_seconds"] = timeout_seconds


class TaskValidationError(TaskExecutionError):
    """任务验证失败"""
    
    def __init__(self, message: str, task: str, validation_errors: list):
        super().__init__(message, task=task)
        self.validation_errors = validation_errors
        self.details["validation_errors"] = validation_errors


class KnowledgeBaseError(SprintCycleError):
    """知识库相关错误"""
    
    def __init__(self, message: str, kb_path: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.kb_path = kb_path
        if kb_path:
            self.details["kb_path"] = kb_path


class KnowledgeNotFoundError(KnowledgeBaseError):
    """知识未找到"""
    
    def __init__(self, query: str, kb_path: Optional[str] = None):
        super().__init__(
            f"未找到相关知识: {query[:50]}...",
            kb_path=kb_path
        )
        self.query = query


class KnowledgeWriteError(KnowledgeBaseError):
    """知识写入失败"""
    
    def __init__(self, message: str, kb_path: str):
        super().__init__(message, kb_path=kb_path)


class ToolExecutionError(SprintCycleError):
    """工具执行错误"""
    
    def __init__(
        self, 
        message: str, 
        tool: str, 
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.tool = tool
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.details["tool"] = tool
        if exit_code is not None:
            self.details["exit_code"] = exit_code
        if stdout:
            self.details["stdout"] = stdout[:500]  # 限制长度
        if stderr:
            self.details["stderr"] = stderr[:500]


class ToolNotFoundError(ToolExecutionError):
    """工具未找到"""
    
    def __init__(self, tool: str, search_paths: Optional[list] = None):
        super().__init__(
            f"工具未找到: {tool}",
            tool=tool,
            details={"search_paths": search_paths or []}
        )


class ToolTimeoutError(ToolExecutionError):
    """工具执行超时"""
    
    def __init__(self, tool: str, timeout_seconds: int, partial_output: Optional[str] = None):
        super().__init__(
            f"工具执行超时: {tool} (超时: {timeout_seconds}秒)",
            tool=tool
        )
        self.timeout_seconds = timeout_seconds
        self.details["timeout_seconds"] = timeout_seconds
        if partial_output:
            self.details["partial_output"] = partial_output[:500]


class ValidationError(SprintCycleError):
    """验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:100]
        super().__init__(message, details)
        self.field = field
        self.value = value


class RollbackError(SprintCycleError):
    """回滚错误"""
    
    def __init__(self, message: str, backup_path: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.backup_path = backup_path
        if backup_path:
            self.details["backup_path"] = backup_path


class FileOperationError(SprintCycleError):
    """文件操作错误"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        super().__init__(message, details)
        self.file_path = file_path
        self.operation = operation


# 异常注册表 - 用于按类型查找
EXCEPTION_REGISTRY = {
    "SprintCycleError": SprintCycleError,
    "ConfigurationError": ConfigurationError,
    "ConfigFileNotFoundError": ConfigFileNotFoundError,
    "ConfigValidationError": ConfigValidationError,
    "TaskExecutionError": TaskExecutionError,
    "TaskTimeoutError": TaskTimeoutError,
    "TaskValidationError": TaskValidationError,
    "KnowledgeBaseError": KnowledgeBaseError,
    "KnowledgeNotFoundError": KnowledgeNotFoundError,
    "KnowledgeWriteError": KnowledgeWriteError,
    "ToolExecutionError": ToolExecutionError,
    "ToolNotFoundError": ToolNotFoundError,
    "ToolTimeoutError": ToolTimeoutError,
    "ValidationError": ValidationError,
    "RollbackError": RollbackError,
    "FileOperationError": FileOperationError,
}


def get_exception_by_name(name: str) -> type:
    """根据名称获取异常类"""
    return EXCEPTION_REGISTRY.get(name, SprintCycleError)


__all__ = [
    "SprintCycleError",
    "ConfigurationError",
    "ConfigFileNotFoundError",
    "ConfigValidationError",
    "TaskExecutionError",
    "TaskTimeoutError",
    "TaskValidationError",
    "KnowledgeBaseError",
    "KnowledgeNotFoundError",
    "KnowledgeWriteError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolTimeoutError",
    "ValidationError",
    "RollbackError",
    "FileOperationError",
    "EXCEPTION_REGISTRY",
    "get_exception_by_name",
]
