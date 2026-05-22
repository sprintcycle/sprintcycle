"""沙箱管理接口协议"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class SandboxManagerProtocol(ABC):
    """沙箱管理器接口"""
    
    @abstractmethod
    def create_sandbox(self, config: Dict[str, Any]) -> str:
        """创建沙箱，返回 sandbox_id"""
        ...
    
    @abstractmethod
    def destroy_sandbox(self, sandbox_id: str) -> None:
        """销毁沙箱"""
        ...
    
    @abstractmethod
    def execute_in_sandbox(self, sandbox_id: str, command: str) -> Dict[str, Any]:
        """在沙箱中执行命令"""
        ...


class HealthCheckAdapterProtocol(ABC):
    """健康检查适配器接口"""
    
    @abstractmethod
    def check(self) -> bool:
        """执行健康检查"""
        ...


class RetryPolicyAdapterProtocol(ABC):
    """重试策略适配器接口"""
    
    @abstractmethod
    def execute_with_retry(self, func: callable, max_retries: int = 3) -> Any:
        """带重试执行"""
        ...


__all__ = [
    "SandboxManagerProtocol",
    "HealthCheckAdapterProtocol",
    "RetryPolicyAdapterProtocol",
]
