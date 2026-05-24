from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable, List

from .model import GuardRule


class GuardPackLoader:
    """从 pack_paths 加载外部治理包。当前只加载显式导出的规则函数，不做隐式扫描。"""

    def __init__(self, pack_paths: Iterable[str]):
        self.pack_paths = [str(p).strip() for p in pack_paths if str(p).strip()]

    def load_rules(self) -> List[GuardRule]:
        rules: List[GuardRule] = []
        for pack_path in self.pack_paths:
            rules.extend(self._load_rules_from_pack(pack_path))
        return rules

    def _load_rules_from_pack(self, pack_path: str) -> List[GuardRule]:
        path = Path(pack_path).expanduser().resolve()
        if not path.exists():
            return []

        if path.is_dir():
            module_path = path / "guard_pack.py"
            if not module_path.is_file():
                return []
        else:
            module_path = path

        spec = importlib.util.spec_from_file_location(f"sprintcycle_guard_pack_{module_path.stem}", module_path)
        if spec is None or spec.loader is None:
            return []

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
        except Exception:
            return []

        exported = getattr(module, "GUARD_RULES", None)
        if isinstance(exported, list):
            return [r for r in exported if isinstance(r, GuardRule)]

        factory = getattr(module, "register_rules", None)
        if callable(factory):
            try:
                result = factory()
            except Exception:
                return []
            if isinstance(result, list):
                return [r for r in result if isinstance(r, GuardRule)]
        return []
