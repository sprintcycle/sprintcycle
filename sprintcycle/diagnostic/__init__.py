"""
Diagnostic Module - 项目诊断模块

提供多维度项目体检和PRD生成能力:
- ProjectDiagnostic: 项目诊断提供者
- ProjectHealthReport: 健康报告
- PRDGenerator: PRD生成器
"""

from .health_report import (
    ProjectHealthReport,
    CodeIssue,
    IssueSeverity,
)

from .provider import (
    ProjectDiagnostic,
    DiagnosticConfig,
)

from .prd_generator import (
    PRDGenerator,
    PRDRuleEngine,
    LLMPRDGenerator,
    PRDRulePriority,
)

__all__ = [
    # 健康报告
    "ProjectHealthReport",
    "CodeIssue",
    "IssueSeverity",
    # 诊断提供者
    "ProjectDiagnostic",
    "DiagnosticConfig",
    # PRD生成器
    "PRDGenerator",
    "PRDRuleEngine",
    "LLMPRDGenerator",
    "PRDRulePriority",
]
