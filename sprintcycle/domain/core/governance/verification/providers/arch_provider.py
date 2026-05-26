from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from ..model import VerificationFinding


class ArchProvider:
    name = "arch"

    def run(self, project_root: str, context: Dict[str, Any]) -> List[VerificationFinding]:
        root = Path(project_root).expanduser().resolve()
        findings: List[VerificationFinding] = []

        findings.extend(self._run_import_linter(root))
        findings.extend(self._run_ruff(root))
        findings.extend(self._run_grimp(root))
        return findings

    def _run_import_linter(self, root: Path) -> List[VerificationFinding]:
        exe = self._resolve_exe("lint-imports", "import-linter")
        pyproject = root / "pyproject.toml"
        if not exe or not pyproject.is_file():
            return [
                VerificationFinding(
                    rule_id="arch:import_linter:skipped",
                    severity="info",
                    message="import-linter 未配置或缺少 pyproject.toml",
                    location={"project_root": str(root)},
                )
            ]
        try:
            proc = subprocess.run(
                [exe, "--config", str(pyproject)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
            )
        except Exception as e:
            return [
                VerificationFinding(
                    rule_id="arch:import_linter:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]
        if proc.returncode == 0:
            return []
        return [
            VerificationFinding(
                rule_id="arch:import_linter:failed",
                severity="error",
                message=(proc.stderr or proc.stdout or "import-linter failed").strip(),
                location={"project_root": str(root), "exit_code": proc.returncode},
            )
        ]

    def _run_ruff(self, root: Path) -> List[VerificationFinding]:
        exe = self._resolve_exe("ruff")
        if not exe:
            return [
                VerificationFinding(
                    rule_id="arch:ruff:skipped",
                    severity="info",
                    message="ruff 未安装",
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
                VerificationFinding(
                    rule_id="arch:ruff:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]
        if proc.returncode == 0:
            return []
        return [
            VerificationFinding(
                rule_id="arch:ruff:failed",
                severity="warning",
                message=(proc.stderr or proc.stdout or "ruff failed").strip(),
                location={"project_root": str(root), "exit_code": proc.returncode},
            )
        ]

    def _run_grimp(self, root: Path) -> List[VerificationFinding]:
        try:
            import grimp  # type: ignore
        except Exception:
            return [
                VerificationFinding(
                    rule_id="arch:grimp:skipped",
                    severity="info",
                    message="grimp 未安装",
                    location={"project_root": str(root)},
                )
            ]

        try:
            graph = grimp.build_graph("sprintcycle")
        except Exception as e:
            return [
                VerificationFinding(
                    rule_id="arch:grimp:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]

        findings: List[VerificationFinding] = []
        sensitive_packages = [
            "sprintcycle.api",
            "sprintcycle.governance",
            "sprintcycle.execution",
            "sprintcycle.application.orchestration",
            "sprintcycle.application.release_plan",
        ]
        suspicious_edges = []
        for pkg in sensitive_packages:
            try:
                importers = graph.find_modules_that_directly_import(pkg)
                if importers:
                    suspicious_edges.append({"module": pkg, "importers": sorted(str(m) for m in importers)[:20]})
            except Exception:
                continue
        if suspicious_edges:
            findings.append(
                VerificationFinding(
                    rule_id="arch:grimp:direct_import_edges",
                    severity="warning",
                    message="检测到对核心包的直接导入关系",
                    location={"edges": suspicious_edges[:10]},
                )
            )
        return findings

    @staticmethod
    def _resolve_exe(*names: str) -> str | None:
        for name in names:
            p = shutil.which(name)
            if p:
                return p
        cand = Path(sys.executable).resolve().parent
        for name in names:
            path = cand / name
            if path.is_file():
                return str(path)
        return None
