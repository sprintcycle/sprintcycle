"""
Coder Agent Base - 核心执行逻辑
"""

import hashlib
import logging
from typing import Any, Dict, Optional

from .base import AgentExecutor, AgentContext, AgentResult, AgentType
from .coder_types import BatchConfig

logger = logging.getLogger(__name__)


class CoderAgent(AgentExecutor):
    """Coder Agent 执行器"""

    def __init__(self, config=None, batch_config: Optional[BatchConfig] = None):
        super().__init__(config)
        self._batch_config = batch_config or BatchConfig()
        self._cache: Dict[str, AgentResult] = {}
        self._cache_enabled = False

    @property
    def agent_type(self) -> AgentType:
        return AgentType.CODER

    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        requirements = self._parse_requirements(task, context)
        result = await self._generate_code(requirements, context)
        
        if result["success"]:
            return AgentResult(
                success=True,
                output=result["code"],
                artifacts={"requirements": requirements, "quality": result.get("quality", {})},
                feedback=result.get("feedback", ""),
                agent_type=self.agent_type,
            )
        else:
            return AgentResult(success=False, error=result.get("error", "Unknown error"), agent_type=self.agent_type)

    def _parse_requirements(self, task: str, context: AgentContext) -> Dict[str, Any]:
        requirements = {"language": "python", "task": task, "context": context.codebase_context}
        if "typescript" in task.lower() or "ts" in task.lower():
            requirements["language"] = "typescript"
        elif "javascript" in task.lower() or "js" in task.lower():
            requirements["language"] = "javascript"
        elif "rust" in task.lower():
            requirements["language"] = "rust"
        # 读取 ArchitectureAgent 产出的架构设计
        arch_design = context.get_dependency("architecture_design") or context.codebase_context.get("architecture_design")
        if arch_design:
            requirements["architecture_design"] = arch_design
        return requirements

    async def _generate_code(self, requirements: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        task = requirements.get("task", "")
        import aiohttp
        from ..llm_provider import resolve_provider
        
        config = resolve_provider()
        arch_section = ""
        if requirements.get("architecture_design"):
            arch_section = f"""

架构设计指导：
{requirements["architecture_design"]}
"""
        prompt = f"""请为以下任务生成高质量的 {requirements.get('language', 'python')} 代码：

任务：{task}{arch_section}

要求：
1. 代码应遵循最佳实践
2. 包含必要的错误处理
3. 添加清晰的注释
4. 保持代码简洁和可读性
5. 如有架构设计指导，请严格遵循
"""
        messages = [{"role": "user", "content": prompt}]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{config.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"},
                    json={"model": config.model, "messages": messages, "temperature": 0.7},
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        code = data["choices"][0]["message"]["content"]
                        quality = self._calculate_quality_score(code, context)
                        return {"success": True, "code": code, "quality": quality, "feedback": f"Generated {requirements.get('language', 'python')} code"}
                    else:
                        return {"success": False, "error": data.get('error', {}).get('message', 'API error')}
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_quality_score(self, code: str, context: AgentContext) -> float:
        score = 0.5
        if "def " in code or "class " in code:
            score += 0.1
        if "try:" in code or "except" in code:
            score += 0.1
        if ": str" in code or ": int" in code or "-> " in code:
            score += 0.1
        if '"""' in code or "'''" in code:
            score += 0.1
        if "# " in code:
            score += 0.1
        return min(score, 1.0)

    def enable_cache(self, cache: Dict[str, AgentResult]) -> None:
        self._cache = cache
        self._cache_enabled = True

    def disable_cache(self) -> None:
        self._cache_enabled = False

    def _get_task_hash(self, task: str, context: AgentContext) -> str:
        import hashlib
        key = f"{task}:{context.prd_id}:{context.sprint_index}"
        return hashlib.md5(key.encode()).hexdigest()
