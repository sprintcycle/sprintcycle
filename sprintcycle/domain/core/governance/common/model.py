"""统一验证模型 - 为 arch_guard 和 verification 提供共享基础。

这是一个统一的验证框架基础模块，定义了验证规则、检查结果和报告的核心模型。
arch_guard 和 verification 都基于此模型实现各自的特定逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Protocol


# =============================================================================
# 通用类型定义
# =============================================================================

Severity = Literal["error", "warning", "info"]
Action = Literal["block", "warn", "info"]


# =============================================================================
# 统一验证模型
# =============================================================================

@dataclass
class Rule:
    """验证规则基类"""
    rule_id: str
    title: str
    severity: Severity = "warning"
    action: Action = "warn"
    gate: str = "default"
    description: str = ""
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """检查结果基类"""
    rule_id: str
    severity: Severity
    message: str
    location: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "location": dict(self.location),
            "metadata": dict(self.metadata),
        }


@dataclass
class Policy:
    """验证策略基类"""
    name: str = "default"
    enabled: bool = True
    rules: List[Rule] = field(default_factory=list)
    block_on_error: bool = True
    block_on_warning: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def enabled_rules_for_gate(self, gate: str) -> List[Rule]:
        return [r for r in self.rules if r.enabled and r.gate == gate]


@dataclass
class Report:
    """验证报告基类"""
    gate: str
    findings: List[Finding]
    metadata: Dict[str, Any]

    def __init__(
        self,
        gate: str = "",
        findings: Optional[List[Finding]] = None,
        violations: Optional[List[Finding]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.gate = gate
        self.findings = list(violations or findings or [])
        self.metadata = dict(metadata or {})

    @property
    def violations(self) -> List[Finding]:
        return self.findings

    @violations.setter
    def violations(self, value: List[Finding]) -> None:
        self.findings = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "findings": [f.to_dict() for f in self.findings],
            "metadata": dict(self.metadata),
        }

    def has_error(self) -> bool:
        return any(f.severity == "error" for f in self.findings)

    def has_warning(self) -> bool:
        return any(f.severity == "warning" for f in self.findings)

    def should_block_ci(self, mode: str = "on_error") -> bool:
        if mode == "none":
            return False
        if mode == "always":
            return True
        return self.has_error()


class Provider(Protocol):
    """验证提供者协议"""
    name: str

    def run(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """执行验证检查"""
        ...


# =============================================================================
# 类型别名（保持向后兼容）
# =============================================================================

# arch_guard 类型别名
GuardRule = Rule
GuardFinding = Finding
GuardPolicy = Policy
GuardReport = Report

# verification 类型别名
VerificationRule = Rule
VerificationFinding = Finding
VerificationPolicy = Policy
VerificationReport = Report

__all__ = [
    # 通用类型
    "Severity",
    "Action",
    # 核心模型
    "Rule",
    "Finding",
    "Policy",
    "Report",
    "Provider",
    # arch_guard 别名（向后兼容）
    "GuardRule",
    "GuardFinding",
    "GuardPolicy",
    "GuardReport",
    # verification 别名（向后兼容）
    "VerificationRule",
    "VerificationFinding",
    "VerificationPolicy",
    "VerificationReport",
]
