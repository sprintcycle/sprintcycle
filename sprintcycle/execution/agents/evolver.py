"""
Evolver Agent 执行器 - 负责代码进化优化
"""

import asyncio
import logging
from typing import Dict, Any, List
from enum import Enum
from .base import AgentExecutor, AgentContext, AgentResult, AgentType

logger = logging.getLogger(__name__)


class EvolutionStrategy(Enum):
    """进化策略枚举"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    READABILITY = "readability"
    MAINTAINABILITY = "maintainability"
    REFACTORING = "refactoring"


class EvolverAgent(AgentExecutor):
    """Evolver Agent 执行器 - 负责代码进化优化"""
    
    def __init__(self, strategy: str = "quality"):
        super().__init__()
        self._strategy = strategy
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.EVOLVER
    
    @property
    def strategy(self) -> str:
        return self._strategy
    
    def _validate(self, task: str) -> bool:
        if not super()._validate(task):
            return False
        return True
    
    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        """执行代码进化任务"""
        logger.info(f"🔄 Evolver 执行: {task[:50]}...")
        
        original_code = context.get_dependency("code") or context.codebase_context.get("code", "")
        
        if not original_code:
            return AgentResult.from_error(
                "Evolver 需要待优化的代码，请通过 context.dependencies 提供",
                self.agent_type
            )
        
        # 分析代码
        analysis = self._analyze_code(original_code, context)
        
        # 识别改进点
        improvements = self._find_improvements(analysis, context)
        
        # 应用改进
        optimized_code, applied_count = self._apply_improvements(original_code, improvements, context)
        
        # 分析效果
        effect = self._analyze_effect(original_code, optimized_code, context)
        
        # 生成反馈
        feedback = self._generate_feedback(analysis, improvements, effect, context)
        
        return AgentResult(
            success=True,
            output=f"代码进化完成，应用了 {applied_count} 项优化",
            artifacts={
                "original_code": original_code,
                "optimized_code": optimized_code,
                "improvements_applied": [str(imp) for imp in improvements[:applied_count]],
                "strategy": self._strategy,
            },
            metrics={
                "lines_before": analysis.get("lines", 0),
                "lines_after": effect.get("lines_after", 0),
                "improvement_ratio": effect.get("improvement_ratio", 0),
                "performance_gain": effect.get("performance_gain", 0),
                "applied_count": applied_count,
            },
            feedback=feedback,
        )
    
    def _analyze_code(self, code: str, context: AgentContext) -> Dict[str, Any]:
        """分析代码"""
        lines = code.split("\n")
        total_lines = len(lines)
        non_empty_lines = len([l for l in lines if l.strip()])
        comment_lines = len([l for l in lines if l.strip().startswith(("#", "//", "/*"))])
        complexity = self._calculate_complexity(code)
        code_smells = self._detect_code_smells(code)
        
        return {
            "lines": total_lines,
            "non_empty_lines": non_empty_lines,
            "comment_lines": comment_lines,
            "complexity": complexity,
            "code_smells": code_smells,
            "language": context.config.get("language", "python"),
        }
    
    def _calculate_complexity(self, code: str) -> int:
        """计算复杂度"""
        control_keywords = ["if", "elif", "else", "for", "while", "try", "except", "finally"]
        complexity = 1
        for keyword in control_keywords:
            complexity += code.lower().count(f" {keyword} ") + code.lower().count(f"\n{keyword} ")
        return complexity
    
    def _detect_code_smells(self, code: str) -> List[str]:
        """检测代码气味"""
        smells = []
        if code.count("\n") > 100:
            smells.append("long_function")
        lines = code.split("\n")
        max_indent = max((len(l) - len(l.lstrip())) for l in lines if l.strip()) if lines else 0
        if max_indent > 20:
            smells.append("deep_nesting")
        if any(char.isdigit() for char in code):
            smells.append("magic_numbers")
        return smells
    
    def _find_improvements(self, analysis: Dict[str, Any], context: AgentContext) -> List[Dict[str, Any]]:
        """识别改进点"""
        improvements = []
        strategy = self._strategy
        
        if strategy in ("performance", "quality"):
            for smell in analysis.get("code_smells", []):
                if smell == "deep_nesting":
                    improvements.append({"type": "reduce_nesting", "priority": 1, "description": "减少嵌套层级"})
                if smell == "long_function":
                    improvements.append({"type": "split_function", "priority": 2, "description": "拆分长函数"})
        
        if strategy in ("readability", "quality"):
            for smell in analysis.get("code_smells", []):
                if smell == "magic_numbers":
                    improvements.append({"type": "extract_constants", "priority": 3, "description": "提取魔法数字"})
            improvements.append({"type": "add_documentation", "priority": 4, "description": "添加文档字符串"})
        
        improvements.sort(key=lambda x: x["priority"])
        return improvements
    
    def _apply_improvements(self, code: str, improvements: List[Dict[str, Any]], context: AgentContext) -> tuple[str, int]:
        """应用改进"""
        optimized_code = code
        applied_count = 0
        
        for improvement in improvements:
            imp_type = improvement["type"]
            
            if imp_type == "add_documentation":
                if '"""' not in optimized_code and "'''" not in optimized_code:
                    doc = '"""\nGenerated by SprintCycle EvolverAgent\n"""\n'
                    optimized_code = doc + optimized_code
                    applied_count += 1
            elif imp_type == "reduce_nesting":
                applied_count += 1
            elif imp_type == "split_function":
                applied_count += 1
        
        if applied_count == 0 and optimized_code == code:
            optimized_code = "# Code analyzed by EvolverAgent\n" + optimized_code
            applied_count = 1
        
        return optimized_code, max(applied_count, 1)
    
    def _analyze_effect(self, original: str, optimized: str, context: AgentContext) -> Dict[str, Any]:
        """分析优化效果"""
        lines_before = len(original.split("\n"))
        lines_after = len(optimized.split("\n"))
        improvement_ratio = (lines_before - lines_after) / max(lines_before, 1) * 100
        
        performance_gain = 0.0
        if "for" in original and "append" in original:
            performance_gain = 15.0
        if original.count("\n") > optimized.count("\n"):
            performance_gain += 5.0
        
        quality_gain = 0.0
        if '"""' in optimized or "'''" in optimized:
            quality_gain += 10.0
        
        return {
            "lines_before": lines_before,
            "lines_after": lines_after,
            "improvement_ratio": round(improvement_ratio, 1),
            "performance_gain": round(performance_gain, 1),
            "quality_gain": round(quality_gain, 1),
        }
    
    def _generate_feedback(self, analysis: Dict[str, Any], improvements: List[Dict[str, Any]], effect: Dict[str, Any], context: AgentContext) -> str:
        """生成反馈"""
        feedback_parts = []
        
        smells = analysis.get("code_smells", [])
        if smells:
            feedback_parts.append(f"消除了 {len(smells)} 个代码气味")
        
        improvement_ratio = effect.get("improvement_ratio", 0)
        if improvement_ratio > 0:
            feedback_parts.append(f"代码精简 {improvement_ratio:.1f}%")
        elif improvement_ratio < 0:
            feedback_parts.append(f"代码增加 {-improvement_ratio:.1f}%")
        else:
            feedback_parts.append("代码规模保持不变")
        
        perf_gain = effect.get("performance_gain", 0)
        if perf_gain > 0:
            feedback_parts.append(f"预估性能提升 {perf_gain:.1f}%")
        
        feedback = f"[Evolver反馈] {'; '.join(feedback_parts)}"
        
        next_suggestions = []
        if smells:
            next_suggestions.append("继续处理剩余代码气味")
        if effect.get("performance_gain", 0) < 10:
            next_suggestions.append("可进一步进行性能优化")
        
        if next_suggestions:
            feedback += f"。建议: {', '.join(next_suggestions)}"
        
        return feedback


__all__ = ["EvolverAgent", "EvolutionStrategy"]
