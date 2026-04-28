"""
ErrorKnowledgeBase - 统一错误知识库

整合所有错误模式、解决方案和历史记录，提供统一的错误查询接口。

功能：
1. 统一的错误模式存储 (ROOT_CAUSE_PATTERNS + ErrorPattern)
2. 模式匹配与置信度计算
3. 历史记录持久化
4. 自学习机制（根据修复结果更新置信度）
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ErrorPattern:
    """错误模式数据类"""
    pattern: str
    error_type: str
    root_cause: str
    suggested_fix: str
    severity: str = "medium"
    success_count: int = 0
    failure_count: int = 0
    last_seen: datetime = field(default_factory=datetime.now)
    first_seen: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_attempts(self) -> int:
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts
    
    @property
    def confidence(self) -> float:
        base_rate = self.success_rate
        attempt_factor = min(self.total_attempts / 5, 1.0)
        return round(base_rate * attempt_factor, 2)
    
    @property
    def pattern_id(self) -> str:
        import hashlib
        hash_input = f"{self.error_type}:{self.pattern[:50]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def matches(self, error_log: str) -> bool:
        try:
            compiled_pattern: Pattern = re.compile(self.pattern, re.MULTILINE | re.IGNORECASE)
            return bool(compiled_pattern.search(error_log))
        except re.error:
            logger.warning(f"Invalid regex: {self.pattern}")
            return False
    
    def extract_values(self, error_log: str) -> Dict[str, str]:
        try:
            compiled_pattern: Pattern = re.compile(self.pattern, re.MULTILINE)
            match = compiled_pattern.search(error_log)
            if match and match.groupdict():
                return match.groupdict()
            elif match:
                return {f"group_{i}": g for i, g in enumerate(match.groups(), 1)}
        except re.error:
            pass
        return {}
    
    def record_success(self) -> None:
        self.success_count += 1
        self.last_seen = datetime.now()
    
    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "error_type": self.error_type,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
            "severity": self.severity,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "confidence": self.confidence,
            "pattern_id": self.pattern_id,
            "last_seen": self.last_seen.isoformat(),
            "first_seen": self.first_seen.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorPattern":
        data = data.copy()
        if "last_seen" in data and isinstance(data["last_seen"], str):
            data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        if "first_seen" in data and isinstance(data["first_seen"], str):
            data["first_seen"] = datetime.fromisoformat(data["first_seen"])
        return cls(**data)


@dataclass
class PatternMatch:
    """模式匹配结果"""
    pattern: ErrorPattern
    matched_text: str
    confidence: float
    extracted_values: Dict[str, str] = field(default_factory=dict)
    
    @property
    def root_cause(self) -> str:
        return self.pattern.root_cause
    
    @property
    def suggested_fix(self) -> str:
        fix = self.pattern.suggested_fix
        for key, value in self.extracted_values.items():
            fix = fix.replace(f"\\{key}", value)
            fix = fix.replace(f"{{{key}}}", value)
        return fix


@dataclass
class FixRecord:
    """修复记录"""
    error_log: str
    pattern_id: str
    fix_applied: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorKnowledgeBase:
    """统一错误知识库"""
    
    DEFAULT_PATTERNS: List[Dict[str, Any]] = [
        {"pattern": r"name '(.+)' is not defined", "error_type": "NameError",
         "root_cause": "变量未定义或拼写错误", "suggested_fix": "确保变量在使用前已定义",
         "severity": "medium", "tags": ["variable", "undefined"]},
        {"pattern": r"unsupported operand type\(s\) for (.+): '(.+)' and '(.+)'", "error_type": "TypeError",
         "root_cause": "类型不匹配的操作", "suggested_fix": "添加类型检查或类型转换",
         "severity": "medium", "tags": ["type", "operation"]},
        {"pattern": r"'NoneType' object (has no attribute|is not iterable)", "error_type": "TypeError",
         "root_cause": "空值未检查", "suggested_fix": "使用 if value is not None 检查",
         "severity": "medium", "tags": ["NoneType", "null-check"]},
        {"pattern": r"No module named '(.+)'", "error_type": "ImportError",
         "root_cause": "依赖包未安装", "suggested_fix": "pip install \\1",
         "severity": "high", "tags": ["import", "dependency"]},
        {"pattern": r"cannot import name '(.+)' from '(.+)'", "error_type": "ImportError",
         "root_cause": "模块路径错误或版本不兼容", "suggested_fix": "检查 import 路径或版本",
         "severity": "high", "tags": ["import", "compatibility"]},
        {"pattern": r"'(.+)' object has no attribute '(.+)'", "error_type": "AttributeError",
         "root_cause": "对象没有该属性", "suggested_fix": "检查对象类型和属性名",
         "severity": "medium", "tags": ["attribute", "typo"]},
        {"pattern": r"list index out of range", "error_type": "IndexError",
         "root_cause": "索引超出列表长度", "suggested_fix": "检查索引范围",
         "severity": "medium", "tags": ["index", "list"]},
        {"pattern": r"KeyError: '?(.+?)'?\s*$", "error_type": "KeyError",
         "root_cause": "字典键不存在", "suggested_fix": "使用 dict.get(key, default)",
         "severity": "low", "tags": ["dictionary", "key"]},
        {"pattern": r"\[Errno 2\] No such file or directory: '(.+)'", "error_type": "FileNotFoundError",
         "root_cause": "文件路径错误", "suggested_fix": "检查文件路径",
         "severity": "high", "tags": ["file", "path"]},
        {"pattern": r"SyntaxError: (.+)", "error_type": "SyntaxError",
         "root_cause": "语法错误", "suggested_fix": "检查语法",
         "severity": "critical", "tags": ["syntax"]},
        {"pattern": r"IndentationError: (.+)", "error_type": "IndentationError",
         "root_cause": "缩进不一致", "suggested_fix": "统一使用空格缩进",
         "severity": "critical", "tags": ["indentation"]},
        {"pattern": r"invalid literal for int\(\) with base 10: '(.+)'", "error_type": "ValueError",
         "root_cause": "字符串转数字失败", "suggested_fix": "验证字符串格式",
         "severity": "medium", "tags": ["conversion", "validation"]},
        {"pattern": r"(division|float division) by zero", "error_type": "ZeroDivisionError",
         "root_cause": "除数为零", "suggested_fix": "检查除数是否为零",
         "severity": "medium", "tags": ["arithmetic"]},
        {"pattern": r"Permission denied: '(.+)'", "error_type": "PermissionError",
         "root_cause": "权限不足", "suggested_fix": "检查文件权限或使用 sudo",
         "severity": "high", "tags": ["permission"]},
        {"pattern": r"(out of memory|MemoryError)", "error_type": "MemoryError",
         "root_cause": "内存不足", "suggested_fix": "优化内存使用",
         "severity": "critical", "tags": ["memory"]},
        {"pattern": r"maximum recursion depth exceeded", "error_type": "RecursionError",
         "root_cause": "递归无终止条件", "suggested_fix": "检查递归终止条件",
         "severity": "high", "tags": ["recursion"]},
    ]
    
    def __init__(self, storage_path: str = ".sprintcycle/error_knowledge", auto_save: bool = True):
        self.storage_path = Path(storage_path)
        self.auto_save = auto_save
        self._lock = asyncio.Lock()
        self._patterns: Dict[str, ErrorPattern] = {}
        self._fix_history: List[FixRecord] = []
        self._init_default_patterns()
        if self.auto_save:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            # 延迟加载，避免在非异步上下文中的问题
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.load())
            except RuntimeError:
                pass  # 没有运行中的事件循环，稍后加载
    
    def _init_default_patterns(self) -> None:
        for pattern_data in self.DEFAULT_PATTERNS:
            pattern = ErrorPattern(**pattern_data)
            self._patterns[pattern.pattern_id] = pattern
    
    @property
    def patterns(self) -> Dict[str, ErrorPattern]:
        return self._patterns.copy()
    
    @property
    def history(self) -> List[FixRecord]:
        return self._fix_history.copy()
    
    def add_pattern(self, pattern: ErrorPattern) -> str:
        self._patterns[pattern.pattern_id] = pattern
        if self.auto_save:
            asyncio.create_task(self.save())
        return pattern.pattern_id
    
    def get_pattern(self, pattern_id: str) -> Optional[ErrorPattern]:
        return self._patterns.get(pattern_id)
    
    def match(self, error_log: str, min_confidence: float = 0.0) -> Optional[PatternMatch]:
        best_match: Optional[PatternMatch] = None
        best_confidence = min_confidence
        
        for pattern in self._patterns.values():
            if pattern.matches(error_log):
                confidence = pattern.confidence if pattern.confidence > 0 else 0.5
                if pattern.error_type.lower() in error_log.lower():
                    confidence = min(confidence + 0.2, 1.0)
                
                if confidence >= best_confidence:
                    extracted = pattern.extract_values(error_log)
                    best_match = PatternMatch(
                        pattern=pattern,
                        matched_text=error_log[:200],
                        confidence=confidence,
                        extracted_values=extracted,
                    )
                    best_confidence = confidence
        
        return best_match
    
    def match_all(self, error_log: str) -> List[PatternMatch]:
        matches = []
        for pattern in self._patterns.values():
            if pattern.matches(error_log):
                confidence = pattern.confidence
                if pattern.error_type.lower() in error_log.lower():
                    confidence = min(confidence + 0.2, 1.0)
                matches.append(PatternMatch(
                    pattern=pattern,
                    matched_text=error_log[:200],
                    confidence=confidence,
                    extracted_values=pattern.extract_values(error_log),
                ))
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches
    
    def record_fix(self, error_log: str, pattern_id: str, fix_applied: str,
                   success: bool, duration: float = 0.0, **metadata) -> None:
        pattern = self._patterns.get(pattern_id)
        if pattern:
            if success:
                pattern.record_success()
            else:
                pattern.record_failure()
        
        record = FixRecord(
            error_log=error_log[:1000],
            pattern_id=pattern_id,
            fix_applied=fix_applied,
            success=success,
            duration=duration,
            metadata=metadata,
        )
        self._fix_history.append(record)
        if len(self._fix_history) > 10000:
            self._fix_history = self._fix_history[-5000:]
        if self.auto_save:
            asyncio.create_task(self.save())
    
    def get_statistics(self) -> Dict[str, Any]:
        total_patterns = len(self._patterns)
        total_fixes = len(self._fix_history)
        successful_fixes = sum(1 for r in self._fix_history if r.success)
        return {
            "total_patterns": total_patterns,
            "total_fixes": total_fixes,
            "successful_fixes": successful_fixes,
            "success_rate": successful_fixes / total_fixes if total_fixes > 0 else 0,
        }
    
    async def save(self) -> None:
        async with self._lock:
            try:
                patterns_file = self.storage_path / "patterns.json"
                with open(patterns_file, "w", encoding="utf-8") as f:
                    json.dump([p.to_dict() for p in self._patterns.values()], f, ensure_ascii=False, indent=2)
                logger.debug(f"Saved {len(self._patterns)} patterns")
            except Exception as e:
                logger.error(f"Save failed: {e}")
    
    async def load(self) -> None:
        async with self._lock:
            try:
                patterns_file = self.storage_path / "patterns.json"
                if patterns_file.exists():
                    with open(patterns_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._patterns = {ErrorPattern.from_dict(d).pattern_id: ErrorPattern.from_dict(d) for d in data}
                    logger.debug(f"Loaded {len(self._patterns)} patterns")
            except Exception as e:
                logger.error(f"Load failed: {e}")


_default_knowledge_base: Optional[ErrorKnowledgeBase] = None


def get_error_knowledge_base() -> ErrorKnowledgeBase:
    global _default_knowledge_base
    if _default_knowledge_base is None:
        _default_knowledge_base = ErrorKnowledgeBase()
    return _default_knowledge_base


def reset_error_knowledge_base() -> ErrorKnowledgeBase:
    global _default_knowledge_base
    _default_knowledge_base = ErrorKnowledgeBase()
    return _default_knowledge_base
