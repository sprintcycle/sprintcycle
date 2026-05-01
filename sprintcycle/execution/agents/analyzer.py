"""
Bug Analyzer Agent - Bug 分析执行器
"""

import re
import logging
import time
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING
from pathlib import Path

from .base import AgentExecutor, AgentContext, AgentResult, AgentType, AgentConfig
from .bug_models import (
    BugReport,
    Severity,
    ErrorCategory,
    Location,
    FixSuggestion,
    FixResult,
    AnalysisRequest,
    AnalysisResult,
    StackFrame,
    ParsedTraceback,
    PatternMatch,
)

logger = logging.getLogger(__name__)


from .patterns import ROOT_CAUSE_PATTERNS
from .traceback_parser import parse_traceback


class BugAnalyzerAgent(AgentExecutor):
    """Bug 分析 Agent"""

    def __init__(self, config=None, llm_client=None):
        super().__init__()
        self._llm_client = llm_client
        self._config = config if config is not None else AgentConfig()

    @property
    def agent_type(self) -> AgentType:
        return AgentType.CUSTOM
    
    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        logger.info("BugAnalyzer 开始分析任务...")
        start_time = time.time()
        
        try:
            error_log = self._extract_error_log(task, context)
            
            if not error_log:
                return AgentResult(
                    success=False,
                    error="未找到可分析的的错误日志",
                    agent_type=self.agent_type,
                )
            
            request = AnalysisRequest(
                error_log=error_log,
                file_paths=context.codebase_context.get("file_paths", []),
                use_llm=self._llm_client is not None,
            )
            
            analysis_result = await self.analyze(request)
            suggestions = await self.suggest_fix(analysis_result.report)
            analysis_result.suggestions = suggestions
            
            duration = time.time() - start_time
            
            return AgentResult(
                success=True,
                output=analysis_result.report.to_summary(),
                artifacts={
                    "report": dataclass_to_dict(analysis_result.report),
                    "suggestions": [dataclass_to_dict(s) for s in suggestions],
                },
                metrics={
                    "duration": duration,
                    "confidence": analysis_result.report.confidence,
                    "suggestions_count": len(suggestions),
                    "llm_used": analysis_result.report.llm_used,
                },
                feedback=f"分析了 {analysis_result.report.error_type} 错误，置信度 {analysis_result.report.confidence:.1%}",
                agent_type=self.agent_type,
            )
            
        except Exception as e:
            logger.error(f"BugAnalyzer 分析失败: {e}")
            return AgentResult.from_error(str(e), self.agent_type)
    
    def _extract_error_log(self, task: str, context: AgentContext) -> Optional[str]:
        if "Traceback" in task or "Error" in task:
            return task
        if context.dependencies.get("error_log"):
            return context.dependencies["error_log"]
        if context.codebase_context.get("error_log"):
            return context.codebase_context["error_log"]
        return None
    
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        start_time = time.time()
        
        parsed = parse_traceback(request.error_log or "", request.language or "python")
        pattern_match = self._match_pattern(parsed.error_type, parsed.error_message)
        
        # 创建 BugReport，location 可能为 None
        loc = parsed.location or Location()
        report = BugReport(
            error_type=parsed.error_type,
            error_message=parsed.error_message,
            category=pattern_match.category,
            location=loc,
            severity=pattern_match.severity,
            root_cause=pattern_match.root_cause,
            suggestions=pattern_match.fixes,
            stack_trace=parsed.full_traceback,
            code_snippet=parsed.code_snippet,
            confidence=pattern_match.confidence,
        )
        
        if request.use_llm and self._llm_client:
            llm_report = await self._llm_analyze(request.error_log, request.code_context or {})
            if llm_report:
                if llm_report.confidence > report.confidence:
                    report = llm_report
                else:
                    report.suggestions.extend(llm_report.suggestions)
                report.llm_used = True
        
        execution_time = time.time() - start_time
        
        return AnalysisResult(
            request=request,
            report=report,
            execution_time=execution_time,
            patterns_matched=pattern_match.matched_patterns,
        )
    
    
    def _match_pattern(self, error_type: str, error_message: str) -> PatternMatch:
        # 第一轮：精确匹配 error_type 与 pattern key
        for pattern_type, pattern_info in ROOT_CAUSE_PATTERNS.items():
            if pattern_type.lower() == error_type.lower():
                return PatternMatch(
                    category=self._type_to_category(pattern_type),
                    severity=pattern_info.get("severity", Severity.MEDIUM),
                    root_cause=", ".join(pattern_info.get("causes", [])),
                    fixes=pattern_info.get("fixes", []),
                    confidence=0.9,
                    matched_patterns=[pattern_type],
                )
        
        # 第二轮：通过 regex pattern 匹配错误消息
        for pattern_type, pattern_info in ROOT_CAUSE_PATTERNS.items():
            for regex_pattern in pattern_info.get("patterns", []):
                if re.search(regex_pattern, error_message, re.IGNORECASE):
                    return PatternMatch(
                        category=self._type_to_category(pattern_type),
                        severity=pattern_info.get("severity", Severity.MEDIUM),
                        root_cause=", ".join(pattern_info.get("causes", [])),
                        fixes=pattern_info.get("fixes", []),
                        confidence=0.85,
                        matched_patterns=[pattern_type, regex_pattern],
                    )
        
        return PatternMatch(
            category=ErrorCategory.UNKNOWN,
            severity=Severity.MEDIUM,
            root_cause="需要更多信息才能确定根因",
            fixes=["查看完整堆栈跟踪", "检查相关代码逻辑", "使用 LLM 进行深度分析"],
            confidence=0.3,
            matched_patterns=[],
        )
    
    def _type_to_category(self, error_type: str) -> ErrorCategory:
        mapping = {
            "NameError": ErrorCategory.NAME,
            "TypeError": ErrorCategory.TYPE,
            "ImportError": ErrorCategory.IMPORT,
            "AttributeError": ErrorCategory.ATTRIBUTE,
            "IndexError": ErrorCategory.INDEX,
            "KeyError": ErrorCategory.KEY,
            "FileNotFoundError": ErrorCategory.RUNTIME,
            "SyntaxError": ErrorCategory.SYNTAX,
            "IndentationError": ErrorCategory.SYNTAX,
            "ValueError": ErrorCategory.VALUE,
            "ZeroDivisionError": ErrorCategory.VALUE,
            "RecursionError": ErrorCategory.RUNTIME,
            "MemoryError": ErrorCategory.MEMORY,
        }
        return mapping.get(error_type, ErrorCategory.UNKNOWN)
    
    async def _llm_analyze(self, error_log: str, code_context: Dict[str, str]) -> Optional[BugReport]:
        if not self._llm_client:
            return None
        
        try:
            import json
            context_str = "\n".join([f"=== {k} ===\n{v[:1000]}" for k, v in code_context.items()])
            
            prompt = f"""你是专业的 Bug 分析专家。请分析以下错误并生成修复报告。
错误日志：
{error_log}
相关代码：
{context_str or "无相关代码上下文"}
请以 JSON 格式输出分析报告：
{{
    "error_type": "错误类型",
    "root_cause": "根本原因分析（简洁，不超过100字）",
    "file_path": "问题文件路径（如能确定）",
    "line_number": 问题行号（如能确定）,
    "severity": "critical|high|medium|low",
    "suggestions": ["修复建议1", "修复建议2"],
    "confidence": 0.0-1.0
}}
只输出 JSON，不要有其他内容。"""
            
            response = await self._llm_client.chat(prompt)
            data = json.loads(response)
            
            return BugReport(
                error_type=data.get("error_type", "Unknown"),
                error_message=error_log[:200],
                category=self._type_to_category(data.get("error_type", "")),
                location=Location(file_path=data.get("file_path"), line_number=data.get("line_number")),
                severity=Severity(data.get("severity", "medium")),
                root_cause=data.get("root_cause", ""),
                suggestions=data.get("suggestions", []),
                confidence=data.get("confidence", 0.8),
                llm_used=True,
            )
            
        except Exception as e:
            logger.warning(f"LLM 分析失败: {e}")
            return None
    
    async def locate(self, report: BugReport, file_paths: List[str]) -> List[Location]:
        locations = []
        search_keywords = self._build_search_keywords(report)
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if not path.exists() or not path.is_file():
                    continue
                
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    if self._line_matches(line, search_keywords):
                        locations.append(Location(
                            file_path=str(path),
                            line_number=i,
                            code_snippet=line.strip(),
                        ))
                
            except Exception as e:
                logger.warning(f"定位文件 {file_path} 失败: {e}")
        
        return locations
    
    def _build_search_keywords(self, report: BugReport) -> List[str]:
        keywords = []
        message = report.error_message
        for match in re.finditer(r"'([^']+)'", message):
            part = match.group(1)
            if part and len(part) > 2:
                keywords.append(part)
        
        if report.error_type == "NameError":
            name_match = re.search(r"name '(\w+)'", message)
            if name_match:
                keywords.append(name_match.group(1))
        
        return keywords
    
    def _line_matches(self, line: str, keywords: List[str]) -> bool:
        if not keywords:
            return False
        for keyword in keywords:
            if keyword in line:
                return True
        return False

    async def suggest_fix(self, report: BugReport) -> List[FixSuggestion]:
        """生成修复建议"""
        suggestions: List[FixSuggestion] = []
        location = report.location or Location()
        file_path = location.file_path or "unknown"

        # 使用字典映射错误类型到处理函数
        fix_handlers = {
            "NameError": lambda: self._fix_name_error(report.error_message, file_path),
            "ImportError": lambda: self._fix_import_error(report.error_message, file_path),
            "KeyError": lambda: self._fix_key_error(report.error_message, file_path),
            "AttributeError": lambda: self._fix_attribute_error(report.error_message, file_path),
            "TypeError": lambda: self._fix_type_error(file_path, location.line_number),
            "ZeroDivisionError": lambda: self._fix_zero_division_error(file_path),
            "IndexError": lambda: self._fix_index_error(file_path),
        }

        handler = fix_handlers.get(report.error_type)
        if handler:
            suggestion = handler()
            if suggestion:
                suggestions.append(suggestion)

        # 添加来自报告的建议
        for report_suggestion in report.suggestions[:2]:
            if not any(s.explanation == report_suggestion for s in suggestions):
                suggestions.append(FixSuggestion(
                    file_path=file_path,
                    old_code="",
                    new_code="",
                    explanation=report_suggestion,
                    confidence=0.6,
                ))

        return suggestions

    def _fix_name_error(self, error_message: str, file_path: str) -> Optional[FixSuggestion]:
        """修复 NameError"""
        match = re.search(r"name '(\w+)'", error_message)
        if match:
            var_name = match.group(1)
            return FixSuggestion(
                file_path=file_path,
                old_code=var_name,
                new_code=f"# TODO: Define {var_name}\n{var_name}",
                explanation=f"变量 {var_name} 未定义，请在使用前定义该变量",
                confidence=0.8,
            )
        return None

    def _fix_import_error(self, error_message: str, file_path: str) -> Optional[FixSuggestion]:
        """修复 ImportError"""
        match = re.search(r"No module named '(.+)'", error_message)
        if match:
            module_name = match.group(1)
            return FixSuggestion(
                file_path=file_path,
                old_code=f"# import {module_name}",
                new_code=f"# pip install {module_name}\nimport {module_name}",
                explanation=f"安装缺失的模块: pip install {module_name}",
                confidence=0.95,
                is_automated=True,
            )
        return None

    def _fix_key_error(self, error_message: str, file_path: str) -> Optional[FixSuggestion]:
        """修复 KeyError"""
        match = re.search(r"KeyError: '?(\w+)'?", error_message)
        if match:
            key_name = match.group(1)
            return FixSuggestion(
                file_path=file_path,
                old_code=f"dict['{key_name}']",
                new_code=f"dict.get('{key_name}', default_value)",
                explanation=f"使用 dict.get() 安全获取键 {key_name}",
                confidence=0.85,
            )
        return None

    def _fix_attribute_error(self, error_message: str, file_path: str) -> Optional[FixSuggestion]:
        """修复 AttributeError"""
        match = re.search(r"has no attribute '(\w+)'", error_message)
        if match:
            attr_name = match.group(1)
            return FixSuggestion(
                file_path=file_path,
                old_code=f"obj.{attr_name}",
                new_code=f"getattr(obj, '{attr_name}', default_value)",
                explanation=f"使用 getattr() 安全获取属性 {attr_name}",
                confidence=0.75,
            )
        return None

    def _fix_type_error(self, file_path: str, line_number: Optional[int]) -> FixSuggestion:
        """修复 TypeError"""
        return FixSuggestion(
            file_path=file_path,
            old_code="# existing code",
            new_code="# Add type check\nif isinstance(value, expected_type):\n    # existing code",
            explanation="添加类型检查以避免类型错误",
            confidence=0.7,
            line_start=line_number,
        )

    def _fix_zero_division_error(self, file_path: str) -> FixSuggestion:
        """修复 ZeroDivisionError"""
        return FixSuggestion(
            file_path=file_path,
            old_code="# denominator",
            new_code="# Add zero check\nif denominator != 0:\n    result = numerator / denominator",
            explanation="在除法前检查除数是否为零",
            confidence=0.9,
        )

    def _fix_index_error(self, file_path: str) -> FixSuggestion:
        """修复 IndexError"""
        return FixSuggestion(
            file_path=file_path,
            old_code="# list[index]",
            new_code="# Add bounds check\nif 0 <= index < len(list):\n    item = list[index]",
            explanation="在访问索引前检查边界",
            confidence=0.8,
        )


    async def apply_fix(self, suggestion: FixSuggestion) -> FixResult:
        file_path = Path(suggestion.file_path)
        
        if not file_path.exists():
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(suggestion.new_code, encoding="utf-8")
                return FixResult(
                    success=True,
                    file_path=str(file_path),
                    diff=suggestion.generate_diff(),
                    lines_changed=1,
                    backup_path=None,
                )
            except Exception as e:
                return FixResult(success=False, file_path=str(file_path), error=str(e))
        
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            backup_path.write_text(content, encoding="utf-8")
            
            if suggestion.old_code and suggestion.old_code in content:
                new_content = content.replace(suggestion.old_code, suggestion.new_code, 1)
            elif suggestion.line_start:
                start_idx = suggestion.line_start - 1
                end_idx = suggestion.line_end or suggestion.line_start
                if start_idx < len(lines):
                    lines[start_idx:end_idx] = [suggestion.new_code]
                    new_content = "\n".join(lines)
                else:
                    raise ValueError(f"行号 {suggestion.line_start} 超出文件范围")
            else:
                new_content = content + "\n" + suggestion.new_code
            
            file_path.write_text(new_content, encoding="utf-8")
            
            old_lines = len(content.split("\n"))
            new_lines = len(new_content.split("\n"))
            lines_changed = abs(new_lines - old_lines)
            
            return FixResult(
                success=True,
                file_path=str(file_path),
                diff=suggestion.generate_diff(),
                lines_changed=lines_changed,
                verified=False,
                backup_path=str(backup_path),
            )
            
        except Exception as e:
            return FixResult(success=False, file_path=str(file_path), error=str(e))


def dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """将 dataclass 对象转换为字典"""
    if hasattr(obj, '__dataclass_fields__'):
        result: Dict[str, Any] = {}
        for name in obj.__dataclass_fields__:
            value = getattr(obj, name)
            if isinstance(value, (list, tuple)):
                result[name] = [dataclass_to_dict(v) if hasattr(v, '__dataclass_fields__') else v for v in value]
            elif isinstance(value, dict):
                result[name] = {k: dataclass_to_dict(v) if hasattr(v, '__dataclass_fields__') else v for k, v in value.items()}
            elif hasattr(value, '__dataclass_fields__'):
                result[name] = dataclass_to_dict(value)
            elif value is not None:
                result[name] = value
        return result
    return obj


__all__ = [
    "BugAnalyzerAgent",
    "BugReport",
    "Severity",
    "ErrorCategory",
    "Location",
    "FixSuggestion",
    "FixResult",
    "AnalysisRequest",
    "AnalysisResult",
    "StackFrame",
    "ParsedTraceback",
    "PatternMatch",
]
