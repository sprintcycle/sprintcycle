"""
DiagnosticPRDGenerator - PRD生成器

基于诊断报告生成结构化PRD:
- 规则优先层: P0问题直接生成PRD
- LLM综合层: 复杂问题需要LLM推理
"""

import logging
from typing import List, Dict, Any, Optional

from .health_report import ProjectHealthReport, Severity
from ..evolution.prd_source import EvolutionPRD, PRDSourceType
from .prd_rules import PRDRulePriority, PRDRule, PRDRuleEngine

logger = logging.getLogger(__name__)


class LLMPRDGenerator:
    """LLM PRD生成器，调用DeepSeek API生成复杂PRD"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, api_base: Optional[str] = None, provider: Optional[str] = None):
        from sprintcycle.llm_provider import resolve_provider
        cfg = resolve_provider(provider=provider, api_key=api_key, api_base=api_base, model=model)
        self._api_key = cfg.api_key
        self._model = cfg.model
        self._api_base = cfg.api_base
    
    def generate(self, report: ProjectHealthReport, project_path: str) -> List[EvolutionPRD]:
        from sprintcycle.llm_provider import call_llm
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
                api_key=self._api_key, api_base=self._api_base, temperature=0.3, max_tokens=2048,
            )
            return self._parse_llm_response(content, project_path)
        except Exception as e:
            logger.warning(f"LLM生成失败: {e}")
            return []
    
    def _build_prompt(self, report: ProjectHealthReport, project_path: str) -> str:
        return f"""基于以下项目健康报告，生成改进建议的PRD:

项目: {report.target}
健康评分: {report.health_score:.1f}

当前状态:
- 覆盖率: {report.coverage_total:.1f}%
- 测试失败: {report.test_failures}
- 类型错误: {report.mypy_errors}
- 高复杂度函数: {report.complexity_high}
- 循环依赖: {len(report.circular_deps)}

有效改动模式: {', '.join(report.effective_patterns)}
失败改动模式: {', '.join(report.failed_patterns)}

请生成一个结构化的PRD，包含:
1. 具体的改进目标
2. 可执行的sprint规划
3. 预期收益评估

以JSON格式输出PRD。"""
    
    def _parse_llm_response(self, content: str, project_path: str) -> List[EvolutionPRD]:
        import json, re
        json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", content)
        if not json_match:
            return []
        try:
            data = json.loads(json_match.group())
            if isinstance(data, dict):
                data = [data]
            prds = []
            for item in data:
                prds.append(EvolutionPRD(
                    name=item.get("name", "LLM生成PRD"), version="v1.0.0", path=project_path,
                    goals=item.get("goals", []), sprints=item.get("sprints", []),
                    source_type=PRDSourceType.DIAGNOSTIC, metadata={"generator": "llm"},
                    confidence=0.7, expected_benefit=item.get("expected_benefit", 5.0),
                    priority=item.get("priority", 50),
                ))
            return prds
        except json.JSONDecodeError as e:
            logger.warning(f"LLM响应JSON解析失败: {e}")
            return []


class DiagnosticPRDGenerator:
    """PRD生成器，组合规则引擎和LLM生成器"""
    
    def __init__(self, rule_engine: Optional[PRDRuleEngine] = None, llm_generator: Optional[LLMPRDGenerator] = None):
        self._rule_engine = rule_engine or PRDRuleEngine()
        self._llm_generator = llm_generator
    
    def generate(self, report: ProjectHealthReport, project_path: str) -> List[EvolutionPRD]:
        # 1. 规则引擎生成P0/P1 PRD
        rule_prds = self._rule_engine.evaluate(report)
        # 2. LLM补充（仅在健康评分较低时）
        llm_prds = []
        if report.health_score < 60 and self._llm_generator:
            llm_prds = self._llm_generator.generate(report, project_path)
        # 3. 合并去重
        seen, unique_prds = set(), []
        for prd in rule_prds + llm_prds:
            if prd.name not in seen:
                seen.add(prd.name)
                unique_prds.append(prd)
        # 4. 按优先级排序
        unique_prds.sort(key=lambda x: x.priority, reverse=True)
        logger.info(f"生成PRD: 规则{len(rule_prds)}个, LLM{len(llm_prds)}个, 去重后{len(unique_prds)}个")
        return unique_prds
