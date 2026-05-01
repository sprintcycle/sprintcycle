"""
Diagnostic Module - 项目诊断模块

提供多维度项目体检和PRD生成能力:
- ProjectDiagnostic: 项目诊断提供者
- ProjectHealthReport: 健康报告
- DiagnosticPRDGenerator: PRD生成器
"""

from .health_report import (
    ProjectHealthReport,
    CodeIssue,
    Severity,
)

from .provider import (
    ProjectDiagnostic,
)

from .prd_generator import (
    DiagnosticPRDGenerator,
    PRDRuleEngine,
    LLMPRDGenerator,
    PRDRulePriority,
)

__all__ = [
    # 健康报告
    "ProjectHealthReport",
    "CodeIssue",
    "Severity",
    # 诊断提供者
    "ProjectDiagnostic",
    # PRD生成器
    "DiagnosticPRDGenerator",
    "PRDRuleEngine",
    "LLMPRDGenerator",
    "PRDRulePriority",
]
