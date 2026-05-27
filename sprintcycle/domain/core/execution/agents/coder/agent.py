"""Coder Agent 核心执行逻辑。

分层设计：LLM 引擎和缓存由 Infrastructure 层实现，通过工厂函数注入 Domain 层。
"""

from dataclasses import dataclass
import hashlib
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Protocol, cast

from loguru import logger

from sprintcycle.domain.generic.prompts.prompt_sources import format_coder_generation_prompt

from sprintcycle.domain.core.execution.project_write import ProjectWritePlan
from ..base import AgentContext, AgentExecutor, AgentResult, AgentType
from .types import BatchConfig

if TYPE_CHECKING:
    from sprintcycle.domain.ports.cache import CacheBackendProtocol as CacheBackend


# 引擎适配器协议（DDD Port）
class EngineAdapterProtocol(Protocol):
    """LLM 引擎适配器协议"""

    name: str

    async def execute(self, prompt: str, context: Dict[str, Any]) -> "EngineResult": ...


@dataclass
class EngineResult:
    """引擎执行结果"""

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    request_id: str = ""
    trace_id: str = ""


@dataclass
class EngineAdapterConfig:
    """引擎适配器配置"""

    timeout_seconds: int = 900
    cwd: str = "."
    max_output_chars: int = 20000


# 工厂函数注册（由 Infrastructure 层实现并注册）
_cache_backend_factory: Optional[Callable[[], "CacheBackend"]] = None
_engine_adapter_factory: Optional[Callable[[str, EngineAdapterConfig], EngineAdapterProtocol]] = None


def register_cache_backend_factory(factory: Callable[[], "CacheBackend"]) -> None:
    """注册缓存后端工厂（由 Infrastructure 层调用）"""
    global _cache_backend_factory
    _cache_backend_factory = factory


def register_engine_adapter_factory(factory: Callable[[str, EngineAdapterConfig], EngineAdapterProtocol]) -> None:
    """注册引擎适配器工厂（由 Infrastructure 层调用）"""
    global _engine_adapter_factory
    _engine_adapter_factory = factory


def _get_cache_backend() -> Optional["CacheBackend"]:
    """获取缓存后端（延迟导入避免循环依赖）"""
    global _cache_backend_factory
    if _cache_backend_factory is not None:
        return _cache_backend_factory()
    from sprintcycle.domain.ports.cache import get_cache_backend
    return get_cache_backend()


