"""
运行工作区：目标项目 A、参考项目 B 列表、写入策略（与 CLI -p / plan·run 对齐）。

write_policy:
- auto: 目标路径已存在则 incremental，否则 create
- create: 强调从零/骨架交付（仍只写入目标 A）
- incremental: 强调在现有 A 上增量修改
- safe: 仅新增文件/目录约束（不修改、不删除已有文件；依赖执行引擎遵守提示）
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from sprintcycle.domain.models import ReleasePlan

# 与 CLI / API / MCP / Dashboard 共用的合法取值
WRITE_POLICIES = frozenset({"auto", "create", "incremental", "safe"})

SAFE_CONSTRAINT = (
    "write_policy:safe — 仅允许新增文件与目录；不得修改、重命名或删除仓库内已有文件。"
    "若需变更行为，请通过新增模块/适配层实现。"
)
CREATE_CONSTRAINT = "write_policy:create — 优先搭建清晰的项目骨架与约定；避免无必要地大规模重写或删除已有代码。"
INCREMENTAL_CONSTRAINT = "write_policy:incremental — 在现有代码基础上增量实现；保留可复用实现，避免整库替换。"


def _strip_list(raw: Optional[Sequence[str]]) -> List[str]:
    if not raw:
        return []
    out: List[str] = []
    for x in raw:
        s = str(x).strip()
        if s:
            out.append(s)
    return out


def normalize_reference_paths(paths: Optional[Sequence[str]]) -> List[str]:
    """解析为绝对路径；必须存在且为目录。"""
    out: List[str] = []
    for s in _strip_list(paths):
        p = Path(s).expanduser()
        try:
            rp = p.resolve()
        except OSError as e:
            raise ValueError(f"参考路径无效: {s!r} ({e})") from e
        if not rp.is_dir():
            raise ValueError(f"参考路径须为已存在目录: {rp}")
        out.append(str(rp))
    return out


def normalize_write_policy(raw: Optional[str]) -> str:
    v = (raw or "auto").strip().lower()
    if v not in WRITE_POLICIES:
        raise ValueError(f"write_policy 须为 auto|create|incremental|safe，当前为 {raw!r}")
    return v


def effective_write_policy(declared: str, target_root: Path) -> str:
    """auto → 按目标目录是否已存在拆分。"""
    if declared != "auto":
        return declared
    exists = target_root.exists() and target_root.is_dir()
    return "incremental" if exists else "create"


def ensure_project_layout(project_path: str) -> str:
    """创建项目根与 `.sprintcycle/{{state,logs}}`（幂等）。返回绝对路径字符串。"""
    root = Path(project_path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / ".sprintcycle" / "state").mkdir(parents=True, exist_ok=True)
    (root / ".sprintcycle" / "logs").mkdir(parents=True, exist_ok=True)
    return str(root)


def policy_constraint_line(effective: str) -> Optional[str]:
    if effective == "safe":
        return SAFE_CONSTRAINT
    if effective == "create":
        return CREATE_CONSTRAINT
    if effective == "incremental":
        return INCREMENTAL_CONSTRAINT
    return None


def attach_workspace_metadata(
    plan: ReleasePlan,
    *,
    reference_paths: Sequence[str],
    write_policy: str,
    effective_write_policy: str,
) -> None:
    meta: Dict[str, Any] = dict(plan.metadata or {})
    meta["reference_project_paths"] = list(reference_paths)
    meta["write_policy"] = write_policy
    meta["effective_write_policy"] = effective_write_policy
    plan.metadata = meta


def apply_policy_to_tasks(plan: ReleasePlan, effective: str) -> None:
    """将策略写入各任务 constraints，便于治理与下游 agent。"""
    line = policy_constraint_line(effective)
    if not line:
        return
    for sp in plan.sprints:
        for t in sp.tasks:
            if line not in (t.constraints or []):
                t.constraints = list(t.constraints or []) + [line]


def build_workspace_prompt_section(
    reference_paths: Sequence[str],
    effective_write_policy: str,
) -> str:
    """拼入 Coder（及同类）生成提示的附加段落。"""
    parts: List[str] = []
    pol = policy_constraint_line(effective_write_policy)
    if pol:
        parts.append(pol)
    if reference_paths:
        lines = "\n".join(f"- {p}" for p in reference_paths)
        parts.append("参考项目（只读，用于风格/结构借鉴；所有写入必须在目标工作区完成）：\n" + lines)
    if not parts:
        return ""
    return "\n\n工作区与策略：\n" + "\n\n".join(parts) + "\n"


__all__ = [
    "WRITE_POLICIES",
    "attach_workspace_metadata",
    "apply_policy_to_tasks",
    "build_workspace_prompt_section",
    "effective_write_policy",
    "ensure_project_layout",
    "normalize_reference_paths",
    "normalize_write_policy",
]
