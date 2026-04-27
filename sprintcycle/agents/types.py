"""
共享类型定义 - 避免循环导入
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class VerificationType(Enum):
    """验证类型"""
    PAGE_LOAD = "page_load"
    ELEMENT_EXISTS = "element_exists"
    TEXT_CONTENT = "text_content"
    CLICK_INTERACTION = "click_interaction"
    FORM_FILL = "form_fill"
    NAVIGATION = "navigation"
    ACCESSIBILITY = "accessibility"
    VISUAL = "visual"


class VerificationSeverity(Enum):
    """问题严重级别"""
    HIGH = "high"      # 关键功能不可用
    MEDIUM = "medium"  # 用户体验问题
    LOW = "low"        # 优化建议


@dataclass
class VerificationResult:
    """验证结果"""
    verification_type: VerificationType
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: VerificationSeverity = VerificationSeverity.LOW
    screenshot_path: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.verification_type.value,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "severity": self.severity.value,
            "screenshot": self.screenshot_path,
            "suggestions": self.suggestions
        }


@dataclass
class PageVerificationReport:
    """页面验证报告"""
    url: str
    page_title: str
    load_time_ms: float
    verifications: List[VerificationResult]
    overall_score: float  # 0-100
    passed_count: int = 0
    failed_count: int = 0
    high_severity_count: int = 0
    
    def __post_init__(self):
        self.passed_count = sum(1 for v in self.verifications if v.passed)
        self.failed_count = sum(1 for v in self.verifications if not v.passed)
        self.high_severity_count = sum(1 for v in self.verifications 
                                        if not v.passed and v.severity == VerificationSeverity.HIGH)
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "page_title": self.page_title,
            "load_time_ms": self.load_time_ms,
            "verifications": [v.to_dict() for v in self.verifications],
            "overall_score": self.overall_score,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "high_severity": self.high_severity_count
        }
    
    def summary(self) -> str:
        """生成摘要报告"""
        emoji = "✅" if self.overall_score >= 80 else "⚠️" if self.overall_score >= 60 else "❌"
        lines = [
            f"{emoji} **页面验证报告: {self.url}**",
            f"📊 得分: **{self.overall_score:.0f}/100**",
            f"✅ 通过: {self.passed_count} | ❌ 失败: {self.failed_count}",
            ""
        ]
        
        if self.verifications:
            lines.append("### 详细结果")
            for v in self.verifications:
                status = "✅" if v.passed else "❌"
                lines.append(f"{status} [{v.verification_type.value}] {v.message}")
                if v.suggestions:
                    for s in v.suggestions:
                        lines.append(f"   💡 {s}")
        
        return "\n".join(lines)


# Re-export for convenience
__all__ = [
    "VerificationType",
    "VerificationSeverity",
    "VerificationResult",
    "PageVerificationReport"
]
