"""
SprintCycle 日志系统

提供统一的日志管理，支持：
- 多级别日志（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 结构化日志输出（JSON 格式）
- 日志轮转（按大小/时间）
- 上下文信息（任务ID、项目路径等）
- 性能日志
"""

import logging
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Union
from functools import wraps
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from contextvars import ContextVar

# 上下文变量
_log_context: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, include_context: bool = True, fmt: Optional[str] = None):
        super().__init__(fmt)
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加上下文信息
        if self.include_context:
            context = _log_context.get()
            if context:
                log_data["context"] = context
        
        # 添加额外字段
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class HumanReadableFormatter(logging.Formatter):
    """人类可读的日志格式化器"""
    
    def __init__(self, fmt: Optional[str] = None):
        if fmt is None:
            fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        super().__init__(fmt, datefmt="%Y-%m-%d %H:%M:%S")
    
    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色（终端支持时）
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            level_colors = {
                'DEBUG': '\033[36m',     # 青色
                'INFO': '\033[32m',       # 绿色
                'WARNING': '\033[33m',   # 黄色
                'ERROR': '\033[31m',     # 红色
                'CRITICAL': '\033[35m',  # 紫色
            }
            reset = '\033[0m'
            level = record.levelname
            if level in level_colors:
                record.levelname = f"{level_colors[level]}{level}{reset}"
        
        return super().format(record)


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._timings: Dict[str, datetime] = {}
    
    def start(self, operation: str, **context) -> str:
        """开始计时"""
        key = f"{operation}_{id(context)}"
        self._timings[key] = datetime.now()
        self.logger.debug(f"⏱️ 开始: {operation}", extra={"extra": context})
        return key
    
    def end(self, key: str, operation: str, success: bool = True) -> Optional[float]:
        """结束计时，返回耗时（秒）"""
        if key not in self._timings:
            return None
        
        start_time = self._timings.pop(key)
        duration = (datetime.now() - start_time).total_seconds()
        
        level = logging.INFO if success else logging.ERROR
        status = "✅" if success else "❌"
        self.logger.log(
            level,
            f"{status} 完成: {operation} (耗时: {duration:.2f}秒)"
        )
        
        return duration
    
    def log_duration(self, operation: str, duration: float, **context):
        """记录操作耗时"""
        self.logger.info(
            f"⏱️ 耗时: {operation} = {duration:.3f}秒",
            extra={"extra": {"duration": duration, **context}}
        )


class SprintLogger:
    """Sprint 专用日志记录器"""
    
    def __init__(self, name: str = "sprintcycle.sprint"):
        self.logger = logging.getLogger(name)
        self.perf = PerformanceLogger(self.logger)
    
    def sprint_start(self, sprint_name: str, total_tasks: int):
        """Sprint 开始"""
        self.logger.info(f"🚀 Sprint 开始: {sprint_name} ({total_tasks} 任务)")
    
    def task_start(self, task_index: int, total: int, task: str):
        """任务开始"""
        self.logger.info(f"📋 任务 {task_index}/{total}: {task[:60]}...")
    
    def task_complete(self, task_index: int, task: str, success: bool, duration: float, files_changed: int = 0):
        """任务完成"""
        status = "✅" if success else "❌"
        self.logger.info(
            f"{status} 任务 {task_index} 完成: {task[:40]}... "
            f"(耗时: {duration:.1f}秒, 文件: {files_changed})"
        )
    
    def sprint_complete(self, sprint_name: str, total: int, success: int, failed: int, duration: float):
        """Sprint 完成"""
        self.logger.info(
            f"🏁 Sprint 完成: {sprint_name} "
            f"(成功: {success}/{total}, 失败: {failed}, 耗时: {duration:.1f}秒)"
        )


def setup_logger(
    name: str = "sprintcycle",
    log_file: Optional[str] = None,
    level: Union[str, int] = logging.INFO,
    structured: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    when: str = "midnight",  # 每天轮转
    **context
) -> logging.Logger:
    """
    设置日志器
    
    Args:
        name: 日志器名称
        log_file: 日志文件路径
        level: 日志级别（字符串或 int）
        structured: 是否使用结构化输出
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的备份文件数量
        when: 日志轮转时间单位
        **context: 额外的上下文信息
    
    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 设置级别
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # 创建格式化器
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    # 控制台处理器
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # 文件处理器（支持轮转）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 尝试使用轮转日志处理器
        try:
            if backup_count > 0:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8"
                )
            else:
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建文件日志处理器: {e}")
    
    return logger


def get_logger(name: str = "sprintcycle") -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)


def set_log_context(**context):
    """设置日志上下文"""
    current = _log_context.get()
    _log_context.set({**current, **context})


def clear_log_context():
    """清除日志上下文"""
    _log_context.set({})


def log_performance(operation: str):
    """性能日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start = datetime.now()
            logger.debug(f"⏱️ 开始: {operation}")
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start).total_seconds()
                logger.info(f"✅ {operation} 完成 (耗时: {duration:.3f}秒)")
                return result
            except Exception as e:
                duration = (datetime.now() - start).total_seconds()
                logger.error(f"❌ {operation} 失败 (耗时: {duration:.3f}秒): {e}")
                raise
        return wrapper
    return decorator


# 预配置的日志实例
default_logger = setup_logger("sprintcycle")
sprint_logger = SprintLogger()

__all__ = [
    "setup_logger",
    "get_logger",
    "set_log_context",
    "clear_log_context",
    "log_performance",
    "StructuredFormatter",
    "HumanReadableFormatter",
    "PerformanceLogger",
    "SprintLogger",
    "LOG_LEVELS",
]
