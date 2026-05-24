"""
Diagnostic Module - 项目诊断模块

提供多维度项目体检与 **诊断用 ``ReleasePlan``** 生成能力:
- ProjectDiagnostic: 项目诊断提供者
- ProjectHealthReport: 健康报告
- DiagnosticReleasePlanGenerator / ReleasePlanRuleEngine: 规则 + LLM 生成计划
"""

from .health_report import (
    CodeIssue,
    ProjectHealthReport,
    Severity,
)
from .provider import (
    ProjectDiagnostic,
)
from .release_plan_generator import (
    DiagnosticReleasePlanGenerator,
    LLMReleasePlanGenerator,
    ReleasePlanRuleEngine,
)
from .release_plan_rules import ReleasePlanRule, ReleasePlanRulePriority

__all__ = [
    # 健康报告
    "ProjectHealthReport",
    "CodeIssue",
    "Severity",
    # 诊断提供者
    "ProjectDiagnostic",
    # 执行计划生成（主线 ReleasePlan）
    "DiagnosticReleasePlanGenerator",
    "ReleasePlanRuleEngine",
    "ReleasePlanRule",
    "LLMReleasePlanGenerator",
    "ReleasePlanRulePriority",
]
