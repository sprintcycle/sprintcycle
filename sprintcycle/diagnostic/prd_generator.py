"""
DiagnosticPRDGenerator - PRD生成器

基于诊断报告生成结构化PRD:
- 规则优先层: P0问题直接生成PRD
- LLM综合层: 复杂问题需要LLM推理
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from .health_report import ProjectHealthReport, Severity
from ..evolution.prd_source import EvolutionPRD, PRDSourceType

logger = logging.getLogger(__name__)


from .prd_rules import PRDRulePriority, PRDRule, PRDRuleEngine



class LLMPRDGenerator:
    """
    LLM PRD生成器
    
    调用DeepSeek API生成复杂PRD
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, api_base: Optional[str] = None, provider: Optional[str] = None):
        """
        初始化LLM生成器
        
        Args:
            api_key: API密钥（从环境变量或参数获取）
            model: 模型名称
            api_base: API基础URL（默认从环境变量LLM_API_BASE读取）
            provider: 提供者名称 (deepseek/openai/anthropic)
        """
        from sprintcycle.llm_provider import resolve_provider
        cfg = resolve_provider(provider=provider, api_key=api_key, api_base=api_base, model=model)
        self._api_key = cfg.api_key
        self._model = cfg.model
        self._api_base = cfg.api_base
        self._url = cfg.chat_endpoint
    
    def generate(
        self, report: ProjectHealthReport, project_path: str
    ) -> List[EvolutionPRD]:
        """
        使用LLM生成PRD
        
        Args:
            report: 健康报告
            project_path: 项目路径
            
        Returns:
            EvolutionPRD列表
        """
        if not self._api_key:
            logger.warning("LLM_API_KEY未设置，跳过LLM生成")
            return []
        
        # 构建prompt
        prompt = self._build_prompt(report, project_path)
        
        try:
            # 调用API
            import requests
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的代码重构专家。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            }
            
            response = requests.post(self._url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return self._parse_llm_response(content, project_path)
            else:
                logger.warning(f"LLM API调用失败: status={response.status_code}, body={response.text[:200]}")
                return []
                
        except Exception as e:
            logger.warning(f"LLM生成失败: {e}")
            return []
    
    def _build_prompt(
        self, report: ProjectHealthReport, project_path: str
    ) -> str:
        """构建LLM prompt"""
        return f"""
基于以下项目健康报告，生成改进建议的PRD:

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

以JSON格式输出PRD。
"""
    
    def _parse_llm_response(
        self, content: str, project_path: str
    ) -> List[EvolutionPRD]:
        """解析LLM响应"""
        import json
        import re
        
        # 提取JSON
        json_match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", content)
        if not json_match:
            return []
        
        try:
            data = json.loads(json_match.group())
            
            # 转换为EvolutionPRD
            if isinstance(data, dict):
                data = [data]
            
            prds = []
            for item in data:
                prd = EvolutionPRD(
                    name=item.get("name", "LLM生成PRD"),
                    version="v1.0.0",
                    path=project_path,
                    goals=item.get("goals", []),
                    sprints=item.get("sprints", []),
                    source_type=PRDSourceType.DIAGNOSTIC,
                    metadata={"generator": "llm"},
                    confidence=0.7,
                    expected_benefit=item.get("expected_benefit", 5.0),
                    priority=item.get("priority", 50),
                )
                prds.append(prd)
            
            return prds
            
        except json.JSONDecodeError as e:
            logger.warning(f"LLM响应JSON解析失败: {e}")
            return []


class DiagnosticPRDGenerator:
    """
    PRD生成器
    
    组合规则引擎和LLM生成器:
    1. 规则优先 - P0问题直接生成
    2. LLM综合 - 复杂问题需要推理
    """
    
    def __init__(
        self,
        rule_engine: Optional[PRDRuleEngine] = None,
        llm_generator: Optional[LLMPRDGenerator] = None,
    ):
        """
        初始化PRD生成器
        
        Args:
            rule_engine: 规则引擎
            llm_generator: LLM生成器
        """
        self._rule_engine = rule_engine or PRDRuleEngine()
        self._llm_generator = llm_generator
    
    def generate(
        self, report: ProjectHealthReport, project_path: str
    ) -> List[EvolutionPRD]:
        """
        生成PRD列表
        
        策略:
        1. 先用规则引擎生成P0/P1 PRD
        2. 如果健康评分<60，调用LLM补充
        3. 去重和排序
        
        Args:
            report: 健康报告
            project_path: 项目路径
            
        Returns:
            EvolutionPRD列表
        """
        # 1. 规则引擎生成
        rule_prds = self._rule_engine.evaluate(report)
        
        # 2. LLM补充（仅在健康评分较低时）
        llm_prds = []
        if report.health_score < 60 and self._llm_generator:
            llm_prds = self._llm_generator.generate(report, project_path)
        
        # 3. 合并
        all_prds = rule_prds + llm_prds
        
        # 4. 去重（基于名称）
        seen = set()
        unique_prds = []
        for prd in all_prds:
            if prd.name not in seen:
                seen.add(prd.name)
                unique_prds.append(prd)
        
        # 5. 按优先级排序
        unique_prds.sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"生成PRD: 规则{len(rule_prds)}个, LLM{len(llm_prds)}个, 去重后{len(unique_prds)}个")
        return unique_prds
