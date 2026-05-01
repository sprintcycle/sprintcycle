"""
Coding Result - 编码结果数据类
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class CodingEngineResult:
    """编码引擎结果"""
    success: bool
    output: str = ""
    error: Optional[str] = None
    strategy: str = ""
    duration: float = 0.0
    artifacts: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    feedback: Optional[str] = None
    code_review: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "strategy": self.strategy,
            "duration": self.duration,
            "artifacts": self.artifacts,
            "timestamp": self.timestamp.isoformat(),
            "feedback": self.feedback,
            "code_review": self.code_review,
        }

    @property
    def has_artifacts(self) -> bool:
        return bool(self.artifacts)

    @property
    def error_summary(self) -> str:
        if self.error:
            return f"[{self.strategy}] {self.error}"
        return ""


@dataclass
class CodeReviewResult:
    """代码审查结果"""
    file_path: str
    issues: List[Dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    approved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "issues": self.issues,
            "score": self.score,
            "suggestions": self.suggestions,
            "approved": self.approved,
        }


@dataclass
class CodeFixResult:
    """代码修复结果"""
    original_code: str
    fixed_code: str
    changes: List[Dict[str, Any]] = field(default_factory=list)
    error_resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "changes": self.changes,
            "error_resolved": self.error_resolved,
        }
