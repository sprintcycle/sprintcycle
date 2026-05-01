"""
PRD Rule Engine - PRD 规则引擎

规则优先层：基于诊断报告的规则匹配和 PRD 生成。
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from .health_report import ProjectHealthReport, Severity
from ..evolution.prd_source import EvolutionPRD, PRDSourceType

logger = logging.getLogger(__name__)


class PRDRulePriority(Enum):
    """PRD规则优先级"""
    P0_CRITICAL = 0  # 必须修复
    P1_HIGH = 1  # 强烈建议
    P2_MEDIUM = 2  # 建议
    P3_LOW = 3  # 可选


@dataclass
class PRDRule:
    """
    PRD生成规则
    
    定义一个诊断规则和对应的PRD生成逻辑
    """
    name: str
    priority: PRDRulePriority
    check: Any  # 检查函数
    generate: Any  # PRD生成函数
    threshold: float = 0.0  # 触发阈值


class PRDRuleEngine:
    """
    预定义5条核心规则:
    1. TestFailure: 测试失败规则
    2. TypeError: 类型错误规则
    3. Coverage: 覆盖率规则
    4. Complexity: 复杂度规则
    5. CircularDep: 循环依赖规则
    """
    
    def __init__(self):
        self._rules: List[PRDRule] = [
            # 规则1: 测试失败
            PRDRule(
                name="test_failure",
                priority=PRDRulePriority.P0_CRITICAL,
                check=lambda r: r.test_failures > 0,
                generate=lambda r, p: self._gen_fix_tests_prd(r, p),
                threshold=0,
            ),
            # 规则2: 类型错误
            PRDRule(
                name="type_error",
                priority=PRDRulePriority.P0_CRITICAL,
                check=lambda r: r.mypy_errors > 0,
                generate=lambda r, p: self._gen_fix_types_prd(r, p),
                threshold=0,
            ),
            # 规则3: 覆盖率不足
            PRDRule(
                name="low_coverage",
                priority=PRDRulePriority.P1_HIGH,
                check=lambda r: r.coverage_total < 70,
                generate=lambda r, p: self._gen_coverage_prd(r, p),
                threshold=70,
            ),
            # 规则4: 高复杂度
            PRDRule(
                name="high_complexity",
                priority=PRDRulePriority.P2_MEDIUM,
                check=lambda r: r.complexity_high > 5,
                generate=lambda r, p: self._gen_refactor_prd(r, p),
                threshold=5,
            ),
            # 规则5: 循环依赖
            PRDRule(
                name="circular_dependency",
                priority=PRDRulePriority.P1_HIGH,
                check=lambda r: len(r.circular_deps) > 0,
                generate=lambda r, p: self._gen_fix_circular_prd(r, p),
                threshold=0,
            ),
        ]
    
    def evaluate(self, report: ProjectHealthReport) -> List[EvolutionPRD]:
        """
        评估报告并生成PRD
        
        Args:
            report: 健康报告
            
        Returns:
            EvolutionPRD列表
        """
        prds = []
        
        for rule in self._rules:
            try:
                if rule.check(report):
                    prd = rule.generate(report, report.target)
                    if prd:
                        prds.append(prd)
            except Exception as e:
                logger.warning(f"规则 {rule.name} 执行失败: {e}", exc_info=True)
        
        return prds
    
    def _gen_fix_tests_prd(
        self, report: ProjectHealthReport, project_path: str
    ) -> EvolutionPRD:
        """生成修复测试的PRD"""
        return EvolutionPRD(
            name="修复测试失败",
            version="v1.0.0",
            path=project_path,
            goals=[f"修复当前 {report.test_failures} 个测试失败"],
            sprints=[{
                "name": "Sprint 1: 修复测试",
                "goals": ["分析测试失败原因", "修复失败的测试"],
                "tasks": [
                    {
                        "task": "运行测试分析失败原因",
                        "agent": "tester",
                        "constraints": ["不要修改测试预期结果"],
                    },
                    {
                        "task": "根据分析结果修复代码",
                        "agent": "coder",
                        "constraints": ["确保修复后测试通过"],
                    },
                ],
            }],
            source_type=PRDSourceType.DIAGNOSTIC,
            metadata={"rule": "test_failure", "failures": report.test_failures},
            confidence=0.95,
            expected_benefit=10.0,
            priority=90,
        )
    
    def _gen_fix_types_prd(
        self, report: ProjectHealthReport, project_path: str
    ) -> EvolutionPRD:
        """生成修复类型错误的PRD"""
        return EvolutionPRD(
            name="修复类型错误",
            version="v1.0.0",
            path=project_path,
            goals=[f"修复当前 {report.mypy_errors} 个类型错误"],
            sprints=[{
                "name": "Sprint 1: 修复类型",
                "goals": ["运行mypy分析类型错误", "添加类型注解"],
                "tasks": [
                    {
                        "task": "分析mypy错误输出",
                        "agent": "coder",
                        "constraints": ["优先修复关键类型错误"],
                    },
                    {
                        "task": "添加缺失的类型注解",
                        "agent": "coder",
                        "constraints": ["使用 type 注释慎重"],
                    },
                ],
            }],
            source_type=PRDSourceType.DIAGNOSTIC,
            metadata={"rule": "type_error", "errors": report.mypy_errors},
            confidence=0.90,
            expected_benefit=8.0,
            priority=85,
        )
    
    def _gen_coverage_prd(
        self, report: ProjectHealthReport, project_path: str
    ) -> EvolutionPRD:
        """生成提升覆盖率的PRD"""
        target_coverage = max(report.coverage_total + 15, 80)
        
        # 找出覆盖率最低的模块
        low_modules = [
            (m, c) for m, c in report.coverage_modules.items()
            if c < 50
        ]
        low_modules.sort(key=lambda x: x[1])
        
        tasks = [
            {
                "task": f"为模块添加单元测试，目标覆盖率: {target_coverage}%",
                "agent": "tester",
                "constraints": ["测试必须有实际断言"],
            },
        ]
        
        if low_modules:
            tasks.append({
                "task": f"优先提升 {low_modules[0][0]} 模块覆盖率（当前: {low_modules[0][1]:.1f}%）",
                "agent": "tester",
                "constraints": ["从核心功能开始"],
            })
        
        return EvolutionPRD(
            name="提升测试覆盖率",
            version="v1.0.0",
            path=project_path,
            goals=[
                f"当前覆盖率: {report.coverage_total:.1f}%",
                f"目标覆盖率: {target_coverage}%",
            ],
            sprints=[{
                "name": "Sprint 1: 提升覆盖率",
                "goals": ["识别低覆盖模块", "添加测试用例"],
                "tasks": tasks,
            }],
            source_type=PRDSourceType.DIAGNOSTIC,
            metadata={
                "rule": "low_coverage",
                "current": report.coverage_total,
                "target": target_coverage,
            },
            confidence=0.85,
            expected_benefit=15.0,
            priority=70,
        )
    
    def _gen_refactor_prd(
        self, report: ProjectHealthReport, project_path: str
    ) -> EvolutionPRD:
        """生成重构高复杂度代码的PRD"""
        return EvolutionPRD(
            name="重构高复杂度函数",
            version="v1.0.0",
            path=project_path,
            goals=[f"降低当前 {report.complexity_high} 个高复杂度函数"],
            sprints=[{
                "name": "Sprint 1: 降低复杂度",
                "goals": ["识别高复杂度函数", "重构为小函数"],
                "tasks": [
                    {
                        "task": "分析并识别需要重构的高复杂度函数",
                        "agent": "coder",
                        "constraints": ["优先重构被频繁调用的函数"],
                    },
                    {
                        "task": "重构高复杂度函数，拆分大函数",
                        "agent": "coder",
                        "constraints": ["保持原有功能不变"],
                    },
                ],
            }],
            source_type=PRDSourceType.DIAGNOSTIC,
            metadata={
                "rule": "high_complexity",
                "count": report.complexity_high,
            },
            confidence=0.75,
            expected_benefit=5.0,
            priority=50,
        )
    
    def _gen_fix_circular_prd(
        self, report: ProjectHealthReport, project_path: str
    ) -> EvolutionPRD:
        """生成修复循环依赖的PRD"""
        return EvolutionPRD(
            name="消除循环依赖",
            version="v1.0.0",
            path=project_path,
            goals=[f"消除当前 {len(report.circular_deps)} 个循环依赖"],
            sprints=[{
                "name": "Sprint 1: 消除循环依赖",
                "goals": ["识别循环依赖关系", "通过接口抽象消除"],
                "tasks": [
                    {
                        "task": f"分析循环依赖: {', '.join(report.circular_deps[:3])}",
                        "agent": "coder",
                        "constraints": ["使用依赖注入解耦"],
                    },
                ],
            }],
            source_type=PRDSourceType.DIAGNOSTIC,
            metadata={
                "rule": "circular_dependency",
                "deps": report.circular_deps,
            },
            confidence=0.80,
            expected_benefit=7.0,
            priority=75,
        )


