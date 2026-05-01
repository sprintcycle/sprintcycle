"""
RegressionTestAgent - 负责回归测试步骤

在 Sprint 内部执行循环中，RegressionTestAgent 在 TesterAgent 之后执行，
确保代码修改没有破坏已有功能。比对修改前后的测试结果，识别回归问题。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base import AgentExecutor, AgentContext, AgentResult, AgentType

logger = logging.getLogger(__name__)


class RegressionTestAgent(AgentExecutor):
    """RegressionTest Agent 执行器 - 负责回归测试"""

    def __init__(self, config=None):
        super().__init__(config)

    @property
    def agent_type(self) -> AgentType:
        return AgentType.REGRESSION_TESTER

    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        """执行回归测试任务"""
        logger.info(f"🔄 RegressionTester 执行: {task[:50]}...")

        # 1. 获取基准测试结果（修改前的快照）
        baseline = self._get_baseline_results(context)
        # 2. 运行当前测试套件
        current = self._run_regression_tests(context)
        # 3. 比对结果
        diff = self._compare_results(baseline, current)
        # 4. 生成回归报告
        report = self._generate_regression_report(diff)

        has_regression = any(d["status"] == "REGRESSION" for d in diff)

        return AgentResult(
            success=not has_regression,
            output=report,
            artifacts={
                "baseline": baseline,
                "current": current,
                "diff": diff,
            },
            feedback=report if has_regression else "回归测试通过，无退化",
            agent_type=self.agent_type,
        )

    def _get_baseline_results(self, context: AgentContext) -> Dict[str, Any]:
        """获取基准测试结果（修改前的快照）"""
        baseline = context.get_dependency("baseline_test_results")
        if baseline:
            return baseline

        # 没有基准快照时，从 codebase_context 获取
        return context.codebase_context.get(
            "baseline_test_results",
            {"tests": [], "pass_count": 0, "fail_count": 0},
        )

    def _run_regression_tests(self, context: AgentContext) -> Dict[str, Any]:
        """运行回归测试套件"""
        # 获取 TesterAgent 的结果作为当前测试状态
        test_result = context.get_dependency("test_results")
        if test_result:
            return test_result

        return {
            "tests": [],
            "pass_count": 0,
            "fail_count": 0,
            "source": "regression_scan",
        }

    def _compare_results(
        self,
        baseline: Dict[str, Any],
        current: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """比对基准与当前测试结果，识别回归"""
        diff: List[Dict[str, Any]] = []

        baseline_tests = {
            t.get("name", f"test_{i}"): t
            for i, t in enumerate(baseline.get("tests", []))
        }
        current_tests = {
            t.get("name", f"test_{i}"): t
            for i, t in enumerate(current.get("tests", []))
        }

        # 检查已有测试是否从 pass 变 fail
        for name, baseline_test in baseline_tests.items():
            if name in current_tests:
                current_test = current_tests[name]
                was_pass = baseline_test.get("status") == "pass"
                now_pass = current_test.get("status") == "pass"

                if was_pass and not now_pass:
                    diff.append({
                        "name": name,
                        "status": "REGRESSION",
                        "detail": f"测试 '{name}' 从 pass 变为 {current_test.get('status', 'unknown')}",
                    })
                elif not was_pass and now_pass:
                    diff.append({
                        "name": name,
                        "status": "FIXED",
                        "detail": f"测试 '{name}' 从 fail 变为 pass",
                    })

        # 检查是否有测试被删除
        for name in baseline_tests:
            if name not in current_tests:
                diff.append({
                    "name": name,
                    "status": "REMOVED",
                    "detail": f"测试 '{name}' 在当前版本中缺失",
                })

        # 检查新增测试
        for name in current_tests:
            if name not in baseline_tests:
                diff.append({
                    "name": name,
                    "status": "NEW",
                    "detail": f"新增测试 '{name}'",
                })

        return diff

    def _generate_regression_report(self, diff: List[Dict[str, Any]]) -> str:
        """生成回归测试报告"""
        if not diff:
            return "✅ 回归测试通过：无退化、无变更"

        regressions = [d for d in diff if d["status"] == "REGRESSION"]
        fixed = [d for d in diff if d["status"] == "FIXED"]
        removed = [d for d in diff if d["status"] == "REMOVED"]
        new = [d for d in diff if d["status"] == "NEW"]

        lines = ["# 回归测试报告", ""]

        if regressions:
            lines.append(f"## ❌ 回归 ({len(regressions)})")
            for r in regressions:
                lines.append(f"- {r['detail']}")
            lines.append("")

        if fixed:
            lines.append(f"## ✅ 修复 ({len(fixed)})")
            for f in fixed:
                lines.append(f"- {f['detail']}")
            lines.append("")

        if removed:
            lines.append(f"## ⚠️ 移除 ({len(removed)})")
            for r in removed:
                lines.append(f"- {r['detail']}")
            lines.append("")

        if new:
            lines.append(f"## 🆕 新增 ({len(new)})")
            for n in new:
                lines.append(f"- {n['detail']}")

        return "\n".join(lines)
