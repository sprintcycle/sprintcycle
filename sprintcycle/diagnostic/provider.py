"""
ProjectDiagnostic - 项目诊断提供者
"""

import logging
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from .health_report import ProjectHealthReport, CodeIssue, Severity

logger = logging.getLogger(__name__)


class ProjectDiagnostic:
    def __init__(
        self,
        project_path: str = ".",
        test_command: str = "python -m pytest tests/ -v --tb=short",
        coverage_command: str = "python -m pytest --cov --cov-report=json",
        complexity_threshold: int = 10,
        timeout: int = 300,
        runtime_config=None,
        runner: Optional[Callable[..., Tuple[int, str, str]]] = None,
    ):
        # 支持从 RuntimeConfig 构造
        if runtime_config is not None:
            self.project_path = getattr(runtime_config, 'repo_path', '.')
            self.test_command = getattr(runtime_config, 'test_command', test_command)
            self.coverage_command = getattr(runtime_config, 'coverage_command', coverage_command)
            self.complexity_threshold = getattr(runtime_config, 'complexity_threshold', complexity_threshold)
            self.timeout = getattr(runtime_config, 'diagnostic_timeout', timeout)
        else:
            self.project_path = project_path
            self.test_command = test_command
            self.coverage_command = coverage_command
            self.complexity_threshold = complexity_threshold
            self.timeout = timeout
        self._runner = runner or self._default_runner
    
    def _default_runner(self, cmd: str, cwd: str = ".", timeout: int = 300) -> Tuple[int, str, str]:
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def run_tests(self) -> Dict[str, Any]:
        rc, stdout, stderr = self._runner(self.test_command, cwd=self.project_path, timeout=self.timeout)
        
        passed = 0
        failed = 0
        errors = 0
        
        if "passed" in stdout:
            match = re.search(r'(\d+) passed', stdout)
            if match:
                passed = int(match.group(1))
        
        if "failed" in stdout:
            match = re.search(r'(\d+) failed', stdout)
            if match:
                failed = int(match.group(1))
        
        return {"returncode": rc, "passed": passed, "failed": failed, "errors": errors, "stdout": stdout, "stderr": stderr}
    
    def check_coverage(self) -> Dict[str, Any]:
        rc, stdout, stderr = self._runner(self.coverage_command, cwd=self.project_path, timeout=self.timeout)
        
        coverage = 0.0
        if "TOTAL" in stdout:
            match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', stdout)
            if match:
                coverage = float(match.group(1))
        
        return {"coverage": coverage, "returncode": rc}
    
    def check_complexity(self) -> List[Dict[str, Any]]:
        issues = []
        try:
            result = subprocess.run(
                ["python", "-m", "mypy", self.project_path, "--no-error-summary"],
                capture_output=True, text=True, timeout=60,
            )
            for line in result.stdout.split("\n"):
                if ":" in line and "error" in line.lower():
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        issues.append({"file": parts[0], "line": parts[1] if len(parts) > 1 else "0", "message": parts[2] if len(parts) > 2 else ""})
        except Exception as e:
            logger.warning(f"Complexity check failed: {e}")
        
        return issues
    
    def diagnose(self) -> ProjectHealthReport:
        report = ProjectHealthReport()
        report.target = self.project_path
        
        test_results = self.run_tests()
        total_tests = test_results["passed"] + test_results["failed"]
        report.test_failures = test_results["failed"]
        report.mypy_errors = len(self.check_complexity())
        
        coverage_results = self.check_coverage()
        report.coverage_total = coverage_results["coverage"]
        
        complexity_issues = self.check_complexity()
        for issue in complexity_issues[:10]:
            code_issue = CodeIssue(
                file=issue["file"],
                line=int(issue["line"]) if issue["line"].isdigit() else 0,
                severity=Severity.MEDIUM,
                message=issue["message"],
            )
            report.code_issues.append(code_issue)
        
        return report
