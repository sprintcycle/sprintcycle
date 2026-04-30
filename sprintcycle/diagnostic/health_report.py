"""
ProjectHealthReport - 项目健康报告

定义项目健康报告的数据结构:
- 多维度诊断结果
- 健康评分计算
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeIssue:
    """
    代码问题
    
    表示一个具体的代码问题
    """
    file: str
    line: int
    severity: IssueSeverity
    message: str
    rule: Optional[str] = None
    tool: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "severity": self.severity.value,
            "message": self.message,
            "rule": self.rule,
            "tool": self.tool,
        }


@dataclass
class ProjectHealthReport:
    """
    项目健康报告
    
    多维度项目体检结果
    """
    # 项目标识
    target: str = ""
    
    # 代码维度
    coverage_total: float = 0.0  # 总覆盖率
    coverage_modules: Dict[str, float] = field(default_factory=dict)  # 各模块覆盖率
    complexity_high: int = 0  # 高复杂度函数数量
    mypy_errors: int = 0  # mypy错误数量
    
    # 测试维度
    test_failures: int = 0  # 测试失败数
    
    # 架构维度
    circular_deps: List[str] = field(default_factory=list)  # 循环依赖
    module_coupling: float = 0.0  # 模块耦合度
    
    # 文档维度
    doc_coverage: float = 0.0  # 文档覆盖率
    outdated_docs: List[str] = field(default_factory=list)  # 过时文档
    
    # 进化维度
    effective_patterns: List[str] = field(default_factory=list)  # 有效改动模式
    failed_patterns: List[str] = field(default_factory=list)  # 失败改动模式
    coverage_trend: float = 0.0  # 覆盖率趋势
    rollback_count: int = 0  # 回滚次数
    
    # 代码问题列表
    code_issues: List[CodeIssue] = field(default_factory=list)
    
    def compute_health_score(self) -> float:
        """
        计算综合健康评分
        
        综合多个维度计算0-100的健康评分
        
        Returns:
            健康评分 (0-100)
        """
        score = 100.0
        
        # 覆盖率扣分 (每降低10%扣10分)
        if self.coverage_total < 50:
            score -= (50 - self.coverage_total) * 0.2
        elif self.coverage_total < 80:
            score -= (80 - self.coverage_total) * 0.15
        
        # 测试失败扣分 (每个失败扣5分)
        score -= min(self.test_failures * 5, 30)
        
        # 类型错误扣分 (每个错误扣1分)
        score -= min(self.mypy_errors, 20)
        
        # 高复杂度扣分 (每个扣2分)
        score -= min(self.complexity_high * 2, 20)
        
        # 循环依赖扣分
        score -= min(len(self.circular_deps) * 10, 30)
        
        # 文档覆盖率扣分
        if self.doc_coverage < 30:
            score -= (30 - self.doc_coverage) * 0.3
        
        # 回滚次数扣分
        score -= min(self.rollback_count * 3, 15)
        
        # 确保评分在0-100范围内
        return max(0.0, min(100.0, score))
    
    @property
    def health_score(self) -> float:
        """健康评分（便捷属性）"""
        return self.compute_health_score()
    
    @property
    def health_level(self) -> str:
        """健康等级"""
        score = self.health_score
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"
    
    @property
    def priority_issues(self) -> List[CodeIssue]:
        """高优先级问题"""
        return [
            issue for issue in self.code_issues
            if issue.severity in (IssueSeverity.CRITICAL, IssueSeverity.HIGH)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "coverage_total": self.coverage_total,
            "coverage_modules": self.coverage_modules,
            "complexity_high": self.complexity_high,
            "mypy_errors": self.mypy_errors,
            "test_failures": self.test_failures,
            "circular_deps": self.circular_deps,
            "module_coupling": self.module_coupling,
            "doc_coverage": self.doc_coverage,
            "outdated_docs": self.outdated_docs,
            "effective_patterns": self.effective_patterns,
            "failed_patterns": self.failed_patterns,
            "coverage_trend": self.coverage_trend,
            "rollback_count": self.rollback_count,
            "code_issues": [i.to_dict() for i in self.code_issues],
            "health_score": self.health_score,
            "health_level": self.health_level,
            "priority_issues_count": len(self.priority_issues),
        }
    
    def get_summary(self) -> str:
        """获取报告摘要"""
        lines = [
            f"项目: {self.target}",
            f"健康评分: {self.health_score:.1f} ({self.health_level})",
            f"覆盖率: {self.coverage_total:.1f}%",
            f"测试失败: {self.test_failures}",
            f"类型错误: {self.mypy_errors}",
            f"高复杂度: {self.complexity_high}",
            f"循环依赖: {len(self.circular_deps)}",
            f"回滚次数: {self.rollback_count}",
        ]
        return "\n".join(lines)
