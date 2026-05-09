"""ADR 索引一致性检查。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from .arch_guard.model import GuardFinding


def check_adr_readme_index(root: Path) -> List[GuardFinding]:
    adr_dir = root / "docs" / "adr"
    findings: List[GuardFinding] = []
    if not adr_dir.is_dir():
        return findings
    readme = adr_dir / "README.md"
    if not readme.is_file():
        findings.append(
            GuardFinding(
                rule_id="adr:readme_missing",
                severity="warning",
                message="docs/adr 下缺少 README.md 索引文件",
                location={"path": str(adr_dir)},
            )
        )
    return findings


def check_adr_readme_strict_glob(root: Path, glob_pattern: str) -> List[GuardFinding]:
    findings: List[GuardFinding] = []
    matches = list(root.glob(glob_pattern))
    if not matches:
        findings.append(
            GuardFinding(
                rule_id="adr:readme_glob_missing",
                severity="warning",
                message=f"ADR README glob 未匹配任何文件: {glob_pattern}",
                location={"glob": glob_pattern},
            )
        )
    return findings
