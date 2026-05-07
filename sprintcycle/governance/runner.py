"""治理执行器：Planning / Review 检查包聚合。"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import time
from pathlib import Path

import yaml
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from loguru import logger

from ..config.quality import runs_architecture_guard, runs_pytest, runs_static_gate
from ..execution.static_analyzer import AnalysisConfig, StaticAnalyzer
from .adr_check import check_adr_readme_index, check_adr_readme_strict_glob
from .compose_hint import check_compose_hints, check_compose_supply_chain_hints
from .report import GovernanceReport, GovernanceViolation, Severity
from .sdd_checks import (
    violations_acceptance_files,
    violations_for_task_spec_refs,
    violations_from_release_plan_validator,
    violations_spec_marker_in_files,
)
from .argv_extensions import extend_argv_items_with_plugins
from .yaml_checks import checks_for_gate, run_argv_checks
from .yaml_merge import load_merged_governance_data

if TYPE_CHECKING:
    from ..config.runtime_config import RuntimeConfig


def _maybe_downgrade_errors_to_warnings(cfg: "RuntimeConfig", violations: List[GovernanceViolation]) -> None:
    """保守「仅观察」：将 error 降为 warning，避免 has_error_severity / 阻断语义误伤。"""
    if not getattr(cfg, "governance_downgrade_errors_to_warnings", False):
        return
    for v in violations:
        if v.severity == "error":
            v.severity = "warning"


def _resolve_lint_imports_exe() -> Optional[str]:
    import sys

    p = shutil.which("lint-imports")
    if p:
        return p
    cand = Path(sys.executable).resolve().parent / "lint-imports"
    if cand.is_file():
        return str(cand)
    return None


def _truncate(s: str, max_len: int = 4000) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 20] + "\n... [truncated]"


class GovernanceRunner:
    """对项目根目录执行 Planning / Review 治理检查。"""

    def __init__(self, runtime_config: "RuntimeConfig"):
        self._cfg = runtime_config

    def _project(self, project_path: str) -> Path:
        return Path(project_path).expanduser().resolve()

    def _load_yaml_data(self, root: Path) -> Dict[str, Any]:
        return load_merged_governance_data(root, self._cfg)

    async def run_planning_gate(self, project_path: str, extra_context: Optional[Dict[str, Any]] = None) -> GovernanceReport:
        root = self._project(project_path)
        t0 = time.perf_counter()
        violations: List[GovernanceViolation] = []
        meta: Dict[str, Any] = {
            "project_path": str(root),
            "effective_quality_level": self._cfg.effective_quality_level(),
            "checks_planned": [],
        }
        level = self._cfg.effective_quality_level()
        meta["checks_planned"].append(f"quality_level={level} (static={runs_static_gate(level)}, pytest={runs_pytest(level)}, arch={runs_architecture_guard(level)})")

        spec_glob = (getattr(self._cfg, "governance_spec_glob", None) or "").strip()
        if spec_glob:
            matches = list(root.glob(spec_glob))
            if not matches:
                violations.append(
                    GovernanceViolation(
                        rule_id="planning:spec_glob",
                        severity="warning",
                        message=f"spec_glob 未匹配任何文件: {spec_glob}",
                        location={"glob": spec_glob, "root": str(root)},
                    )
                )
            else:
                meta["checks_planned"].append(f"spec_glob matched {len(matches)} file(s)")
                marker = (getattr(self._cfg, "governance_spec_marker", None) or "").strip()
                if marker:
                    violations.extend(violations_spec_marker_in_files(root, spec_glob, marker))
                    meta["checks_planned"].append("spec_marker scan")

        acc_glob = (getattr(self._cfg, "governance_acceptance_glob", None) or "").strip()
        if acc_glob:
            violations.extend(violations_acceptance_files(root, acc_glob))
            meta["checks_planned"].append("acceptance_glob")

        rp = (extra_context or {}).get("release_plan")
        if rp is not None and getattr(self._cfg, "governance_planning_validate_release_plan", True):
            from ..release_plan.models import ReleasePlan

            if isinstance(rp, ReleasePlan):
                violations.extend(violations_from_release_plan_validator(rp))
                violations.extend(violations_for_task_spec_refs(root, rp))
                meta["checks_planned"].append("release_plan_validator+spec_ref")

        data = self._load_yaml_data(root)
        planning_argv = extend_argv_items_with_plugins("planning", checks_for_gate(data, "planning"), self._cfg, root)
        violations.extend(run_argv_checks(planning_argv, root, "planning"))

        if extra_context:
            meta["context_keys"] = sorted(str(k) for k in extra_context.keys())

        _maybe_downgrade_errors_to_warnings(self._cfg, violations)
        meta["duration_sec"] = round(time.perf_counter() - t0, 3)
        return GovernanceReport(gate="planning", violations=violations, metadata=meta)

    async def run_review_gate(self, project_path: str) -> GovernanceReport:
        root = self._project(project_path)
        t0 = time.perf_counter()
        violations: List[GovernanceViolation] = []
        meta: Dict[str, Any] = {"project_path": str(root), "steps": []}

        data = self._load_yaml_data(root)
        review_argv = extend_argv_items_with_plugins("review", checks_for_gate(data, "review"), self._cfg, root)
        yv = run_argv_checks(review_argv, root, "review")
        violations.extend(yv)
        if yv or review_argv:
            meta["steps"].append("yaml_review_checks")

        level = self._cfg.effective_quality_level()
        if getattr(self._cfg, "governance_review_static", True) and runs_static_gate(level):
            cfg = AnalysisConfig(
                ruff_enabled=True,
                mypy_enabled=True,
                max_results=80,
            )
            analyzer = StaticAnalyzer(str(root), cfg)
            try:
                results = await analyzer.analyze_python(None)
                meta["steps"].append("static_analyzer")
                meta["static_findings"] = len(results)
                max_static = 50
                for i, r in enumerate(results):
                    if i >= max_static:
                        violations.append(
                            GovernanceViolation(
                                rule_id="static:truncated",
                                severity="warning",
                                message=f"静态问题仅展示前 {max_static} 条，共 {len(results)} 条",
                                location={},
                            )
                        )
                        break
                    sev: Severity
                    if r.severity == "error":
                        sev = "error"
                    elif r.severity == "warning":
                        sev = "warning"
                    else:
                        sev = "info"
                    violations.append(
                        GovernanceViolation(
                            rule_id=f"static:{r.tool}:{r.code}",
                            severity=sev,
                            message=f"{r.file_path}:{r.line} {r.message}",
                            location={
                                "file": r.file_path,
                                "line": r.line,
                                "column": r.column,
                                "tool": r.tool,
                                "code": r.code,
                            },
                        )
                    )
            except Exception as e:
                violations.append(
                    GovernanceViolation(
                        rule_id="static:analyzer",
                        severity="warning",
                        message=f"静态分析异常: {e}",
                        location={},
                    )
                )
        else:
            meta["steps"].append("static_skipped")

        if getattr(self._cfg, "governance_review_import_linter", True):
            exe = _resolve_lint_imports_exe()
            pyproject = root / "pyproject.toml"
            if not exe:
                meta["steps"].append("import_linter_skipped_no_binary")
                violations.append(
                    GovernanceViolation(
                        rule_id="import_linter:missing",
                        severity="warning",
                        message="未找到 lint-imports，可安装 dev 依赖: pip install import-linter",
                        location={},
                    )
                )
            elif not pyproject.is_file():
                meta["steps"].append("import_linter_skipped_no_pyproject")
            else:
                try:
                    proc = subprocess.run(
                        [exe, "--config", str(pyproject)],
                        cwd=str(root),
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    meta["steps"].append("import_linter")
                    if proc.returncode != 0:
                        violations.append(
                            GovernanceViolation(
                                rule_id="import_linter:contracts",
                                severity="error",
                                message=_truncate(
                                    (proc.stderr or "").strip() + "\n" + (proc.stdout or "").strip()
                                )
                                or "import-linter 未通过",
                                location={"exit_code": proc.returncode},
                            )
                        )
                except Exception as e:
                    violations.append(
                        GovernanceViolation(
                            rule_id="import_linter:error",
                            severity="warning",
                            message=str(e),
                            location={},
                        )
                    )
        else:
            meta["steps"].append("import_linter_disabled")

        if getattr(self._cfg, "governance_check_adr", False):
            adr_dir = root / "docs" / "adr"
            if adr_dir.is_dir():
                adr_docs = [p for p in adr_dir.glob("*.md") if p.name.lower() != "readme.md"]
                if not adr_docs:
                    violations.append(
                        GovernanceViolation(
                            rule_id="adr:empty",
                            severity="warning",
                            message="docs/adr 下无 ADR 正文（*.md，不含 README）",
                            location={"path": str(adr_dir)},
                        )
                    )
                adr_glob = (getattr(self._cfg, "governance_adr_glob", None) or "").strip()
                if adr_glob:
                    violations.extend(check_adr_readme_strict_glob(root, adr_glob))
                    meta["steps"].append("adr_scan_strict_glob")
                else:
                    violations.extend(check_adr_readme_index(root))
                    meta["steps"].append("adr_scan")
            else:
                meta["steps"].append("adr_dir_missing")

        if getattr(self._cfg, "governance_check_compose", False):
            compose = root / "docker-compose.yml"
            alt = root / "compose.yaml"
            cfile = compose if compose.is_file() else alt if alt.is_file() else None
            if not cfile:
                violations.append(
                    GovernanceViolation(
                        rule_id="compose:missing",
                        severity="warning",
                        message="未找到 docker-compose.yml 或 compose.yaml",
                        location={"root": str(root)},
                    )
                )
            else:
                text = cfile.read_text(encoding="utf-8", errors="replace")
                violations.extend(check_compose_hints(cfile, text))
                meta["steps"].append("compose_hint")
                if getattr(self._cfg, "governance_compose_supply_chain", False):
                    try:
                        cdoc = yaml.safe_load(text)
                    except Exception:
                        cdoc = None
                    if isinstance(cdoc, dict) and isinstance(cdoc.get("services"), dict):
                        violations.extend(check_compose_supply_chain_hints(cfile, cdoc["services"]))
                        meta["steps"].append("compose_supply_chain")

        _maybe_downgrade_errors_to_warnings(self._cfg, violations)
        meta["duration_sec"] = round(time.perf_counter() - t0, 3)
        return GovernanceReport(gate="review", violations=violations, metadata=meta)


def run_planning_gate_sync(
    project_path: str,
    runtime_config: "RuntimeConfig",
    extra_context: Optional[Dict[str, Any]] = None,
) -> GovernanceReport:
    return asyncio.run(GovernanceRunner(runtime_config).run_planning_gate(project_path, extra_context=extra_context))


def run_review_gate_sync(project_path: str, runtime_config: "RuntimeConfig") -> GovernanceReport:
    return asyncio.run(GovernanceRunner(runtime_config).run_review_gate(project_path))


def persist_report(report: GovernanceReport, project_path: str, runtime_config: "RuntimeConfig") -> Optional[Path]:
    """将最近一次报告写入 ``<report_dir>/governance_last.json``。"""
    rel = getattr(runtime_config, "governance_report_dir", None) or ".sprintcycle"
    root = Path(project_path).expanduser().resolve()
    out_dir = (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "governance_last.json"
        import json

        payload = report.to_dict()
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        from .history import append_history_snapshot

        append_history_snapshot(report, project_path, runtime_config)
        return path
    except Exception as e:
        logger.warning("写入治理报告失败: {}", e)
        return None


def persist_planning_report(report: GovernanceReport, project_path: str, runtime_config: "RuntimeConfig") -> Optional[Path]:
    """将 Planning 门报告写入 ``<report_dir>/governance_planning_last.json``（与 Sprint 钩子路径一致）。"""
    rel = getattr(runtime_config, "governance_report_dir", None) or ".sprintcycle"
    root = Path(project_path).expanduser().resolve()
    out_dir = (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "governance_planning_last.json"
        import json

        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        from .history import append_history_snapshot

        append_history_snapshot(report, project_path, runtime_config)
        return path
    except Exception as e:
        logger.warning("写入 Planning 治理报告失败: {}", e)
        return None


def emit_governance_gate_cli_sync(
    project_path: str,
    runtime_config: "RuntimeConfig",
    gate: str,
    report: GovernanceReport,
) -> None:
    """``sprintcycle governance check`` 可选：向执行事件后端派发 ``GOVERNANCE_GATE``（与 Dashboard SSE 对齐）。"""
    if not bool(getattr(runtime_config, "governance_cli_emit_events", False)):
        return
    from ..execution.events import (
        Event,
        EventType,
        ensure_default_execution_event_backend_for_project,
        get_execution_event_backend,
    )

    ensure_default_execution_event_backend_for_project(project_path, runtime_config)
    bus = get_execution_event_backend()
    viol = list(report.violations)
    compose_hits = [
        {"rule_id": v.rule_id, "message": (v.message or "")[:400]}
        for v in viol
        if str(v.rule_id).startswith("compose:")
    ]
    n_err = sum(1 for v in viol if v.severity == "error")
    n_warn = sum(1 for v in viol if v.severity == "warning")

    async def _emit() -> None:
        await bus.emit(
            Event(
                type=EventType.GOVERNANCE_GATE,
                data={
                    "gate": gate,
                    "sprint_name": "__cli__",
                    "error_count": n_err,
                    "warning_count": n_warn,
                    "compose_rule_ids": [h["rule_id"] for h in compose_hits],
                    "compose_hits": compose_hits[:15],
                    "violation_rule_ids_sample": [v.rule_id for v in viol[:24]],
                },
            )
        )

    asyncio.run(_emit())


def run_governance_check_and_persist(
    project_path: str,
    runtime_config: "RuntimeConfig",
    gate: str,
) -> Tuple[Optional[GovernanceReport], Optional[GovernanceReport], bool]:
    """执行 Planning/Review 门禁、落盘、可选 CLI 事件；返回报告与是否应按 block_on 视为失败。"""
    planning_report: Optional[GovernanceReport] = None
    review_report: Optional[GovernanceReport] = None
    if gate in ("planning", "both"):
        planning_report = run_planning_gate_sync(project_path, runtime_config)
        if planning_report is not None:
            persist_planning_report(planning_report, project_path, runtime_config)
            emit_governance_gate_cli_sync(project_path, runtime_config, "planning", planning_report)
    if gate in ("review", "both"):
        review_report = run_review_gate_sync(project_path, runtime_config)
        if review_report is not None:
            persist_report(review_report, project_path, runtime_config)
            emit_governance_gate_cli_sync(project_path, runtime_config, "review", review_report)

    block_on = (runtime_config.governance_block_on or "none").strip().lower()
    fail = False
    if gate in ("planning", "both") and planning_report is not None:
        if block_on == "planning_and_review" and planning_report.has_error_severity():
            fail = True
    if gate in ("review", "both") and review_report is not None:
        if block_on in ("review_only", "planning_and_review") and review_report.has_error_severity():
            fail = True
    return planning_report, review_report, fail
