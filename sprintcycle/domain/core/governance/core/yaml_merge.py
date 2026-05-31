"""合并主治理 YAML 与 ``governance_pack_paths``（V7 对齐：多规则包顺序叠加）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def resolve_governance_file(root: Path, raw: str) -> Optional[Path]:
    """将相对路径解析为项目根下的绝对路径；不存在则返回 None。"""
    s = (raw or "").strip()
    if not s:
        return None
    p = Path(s)
    if not p.is_absolute():
        p = (root / s).resolve()
    else:
        p = p.expanduser().resolve()
    return p if p.is_file() else None


def merge_governance_documents(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    顺序合并多份治理 YAML：``planning`` / ``review`` / ``task_after`` 列表按文件顺序拼接；
    亦合并 ``gates.planning`` / ``gates.review`` 列表；其它标量键以后覆盖前。
    """
    out: Dict[str, Any] = {}
    planning: List[Any] = []
    review: List[Any] = []
    task_after: List[Any] = []

    for d in docs:
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if k in ("planning", "review", "task_after", "gates"):
                continue
            out[k] = v
        planning.extend(d.get("planning") or [])
        review.extend(d.get("review") or [])
        task_after.extend(d.get("task_after") or [])
        g = d.get("gates")
        if isinstance(g, dict):
            gp, gr = g.get("planning"), g.get("review")
            if isinstance(gp, list):
                planning.extend(gp)
            if isinstance(gr, list):
                review.extend(gr)

    if planning:
        out["planning"] = planning
    if review:
        out["review"] = review
    if task_after:
        out["task_after"] = task_after
    return out


def _load_governance_yaml_cached():
    """延迟加载 load_governance_yaml"""
    from sprintcycle.domain.core.governance.arch_guard.checks import load_governance_yaml
    return load_governance_yaml


def load_merged_governance_data(root: Path, cfg: Any) -> Dict[str, Any]:
    """加载 ``governance_config_path`` 后按顺序叠加 ``governance_pack_paths``。"""
    docs: List[Dict[str, Any]] = []
    main = getattr(cfg, "governance_config_path", None) or ""
    mp = resolve_governance_file(root, str(main))
    if mp is not None:
        load_governance_yaml = _load_governance_yaml_cached()
        docs.append(load_governance_yaml(mp))

    packs = getattr(cfg, "governance_pack_paths", None) or []
    if isinstance(packs, str):
        packs = [packs]
    for rel in packs:
        pp = resolve_governance_file(root, str(rel).strip())
        if pp is not None:
            load_governance_yaml = _load_governance_yaml_cached()
            docs.append(load_governance_yaml(pp))

    if not docs:
        return {}
    return merge_governance_documents(docs)
