"""发布计划生成器协议"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sprintcycle.domain.models import ReleasePlan


class ReleasePlanGeneratorProtocol(ABC):
    """发布计划生成器接口"""
    
    @abstractmethod
    def generate_from_diagnostic(self, diagnostic_slices: List[Dict[str, Any]]) -> "ReleasePlan":
        """从诊断切片生成发布计划"""
        ...
    
    @abstractmethod
    def generate_from_user_intent(self, intent: str, context: Optional[Dict[str, Any]] = None) -> "ReleasePlan":
        """从用户意图生成发布计划"""
        ...


class ReleasePlanParserProtocol(ABC):
    """发布计划解析器接口"""
    
    @abstractmethod
    def parse(self, content: str) -> "ReleasePlan":
        """解析 YAML/JSON 内容为 ReleasePlan"""
        ...
    
    @abstractmethod
    def parse_file(self, file_path: str) -> "ReleasePlan":
        """从文件解析 ReleasePlan"""
        ...
    
    @abstractmethod
    def validate(self, release_plan: "ReleasePlan") -> bool:
        """验证发布计划"""
        ...


class ReleasePlanValidatorProtocol(ABC):
    """发布计划验证器接口"""
    
    @abstractmethod
    def validate(self, release_plan: "ReleasePlan") -> "ValidationResult":
        """验证发布计划"""
        ...


class ValidationResult:
    """验证结果"""
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.success = is_valid


__all__ = [
    "ReleasePlanGeneratorProtocol",
    "ReleasePlanParserProtocol",
    "ReleasePlanValidatorProtocol",
    "ValidationResult",
]
