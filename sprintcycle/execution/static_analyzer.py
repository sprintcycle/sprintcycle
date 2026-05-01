"""
静态代码分析工具封装
"""

import asyncio
import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    tool: str
    file_path: str
    line: int
    column: int
    code: str
    message: str
    severity: str
    fix: Optional[str] = None
    rule_url: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line}:{self.column} [{self.code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "fix": self.fix,
            "rule_url": self.rule_url,
        }

    @classmethod
    def from_ruff(cls, data: Dict[str, Any]) -> "AnalysisResult":
        location = data.get("location", {})
        fix = data.get("fix")
        return cls(
            tool="ruff",
            file_path=data.get("filename", ""),
            line=location.get("row", 0),
            column=location.get("column", 0),
            code=data.get("code", ""),
            message=data.get("message", ""),
            severity=_map_ruff_severity(data.get("severity", {})),
            fix=fix.get("applicability") if fix else None,
            rule_url=f"https://docs.astral.sh/ruff/rules/{data.get('code', '').lower()}/",
        )

    @classmethod
    def from_mypy(cls, file_path: str, line: int, message: str) -> "AnalysisResult":
        code_match = re.search(r"\[([A-Z]\d+)\]", message)
        code = code_match.group(1) if code_match else "type-error"
        return cls(
            tool="mypy",
            file_path=file_path,
            line=line,
            column=0,
            code=code,
            message=message,
            severity="error" if "error" in message.lower() else "warning",
        )


def _map_ruff_severity(severity: Dict[str, Any]) -> str:
    if isinstance(severity, dict):
        level = severity.get("type", "warning")
    else:
        level = str(severity)
    mapping = {"error": "error", "warning": "warning", "info": "info"}
    return mapping.get(level.lower(), "warning")


@dataclass
class AnalysisConfig:
    """
    分析配置（deprecated in v0.9.1）
    
    推荐直接使用 RuntimeConfig 的相关字段。
    """
    ruff_enabled: bool = True
    ruff_rules: List[str] = field(default_factory=lambda: ["E", "F", "W", "I", "UP", "B", "C4"])
    ruff_ignore: List[str] = field(default_factory=list)
    ruff_fix: bool = False
    mypy_enabled: bool = True
    mypy_strict: bool = False
    mypy_ignore_missing_imports: bool = True
    semgrep_enabled: bool = False
    semgrep_rules: List[str] = field(default_factory=lambda: ["security", "best-practice"])
    auto_fix: bool = False
    confidence_threshold: float = 0.9
    max_results: int = 100


class StaticAnalyzer:
    """静态代码分析器"""
    
    def __init__(self, project_path: str, config: Optional[AnalysisConfig] = None):
        self.project_path = Path(project_path).resolve()
        self.config = config or AnalysisConfig()
        self._tool_cache: Dict[str, bool] = {}
    
    def _is_tool_available(self, tool: str) -> bool:
        if tool in self._tool_cache:
            return self._tool_cache[tool]
        try:
            result = subprocess.run(["which", tool], capture_output=True, text=True, timeout=5)
            available = result.returncode == 0
            self._tool_cache[tool] = available
            return available
        except Exception:
            self._tool_cache[tool] = False
            return False
    
    async def analyze_python(self, files: Optional[List[str]] = None) -> List[AnalysisResult]:
        """分析 Python 文件"""
        results = []
        
        if self.config.ruff_enabled and self._is_tool_available("ruff"):
            results.extend(await self._analyze_with_ruff(files))
        
        if self.config.mypy_enabled and self._is_tool_available("mypy"):
            results.extend(await self._analyze_with_mypy(files))
        
        return results
    
    async def _analyze_with_ruff(self, files: Optional[List[str]] = None) -> List[AnalysisResult]:
        """使用 Ruff 分析"""
        cmd = ["ruff", "check", "--output-format=json"]
        
        if self.config.ruff_rules:
            cmd.extend(["--select", ",".join(self.config.ruff_rules)])
        
        if self.config.ruff_ignore:
            cmd.extend(["--ignore", ",".join(self.config.ruff_ignore)])
        
        if self.config.ruff_fix:
            cmd.append("--fix")
        
        if files:
            cmd.extend(files)
        else:
            cmd.append(str(self.project_path))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    return [AnalysisResult.from_ruff(item) for item in data]
                except json.JSONDecodeError:
                    logger.warning("Failed to parse ruff output")
        except Exception as e:
            logger.warning(f"Ruff analysis failed: {e}")
        
        return []
    
    async def _analyze_with_mypy(self, files: Optional[List[str]] = None) -> List[AnalysisResult]:
        """使用 MyPy 分析"""
        cmd = ["python", "-m", "mypy", "--no-error-summary", "--output-format=json"]
        
        if self.config.mypy_ignore_missing_imports:
            cmd.append("--ignore-missing-imports")
        
        if self.config.mypy_strict:
            cmd.append("--strict")
        
        if files:
            cmd.extend(files)
        else:
            cmd.append(str(self.project_path))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    results = []
                    for item in data:
                        if "message" in item:
                            results.append(AnalysisResult.from_mypy(
                                item.get("file", ""),
                                item.get("line", 0),
                                item.get("message", "")
                            ))
                    return results
                except json.JSONDecodeError:
                    logger.warning("Failed to parse mypy output")
        except Exception as e:
            logger.warning(f"MyPy analysis failed: {e}")
        
        return []
    
    async def analyze_file(self, file_path: str) -> List[AnalysisResult]:
        """分析单个文件"""
        return await self.analyze_python([file_path])
    
    async def auto_fix(self, result: AnalysisResult) -> bool:
        """自动修复问题"""
        if result.tool == "ruff" and self.config.ruff_fix:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ruff", "check", "--fix", result.file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                return proc.returncode == 0
            except Exception as e:
                logger.warning(f"Auto-fix failed: {e}")
        return False
