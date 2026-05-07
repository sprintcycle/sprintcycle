"""
扩展 argv 检查项：stdlib ``importlib.metadata.entry_points`` 与可选 pluggy。

第三方包在 ``pyproject.toml`` 中注册::

    [project.entry-points.\"sprintcycle_governance.review_argv\"]
    mypack = \"mypkg.governance:review_argv_items\"

其中 ``review_argv_items`` 可为：

- 无参可调用 ``() -> list[dict]``，或
- ``(runtime_config: Any, project_root: Path) -> list[dict]``

``planning`` 门使用组名 ``sprintcycle_governance.planning_argv``。

可选 **pluggy**（``pip install sprintcycle[governance-ext]`` 且 ``[governance] pluggy_argv = true``）：
组 ``sprintcycle_governance.pluggy_plugin`` 指向可调用 ``register(pm: PluginManager)``，在 manager 上注册 ``extra_governance_argv`` hookimpl。
"""

from __future__ import annotations

import importlib.metadata
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

_GATE_GROUPS = {
    "planning": "sprintcycle_governance.planning_argv",
    "review": "sprintcycle_governance.review_argv",
}


def _call_ep_callable(fn: Any, cfg: Any, root: Path) -> List[Dict[str, Any]]:
    try:
        import inspect

        sig = len(inspect.signature(fn).parameters)
    except (TypeError, ValueError):
        sig = 0
    try:
        if sig == 0:
            raw = fn()
        else:
            raw = fn(cfg, root)
    except Exception as e:
        logger.warning("治理 argv 扩展点执行失败: {}", e)
        return []
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for x in raw:
        if isinstance(x, dict):
            out.append(x)
    return out


def load_entry_point_argv_extensions(gate: str, cfg: Any, root: Path) -> List[Dict[str, Any]]:
    if not bool(getattr(cfg, "governance_argv_entry_points", True)):
        return []
    group = _GATE_GROUPS.get(gate)
    if not group:
        return []
    eps = importlib.metadata.entry_points()
    try:
        selected = eps.select(group=group)  # type: ignore[union-attr]
    except AttributeError:
        selected = [ep for ep in eps if ep.group == group]  # type: ignore[attr-defined]
    merged: List[Dict[str, Any]] = []
    for ep in selected:
        try:
            fn = ep.load()
        except Exception as e:
            logger.warning("加载治理 argv 扩展点 {} 失败: {}", ep.name, e)
            continue
        if not callable(fn):
            continue
        merged.extend(_call_ep_callable(fn, cfg, root))
    return merged


def _merge_pluggy_argv(gate: str, base: List[Dict[str, Any]], cfg: Any, root: Path) -> List[Dict[str, Any]]:
    if not bool(getattr(cfg, "governance_pluggy_argv", False)):
        return base
    from .pluggy_host import merge_argv_via_pluggy

    return merge_argv_via_pluggy(gate, base, cfg, root)


def extend_argv_items_with_plugins(
    gate: str,
    yaml_items: List[Dict[str, Any]],
    cfg: Any,
    root: Path,
) -> List[Dict[str, Any]]:
    """YAML 原始列表 → 按 TOML/tags 过滤 → entry_points → 可选 pluggy → 再过滤（插件条目也受 tags 约束）。"""
    from .yaml_checks import filter_argv_items_by_governance_sources

    step1 = filter_argv_items_by_governance_sources(yaml_items, cfg)
    step2: List[Dict[str, Any]] = list(step1)
    step2.extend(load_entry_point_argv_extensions(gate, cfg, root))
    step2 = _merge_pluggy_argv(gate, step2, cfg, root)
    return filter_argv_items_by_governance_sources(step2, cfg)
