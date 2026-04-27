#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SprintCycle 问题扫描器"""
import os, ast, json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class IssueSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class IssueType(Enum):
    MISSING_FILE = "missing_file"
    MISSING_DEPENDENCY = "missing_dependency"
    SYNTAX_ERROR = "syntax_error"
    CONFIG_ERROR = "config_error"
    UNUSED_IMPORT = "unused_import"

@dataclass
class Issue:
    issue_type: IssueType
    severity: IssueSeverity
    file_path: str
    line: Optional[int] = None
    message: str = ""
    details: Dict = field(default_factory=dict)
    fix_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": self.issue_type.value,
            "severity": self.severity.value,
            "file": self.file_path,
            "line": self.line,
            "message": self.message,
            "details": self.details,
            "fix_suggestion": self.fix_suggestion
        }

@dataclass
class ScanResult:
    project_path: str
    issues: List[Issue] = field(default_factory=list)
    scanned_files: int = 0
    scan_duration: float = 0.0
    
    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
    
    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)
    
    def to_dict(self) -> Dict:
        return {
            "project_path": self.project_path,
            "issues": [i.to_dict() for i in self.issues],
            "scanned_files": self.scanned_files,
            "scan_duration": self.scan_duration,
            "summary": {
                "critical": self.critical_count,
                "warning": self.warning_count,
                "info": self.info_count,
                "total": len(self.issues)
            }
        }

class ProjectScanner:
    COMMON_FILES = [".env", ".env.example", "__init__.py", "requirements.txt", "pyproject.toml", "README.md", ".gitignore", "setup.py"]
    
    PYTHON_BUILTINS = {"os", "sys", "json", "yaml", "time", "datetime", "pathlib", "collections", "functools", "itertools", "re", "math", "random", "hashlib", "base64", "urllib", "http", "threading", "multiprocessing", "asyncio", "concurrent", "pickle", "shelve", "sqlite3", "csv", "io", "warnings", "logging", "traceback", "gc", "weakref", "abc", "copy", "types", "typing", "enum"}
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.issues: List[Issue] = []
        
    def scan(self) -> ScanResult:
        import time
        start_time = time.time()
        self._scan_missing_files()
        self._scan_python_files()
        self._scan_dependencies()
        self._scan_config_files()
        self._scan_gitignore()
        duration = time.time() - start_time
        return ScanResult(project_path=str(self.project_path), issues=self.issues, scanned_files=len(list(self.project_path.rglob("*.py"))), scan_duration=duration)
    
    def _scan_missing_files(self):
        for filename in self.COMMON_FILES:
            filepath = self.project_path / filename
            if not filepath.exists():
                severity = IssueSeverity.WARNING
                if filename in [".env", "requirements.txt"]:
                    severity = IssueSeverity.CRITICAL
                self.issues.append(Issue(issue_type=IssueType.MISSING_FILE, severity=severity, file_path=str(filepath.relative_to(self.project_path)), message=f"Missing file: {filename}", fix_suggestion=self._get_suggestion(filename)))
    
    def _scan_python_files(self):
        for pyfile in self.project_path.rglob("*.py"):
            if any(part.startswith(".") or "venv" in part for part in pyfile.parts):
                continue
            self._check_python_file(pyfile)
    
    def _check_python_file(self, filepath: Path):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            try:
                ast.parse(content)
            except SyntaxError as e:
                self.issues.append(Issue(issue_type=IssueType.SYNTAX_ERROR, severity=IssueSeverity.CRITICAL, file_path=str(filepath.relative_to(self.project_path)), line=e.lineno, message=f"Syntax error: {e.msg}"))
                return
            tree = ast.parse(content)
            self._analyze_ast(filepath, tree)
        except UnicodeDecodeError:
            self.issues.append(Issue(issue_type=IssueType.SYNTAX_ERROR, severity=IssueSeverity.WARNING, file_path=str(filepath.relative_to(self.project_path)), message="File encoding is not UTF-8"))
    
    def _analyze_ast(self, filepath: Path, tree: ast.AST):
        imports, used_names = [], set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split(".")[0])
            if isinstance(node, ast.Name):
                used_names.add(node.id)
        for imp in imports:
            if imp not in self.PYTHON_BUILTINS and imp not in used_names:
                self.issues.append(Issue(issue_type=IssueType.UNUSED_IMPORT, severity=IssueSeverity.INFO, file_path=str(filepath.relative_to(self.project_path)), message=f"Possibly unused import: {imp}"))
    
    def _scan_dependencies(self):
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, "r") as f:
                    deps = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                if not deps:
                    self.issues.append(Issue(issue_type=IssueType.MISSING_DEPENDENCY, severity=IssueSeverity.WARNING, file_path="requirements.txt", message="requirements.txt is empty"))
            except Exception as e:
                self.issues.append(Issue(issue_type=IssueType.CONFIG_ERROR, severity=IssueSeverity.CRITICAL, file_path="requirements.txt", message=str(e)))
    
    def _scan_config_files(self):
        for name in ["config.yaml", "pyproject.toml"]:
            filepath = self.project_path / name
            if filepath.exists():
                self._validate_config_file(filepath)
    
    def _validate_config_file(self, filepath: Path):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if filepath.suffix == ".yaml":
                import yaml
                yaml.safe_load(content)
            elif filepath.suffix == ".json" or filepath.name == "package.json":
                json.loads(content)
        except Exception as e:
            self.issues.append(Issue(issue_type=IssueType.CONFIG_ERROR, severity=IssueSeverity.CRITICAL, file_path=str(filepath.name), message=str(e)[:80]))
    
    def _scan_gitignore(self):
        if not (self.project_path / ".gitignore").exists():
            self.issues.append(Issue(issue_type=IssueType.MISSING_FILE, severity=IssueSeverity.INFO, file_path=".gitignore", message="Missing .gitignore", fix_suggestion="Create .gitignore"))
    
    def _get_suggestion(self, filename: str) -> str:
        d = {
            ".env": "# Environment variables",
            ".env.example": "# Environment example",
            "requirements.txt": "# Dependencies",
            "pyproject.toml": "[project]",
            "README.md": "# Project Name",
            ".gitignore": "__pycache__/",
            "setup.py": "from setuptools import setup",
            "__init__.py": "# Package init"
        }
        return d.get(filename, "# Create file")

def quick_scan(project_path: str) -> ScanResult:
    return ProjectScanner(project_path).scan()
