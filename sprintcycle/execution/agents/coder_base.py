"""
Coder Agent Base - 核心执行逻辑
"""

import hashlib
import logging
import os
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

    def _build_generation_prompt(self, requirements: Dict[str, Any], context: AgentContext) -> str:
        task = requirements.get("task", "")
        arch_section = ""
        if requirements.get("architecture_design"):
            arch_section = f"""

架构设计指导：
{requirements["architecture_design"]}
"""
        return f"""请为以下任务生成高质量的 {requirements.get('language', 'python')} 代码：

任务：{task}{arch_section}

要求：
1. 代码应遵循最佳实践
2. 包含必要的错误处理
3. 添加清晰的注释
4. 保持代码简洁和可读性
5. 如有架构设计指导，请严格遵循
"""

    def _resolve_coding_engine(self, context: AgentContext) -> str:
        return (
            (context.metadata or {}).get("coding_engine")
            or context.codebase_context.get("coding_engine")
            or os.environ.get("SPRINTCYCLE_CODING_ENGINE", "aider")
            or "aider"
        ).strip().lower()

    def _project_cwd(self, context: AgentContext) -> str:
        return str(context.codebase_context.get("project_path") or ".")

    async def _generate_code(self, requirements: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        from ..llm_provider import resolve_provider, call_llm_async

        task = requirements.get("task", "")
        engine = self._resolve_coding_engine(context)
        # 与 sprintcycle.config / 文档中的别名对齐
        if engine in ("claude", "claude-code"):
            engine = "claude_code"
        if engine in ("cursor", "cursor-cookbook"):
            engine = "cursor_cookbook"

        if engine == "aider":
            from ..engines.aider import check_aider_cli, run_aider_message

            if check_aider_cli():
                cwd = self._project_cwd(context)
                prompt = self._build_generation_prompt(requirements, context)
                cfg = resolve_provider()
                rc, out, err = await run_aider_message(
                    prompt, cwd=cwd, timeout=600, model=cfg.model if cfg.model else None
                )
                if rc == 0:
                    combined = (out or "") + ("\n" + err if err else "")
                    quality = self._calculate_quality_score(combined, context)
                    return {
                        "success": True,
                        "code": combined or "(aider 完成，无 stdout)",
                        "quality": quality,
                        "feedback": "Generated via Aider CLI",
                    }
                logger.warning("Aider 退出码 %s，回退 LiteLLM: %s", rc, err[:500] if err else "")
            else:
                logger.warning("未检测到 aider 命令，回退 LiteLLM 直调")

        if engine == "claude_code":
            from ..engines.claude_code import check_claude_code_cli, run_claude_print_message

            if check_claude_code_cli():
                cwd = self._project_cwd(context)
                prompt = self._build_generation_prompt(requirements, context)
                rc, out, err = await run_claude_print_message(prompt, cwd=cwd, timeout=600)
                if rc == 0:
                    combined = (out or "") + ("\n" + err if err else "")
                    quality = self._calculate_quality_score(combined, context)
                    return {
                        "success": True,
                        "code": combined or "(Claude Code 完成，无 stdout)",
                        "quality": quality,
                        "feedback": "Generated via Claude Code CLI (-p)",
                    }
                logger.warning("Claude Code 退出码 %s，回退 LiteLLM: %s", rc, err[:500] if err else "")
            else:
                logger.warning("未检测到 claude 命令（Claude Code），回退 LiteLLM 直调")

        if engine == "cursor_cookbook":
            from ..engines.cursor_cookbook import run_cursor_cookbook_flow

            cwd = self._project_cwd(context)
            prompt = self._build_generation_prompt(requirements, context)
            cb = context.codebase_context or {}
            overlay = str(cb.get("prd_overlay") or "")[:8000]
            arch = str(
                (requirements.get("architecture_design") or cb.get("architecture_design") or "")
            )[:8000]
            title = f"SprintCycle — {context.sprint_name or 'coder'}"
            rc, out, err = await run_cursor_cookbook_flow(
                cwd=cwd,
                title=title,
                task_prompt=prompt,
                prd_overlay_hint=overlay,
                architecture_hint=arch,
                timeout=600,
            )
            if rc == 0:
                combined = (out or "") + ("\n" + err if err else "")
                quality = self._calculate_quality_score(combined, context)
                return {
                    "success": True,
                    "code": combined or "(Cursor Cookbook 已生成)",
                    "quality": quality,
                    "feedback": "Cursor Cookbook file (+ optional agent CLI)",
                }
            logger.warning("Cursor Cookbook / Agent 退出码 %s，回退 LiteLLM: %s", rc, err[:500] if err else "")

        config = resolve_provider()
        
        prompt = self._build_generation_prompt(requirements, context)
        messages = [{"role": "user", "content": prompt}]
        
        try:
            code = await call_llm_async(
                model=config.model,
                messages=messages,
                api_key=config.api_key,
                api_base=config.api_base,
                temperature=0.7,
                max_tokens=4096,
            )
            quality = self._calculate_quality_score(code, context)
            return {
                "success": True,
                "code": code,
                "quality": quality,
                "feedback": f"Generated {requirements.get('language', 'python')} code"
            }
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
