from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from ..model import GuardFinding


class RuffAdapter:
    def run(self, project_root: str) -> List[GuardFinding]:
        root = Path(project_root).expanduser().resolve()
        exe = self._resolve_exe()
        if not exe:
            return [
                GuardFinding(
                    rule_id="ruff:missing",
                    severity="warning",
                    message="未找到 ruff 可执行文件，跳过 ruff 检查",
                    location={"project_root": str(root)},
                )
            ]

        try:
            proc = subprocess.run(
                [exe, "check", str(root), "--output-format", "json"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
            )
        except Exception as e:
            return [
                GuardFinding(
                    rule_id="ruff:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]

        if proc.returncode == 0:
            return []

        findings: List[GuardFinding] = []
        raw = (proc.stdout or "").strip()
        if raw:
            try:
                data = json.loads(raw)
            except Exception:
                data = []
        else:
            data = []

        if isinstance(data, list):
            for item in data[:300]:
                if not isinstance(item, dict):
                    continue
                findings.append(
                    GuardFinding(
                        rule_id=f"ruff:{item.get('code', 'unknown')}",
                        severity="warning",
                        message=item.get("message", "ruff issue"),
                        location={
                            "file": item.get("filename") or item.get("file") or "",
                            "line": item.get("location", {}).get("row")
                            if isinstance(item.get("location"), dict)
                            else item.get("line"),
                            "column": item.get("location", {}).get("column")
                            if isinstance(item.get("location"), dict)
                            else item.get("column"),
                            "fixable": item.get("fix") is not None,
                        },
                    )
                )
        if not findings:
            findings.append(
                GuardFinding(
                    rule_id="ruff:issues",
                    severity="warning",
                    message=(proc.stderr or proc.stdout or "ruff 检查未通过").strip(),
                    location={"project_root": str(root), "exit_code": proc.returncode},
                )
            )
        return findings

    @staticmethod
    def _resolve_exe() -> str | None:
        p = shutil.which("ruff")
        if p:
            return p
        cand = Path(sys.executable).resolve().parent / "ruff"
        if cand.is_file():
            return str(cand)
        return None
