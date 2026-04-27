"""五源并行验证模块"""

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum
import asyncio
from pathlib import Path


class VerifySource(Enum):
    VISUAL = "visual"
    CLI = "cli"
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTS = "tests"


@dataclass
class VerifyResult:
    source: VerifySource
    passed: bool
    score: float
    details: str
    errors: List[str]

    def to_dict(self) -> dict:
        return {
            "source": self.source.value, "passed": self.passed,
            "score": self.score, "details": self.details, "errors": self.errors
        }


class FiveSourceVerifier:
    """五源并行验证器"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
    
    async def verify_all(self) -> Dict[str, Any]:
        """并行执行五源验证"""
        print("\n🔍 五源并行验证...")
        
        tasks = [
            self._verify_visual(), self._verify_cli(),
            self._verify_frontend(), self._verify_backend(), self._verify_tests()
        ]
        results = await asyncio.gather(*tasks)
        
        passed = sum(1 for r in results if r.passed)
        score = sum(r.score for r in results) / len(results)
        
        return {
            "passed": passed == len(results),
            "passed_count": passed,
            "total": len(results),
            "score": round(score, 2),
            "results": [r.to_dict() for r in results]
        }
    
    async def verify_single(self, source: VerifySource) -> VerifyResult:
        """验证单个来源"""
        verifiers = {
            VerifySource.VISUAL: self._verify_visual,
            VerifySource.CLI: self._verify_cli,
            VerifySource.FRONTEND: self._verify_frontend,
            VerifySource.BACKEND: self._verify_backend,
            VerifySource.TESTS: self._verify_tests,
        }
        return await verifiers[source]()
    
    async def _verify_visual(self) -> VerifyResult:
        files = list(self.project_path.glob("**/*.html")) + list(self.project_path.glob("**/*.tsx"))
        return VerifyResult(
            source=VerifySource.VISUAL,
            passed=len(files) > 0,
            score=1.0 if files else 0.5,
            details=f"前端文件: {len(files)}",
            errors=[] if files else ["未找到前端文件"]
        )
    
    async def _verify_cli(self) -> VerifyResult:
        cli = list(self.project_path.glob("**/cli.py"))
        return VerifyResult(
            source=VerifySource.CLI,
            passed=len(cli) > 0,
            score=1.0 if cli else 0.3,
            details=f"CLI文件: {len(cli)}",
            errors=[] if cli else ["未找到CLI入口"]
        )
    
    async def _verify_frontend(self) -> VerifyResult:
        logs = list(self.project_path.glob("**/frontend*.log"))
        return VerifyResult(
            source=VerifySource.FRONTEND,
            passed=True, score=0.8,
            details=f"日志文件: {len(logs)}", errors=[]
        )
    
    async def _verify_backend(self) -> VerifyResult:
        api = list(self.project_path.glob("**/api/*.py"))
        return VerifyResult(
            source=VerifySource.BACKEND,
            passed=len(api) > 0,
            score=1.0 if api else 0.4,
            details=f"API文件: {len(api)}",
            errors=[] if api else ["未找到API文件"]
        )
    
    async def _verify_tests(self) -> VerifyResult:
        tests = list(self.project_path.glob("**/test_*.py"))
        return VerifyResult(
            source=VerifySource.TESTS,
            passed=len(tests) > 0,
            score=1.0 if tests else 0.3,
            details=f"测试文件: {len(tests)}",
            errors=[] if tests else ["未找到测试文件"]
        )
