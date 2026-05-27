"""治理协议 - Domain 层定义，Governance 层实现"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from sprintcycle.domain.generic.models import ReleasePlan


@dataclass
class GovernanceCheckResult:
    """治理检查结果"""
    passed: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_violation(self, violation: str) -> None:
        self.violations.append(violation)
        self.passed = False

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)


class GovernanceCheckProtocol(ABC):
    """治理检查接口"""

    @abstractmethod
    def check(self, context: Dict[str, Any]) -> GovernanceCheckResult:
        """执行检查"""
        ...

    @abstractmethod
    def get_rule_id(self) -> str:
        """获取规则ID"""
        ...


class ArchitectureCheckProtocol(ABC):
    """架构检查接口"""

    @abstractmethod
    def check_architecture(self, project_path: str) -> GovernanceCheckResult:
        """检查架构"""
        ...


class QualityGateProtocol(ABC):
    """质量门禁接口"""

    @abstractmethod
    def evaluate(self, release_plan: "ReleasePlan") -> GovernanceCheckResult:
        """评估发布计划"""
        ...


__all__ = [
    "GovernanceCheckResult",
    "GovernanceCheckProtocol",
    "ArchitectureCheckProtocol",
    "QualityGateProtocol",
]
