"""可选 pluggy：合并 ``extra_governance_argv`` hook 返回的 argv 条目。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..domain.quality_spec.plugin_protocols import QualityPlugin
from ..domain.quality_spec.registry import QualityRegistry


def merge_argv_via_plugin(
    gate: str,
    base_items: List[Dict[str, Any]],
    cfg: Any,
    root: Path,
) -> List[Dict[str, Any]]:
    try:
        import importlib.metadata

        import pluggy
    except ImportError:
        logger.warning("未安装 pluggy，跳过 pluggy argv 合并；请 pip install -U sprintcycle 或 pip install pluggy")
        return list(base_items)

    hookspec = pluggy.HookspecMarker("sprintcycle_governance")
    hookimpl = pluggy.HookimplMarker("sprintcycle_governance")

    class GovernanceArgvSpecs:
        @hookspec(firstresult=False)
        def extra_governance_argv(
            self,
            gate: str,
            project_path: str,
            runtime_config: Any,
        ) -> List[Dict[str, Any]] | None: ...

    pm = pluggy.PluginManager("sprintcycle_governance")
    pm.add_hookspecs(GovernanceArgvSpecs)

    class _Builtin:
        @hookimpl
        def extra_governance_argv(self, gate: str, project_path: str, runtime_config: Any) -> List[Dict[str, Any]]:
            return []

    pm.register(_Builtin())

    quality_registry = QualityRegistry()
    eps = importlib.metadata.entry_points()
    try:
        plug_eps = eps.select(group="sprintcycle_governance.pluggy_plugin")  # type: ignore[union-attr]
    except AttributeError:
        plug_eps = [ep for ep in eps if getattr(ep, "group", None) == "sprintcycle_governance.pluggy_plugin"]
    for ep in plug_eps:
        try:
            reg = ep.load()
        except Exception as e:
            logger.warning("加载 pluggy 治理插件 {} 失败: {}", ep.name, e)
            continue
        try:
            if callable(reg):
                result = reg(pm)
                if isinstance(result, QualityPlugin):
                    result.register(quality_registry)
            elif isinstance(reg, QualityPlugin):
                reg.register(quality_registry)
        except Exception as e:
            logger.warning("注册 pluggy 治理插件 {} 失败: {}", ep.name, e)

    chunks = pm.hook.extra_governance_argv(
        gate=gate,
        project_path=str(root),
        runtime_config=cfg,
    )
    extra: List[Dict[str, Any]] = []
    for ch in chunks or []:
        if not ch:
            continue
        for item in ch:
            if isinstance(item, dict):
                extra.append(item)
    if quality_registry.list_rules():
        for rule in quality_registry.list_rules():
            if isinstance(rule, dict):
                extra.append(rule)
            elif hasattr(rule, "to_dict"):
                extra.append(rule.to_dict())
    return list(base_items) + extra
