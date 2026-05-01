"""
Bug 分析数据模型

定义 Bug 分析过程中使用的数据结构和类型：
- BugReport: Bug 分析报告
- FixSuggestion: 修复建议
- FixResult: 修复结果
- Severity: 严重程度枚举
- Location: 问题位置

v0.9.1: 从 Pydantic 迁移到 dataclass，消除 type: ignore 警告
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from sprintcycle.exceptions import Severity


class ErrorCategory(str, Enum):
    """错误类型分类"""
    SYNTAX = "syntax"              # 语法错误
    IMPORT = "import"              # 导入错误
    TYPE = "type"                  # 类型错误
    NAME = "name"                  # 名称错误
    VALUE = "value"                # 值错误
    INDEX = "index"                # 索引错误
    KEY = "key"                    # 键错误
    ATTRIBUTE = "attribute"        # 属性错误
    MEMORY = "memory"              # 内存错误
    RUNTIME = "runtime"            # 运行时错误
    UNKNOWN = "unknown"            # 未知错误


@dataclass
class Location:
    """问题位置"""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    code_snippet: Optional[str] = None

    def __str__(self) -> str:
        """格式化位置信息"""
        parts = []
        if self.file_path:
            parts.append(f"{self.file_path}")
        if self.line_number:
            parts.append(f":{self.line_number}")
        if self.column_number:
            parts.append(f":{self.column_number}")
        if self.function_name:
            parts.append(f" in {self.function_name}")
        return "".join(parts) or "unknown location"


@dataclass
class BugReport:
    """Bug 分析报告"""
    # 错误基本信息
    error_type: str = ""
    error_message: str = ""
    category: ErrorCategory = ErrorCategory.UNKNOWN
    
    # 位置信息 - 支持 None
    location: Optional[Location] = None
    
    # 分析结果
    severity: Severity = Severity.MEDIUM
    root_cause: str = ""
    suggestions: List[str] = field(default_factory=list)
    
    # 上下文
    stack_trace: Optional[str] = None
    code_snippet: Optional[str] = None
    related_files: List[str] = field(default_factory=list)
    
    # 元数据
    confidence: float = 1.0
    llm_used: bool = False

    def to_summary(self) -> str:
        """生成简洁的摘要"""
        loc_str = str(self.location) if self.location else "unknown"
        return (
            f"[{self.severity.value.upper()}] {self.error_type}: {self.error_message[:100]}\n"
            f"位置: {loc_str}\n"
            f"根因: {self.root_cause[:200]}\n"
            f"建议: {'; '.join(self.suggestions[:3])}"
        )


@dataclass
class FixSuggestion:
    """修复建议"""
    file_path: str = ""
    old_code: str = ""
    new_code: str = ""
    explanation: str = ""
    confidence: float = 0.8
    
    # 修复位置
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    
    # 额外信息
    is_automated: bool = False
    warnings: List[str] = field(default_factory=list)

    def generate_diff(self) -> str:
        """生成 diff 格式的变更"""
        return (
            f"--- a/{self.file_path}\n"
            f"+++ b/{self.file_path}\n"
            f"@@ -{self.line_start or '?'}, +{self.line_end or '?'} @@\n"
            f"- {self.old_code}\n"
            f"+ {self.new_code}"
        )


@dataclass
class FixResult:
    """修复结果"""
    success: bool = False
    file_path: str = ""
    
    # 变更信息
    diff: Optional[str] = None
    lines_changed: int = 0
    
    # 错误信息（如有）
    error: Optional[str] = None
    
    # 验证信息
    verified: bool = False
    backup_path: Optional[str] = None

    def to_summary(self) -> str:
        """生成结果摘要"""
        if self.success:
            return f"✅ 修复成功: {self.file_path} ({self.lines_changed} 行变更)"
        else:
            return f"❌ 修复失败: {self.file_path} - {self.error}"


@dataclass
class AnalysisRequest:
    """分析请求"""
    error_log: str = ""
    code_context: Optional[Dict[str, str]] = None
    file_paths: List[str] = field(default_factory=list)
    
    # 分析选项
    use_llm: bool = True
    max_depth: Optional[int] = 3
    
    # 语言
    language: Optional[str] = "python"


@dataclass
class AnalysisResult:
    """完整分析结果"""
    # 原始请求
    request: AnalysisRequest = field(default_factory=AnalysisRequest)
    
    # 分析报告
    report: BugReport = field(default_factory=BugReport)
    
    # 修复建议（可能为空）
    suggestions: List[FixSuggestion] = field(default_factory=list)
    
    # 执行信息
    execution_time: float = 0.0
    patterns_matched: List[str] = field(default_factory=list)

    def get_best_fix(self) -> Optional[FixSuggestion]:
        """获取最佳修复建议（置信度最高）"""
        if not self.suggestions:
            return None
        return max(self.suggestions, key=lambda s: s.confidence)


@dataclass
class StackFrame:
    """堆栈帧信息"""
    file_path: str = ""
    line_number: int = 0
    function_name: Optional[str] = None
    code: Optional[str] = None
    column_number: Optional[int] = None


@dataclass
class ParsedTraceback:
    """解析后的追踪信息"""
    error_type: str = ""
    error_message: str = ""
    full_traceback: str = ""
    location: Optional[Location] = None
    code_snippet: Optional[str] = None
    frames: List[StackFrame] = field(default_factory=list)


@dataclass
class PatternMatch:
    """模式匹配结果"""
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: Severity = Severity.MEDIUM
    root_cause: str = ""
    fixes: List[str] = field(default_factory=list)
    confidence: float = 0.0
    matched_patterns: List[str] = field(default_factory=list)
