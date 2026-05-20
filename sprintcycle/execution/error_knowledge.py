"""
ErrorKnowledgeBase - 统一错误知识库（精简版）

整合错误模式、解决方案，提供统一的错误查询接口。
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern

from loguru import logger

# Default patterns - can be overridden by config file
DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    {"pattern": r"name '(.+)' is not defined", "error_type": "NameError", "root_cause": "变量未定义", "suggested_fix": "确保变量在使用前已定义", "severity": "medium", "tags": ["variable"]},
    {"pattern": r"unsupported operand type\(s\) for (.+): '(.+)' and '(.+)'", "error_type": "TypeError", "root_cause": "类型不匹配", "suggested_fix": "添加类型检查或转换", "severity": "medium", "tags": ["type"]},
    {"pattern": r"'NoneType' object (has no attribute|is not iterable)", "error_type": "TypeError", "root_cause": "空值未检查", "suggested_fix": "使用 if value is not None", "severity": "medium", "tags": ["NoneType"]},
    {"pattern": r"No module named '(.+)'", "error_type": "ImportError", "root_cause": "依赖包未安装", "suggested_fix": "pip install \\1", "severity": "high", "tags": ["import", "dependency"]},
    {"pattern": r"cannot import name '(.+)' from '(.+)'", "error_type": "ImportError", "root_cause": "模块路径错误或版本不兼容", "suggested_fix": "检查 import 路径或版本", "severity": "high", "tags": ["import"]},
    {"pattern": r"'(.+)' object has no attribute '(.+)'", "error_type": "AttributeError", "root_cause": "对象没有该属性", "suggested_fix": "检查对象类型和属性名", "severity": "medium", "tags": ["attribute"]},
    {"pattern": r"list index out of range", "error_type": "IndexError", "root_cause": "索引超出列表长度", "suggested_fix": "检查索引范围", "severity": "medium", "tags": ["index"]},
    {"pattern": r"KeyError: '?(.+?)'?\s*$", "error_type": "KeyError", "root_cause": "字典键不存在", "suggested_fix": "使用 dict.get(key, default)", "severity": "low", "tags": ["dictionary"]},
    {"pattern": r"\[Errno 2\] No such file or directory: '(.+)'", "error_type": "FileNotFoundError", "root_cause": "文件路径错误", "suggested_fix": "检查文件路径", "severity": "high", "tags": ["file"]},
    {"pattern": r"SyntaxError: (.+)", "error_type": "SyntaxError", "root_cause": "语法错误", "suggested_fix": "检查语法", "severity": "critical", "tags": ["syntax"]},
    {"pattern": r"IndentationError: (.+)", "error_type": "IndentationError", "root_cause": "缩进不一致", "suggested_fix": "统一使用空格缩进", "severity": "critical", "tags": ["indentation"]},
    {"pattern": r"Permission denied: '(.+)'", "error_type": "PermissionError", "root_cause": "权限不足", "suggested_fix": "检查文件权限", "severity": "high", "tags": ["permission"]},
    {"pattern": r"(out of memory|MemoryError)", "error_type": "MemoryError", "root_cause": "内存不足", "suggested_fix": "优化内存使用", "severity": "critical", "tags": ["memory"]},
    {"pattern": r"maximum recursion depth exceeded", "error_type": "RecursionError", "root_cause": "递归无终止条件", "suggested_fix": "检查递归终止条件", "severity": "high", "tags": ["recursion"]},
]


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
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_attempts(self) -> int:
        return self.success_count + self.failure_count

    @property
    def confidence(self) -> float:
        if self.total_attempts == 0:
            return 0.5
        rate = self.success_count / self.total_attempts
        return round(rate * min(self.total_attempts / 5, 1.0), 2)

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
            return False

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
            "confidence": self.confidence,
            "pattern_id": self.pattern_id,
            "last_seen": self.last_seen.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorPattern":
        valid_fields = {"pattern", "error_type", "root_cause", "suggested_fix", "severity", "success_count", "failure_count", "last_seen", "tags", "metadata"}
        data = {k: v for k, v in data.items() if k in valid_fields}
        if "last_seen" in data and isinstance(data["last_seen"], str):
            data["last_seen"] = datetime.fromisoformat(data["last_seen"])
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
        return self.pattern.suggested_fix


class ErrorKnowledgeBase:
    """统一错误知识库（精简版）"""

    def __init__(self, storage_path: str = ".sprintcycle/error_knowledge", patterns: Optional[List[Dict[str, Any]]] = None):
        self.storage_path = Path(storage_path)
        self._patterns: Dict[str, ErrorPattern] = {}
        self._lock = asyncio.Lock()
        self._init_default_patterns(patterns or DEFAULT_PATTERNS)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _init_default_patterns(self, patterns: List[Dict[str, Any]]) -> None:
        for pattern_data in patterns:
            pattern = ErrorPattern(**pattern_data)
            self._patterns[pattern.pattern_id] = pattern

    def match(self, error_log: str, min_confidence: float = 0.0) -> Optional[PatternMatch]:
        best_match: Optional[PatternMatch] = None
        best_confidence = min_confidence

        for pattern in self._patterns.values():
            if pattern.matches(error_log):
                confidence = pattern.confidence
                if pattern.error_type.lower() in error_log.lower():
                    confidence = min(confidence + 0.2, 1.0)

                if confidence >= best_confidence:
                    best_match = PatternMatch(
                        pattern=pattern,
                        matched_text=error_log[:200],
                        confidence=confidence,
                    )
                    best_confidence = confidence

        return best_match

    def add_pattern(self, pattern: ErrorPattern) -> str:
        self._patterns[pattern.pattern_id] = pattern
        return pattern.pattern_id

    def record_fix(self, pattern_id: str, success: bool) -> None:
        pattern = self._patterns.get(pattern_id)
        if pattern:
            if success:
                pattern.record_success()
            else:
                pattern.record_failure()

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "total_patterns": len(self._patterns),
            "avg_confidence": sum(p.confidence for p in self._patterns.values()) / max(1, len(self._patterns)),
        }

    async def save(self) -> None:
        async with self._lock:
            try:
                patterns_file = self.storage_path / "patterns.json"
                with open(patterns_file, "w", encoding="utf-8") as f:
                    json.dump([p.to_dict() for p in self._patterns.values()], f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.debug(f"Save failed: {e}")

    async def load(self) -> None:
        async with self._lock:
            try:
                patterns_file = self.storage_path / "patterns.json"
                if patterns_file.exists():
                    with open(patterns_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._patterns = {ErrorPattern.from_dict(d).pattern_id: ErrorPattern.from_dict(d) for d in data}
            except Exception as e:
                logger.debug(f"Load failed: {e}")


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
