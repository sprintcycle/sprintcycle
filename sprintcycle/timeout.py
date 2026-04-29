"""
SprintCycle 超时处理模块 v4.10

提供任务执行的超时处理功能：
- 可配置超时时间
- 指数退避重试
- 超时预测
- 任务跳过策略
"""
import signal
import time
import subprocess
from typing import Callable, Any, Dict, Optional
from functools import wraps
from dataclasses import dataclass


@dataclass
class TimeoutResult:
    """超时结果"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration: float = 0
    timed_out: bool = False


class TimeoutHandler:
    """
    超时处理增强 v4.10
    
    功能：
    - 支持函数和进程超时
    - 指数退避重试机制
    - 智能超时预测
    - 任务跳过策略
    """
    
    def __init__(
        self,
        default_timeout: int = 120,
        max_retries: int = 3,
        backoff_multiplier: float = 1.5,
        max_backoff: int = 300
    ):
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
        self._active_timers: Dict[str, float] = {}
    
    def with_timeout(
        self,
        timeout: Optional[int] = None,
        task_name: Optional[str] = None
    ) -> Callable:
        """超时装饰器 v4.10"""
        timeout = timeout or self.default_timeout
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"任务执行超时: {task_name or func.__name__}")
                
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout))
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    return TimeoutResult(
                        success=True,
                        result=result,
                        duration=duration
                    )
                except TimeoutError as e:
                    duration = time.time() - start_time
                    return TimeoutResult(
                        success=False,
                        error=str(e),
                        duration=duration,
                        timed_out=True
                    )
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            
            return wrapper
        return decorator
    
    def execute_with_timeout(
        self,
        func: Callable,
        timeout: Optional[int] = None,
        *args,
        **kwargs
    ) -> TimeoutResult:
        """执行函数并设置超时 v4.10"""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Function execution timeout")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            return TimeoutResult(
                success=True,
                result=result,
                duration=duration
            )
        except TimeoutError as e:
            duration = time.time() - start_time
            return TimeoutResult(
                success=False,
                error=str(e),
                duration=duration,
                timed_out=True
            )
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def execute_with_retry(
        self,
        func: Callable,
        max_retries: Optional[int] = None,
        backoff: Optional[float] = None,
        *args,
        **kwargs
    ) -> Dict:
        """带重试的执行 v4.10 - 返回字典格式"""
        max_retries = max_retries if max_retries is not None else self.max_retries
        backoff = backoff if backoff is not None else self.backoff_multiplier
        
        last_result = None
        current_timeout = float(self.default_timeout)
        attempts = 0
        
        for attempt in range(max_retries + 1):
            attempts += 1
            result = self.execute_with_timeout(func, current_timeout, *args, **kwargs)
            
            if result.success:
                return {
                    "success": True,
                    "result": result.result,
                    "duration": result.duration,
                    "attempts": attempts,
                    "timed_out": False
                }
            
            last_result = result
            if attempt < max_retries:
                time.sleep(min(current_timeout, self.max_backoff))
                current_timeout = min(
                    current_timeout * backoff,
                    self.max_backoff
                )
        
        return {
            "success": False,
            "result": last_result.error if last_result else None,
            "duration": last_result.duration if last_result else 0,
            "attempts": attempts,
            "timed_out": True
        }
    
    def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Callable,
        timeout: Optional[int] = None,
        *args,
        **kwargs
    ) -> Dict:
        """v4.10: 执行带降级的函数"""
        timeout = timeout or self.default_timeout
        
        result = self.execute_with_timeout(primary_func, timeout, *args, **kwargs)
        
        if result.success:
            return {
                "success": True,
                "result": result.result,
                "duration": result.duration,
                "used_fallback": False
            }
        
        # 执行降级函数
        fallback_result = self.execute_with_timeout(fallback_func, timeout)
        
        return {
            "success": fallback_result.success,
            "result": fallback_result.result if fallback_result.success else None,
            "duration": fallback_result.duration,
            "used_fallback": True
        }
    
    def predict_timeout(self, task: str, context: Optional[Dict[str, Any]] = None) -> int:
        """预测任务超时时间 v4.10
        
        基于任务描述中的关键字判断超时时间：
        - simple/small → 60秒
        - medium → 120秒
        - complex/large → 300秒
        - test 相关 → 60秒
        """
        task_lower = task.lower()
        
        # 测试任务优先判断
        if "test" in task_lower:
            return 60
        
        # 根据关键字确定基础超时时间
        if any(k in task_lower for k in ["simple", "small", "小型", "简单"]):
            return 60
        elif any(k in task_lower for k in ["medium", "中型", "中等"]):
            return 120
        elif any(k in task_lower for k in ["complex", "large", "复杂", "大型"]):
            return 300
        
        # 默认返回 default_timeout
        return self.default_timeout
    
    def should_skip(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """判断任务是否应该跳过 v4.10"""
        if not task or not task.strip():
            return True
        
        skip_keywords = ["skip", "跳过", "ignore", "忽略"]
        if any(k in task.lower() for k in skip_keywords):
            return True
        
        return False
    
    def execute_subprocess(
        self,
        cmd: list,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None
    ) -> TimeoutResult:
        """执行子进程并设置超时 v4.10"""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            duration = time.time() - start_time
            
            return TimeoutResult(
                success=result.returncode == 0,
                result={
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                },
                duration=duration
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TimeoutResult(
                success=False,
                error="Process execution timeout",
                duration=duration,
                timed_out=True
            )
        except Exception as e:
            duration = time.time() - start_time
            return TimeoutResult(
                success=False,
                error=str(e),
                duration=duration
            )
    
    def get_timeout_stats(self) -> Dict:
        """v4.10: 获取超时统计"""
        history = getattr(self, 'timeout_history', [])
        
        if not history:
            return {
                "total": 0,
                "avg_timeout": 0,
                "max_timeout": 0,
                "min_timeout": 0
            }
        
        timeouts = [h.get("timeout_seconds", 0) for h in history]
        
        return {
            "total": len(timeouts),
            "avg_timeout": sum(timeouts) / len(timeouts) if timeouts else 0,
            "max_timeout": max(timeouts) if timeouts else 0,
            "min_timeout": min(timeouts) if timeouts else 0
        }
    
    def start_timer(self, task_id: str) -> None:
        """开始计时"""
        self._active_timers[task_id] = time.time()
    
    def get_duration(self, task_id: str) -> float:
        """获取任务已执行时间"""
        if task_id in self._active_timers:
            return time.time() - self._active_timers[task_id]
        return 0
    
    def clear_timer(self, task_id: str) -> None:
        """清除计时器"""
        self._active_timers.pop(task_id, None)


__all__ = ["TimeoutHandler", "TimeoutResult"]
