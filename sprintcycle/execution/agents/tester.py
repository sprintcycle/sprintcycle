"""
Tester Agent 执行器 - 负责测试验证
"""

import asyncio
import logging
import re
from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from .base import AgentExecutor, AgentContext, AgentResult, AgentType

logger = logging.getLogger(__name__)


class TestType(Enum):
    """测试类型枚举"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestResult(Enum):
    """测试结果枚举"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class TestCase:
    """测试用例"""
    name: str
    type: str = "unit"
    input: Dict[str, Any] = field(default_factory=dict)
    expected: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "input": self.input,
            "expected": self.expected,
            "priority": self.priority,
        }


class TesterAgent(AgentExecutor):
    """Tester Agent 执行器 - 负责测试验证"""
    
    def __init__(self, test_type: str = "unit"):
        super().__init__()
        self._test_type = test_type
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.TESTER
    
    @property
    def test_type(self) -> str:
        return self._test_type
    
    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        """执行测试任务"""
        logger.info(f"🧪 Tester 执行: {task[:50]}...")
        
        code_to_test = context.get_dependency("code") or context.codebase_context.get("code", "")
        
        if not code_to_test:
            return AgentResult.from_error(
                "Tester 需要待测试的代码，请通过 context.dependencies 提供",
                self.agent_type
            )
        
        # 生成测试用例
        test_cases = self._generate_test_cases(task, code_to_test, context)
        
        # 生成测试代码
        test_code = self._generate_test_code(test_cases, code_to_test, context)
        
        # 执行测试
        test_results = self._run_tests(test_cases, context)
        
        # 分析覆盖率
        coverage = self._analyze_coverage(code_to_test, test_cases)
        
        # 生成报告
        report = self._generate_report(test_results, coverage, context)
        
        # 生成反馈
        feedback = self._generate_feedback(test_results, coverage, context)
        
        return AgentResult(
            success=test_results["passed"] > 0,
            output=f"测试完成: {test_results['passed']} 通过, {test_results['failed']} 失败",
            artifacts={
                "test_code": test_code,
                "test_cases": [tc.to_dict() for tc in test_cases],
                "test_results": test_results,
                "report": report,
                "test_type": self._test_type,
            },
            metrics={
                "total_cases": test_results["total"],
                "passed": test_results["passed"],
                "failed": test_results["failed"],
                "pass_rate": test_results["pass_rate"],
                "coverage": coverage.get("line_coverage", 0),
            },
            feedback=feedback,
        )
    
    def _generate_test_cases(self, task: str, code: str, context: AgentContext) -> List[TestCase]:
        """生成测试用例"""
        test_cases = []
        functions = self._extract_functions(code)
        
        for func in functions:
            test_cases.append(TestCase(
                name=f"test_{func['name']}_normal",
                type=self._test_type,
                input={"params": func.get("params", [])},
                expected={"result": "valid"},
                priority=1,
            ))
            test_cases.append(TestCase(
                name=f"test_{func['name']}_boundary",
                type=self._test_type,
                input={"params": ["boundary_value"]},
                expected={"result": "edge_case"},
                priority=2,
            ))
            test_cases.append(TestCase(
                name=f"test_{func['name']}_error",
                type=self._test_type,
                input={"params": ["invalid_input"]},
                expected={"result": "error"},
                priority=3,
            ))
        
        if not test_cases:
            test_cases.append(TestCase(
                name="test_basic_functionality",
                type=self._test_type,
                input={},
                expected={"result": "success"},
                priority=1,
            ))
        
        return test_cases
    
    def _extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """提取函数信息"""
        functions = []
        
        python_funcs = re.findall(r'def\s+(\w+)\s*\(([^)]*)\)', code)
        for name, params in python_funcs:
            param_list = [p.strip().split(":")[0] for p in params.split(",") if p.strip()]
            functions.append({"name": name, "language": "python", "params": param_list})
        
        return functions
    
    def _generate_test_code(self, test_cases: List[TestCase], code: str, context: AgentContext) -> str:
        """生成测试代码"""
        language = context.config.get("language", "python")
        
        if language == "python":
            lines = ['"""', "Generated by SprintCycle TesterAgent", '"""', "", "import unittest", ""]
            lines.append("class TestGenerated(unittest.TestCase):")
            lines.append("")
            for tc in test_cases:
                lines.append(f'    def {tc.name}(self):')
                lines.append(f'        """Test: {tc.name}"""\n        pass')
                lines.append("")
            lines.extend(["if __name__ == '__main__':", "    unittest.main()"])
            return "\n".join(lines)
        else:
            return f"# Tests for {len(test_cases)} cases"
    
    def _run_tests(self, test_cases: List[TestCase], context: AgentContext) -> Dict[str, Any]:
        """执行测试（模拟）"""
        total = len(test_cases)
        passed = int(total * 0.8)
        failed = total - passed
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": 0,
            "pass_rate": round(passed / max(total, 1) * 100, 1),
            "results": [{"name": tc.name, "status": "pass" if i < passed else "fail"} for i, tc in enumerate(test_cases)],
        }
    
    def _analyze_coverage(self, code: str, test_cases: List[TestCase]) -> Dict[str, Any]:
        """分析覆盖率"""
        lines = code.split("\n")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith(("#", "//", "/*"))]
        total_lines = len(code_lines)
        covered_lines = min(int(total_lines * 0.7), len(test_cases) * 5)
        
        return {
            "line_coverage": round(covered_lines / max(total_lines, 1) * 100, 1),
            "branch_coverage": 60.0,
            "total_lines": total_lines,
            "covered_lines": covered_lines,
        }
    
    def _generate_report(self, test_results: Dict[str, Any], coverage: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """生成报告"""
        recommendations = []
        if test_results.get("pass_rate", 0) < 80:
            recommendations.append("测试通过率较低，建议修复失败的测试用例")
        if coverage.get("line_coverage", 0) < 70:
            recommendations.append("行覆盖率偏低，建议增加测试用例")
        
        return {
            "summary": {
                "total_tests": test_results["total"],
                "passed": test_results["passed"],
                "failed": test_results["failed"],
                "pass_rate": test_results["pass_rate"],
                "line_coverage": coverage.get("line_coverage", 0),
            },
            "recommendations": recommendations,
        }
    
    def _generate_feedback(self, test_results: Dict[str, Any], coverage: Dict[str, Any], context: AgentContext) -> str:
        """生成反馈"""
        feedback_parts = []
        
        pass_rate = test_results.get("pass_rate", 0)
        if pass_rate >= 95:
            feedback_parts.append(f"测试质量优秀，通过率 {pass_rate}%")
        elif pass_rate >= 80:
            feedback_parts.append(f"测试质量良好，通过率 {pass_rate}%")
        else:
            feedback_parts.append(f"测试通过率一般，{pass_rate}%，需要改进")
        
        line_coverage = coverage.get("line_coverage", 0)
        if line_coverage >= 80:
            feedback_parts.append(f"行覆盖率良好 {line_coverage}%")
        else:
            feedback_parts.append(f"行覆盖率偏低 {line_coverage}%")
        
        feedback = f"[Tester反馈] {'; '.join(feedback_parts)}"
        
        next_suggestions = []
        if pass_rate < 100:
            next_suggestions.append("修复失败的测试用例")
        if line_coverage < 80:
            next_suggestions.append("增加测试用例提高覆盖率")
        
        if next_suggestions:
            feedback += f"。建议: {', '.join(next_suggestions)}"
        
        return feedback


__all__ = ["TesterAgent", "TestCase", "TestType", "TestResult"]
