from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .model import GuardPolicy


@dataclass
class ArchGuardConfig:
    enabled: bool = True
    project_root: str = "."
    policy: GuardPolicy = field(default_factory=GuardPolicy)

    planning_enabled: bool = True
    review_enabled: bool = True
    local_enabled: bool = False

    use_import_linter: bool = True
    use_grimp: bool = True
    use_archon: bool = True
    use_ruff: bool = True
    use_typecheck: bool = False

    block_on: str = "review_only"
    report_dir: str = ".sprintcycle/governance"
    pack_paths: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_runtime_config(cls, runtime_config: Any, project_root: str) -> "ArchGuardConfig":
        raw_policy = getattr(runtime_config, "arch_guard_policy", None)
        policy = raw_policy if isinstance(raw_policy, GuardPolicy) else GuardPolicy()
        pack_paths = list(getattr(runtime_config, "governance_pack_paths", None) or [])
        metadata = dict(getattr(runtime_config, "governance_metadata", None) or {})

        return cls(
            enabled=bool(getattr(runtime_config, "governance_enabled", False)),
            project_root=project_root,
            policy=policy,
            planning_enabled=bool(getattr(runtime_config, "governance_planning_enabled", True)),
            review_enabled=bool(getattr(runtime_config, "governance_review_enabled", True)),
            local_enabled=bool(getattr(runtime_config, "governance_local_enabled", False)),
            use_import_linter=bool(getattr(runtime_config, "governance_use_import_linter", True)),
            use_grimp=bool(getattr(runtime_config, "governance_use_grimp", True)),
            use_archon=bool(getattr(runtime_config, "governance_use_archon", True)),
            use_ruff=bool(getattr(runtime_config, "governance_use_ruff", True)),
            use_typecheck=bool(getattr(runtime_config, "governance_use_typecheck", False)),
            block_on=str(getattr(runtime_config, "governance_block_on", "review_only") or "review_only"),
            report_dir=str(
                getattr(runtime_config, "governance_report_dir", ".sprintcycle/governance") or ".sprintcycle/governance"
            ),
            pack_paths=[str(p).strip() for p in pack_paths if str(p).strip()],
            metadata=metadata,
        )
