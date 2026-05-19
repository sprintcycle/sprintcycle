from __future__ import annotations

from pathlib import Path
from typing import List

from ..model import GuardFinding


class GrimpAdapter:
    def run(self, project_root: str) -> List[GuardFinding]:
        root = Path(project_root).expanduser().resolve()
        package_root = root / "sprintcycle"
        if not package_root.is_dir():
            return []

        try:
            import grimp  # type: ignore
        except Exception:
            return [
                GuardFinding(
                    rule_id="grimp:missing",
                    severity="warning",
                    message="未安装 grimp，跳过依赖图分析",
                    location={"project_root": str(root)},
                )
            ]

        findings: List[GuardFinding] = []
        try:
            graph = grimp.build_graph("sprintcycle")
        except Exception as e:
            return [
                GuardFinding(
                    rule_id="grimp:error",
                    severity="warning",
                    message=str(e),
                    location={"project_root": str(root)},
                )
            ]

        # 轻量核心边界检查：治理模块不应被高频边缘模块反向穿透到内部实现层。
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
                importing_modules = graph.find_modules_that_directly_import(pkg)
                if importing_modules:
                    suspicious_edges.append(
                        {
                            "module": pkg,
                            "importers": sorted(str(m) for m in importing_modules)[:20],
                        }
                    )
            except Exception:
                continue

        if suspicious_edges:
            findings.append(
                GuardFinding(
                    rule_id="grimp:direct_import_edges",
                    severity="warning",
                    message="检测到对核心包的直接导入关系，请检查是否符合边界设计",
                    location={"edges": suspicious_edges[:10]},
                )
            )

        return findings
