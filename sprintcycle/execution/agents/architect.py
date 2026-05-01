"""
ArchitectureAgent - 负责架构设计步骤

在 Sprint 内部执行循环中，ArchitectureAgent 在 CoderAgent 之前执行，
分析需求、评估现有架构、设计解决方案，并将架构设计文档注入 context
供后续 CoderAgent 读取。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base import AgentExecutor, AgentContext, AgentResult, AgentType

logger = logging.getLogger(__name__)


class ArchitectureAgent(AgentExecutor):
    """Architecture Agent 执行器 - 负责架构设计"""

    def __init__(self, config=None):
        super().__init__(config)

    @property
    def agent_type(self) -> AgentType:
        return AgentType.ARCHITECT

    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        """执行架构设计任务"""
        logger.info(f"🏗️ Architect 执行: {task[:50]}...")

        # 1. 分析需求
        requirements = self._analyze_requirements(task, context)
        # 2. 评估现有架构
        current_state = self._evaluate_current_architecture(context)
        # 3. 设计解决方案
        design = self._design_solution(requirements, current_state)
        # 4. 生成架构文档
        arch_doc = self._generate_architecture_document(design)

        # 将架构设计注入 context，供 CoderAgent 读取
        context.dependencies["architecture_design"] = arch_doc
        context.codebase_context["architecture_design"] = arch_doc

        return AgentResult(
            success=True,
            output=arch_doc,
            artifacts={
                "requirements": requirements,
                "current_state": current_state,
                "design": design,
            },
            feedback=f"架构设计完成: {design.get('summary', '')}",
            agent_type=self.agent_type,
        )

    def _analyze_requirements(
        self, task: str, context: AgentContext
    ) -> Dict[str, Any]:
        """分析需求和约束"""
        requirements: Dict[str, Any] = {
            "task": task,
            "project_goals": context.project_goals,
            "constraints": context.metadata.get("constraints", []),
            "existing_modules": list(context.codebase_context.keys()),
        }

        # 如果有前序 Sprint 的反馈，纳入需求分析
        if context.feedback_history:
            requirements["feedback_items"] = context.feedback_history[-5:]

        # 如果有改进建议，纳入需求
        improvement = context.get_dependency("improvement_suggestions")
        if improvement:
            requirements["improvement_suggestions"] = improvement

        return requirements

    def _evaluate_current_architecture(
        self, context: AgentContext
    ) -> Dict[str, Any]:
        """评估现有架构状态"""
        current_state: Dict[str, Any] = {
            "existing_code": context.codebase_context.get("code", ""),
            "module_structure": context.codebase_context.get("modules", {}),
            "tech_stack": context.codebase_context.get("tech_stack", "python"),
            "known_issues": context.codebase_context.get("issues", []),
        }

        # 检查是否有已有的架构设计（增量设计场景）
        existing_design = context.get_dependency("architecture_design")
        if existing_design:
            current_state["existing_design"] = existing_design

        return current_state

    def _design_solution(
        self,
        requirements: Dict[str, Any],
        current_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """设计解决方案"""
        design: Dict[str, Any] = {
            "summary": f"为 '{requirements.get('task', '')[:50]}' 设计架构方案",
            "components": [],
            "dependencies": [],
            "patterns": [],
            "decisions": [],
        }

        task = requirements.get("task", "").lower()

        # 根据任务类型推荐架构模式
        if any(kw in task for kw in ["重构", "refactor", "迁移", "migrate"]):
            design["patterns"].append("strangler_fig")
            design["decisions"].append("采用渐进式重构策略")
        elif any(kw in task for kw in ["新增", "添加", "add", "implement"]):
            design["patterns"].append("module_extension")
            design["decisions"].append("在现有模块基础上扩展")
        elif any(kw in task for kw in ["优化", "optimize", "进化", "evolve"]):
            design["patterns"].append("iterative_optimization")
            design["decisions"].append("采用迭代优化策略，保留回滚能力")
        else:
            design["patterns"].append("standard")
            design["decisions"].append("遵循项目现有架构规范")

        # 考虑已有问题
        known_issues = current_state.get("known_issues", [])
        if known_issues:
            design["decisions"].append(
                f"注意已有 {len(known_issues)} 个已知问题需规避"
            )

        return design

    def _generate_architecture_document(self, design: Dict[str, Any]) -> str:
        """生成架构设计文档"""
        lines = [
            f"# 架构设计: {design.get('summary', '')}",
            "",
            "## 推荐模式",
        ]
        for pattern in design.get("patterns", []):
            lines.append(f"- {pattern}")

        lines.append("")
        lines.append("## 设计决策")
        for decision in design.get("decisions", []):
            lines.append(f"- {decision}")

        components = design.get("components", [])
        if components:
            lines.append("")
            lines.append("## 组件")
            for comp in components:
                lines.append(f"- {comp}")

        return "\n".join(lines)
