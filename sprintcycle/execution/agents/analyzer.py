"""
Bug Analyzer Agent - Bug 分析执行器
"""

import re
import logging
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from .base import AgentExecutor, AgentContext, AgentResult, AgentType, AgentConfig
from .bug_models import (
    BugReport,
    BugSeverity,
    ErrorCategory,
    Location,
    FixSuggestion,
    FixResult,
    AnalysisRequest,
    AnalysisResult,
)

logger = logging.getLogger(__name__)


ROOT_CAUSE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "NameError": {
        "patterns": [r"name .+ is not defined"],
        "causes": ["变量未定义", "变量名拼写错误", "缺少 import"],
        "fixes": ["确保变量在使用前已定义", "检查变量名拼写", "添加缺失的 import"],
        "severity": BugSeverity.MEDIUM,
    },
    "TypeError": {
        "patterns": [r"unsupported operand", r"NoneType"],
        "causes": ["类型不匹配", "空值未处理"],
        "fixes": ["添加类型检查", "处理 None 情况"],
        "severity": BugSeverity.MEDIUM,
    },
    "ImportError": {
        "patterns": [r"No module named", r"cannot import name"],
        "causes": ["依赖未安装", "模块路径错误"],
        "fixes": ["pip install", "检查 import 路径"],
        "severity": BugSeverity.HIGH,
    },
    "AttributeError": {
        "patterns": [r"has no attribute"],
        "causes": ["对象没有该属性", "属性名拼写错误"],
        "fixes": ["检查属性名", "使用 hasattr", "使用 getattr"],
        "severity": BugSeverity.MEDIUM,
    },
    "IndexError": {
        "patterns": [r"index out of range"],
        "causes": ["索引越界"],
        "fixes": ["检查序列长度", "使用 try-except"],
        "severity": BugSeverity.MEDIUM,
    },
    "KeyError": {
        "patterns": [r"KeyError"],
        "causes": ["字典键不存在"],
        "fixes": ["使用 dict.get()", "检查键存在"],
        "severity": BugSeverity.LOW,
    },
    "FileNotFoundError": {
        "patterns": [r"No such file or directory"],
        "causes": ["文件不存在", "路径错误"],
        "fixes": ["检查文件路径", "使用 Path 检查"],
        "severity": BugSeverity.HIGH,
    },
    "SyntaxError": {
        "patterns": [r"invalid syntax"],
        "causes": ["语法错误", "括号不匹配"],
        "fixes": ["检查语法", "检查缩进"],
        "severity": BugSeverity.CRITICAL,
    },
    "IndentationError": {
        "patterns": [r"unexpected indent", r"expected an indented block"],
        "causes": ["缩进不一致", "混用空格和 Tab"],
        "fixes": ["统一缩进", "配置编辑器"],
        "severity": BugSeverity.CRITICAL,
    },
    "ValueError": {
        "patterns": [r"invalid literal for int", r"could not convert"],
        "causes": ["值转换失败", "参数值不符合预期"],
        "fixes": ["验证输入", "使用 try-except"],
        "severity": BugSeverity.MEDIUM,
    },
    "ZeroDivisionError": {
        "patterns": [r"division by zero"],
        "causes": ["除数为零"],
        "fixes": ["检查除数", "使用 if denominator != 0"],
        "severity": BugSeverity.MEDIUM,
    },
    "PermissionError": {
        "patterns": [r"Permission denied"],
        "causes": ["没有权限"],
        "fixes": ["检查权限", "使用 sudo"],
        "severity": BugSeverity.HIGH,
    },
    "MemoryError": {
        "patterns": [r"out of memory"],
        "causes": ["内存不足", "加载过大文件"],
        "fixes": ["优化内存", "使用生成器"],
        "severity": BugSeverity.CRITICAL,
    },
    "RecursionError": {
        "patterns": [r"maximum recursion depth"],
        "causes": ["递归过深", "没有终止条件"],
        "fixes": ["检查终止条件", "改用迭代"],
        "severity": BugSeverity.HIGH,
    },
}


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
                    "report": analysis_result.report.model_dump(),
                    "suggestions": [s.model_dump() for s in suggestions],
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
        
        parsed = self._parse_traceback(request.error_log or "", request.language or "python")
        pattern_match = self._match_pattern(parsed.error_type, parsed.error_message)
        
        report = BugReport(  # type: ignore[call-arg]
            error_type=parsed.error_type,
            error_message=parsed.error_message,
            category=pattern_match.category,
            location=parsed.location,
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
    
    def _parse_traceback(self, error_log: str, language: str = "python") -> "ParsedTraceback":
        parsed = ParsedTraceback()
        parsed.full_traceback = error_log
        
        if language == "python":
            self._parse_python_traceback(error_log, parsed)
        elif language in ("javascript", "typescript"):
            self._parse_js_traceback(error_log, parsed)
        else:
            self._parse_generic_error(error_log, parsed)
        
        return parsed
    
    def _parse_python_traceback(self, error_log: str, parsed: "ParsedTraceback") -> None:
        lines = error_log.strip().split("\n")
        
        if lines:
            error_line = lines[-1].strip()
            match = re.match(r"(\w+):\s*(.*)", error_line)
            if match:
                parsed.error_type = match.group(1)
                parsed.error_message = match.group(2)
            else:
                parsed.error_type = "Error"
                parsed.error_message = error_line
        
        frame_pattern = r'File "(.+)", line (\d+)(?:, in (.+))?\s*\n\s*(.+)'
        matches = re.finditer(frame_pattern, error_log)
        
        for match in matches:
            frame = StackFrame(
                file_path=match.group(1),
                line_number=int(match.group(2)),
                function_name=match.group(3),
                code=match.group(4).strip() if match.group(4) else None,
            )
            parsed.frames.append(frame)
        
        for frame in parsed.frames:
            if not self._is_stdlib_path(frame.file_path):
                parsed.location = Location(
                    file_path=frame.file_path,
                    line_number=frame.line_number,
                    function_name=frame.function_name,
                )
                parsed.code_snippet = frame.code
                break
        
        if not parsed.location and parsed.frames:
            frame = parsed.frames[-1]
            parsed.location = Location(
                file_path=frame.file_path,
                line_number=frame.line_number,
                function_name=frame.function_name,
            )
            parsed.code_snippet = frame.code
    
    def _parse_js_traceback(self, error_log: str, parsed: "ParsedTraceback") -> None:
        match = re.search(r"(\w+Error):\s*(.*?)(?:\s+at\s+|\n|$)", error_log, re.DOTALL)
        if match:
            parsed.error_type = match.group(1)
            parsed.error_message = match.group(2).strip()
        
        frame_pattern = r"at\s+(?:(.+?)\s+\)?(.+?):(\d+):(\d+)\)?"
        matches = re.finditer(frame_pattern, error_log)
        
        for match in matches:
            frame = StackFrame(
                file_path=match.group(2),
                line_number=int(match.group(3)),
                function_name=match.group(1),
                column_number=int(match.group(4)),
            )
            parsed.frames.append(frame)
        
        if parsed.frames:
            frame = parsed.frames[0]
            parsed.location = Location(
                file_path=frame.file_path,
                line_number=frame.line_number,
                column_number=frame.column_number,
                function_name=frame.function_name,
            )
    
    def _parse_generic_error(self, error_log: str, parsed: "ParsedTraceback") -> None:
        lines = error_log.strip().split("\n")
        
        if lines:
            match = re.match(r"(\w+Error|\w+Exception):\s*(.*)", lines[-1].strip())
            if match:
                parsed.error_type = match.group(1)
                parsed.error_message = match.group(2)
            else:
                parsed.error_type = "UnknownError"
                parsed.error_message = lines[-1].strip()
        
        path_pattern = r"([/\w]+\.[\w]+):(\d+)"
        match = re.search(path_pattern, error_log)
        if match:
            parsed.location = Location(
                file_path=match.group(1),
                line_number=int(match.group(2)),
            )
    
    def _is_stdlib_path(self, file_path: str) -> bool:
        stdlib_paths = ["/usr/lib/python", "/usr/local/lib/python", "lib/python", "site-packages"]
        return any(p in file_path for p in stdlib_paths)
    
    def _match_pattern(self, error_type: str, error_message: str) -> "PatternMatch":
        # 第一轮：精确匹配 error_type 与 pattern key
        for pattern_type, pattern_info in ROOT_CAUSE_PATTERNS.items():
            if pattern_type.lower() == error_type.lower():
                return PatternMatch(
                    category=self._type_to_category(pattern_type),
                    severity=pattern_info.get("severity", BugSeverity.MEDIUM),
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
                        severity=pattern_info.get("severity", BugSeverity.MEDIUM),
                        root_cause=", ".join(pattern_info.get("causes", [])),
                        fixes=pattern_info.get("fixes", []),
                        confidence=0.85,
                        matched_patterns=[pattern_type, regex_pattern],
                    )
        
        return PatternMatch(
            category=ErrorCategory.UNKNOWN,
            severity=BugSeverity.MEDIUM,
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
                severity=BugSeverity(data.get("severity", "medium")),
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
    
    # 修复建议生成策略
    _FIX_STRATEGIES = {
        "NameError": {
            "pattern": r"name '(\w+)'",
            "group_idx": 1,
            "generate": lambda m, loc: FixSuggestion(  # type: ignore[call-arg]
                file_path=loc.file_path or "unknown",
                old_code=m.group(1),
                new_code=f"# TODO: Define {m.group(1)}\n{m.group(1)}",
                explanation=f"变量 {m.group(1)} 未定义，请在使用前定义该变量",
                confidence=0.8,
            )
        },
        "ImportError": {
            "pattern": r"No module named '(.+)'",
            "group_idx": 1,
            "generate": lambda m, loc: FixSuggestion(  # type: ignore[call-arg]
                file_path=loc.file_path or "unknown",
                old_code=f"# import {m.group(1)}",
                new_code=f"# pip install {m.group(1)}\nimport {m.group(1)}",
                explanation=f"安装缺失的模块: pip install {m.group(1)}",
                confidence=0.95,
                is_automated=True,
            )
        },
        "KeyError": {
            "pattern": r"KeyError: '?(\w+)'?",
            "group_idx": 1,
            "generate": lambda m, loc: FixSuggestion(  # type: ignore[call-arg]
                file_path=loc.file_path or "unknown",
                old_code=f"dict['{m.group(1)}']",
                new_code=f"dict.get('{m.group(1)}', default_value)",
                explanation=f"使用 dict.get() 安全获取键 {m.group(1)}",
                confidence=0.85,
            )
        },
        "AttributeError": {
            "pattern": r"has no attribute '(\w+)'",
            "group_idx": 1,
            "generate": lambda m, loc: FixSuggestion(  # type: ignore[call-arg]
                file_path=loc.file_path or "unknown",
                old_code=f"obj.{m.group(1)}",
                new_code=f"getattr(obj, '{m.group(1)}', default_value)",
                explanation=f"使用 getattr() 安全获取属性 {m.group(1)}",
                confidence=0.75,
            )
        },
    }
    
    # 简单的固定建议模板
    _FIX_TEMPLATES = {
        "TypeError": lambda loc: FixSuggestion(  # type: ignore[call-arg]
            file_path=loc.file_path or "unknown",
            old_code="# existing code",
            new_code="# Add type check\nif isinstance(value, expected_type):\n    # existing code",
            explanation="添加类型检查以避免类型错误",
            confidence=0.7,
            line_start=loc.line_number,
        ),
        "ZeroDivisionError": lambda loc: FixSuggestion(  # type: ignore[call-arg]
            file_path=loc.file_path or "unknown",
            old_code="# denominator",
            new_code="# Add zero check\nif denominator != 0:\n    result = numerator / denominator",
            explanation="在除法前检查除数是否为零",
            confidence=0.9,
        ),
        "IndexError": lambda loc: FixSuggestion(  # type: ignore[call-arg]
            file_path=loc.file_path or "unknown",
            old_code="# list[index]",
            new_code="# Add bounds check\nif 0 <= index < len(list):\n    item = list[index]",
            explanation="在访问索引前检查边界",
            confidence=0.8,
        ),
    }

    async def suggest_fix(self, report: BugReport) -> List[FixSuggestion]:
        """生成修复建议"""
        suggestions = []
        error_type = report.error_type
        location = report.location
        
        # 使用策略模式处理需要正则匹配的修复
        if error_type in self._FIX_STRATEGIES:
            strategy = self._FIX_STRATEGIES[error_type]
            match = re.search(str(strategy["pattern"]), report.error_message)
            if match:
                suggestions.append(strategy["generate"](match, location))  # type: ignore[arg-type,misc,operator]
        
        # 使用模板处理固定的修复建议
        elif error_type in self._FIX_TEMPLATES:
            suggestions.append(self._FIX_TEMPLATES[error_type](location))
        
        # 添加来自报告的建议
        for suggestion in report.suggestions[:2]:
            if not any(s.explanation == suggestion for s in suggestions):
                suggestions.append(FixSuggestion(  # type: ignore[call-arg]
                    file_path=str(getattr(location, "file_path", None) or "unknown"),
                    old_code="",
                    new_code="",
                    explanation=suggestion,
                    confidence=0.6,
                ))
        
        
        return suggestions


    async def apply_fix(self, suggestion: FixSuggestion) -> FixResult:
        file_path = Path(suggestion.file_path)
        
        if not file_path.exists():
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(suggestion.new_code, encoding="utf-8")
                return FixResult(  # type: ignore[call-arg]
                    success=True,
                    file_path=str(file_path),
                    diff=suggestion.generate_diff(),
                    lines_changed=1,
                    backup_path=None,
                )
            except Exception as e:
                return FixResult(success=False, file_path=str(file_path), error=str(e))  # type: ignore[call-arg]
        
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
            
            return FixResult(  # type: ignore[call-arg]
                success=True,
                file_path=str(file_path),
                diff=suggestion.generate_diff(),
                lines_changed=lines_changed,
                verified=False,
                backup_path=str(backup_path),
            )
            
        except Exception as e:
            return FixResult(success=False, file_path=str(file_path), error=str(e))  # type: ignore[call-arg]


class StackFrame:
    def __init__(self, file_path: str, line_number: int, function_name: Optional[str] = None,
                 code: Optional[str] = None, column_number: Optional[int] = None):
        self.file_path = file_path
        self.line_number = line_number
        self.function_name = function_name
        self.code = code
        self.column_number = column_number


class ParsedTraceback:
    def __init__(self):
        self.error_type: str = ""
        self.error_message: str = ""
        self.full_traceback: str = ""
        self.location: Optional[Location] = None
        self.code_snippet: Optional[str] = None
        self.frames: List[StackFrame] = []


class PatternMatch:
    def __init__(self, category: ErrorCategory, severity: BugSeverity, root_cause: str,
                 fixes: List[str], confidence: float, matched_patterns: List[str]):
        self.category = category
        self.severity = severity
        self.root_cause = root_cause
        self.fixes = fixes
        self.confidence = confidence
        self.matched_patterns = matched_patterns


__all__ = [
    "BugAnalyzerAgent",
    "BugReport",
    "BugSeverity",
    "ErrorCategory",
    "Location",
    "FixSuggestion",
    "FixResult",
    "AnalysisRequest",
    "AnalysisResult",
]
