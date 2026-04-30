"""
Bug 分析数据模型

定义 Bug 分析过程中使用的数据结构和类型：
- BugReport: Bug 分析报告
- FixSuggestion: 修复建议
- FixResult: 修复结果
- BugSeverity: 严重程度枚举
- Location: 问题位置
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class BugSeverity(str, Enum):
    """Bug 严重程度枚举"""
    CRITICAL = "critical"  # 系统崩溃、数据丢失
    HIGH = "high"          # 功能完全不可用
    MEDIUM = "medium"      # 功能部分受损
    LOW = "low"           # 界面问题或小问题


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


class Location(BaseModel):
    """问题位置"""
    file_path: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    function_name: str | None = None
    class_name: str | None = None
    code_snippet: str | None = None

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


class BugReport(BaseModel):
    """Bug 分析报告"""
    # 错误基本信息
    error_type: str = Field(..., description="异常类型（如 NameError, TypeError）")
    error_message: str = Field(..., description="原始错误信息")
    category: ErrorCategory = Field(ErrorCategory.UNKNOWN, description="错误分类")
    
    # 位置信息
    location: Location | None = Field(default_factory=Location, description="问题位置")
    
    # 分析结果
    severity: BugSeverity = Field(BugSeverity.MEDIUM, description="严重程度")
    root_cause: str = Field(..., description="根因分析")
    suggestions: List[str] = Field(default_factory=list, description="修复建议列表")
    
    # 上下文
    stack_trace: str | None = None
    code_snippet: str | None = None
    related_files: List[str] = Field(default_factory=list, description="相关文件")
    
    # 元数据
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="分析置信度")
    llm_used: bool = Field(False, description="是否使用了 LLM 分析")

    def to_summary(self) -> str:
        """生成简洁的摘要"""
        return (
            f"[{self.severity.value.upper()}] {self.error_type}: {self.error_message[:100]}\n"
            f"位置: {self.location}\n"
            f"根因: {self.root_cause[:200]}\n"
            f"建议: {'; '.join(self.suggestions[:3])}"
        )


class FixSuggestion(BaseModel):
    """修复建议"""
    file_path: str = Field(..., description="需要修改的文件路径")
    old_code: str = Field(..., description="原始代码")
    new_code: str = Field(..., description="修复后的代码")
    explanation: str = Field(..., description="修复说明")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="修复置信度 (0-1)")
    
    # 修复位置
    line_start: int | None = None
    line_end: int | None = None
    
    # 额外信息
    is_automated: bool = Field(False, description="是否可自动修复")
    warnings: List[str] = Field(default_factory=list, description="修复警告")

    def generate_diff(self) -> str:
        """生成 diff 格式的变更"""
        return (
            f"--- a/{self.file_path}\n"
            f"+++ b/{self.file_path}\n"
            f"@@ -{self.line_start or '?'}, +{self.line_end or '?'} @@\n"
            f"- {self.old_code}\n"
            f"+ {self.new_code}"
        )


class FixResult(BaseModel):
    """修复结果"""
    success: bool = Field(..., description="修复是否成功")
    file_path: str = Field(..., description="修改的文件路径")
    
    # 变更信息
    diff: str | None = None
    lines_changed: int = 0
    
    # 错误信息（如有）
    error: str | None = None
    
    # 验证信息
    verified: bool = Field(False, description="是否已验证")
    backup_path: str | None = None

    def to_summary(self) -> str:
        """生成结果摘要"""
        if self.success:
            return f"✅ 修复成功: {self.file_path} ({self.lines_changed} 行变更)"
        else:
            return f"❌ 修复失败: {self.file_path} - {self.error}"


class AnalysisRequest(BaseModel):
    """分析请求"""
    error_log: str = Field(..., description="错误日志或 traceback")
    code_context: Dict[str, str] | None = None
    file_paths: List[str] = Field(default_factory=list, description="相关文件路径列表")
    
    # 分析选项
    use_llm: bool = Field(True, description="是否使用 LLM 进行深度分析")
    max_depth: int | None = 3
    
    # 语言
    language: str | None = "python"


class AnalysisResult(BaseModel):
    """完整分析结果"""
    # 原始请求
    request: AnalysisRequest = Field(..., description="分析请求")
    
    # 分析报告
    report: BugReport = Field(..., description="Bug 分析报告")
    
    # 修复建议（可能为空）
    suggestions: List[FixSuggestion] = Field(default_factory=list, description="修复建议列表")
    
    # 执行信息
    execution_time: float = Field(0.0, description="分析耗时（秒）")
    patterns_matched: List[str] = Field(default_factory=list, description="匹配到的模式列表")

    def get_best_fix(self) -> Optional[FixSuggestion]:
        """获取最佳修复建议（置信度最高）"""
        if not self.suggestions:
            return None
        return max(self.suggestions, key=lambda s: s.confidence)
