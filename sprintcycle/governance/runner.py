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
from ..quality_spec.context import build_quality_context
from ..quality_spec.reports.finding import Finding as QualityFinding
from ..quality_spec.reports.report import Report as QualityReport
from ..quality_spec.spec.task_spec import TaskSpec
from ..quality_spec.rules.planning_rules import default_planning_rules
from ..quality_spec.rules.review_rules import default_review_rules
from .arch_guard.adr_check import check_adr_readme_index, check_adr_readme_strict_glob
from .arch_guard.compose_hint import check_compose_hints, check_compose_supply_chain_hints
from .arch_guard.model import GuardFinding, GuardReport, GuardSeverity
from .arch_guard.sdd_checks import (
    violations_acceptance_files,
    violations_for_task_spec_refs,
    violations_from_release_plan_validator,
    violations_spec_marker_in_files,
)
from .arch_guard.argv_extensions import extend_argv_items_with_plugins
from .arch_guard.yaml_checks import checks_for_gate, run_argv_checks
from .hitl import HitlDecision, HitlGate, HitlPolicyResult
from .observability import ObservabilityFacade, create_observability_facade
from .yaml_merge import load_merged_governance_data

if TYPE_CHECKING:
    from ..config.runtime_config import RuntimeConfig


def _maybe_downgrade_errors_to_warnings(cfg: "RuntimeConfig", findings: List[GuardFinding]) -> None:
    """保守「仅观察」：将 error 降为 warning，避免 has_error_severity / 阻断语义误伤。"""
    if not getattr(cfg, "governance_downgrade_errors_to_warnings", False):
        return
    for v in findings:
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
        self._observability: Optional[ObservabilityFacade] = None

    def _project(self, project_path: str) -> Path:
        return Path(project_path).expanduser().resolve()

    def _load_yaml_data(self, root: Path) -> Dict[str, Any]:
        return load_merged_governance_data(root, self._cfg)

    def _observability_facade(self, project_path: str) -> ObservabilityFacade:
        if self._observability is None:
            self._observability = create_observability_facade(project_path, self._cfg)
        return self._observability

    async def _maybe_trigger_hitl(
        self,
        *,
        project_path: str,
        gate: str,
        title: str,
        summary: str,
        context: Dict[str, Any],
        risk_level: str = "medium",
    ) -> Optional[HitlPolicyResult]:
        policy = evaluate_hitl_policy(gate=gate, context={**context, "summary": summary, "risk_level": risk_level}, config=self._cfg)
        if not policy.should_trigger:
            return policy
        observability = self._observability_facade(project_path)
        result = await observability.request_human_decision(
            execution_id=str(context.get("execution_id") or "__governance__"),
            gate=gate,
            title=title,
            summary=summary,
            context={**context, "policy": policy.metadata},
            risk_level=policy.risk_level,
            timeout_seconds=policy.timeout_seconds,
            wait=True,
        )
        context["hitl_decision"] = result.decision
        if result.decision in {HitlDecision.REQUEST_CHANGES.value, HitlDecision.MODIFY.value, HitlDecision.RETRY.value}:
            current = await observability.get_request(result.request_id)
            if current is not None:
                ctx = current.get("applied_context") or current.get("context") or {}
                context.update({"hitl": ctx.get("hitl", {}), "hitl_applied_context": ctx})
        return policy

    async def run_planning_gate(self, project_path: str, extra_context: Optional[Dict[str, Any]] = None) -> GuardReport:
        root = self._project(project_path)
        t0 = time.perf_counter()
        violations: List[GuardFinding] = []
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
                    GuardFinding(
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
        task_specs: List[TaskSpec] = []
        if rp is not None and getattr(self._cfg, "governance_planning_validate_release_plan", True):
            from ..release_plan.models import ReleasePlan

            if isinstance(rp, ReleasePlan):
                task_specs = rp.to_task_specs()
                meta["task_spec_count"] = len(task_specs)
                for spec in task_specs:
                    try:
                        spec.validate_minimal()
                    except Exception as e:
                        violations.append(
                            GuardFinding(
                                rule_id="planning:task_spec:minimal",
                                severity="error",
                                message=f"TaskSpec 校验失败: {e}",
                                location={"task_id": spec.id or ""},
                            )
                        )
                violations.extend(violations_from_release_plan_validator(rp))
                violations.extend(violations_for_task_spec_refs(root, rp))
                meta["checks_planned"].append("release_plan_validator+spec_ref")

        if extra_context:
            meta["context_keys"] = sorted(str(k) for k in extra_context.keys())
            if task_specs:
                ctx = build_quality_context(
                    project_path=str(root),
                    gate="planning",
                    extra=extra_context,
                    spec=task_specs[0] if len(task_specs) == 1 else task_specs,
                )
                meta["quality_context_gate"] = ctx.gate

        data = self._load_yaml_data(root)
        planning_rules = default_planning_rules().rules
        planning_argv = extend_argv_items_with_plugins("planning", checks_for_gate(data, "planning"), self._cfg, root)
        violations.extend(run_argv_checks(planning_argv, root, "planning"))
        meta["planning_rule_count"] = len(planning_rules)

        if extra_context:
            meta["context_keys"] = sorted(str(k) for k in extra_context.keys())

        if getattr(self._cfg, "hitl_enabled", False):
            hitl_ctx = {"project_path": str(root), **(extra_context or {}), "violation_count": len(violations), "gate": "planning"}
            policy = await self._maybe_trigger_hitl(
                project_path=str(root),
                gate=HitlGate.BEFORE_SPRINT.value,
                title="Planning 门人工确认",
                summary="规划阶段需要人工确认后再继续",
                context=hitl_ctx,
                risk_level=str(getattr(self._cfg, "hitl_default_risk_level", "medium")),
            )
            if policy is not None:
                meta["hitl_policy_mode"] = policy.mode
                meta["hitl_policy_risk_level"] = policy.risk_level

        _maybe_downgrade_errors_to_warnings(self._cfg, violations)
        meta["duration_sec"] = round(time.perf_counter() - t0, 3)
        return GuardReport(gate="planning", findings=violations, metadata=meta)

    async def run_review_gate(self, project_path: str) -> GuardReport:
        root = self._project(project_path)
        t0 = time.perf_counter()
        violations: List[GuardFinding] = []
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
                            GuardFinding(
                                rule_id="static:truncated",
                                severity="warning",
                                message=f"静态问题仅展示前 {max_static} 条，共 {len(results)} 条",
                                location={},
                            )
                        )
                        break
                    sev: GuardSeverity
                    if r.severity == "error":
                        sev = "error"
                    elif r.severity == "warning":
                        sev = "warning"
                    else:
                        sev = "info"
                    violations.append(
                        GuardFinding(
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
                    GuardFinding(
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
                    GuardFinding(
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
                            GuardFinding(
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
                        GuardFinding(
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
                        GuardFinding(
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
                    GuardFinding(
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

        if getattr(self._cfg, "hitl_enabled", False):
            hitl_ctx = {"project_path": str(root), "violation_count": len(violations), "gate": "review"}
            policy = await self._maybe_trigger_hitl(
                project_path=str(root),
                gate=HitlGate.EXECUTION_APPROVAL.value,
                title="Review 门人工审批",
                summary="Review 阶段存在治理结果，需要人工审批",
                context=hitl_ctx,
                risk_level=str(getattr(self._cfg, "hitl_default_risk_level", "medium")),
            )
            if policy is not None:
                meta["hitl_policy_mode"] = policy.mode
                meta["hitl_policy_risk_level"] = policy.risk_level

        try:
            from ..quality_spec.adapters.deal_adapter import DealAdapter
            from ..quality_spec.adapters.bandit_adapter import BanditAdapter
            from ..quality_spec.adapters.arch_adapter import ArchAdapter
            from ..quality_spec.context import build_quality_context
            from ..quality_spec.reports.report import Report as QualityReport
        except Exception:
            DealAdapter = BanditAdapter = ArchAdapter = None  # type: ignore[assignment]
            build_quality_context = None  # type: ignore[assignment]
            QualityReport = None  # type: ignore[assignment]

        if build_quality_context is not None and QualityReport is not None:
            qctx = build_quality_context(project_path=str(root), gate="review", extra={"project_path": str(root)})
            meta["quality_context_gate"] = qctx.gate
            if DealAdapter is not None:
                try:
                    deal_report = await DealAdapter().check_contracts(qctx.extra)
                    violations.extend(
                        GuardFinding(
                            rule_id=finding.rule_id,
                            severity=finding.severity,
                            message=finding.message,
                            location=finding.location,
                        )
                        for finding in deal_report.findings
                    )
                    meta["steps"].append("quality_spec_deal")
                except Exception as e:
                    violations.append(
                        GuardFinding(
                            rule_id="quality_spec:deal",
                            severity="warning",
                            message=str(e),
                            location={},
                        )
                    )
            if BanditAdapter is not None:
                try:
                    bandit_report = await BanditAdapter().scan(qctx.extra)
                    violations.extend(
                        GuardFinding(
                            rule_id=finding.rule_id,
                            severity=finding.severity,
                            message=finding.message,
                            location=finding.location,
                        )
                        for finding in bandit_report.findings
                    )
                    meta["steps"].append("quality_spec_bandit")
                except Exception as e:
                    violations.append(
                        GuardFinding(
                            rule_id="quality_spec:bandit",
                            severity="warning",
                            message=str(e),
                            location={},
                        )
                    )
            if ArchAdapter is not None:
                try:
                    arch_report = await ArchAdapter().analyze_architecture(qctx.extra)
                    violations.extend(
                        GuardFinding(
                            rule_id=finding.rule_id,
                            severity=finding.severity,
                            message=finding.message,
                            location=finding.location,
                        )
                        for finding in arch_report.findings
                    )
                    meta["steps"].append("quality_spec_arch")
                except Exception as e:
                    violations.append(
                        GuardFinding(
                            rule_id="quality_spec:arch",
                            severity="warning",
                            message=str(e),
                            location={},
                        )
                    )

        _maybe_downgrade_errors_to_warnings(self._cfg, violations)
        meta["duration_sec"] = round(time.perf_counter() - t0, 3)
        return GuardReport(gate="review", findings=violations, metadata=meta)


def run_planning_gate_sync(
    project_path: str,
    runtime_config: "RuntimeConfig",
    extra_context: Optional[Dict[str, Any]] = None,
) -> GuardReport:
    return asyncio.run(GovernanceRunner(runtime_config).run_planning_gate(project_path, extra_context=extra_context))


def run_review_gate_sync(project_path: str, runtime_config: "RuntimeConfig") -> GuardReport:
    return asyncio.run(GovernanceRunner(runtime_config).run_review_gate(project_path))


def persist_report(report: GuardReport, project_path: str, runtime_config: "RuntimeConfig") -> Optional[Path]:
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


def persist_planning_report(report: GuardReport, project_path: str, runtime_config: "RuntimeConfig") -> Optional[Path]:
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
    report: GuardReport,
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
) -> Tuple[Optional[GuardReport], Optional[GuardReport], bool]:
    """执行 Planning/Review 门禁、落盘、可选 CLI 事件；返回报告与是否应按 block_on 视为失败。"""
    planning_report: Optional[GuardReport] = None
    review_report: Optional[GuardReport] = None
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
