from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sprintcycle.domain.core.governance.common.model import Policy as VerificationPolicy


@dataclass
class VerificationConfig:
    enabled: bool = True
    project_root: str = "."
    policy: VerificationPolicy = field(default_factory=VerificationPolicy)

    run_test: bool = True
    run_verify: bool = True
    run_arch: bool = True
    run_security: bool = True

    use_playwright: bool = True
    use_cli: bool = True
    use_visual: bool = True
    use_pytest: bool = True
    use_import_linter: bool = True
    use_grimp: bool = True
    use_ruff: bool = True
    use_typecheck: bool = False
    use_secret_scan: bool = True

    pack_paths: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_runtime_config(cls, runtime_config: Any, project_root: str) -> "VerificationConfig":
        policy = getattr(runtime_config, "verification_policy", None)
        if not isinstance(policy, VerificationPolicy):
            policy = VerificationPolicy()
        return cls(
            enabled=bool(getattr(runtime_config, "verification_enabled", True)),
            project_root=project_root,
            policy=policy,
            run_test=bool(getattr(runtime_config, "verification_run_test", True)),
            run_verify=bool(getattr(runtime_config, "verification_run_verify", True)),
            run_arch=bool(getattr(runtime_config, "verification_run_arch", True)),
            run_security=bool(getattr(runtime_config, "verification_run_security", True)),
            use_playwright=bool(getattr(runtime_config, "verification_use_playwright", True)),
            use_cli=bool(getattr(runtime_config, "verification_use_cli", True)),
            use_visual=bool(getattr(runtime_config, "verification_use_visual", True)),
            use_pytest=bool(getattr(runtime_config, "verification_use_pytest", True)),
            use_import_linter=bool(getattr(runtime_config, "verification_use_import_linter", True)),
            use_grimp=bool(getattr(runtime_config, "verification_use_grimp", True)),
            use_ruff=bool(getattr(runtime_config, "verification_use_ruff", True)),
            use_typecheck=bool(getattr(runtime_config, "verification_use_typecheck", False)),
            use_secret_scan=bool(getattr(runtime_config, "verification_use_secret_scan", True)),
            pack_paths=[
                str(p).strip()
                for p in list(getattr(runtime_config, "verification_pack_paths", None) or [])
                if str(p).strip()
            ],
            metadata=dict(getattr(runtime_config, "verification_metadata", None) or {}),
        )