def _resolve_engine_adapter(
    engine: str,
    config: EngineAdapterConfig,
) -> EngineAdapterProtocol:
    """解析引擎适配器（延迟导入避免循环依赖）"""
    global _engine_adapter_factory
    if _engine_adapter_factory is not None:
        return _engine_adapter_factory(engine, config)
    from sprintcycle.domain.ports.llm import resolve_engine_adapter as _resolve

    return _resolve(
        engine,
        EngineAdapterConfig(
            timeout_seconds=config.timeout_seconds,
            cwd=config.cwd,
            max_output_chars=config.max_output_chars,
        ),
    )


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
        arch_design = context.get_dependency("architecture_design") or context.codebase_context.get(
            "architecture_design"
        )
        if arch_design:
            requirements["architecture_design"] = arch_design
        return requirements

    def _resolve_write_policy(self, context: AgentContext) -> str:
        wp = (
            (context.metadata or {}).get("write_policy")
            or context.codebase_context.get("write_policy")
            or "incremental"
        )
        return str(wp).strip().lower()

    def _resolve_project_write_plan(self, context: AgentContext) -> Optional[ProjectWritePlan]:
        plan = context.metadata.get("project_write_plan") if context.metadata else None
        if isinstance(plan, ProjectWritePlan):
            return plan
        plan = context.codebase_context.get("project_write_plan")
        if isinstance(plan, ProjectWritePlan):
            return plan
        return self.get_project_write_plan()

    def _build_generation_prompt(self, requirements: Dict[str, Any], context: AgentContext) -> str:
        from sprintcycle.domain.core.execution.core.run_workspace import build_workspace_prompt_section

        task = requirements.get("task", "")
        arch = requirements.get("architecture_design")
        cb = context.codebase_context or {}
        refs = cb.get("reference_project_paths") or []
        wp = self._resolve_write_policy(context)
        ws = build_workspace_prompt_section(refs if isinstance(refs, list) else [], wp)
        plan = self._resolve_project_write_plan(context)
        plan_section = ""
        if plan is not None:
            references = []
            for ref in plan.references:
                if ref.exists:
                    references.append(
                        f"- {ref.path} | entry_points={','.join(ref.entry_points) or 'none'} | languages={','.join(ref.languages) or 'unknown'}"
                    )
            if not references:
                references = ["- none"]
            diff = plan.diff_summary
            diff_lines = []
            if diff is not None:
                hint_lines = []
                for hint in diff.change_hints:
                    hint_lines.append(f"- {hint.path}: {hint.action} ({hint.mode}) {hint.reason}".strip())
                diff_lines = [
                    f"total_files={diff.total_files}",
                    f"created={','.join(diff.created_files) or 'none'}",
                    f"modified={','.join(diff.modified_files) or 'none'}",
                    f"skipped={','.join(diff.skipped_files) or 'none'}",
                    f"backups={diff.backup_count}",
                    "change_hints:",
                    *(hint_lines or ["- none"]),
                ]
            plan_section = "\n".join(
                [
                    "[PROJECT WRITE PLAN]",
                    f"target={plan.target_path}",
                    f"write_policy={plan.write_policy}",
                    f"target_exists={plan.target_exists}",
                    "references:",
                    *references,
                    "diff_summary:",
                    *diff_lines,
                ]
            )
        if wp == "create":
            mode_hint = "你在创建新项目骨架。优先生成清晰、最小、可运行的初始结构。"
        elif wp == "safe":
            mode_hint = "你在安全新增模式。只新增文件或代码片段，不要改写已有文件内容。若目标文件已存在，则拒绝覆盖，仅建议追加或新建文件。"
        else:
            mode_hint = "你在增量改写模式。优先局部修改，保持已有代码结构，输出局部补丁式改写计划，并明确哪些文件应改、哪些应新建。"
        return format_coder_generation_prompt(
            language=str(requirements.get("language", "python")),
            task=f"{mode_hint}\n\n{task}",
            architecture_design=str(arch) if arch else None,
            workspace_section="\n\n".join([ws, plan_section]).strip(),
        )

    def _resolve_coding_engine(self, context: AgentContext) -> str:
        return (
            ((context.metadata or {}).get("coding_engine") or context.codebase_context.get("coding_engine") or "cursor")
            .strip()
            .lower()
        )

    def _project_cwd(self, context: AgentContext) -> str:
        return str(context.codebase_context.get("project_path") or ".")

    def _coder_gen_cache_key(self, engine: str, prompt: str) -> str:
        raw = f"v1|{engine}|{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _maybe_get_codegen_cache(self, context: AgentContext, cache_key: str) -> Optional[Dict[str, Any]]:
        if not context.config.get("cache_llm_codegen", True):
            return None
        cache = _get_cache_backend()
        if cache is None:
            return None
        v = cache.get(cache_key)
        if isinstance(v, dict) and v.get("success"):
            return cast(Dict[str, Any], v)
        return None

    def _maybe_put_codegen_cache(self, context: AgentContext, cache_key: str, result: Dict[str, Any]) -> None:
        if not context.config.get("cache_llm_codegen", True):
            return
        if not result.get("success"):
            return
        cache = _get_cache_backend()
        if cache is None:
            return
        cache.set(cache_key, result, ttl_hours=24)

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

        adapter = _resolve_engine_adapter(
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
                    "project_write_plan": self._resolve_project_write_plan(context),
                    "write_policy": self._resolve_write_policy(context),
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
            return {
                "success": False,
                "error": str(e),
                "error_code": "adapter_exception",
                "request_id": "",
                "trace_id": "",
            }

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
        return hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()


__all__ = [
    "CoderAgent",
    "EngineAdapterProtocol",
    "EngineResult",
    "EngineAdapterConfig",
    "register_cache_backend_factory",
    "register_engine_adapter_factory",
]
