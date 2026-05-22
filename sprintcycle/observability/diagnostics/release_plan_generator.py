"""
诊断驱动的 ``ReleasePlan`` 生成。

- 规则优先层：P0/P1 问题由 ``ReleasePlanRuleEngine`` 直接生成计划草案
- LLM 综合层：复杂场景由 ``LLMReleasePlanGenerator`` 推理补全
"""

import json
import re
from typing import List, Optional

from loguru import logger

from ...application.release_plan.builders import release_plan_from_diagnostic_slices
from sprintcycle.domain.models import ReleasePlan
from .health_report import ProjectHealthReport
from .release_plan_rules import ReleasePlanRuleEngine


class LLMReleasePlanGenerator:
    """调用 LLM 生成复杂场景下的 ``ReleasePlan`` 草案。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        from sprintcycle.infrastructure.llm_provider import resolve_provider

        cfg = resolve_provider(provider=provider, api_key=api_key, api_base=api_base, model=model)
        self._api_key = cfg.api_key
        self._model = cfg.model
        self._api_base = cfg.api_base

    def generate(self, report: ProjectHealthReport, project_path: str) -> List[ReleasePlan]:
        from sprintcycle.infrastructure.llm_provider import call_llm

        if not self._api_key:
            logger.warning("LLM_API_KEY未设置，跳过LLM生成")
            return []
        try:
            content = call_llm(
                model=self._model,
                messages=[
                    {"role": "system", "content": "你是一个专业的代码重构专家。"},
                    {"role": "user", "content": self._build_prompt(report, project_path)},
                ],
                api_key=self._api_key,
                api_base=self._api_base,
                temperature=0.3,
                max_tokens=2048,
            )
            return self._parse_llm_response(content, project_path)
        except Exception as e:
            logger.warning(f"LLM生成失败: {e}")
            return []

    def _build_prompt(self, report: ProjectHealthReport, project_path: str) -> str:
        return f"""基于以下项目健康报告，生成改进建议的**多 Sprint 执行计划**（JSON，结构与 ReleasePlan 兼容：project.name、project.path、sprints[].name、goals、tasks[].description 等）。

项目: {report.target}
健康评分: {report.health_score:.1f}

当前状态:
- 覆盖率: {report.coverage_total:.1f}%
- 测试失败: {report.test_failures}
- 类型错误: {report.mypy_errors}
- 高复杂度函数: {report.complexity_high}
- 循环依赖: {len(report.circular_deps)}

有效改动模式: {", ".join(report.effective_patterns)}
失败改动模式: {", ".join(report.failed_patterns)}

请生成结构化 JSON，包含:
1. 具体的改进目标
2. 可执行的 sprint 规划
3. 预期收益评估

仅输出 JSON（对象或对象数组），不要 Markdown 围栏。"""

    def _parse_llm_response(self, content: str, project_path: str) -> List[ReleasePlan]:
        json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", content)
        if not json_match:
            return []
        try:
            data = json.loads(json_match.group())
            if isinstance(data, dict):
                data = [data]
            plans: List[ReleasePlan] = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                name = item.get("name", "LLM生成执行计划")
                sprints_raw = item.get("sprints", [])
                sprint_dicts = [sp for sp in sprints_raw if isinstance(sp, dict)]
                if not sprint_dicts:
                    continue
                plans.append(
                    release_plan_from_diagnostic_slices(
                        plan_name=str(name),
                        project_path=project_path,
                        sprint_dicts=sprint_dicts,
                        rule="llm",
                        confidence=0.7,
                        expected_benefit=float(item.get("expected_benefit", 5.0)),
                        priority=int(item.get("priority", 50)),
                        extra_metadata={"generator": "llm"},
                    )
                )
            return plans
        except json.JSONDecodeError as e:
            logger.warning(f"LLM响应JSON解析失败: {e}")
            return []


class DiagnosticReleasePlanGenerator:
    """组合 ``ReleasePlanRuleEngine`` 与可选 ``LLMReleasePlanGenerator`` 的计划生成器。"""

    def __init__(
        self,
        rule_engine: Optional[ReleasePlanRuleEngine] = None,
        llm_generator: Optional[LLMReleasePlanGenerator] = None,
    ):
        self._rule_engine = rule_engine or ReleasePlanRuleEngine()
        self._llm_generator = llm_generator

    def generate(self, report: ProjectHealthReport, project_path: str) -> List[ReleasePlan]:
        rule_plans = self._rule_engine.evaluate(report)
        llm_plans: List[ReleasePlan] = []
        if report.health_score < 60 and self._llm_generator:
            llm_plans = self._llm_generator.generate(report, project_path)
        seen: set[str] = set()
        unique_plans: List[ReleasePlan] = []
        for plan in rule_plans + llm_plans:
            key = plan.project.name
            if key not in seen:
                seen.add(key)
                unique_plans.append(plan)
        unique_plans.sort(
            key=lambda p: int(p.metadata.get("diagnostic_priority", 0)),
            reverse=True,
        )
        logger.info(f"生成执行计划: 规则{len(rule_plans)}个, LLM{len(llm_plans)}个, 去重后{len(unique_plans)}个")
        return unique_plans


__all__ = [
    "LLMReleasePlanGenerator",
    "DiagnosticReleasePlanGenerator",
    "ReleasePlanRuleEngine",
]
