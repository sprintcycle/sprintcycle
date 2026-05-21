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
    # Check for unindexed ADR files
    readme_text = readme.read_text(encoding="utf-8")
    adr_files = sorted(f for f in adr_dir.iterdir() if f.suffix == ".md" and f.name != "README.md")
    for adr_file in adr_files:
        if adr_file.name not in readme_text:
            findings.append(
                GuardFinding(
                    rule_id="adr:unindexed",
                    severity="warning",
                    message=f"{adr_file.name} 未在 README.md 中索引",
                    location={"path": str(adr_file)},
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
    # Strict check: each matched file must be referenced in README.md
    has_readme = False
    for matched in matches:
        if matched.name == "README.md":
            has_readme = True
            continue
        if matched.suffix != ".md":
            continue
        parent = matched.parent
        readme = parent / "README.md"
        if not readme.is_file():
            findings.append(
                GuardFinding(
                    rule_id="adr:readme_required",
                    severity="error",
                    message=f"缺少 README.md 用于索引 {matched.name}",
                    location={"path": str(matched)},
                )
            )
            continue
        has_readme = True
        readme_text = readme.read_text(encoding="utf-8")
        if matched.name not in readme_text:
            findings.append(
                GuardFinding(
                    rule_id="adr:glob_not_indexed",
                    severity="error",
                    message=f"{matched.name} 未在 README.md 中索引 (strict glob: {glob_pattern})",
                    location={"path": str(matched)},
                )
            )
    # Check for phantom: files referenced in README but missing from glob
    if has_readme:
        for readme in set(
            m.parent / "README.md" for m in matches if m.name != "README.md" and (m.parent / "README.md").is_file()
        ):
            readme_text = readme.read_text(encoding="utf-8")
            matched_names = {m.name for m in matches}
            import re

            for ref in re.finditer(r"\(([^)]+)\)", readme_text):
                ref_file = ref.group(1)
                ref_name = ref_file.rstrip("/").split("/")[-1]
                if ref_name.endswith(".md") and ref_name != "README.md" and ref_name not in matched_names:
                    findings.append(
                        GuardFinding(
                            rule_id="adr:readme_not_in_glob",
                            severity="error",
                            message=f"README 引用了 {ref_name}，但 glob ({glob_pattern}) 未匹配",
                            location={"path": str(readme), "ref": ref_name},
                        )
                    )
    return findings
