"""
Coder Agent Base - 核心执行逻辑
"""

import hashlib
from typing import Any, Dict, Optional, cast

from loguru import logger

from sprintcycle.prompt_sources import format_coder_generation_prompt
from sprintcycle.run_workspace import build_workspace_prompt_section

from .base import AgentContext, AgentExecutor, AgentResult, AgentType
from .coder_types import BatchConfig


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
        arch_design = context.get_dependency("architecture_design") or context.codebase_context.get("architecture_design")
        if arch_design:
            requirements["architecture_design"] = arch_design
        return requirements

    def _build_generation_prompt(self, requirements: Dict[str, Any], context: AgentContext) -> str:
        task = requirements.get("task", "")
        arch = requirements.get("architecture_design")
        cb = context.codebase_context or {}
        refs = cb.get("reference_project_paths") or []
        eff = str(cb.get("effective_write_policy") or "").strip().lower()
        if not eff:
            rp = cb.get("release_plan")
            meta = getattr(rp, "metadata", None) or {} if rp is not None else {}
            eff = str(meta.get("effective_write_policy") or "").strip().lower()
        ws = build_workspace_prompt_section(
            refs if isinstance(refs, list) else [],
            eff or "incremental",
        )
        return format_coder_generation_prompt(
            language=str(requirements.get("language", "python")),
            task=str(task),
            architecture_design=str(arch) if arch else None,
            workspace_section=ws,
        )

    def _resolve_coding_engine(self, context: AgentContext) -> str:
        return (
            (context.metadata or {}).get("coding_engine")
            or context.codebase_context.get("coding_engine")
            or "cursor"
        ).strip().lower()

    def _project_cwd(self, context: AgentContext) -> str:
        return str(context.codebase_context.get("project_path") or ".")

    def _coder_gen_cache_key(self, engine: str, prompt: str) -> str:
        raw = f"v1|{engine}|{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _maybe_get_codegen_cache(self, context: AgentContext, cache_key: str) -> Optional[Dict[str, Any]]:
        if not context.config.get("cache_llm_codegen", True):
            return None
        from ..cache import get_cache

        v = get_cache().get(cache_key)
        if isinstance(v, dict) and v.get("success"):
            return cast(Dict[str, Any], v)
        return None

    def _maybe_put_codegen_cache(self, context: AgentContext, cache_key: str, result: Dict[str, Any]) -> None:
        if not context.config.get("cache_llm_codegen", True):
            return
        if not result.get("success"):
            return
        from ..cache import get_cache

        get_cache().set(cache_key, result, ttl_hours=24)

    async def _generate_code(self, requirements: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        engine = self._resolve_coding_engine(context)
        if engine not in ("cursor", "claude", "trae"):
            return {"success": False, "error": f"unsupported coding engine: {engine}"}

        cache_prompt = self._build_generation_prompt(requirements, context)
        gen_ck = self._coder_gen_cache_key(engine, cache_prompt)
        cached = self._maybe_get_codegen_cache(context, gen_ck)
        if cached is not None:
            return cached

        def _finish_ok(payload: Dict[str, Any]) -> Dict[str, Any]:
            self._maybe_put_codegen_cache(context, gen_ck, payload)
            return payload

        from ..engine_adapters import EngineAdapterConfig, resolve_engine_adapter

        adapter = resolve_engine_adapter(
            engine,
            EngineAdapterConfig(
                timeout_seconds=int(context.config.get("engine_timeout_seconds", 900)),
                cwd=self._project_cwd(context),
                max_output_chars=int(context.config.get("engine_max_output_chars", 20000)),
            ),
        )
        try:
            res = await adapter.execute(
                cache_prompt,
                {
                    "project_path": self._project_cwd(context),
                    "sprint_name": context.sprint_name,
                    "release_plan_id": context.release_plan_id,
                    "codebase_context": context.codebase_context,
                    "architecture_design": requirements.get("architecture_design"),
                    "quality_level": context.metadata.get("quality_level") if context.metadata else None,
                },
            )
            if res.success:
                code = res.output or ""
                quality = self._calculate_quality_score(code, context)
                return _finish_ok(
                    {
                        "success": True,
                        "code": code,
                        "quality": quality,
                        "feedback": f"Generated via {adapter.__class__.__name__}",
                        "engine": adapter.name,
                        "engine_metadata": res.metadata or {},
                        "request_id": res.request_id,
                        "trace_id": res.trace_id,
                    }
                )
            logger.warning("{} 执行失败: {}", adapter.name, res.error)
            return {
                "success": False,
                "error": res.error or f"{adapter.name} failed",
                "error_code": res.error_code,
                "engine_metadata": res.metadata or {},
                "request_id": res.request_id,
                "trace_id": res.trace_id,
            }
        except Exception as e:
            logger.error("Code generation failed: {}", e)
            return {"success": False, "error": str(e), "error_code": "adapter_exception", "request_id": "", "trace_id": ""}

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
        key = f"{task}:{context.release_plan_id}:{context.sprint_index}"
        return hashlib.md5(key.encode()).hexdigest()
