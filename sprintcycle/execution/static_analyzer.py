"""
静态代码分析工具封装

集成成熟的开源工具：
- Ruff: Python Linter + Formatter (极快)
- MyPy: 类型检查
- Semgrep: 代码模式匹配

优点：
1. 无需 LLM 调用，速度快
2. 专业工具，准确率高
3. 可扩展（添加更多规则）

使用方式：
```python
from .static_analyzer import StaticAnalyzer, AnalysisResult

# 初始化
analyzer = StaticAnalyzer(project_path="/path/to/project")

# 分析 Python 代码
results = await analyzer.analyze_python(files=["src/main.py"])

# 分析特定文件
results = await analyzer.analyze_file("src/utils.py")

# 自动修复
for result in results:
    if result.fix:
        await analyzer.auto_fix(result)
```
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
    """分析配置"""
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
        results: List[AnalysisResult] = []
        target = str(self.project_path) if not files else " ".join(files)
        
        if self.config.ruff_enabled and self._is_tool_available("ruff"):
            ruff_results = await self._run_ruff(target)
            results.extend(ruff_results)
        
        if self.config.mypy_enabled and self._is_tool_available("mypy"):
            mypy_results = await self._run_mypy(target)
            results.extend(mypy_results)
        
        if self.config.semgrep_enabled and self._is_tool_available("semgrep"):
            semgrep_results = await self._run_semgrep(target)
            results.extend(semgrep_results)
        
        results = self._dedupe_results(results)[:self.config.max_results]
        return results
    
    async def analyze_file(self, file_path: str) -> List[AnalysisResult]:
        if not Path(file_path).is_absolute():
            file_path = str(self.project_path / file_path)
        return await self.analyze_python(files=[file_path])
    
    async def _run_ruff(self, target: str) -> List[AnalysisResult]:
        cmd = ["ruff", "check", "--output-format=json"]
        if self.config.ruff_rules:
            cmd.extend(["--select", ",".join(self.config.ruff_rules)])
        if self.config.ruff_ignore:
            cmd.extend(["--ignore", ",".join(self.config.ruff_ignore)])
        cmd.append(target)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_path),
            )
            stdout, _ = await process.communicate()
            if stdout:
                try:
                    data = json.loads(stdout.decode("utf-8"))
                    return [AnalysisResult.from_ruff(item) for item in data]
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            logger.warning(f"Ruff 执行失败: {e}")
        return []
    
    async def _run_mypy(self, target: str) -> List[AnalysisResult]:
        cmd = ["mypy", "--output=json", "--no-error-summary"]
        if self.config.mypy_ignore_missing_imports:
            cmd.append("--ignore-missing-imports")
        if self.config.mypy_strict:
            cmd.append("--strict")
        cmd.append(target)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_path),
            )
            stdout, _ = await process.communicate()
            results = []
            if stdout:
                for line in stdout.decode("utf-8").strip().split("\n"):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if "message" in data:
                            results.append(AnalysisResult.from_mypy(
                                file_path=data.get("file", ""),
                                line=data.get("line", 0),
                                message=data.get("message", ""),
                            ))
                    except json.JSONDecodeError:
                        simple_match = re.match(r"(.+?):(\d+): (.+)", line)
                        if simple_match:
                            results.append(AnalysisResult.from_mypy(
                                file_path=simple_match.group(1),
                                line=int(simple_match.group(2)),
                                message=simple_match.group(3),
                            ))
            return results
        except Exception as e:
            logger.warning(f"MyPy 执行失败: {e}")
        return []
    
    async def _run_semgrep(self, target: str) -> List[AnalysisResult]:
        results = []
        patterns = {"security": "eval($X)", "best-practice": "open(...)"}
        for rule in self.config.semgrep_rules:
            cmd = ["semgrep", "--quiet", "--json", "--pattern", patterns.get(rule, ""), target]
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.project_path),
                )
                stdout, _ = await process.communicate()
                if stdout:
                    data = json.loads(stdout.decode("utf-8"))
                    for r in data.get("results", []):
                        results.append(AnalysisResult(
                            tool="semgrep",
                            file_path=r.get("path", ""),
                            line=r.get("start", {}).get("line", 0),
                            column=r.get("start", {}).get("col", 0),
                            code=r.get("check_id", ""),
                            message=r.get("extra", {}).get("message", ""),
                            severity="warning",
                        ))
            except Exception as e:
                logger.debug(f"Semgrep 规则 {rule} 执行失败: {e}")
        return results
    
    def _dedupe_results(self, results: List[AnalysisResult]) -> List[AnalysisResult]:
        seen = set()
        deduped = []
        for result in results:
            key = (result.file_path, result.line, result.column, result.code)
            if key not in seen:
                seen.add(key)
                deduped.append(result)
        return deduped
    
    async def auto_fix(self, result: AnalysisResult) -> bool:
        if not self.config.auto_fix:
            return False
        if result.tool == "ruff" and result.fix:
            return await self._ruff_fix(result.file_path)
        return False
    
    async def _ruff_fix(self, file_path: str) -> bool:
        cmd = ["ruff", "check", "--fix", file_path]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_path),
            )
            await process.communicate()
            return True
        except Exception:
            return False
    
    def get_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        if not results:
            return {"total": 0, "errors": 0, "warnings": 0, "infos": 0}
        errors = [r for r in results if r.severity == "error"]
        warnings = [r for r in results if r.severity == "warning"]
        return {
            "total": len(results),
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len([r for r in results if r.severity == "info"]),
            "fixable": len([r for r in results if r.fix]),
        }


ERROR_CODE_HINTS = {
    "E501": "行太长，建议拆分为多行或使用括号续行",
    "F401": "导入了但未使用，可以删除或用 _ 前缀",
    "F811": "名称重复定义",
    "W291": "行尾有多余空格",
    "W293": "行尾有空行",
    "E302": "需要两个空行分隔",
    "E231": "缺少空格",
    "I001": "导入顺序需要排序（运行 isort）",
    "UP007": "使用 | 代替 Optional[]",
    "UP006": "使用 list[] 代替 List[]",
}


__all__ = ["StaticAnalyzer", "AnalysisResult", "AnalysisConfig", "ERROR_CODE_HINTS"]
