from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ArchGuardConfig
from .invariants import (
    check_compatibility_flags,
    check_event_shape,
    check_evolution_mainline,
    check_extension_point_usage,
    check_hook_context_usage,
    check_release_plan,
    check_report_shape,
    check_spec_refs,
)
from .loader import GuardPackLoader
from sprintcycle.domain.core.governance.common.model import Finding as GuardFinding, Report as GuardReport
from .registry import GuardRegistry


class ArchGuardEngine:
    def __init__(
        self,
        config: ArchGuardConfig,
        import_linter_adapter=None,
        grimp_adapter=None,
        archguard_adapter=None,
        ruff_adapter=None,
        typecheck_adapter=None,
    ):
        self.config = config
        self.registry = GuardRegistry()
        self._import_linter = import_linter_adapter
        self._grimp = grimp_adapter
        self._archon = archguard_adapter
        self._ruff = ruff_adapter
        self._typecheck = typecheck_adapter
        self._register_builtin_rules()
        self._register_pack_rules()

    def _load_adapters(self) -> None:
        """检查适配器是否已注入，未注入则抛出错误"""
        if any([
            self._import_linter is None and self.config.use_import_linter,
            self._grimp is None and self.config.use_grimp,
            self._archon is None and self.config.use_archon,
            self._ruff is None and self.config.use_ruff,
            self._typecheck is None and self.config.use_typecheck,
        ]):
            raise RuntimeError(
                "ArchGuardEngine 缺少必需的适配器。请通过依赖注入提供以下适配器："
                "import_linter_adapter, grimp_adapter, archguard_adapter, "
                "ruff_adapter, typecheck_adapter"
            )

    def _register_builtin_rules(self) -> None:
        from sprintcycle.domain.core.governance.common.model import Rule as GuardRule

        builtin = [
            GuardRule(
                rule_id="planning:release_plan",
                title="ReleasePlan 合法性",
                severity="error",
                action="block",
                gate="planning",
            ),
            GuardRule(
                rule_id="planning:spec_refs", title="Spec 引用检查", severity="warning", action="warn", gate="planning"
            ),
            GuardRule(
                rule_id="review:hook_context", title="Hook 上下文合法性", severity="info", action="info", gate="review"
            ),
            GuardRule(
                rule_id="review:report_shape", title="报告结构合法性", severity="warning", action="warn", gate="review"
            ),
            GuardRule(
                rule_id="review:event_shape", title="事件结构合法性", severity="warning", action="warn", gate="review"
            ),
            GuardRule(
                rule_id="review:extension_point_usage",
                title="扩展点接入方式",
                severity="error",
                action="block",
                gate="review",
            ),
            GuardRule(
                rule_id="review:evolution_mainline", title="演进主线声明", severity="info", action="info", gate="review"
            ),
            GuardRule(
                rule_id="review:compatibility_flags",
                title="兼容性标识",
                severity="warning",
                action="warn",
                gate="review",
            ),
        ]
        for rule in builtin:
            self.registry.register_rule(rule)

        # 默认规则检查器
        self.registry.register_check("planning:release_plan", self._check_planning_release_plan)
        self.registry.register_check("planning:spec_refs", self._check_planning_spec_refs)
        self.registry.register_check("review:hook_context", self._check_review_hook_context)
        self.registry.register_check("review:report_shape", self._check_review_report_shape)
        self.registry.register_check("review:event_shape", self._check_review_event_shape)
        self.registry.register_check("review:extension_point_usage", self._check_review_extension_point_usage)
        self.registry.register_check("review:evolution_mainline", self._check_review_evolution_mainline)
        self.registry.register_check("review:compatibility_flags", self._check_review_compatibility_flags)

    def _register_pack_rules(self) -> None:
        loader = GuardPackLoader(self.config.pack_paths)
        for rule in loader.load_rules():
            self.registry.register_rule(rule)

    def _check_planning_release_plan(self, ctx) -> List[GuardFinding]:
        root = Path(ctx.project_root)
        release_plan = ctx.context.get("release_plan")
        if release_plan is None:
            return []
        return self._to_findings(check_release_plan(release_plan)) + self._to_findings(
            check_spec_refs(root, release_plan)
        )

    def _check_planning_spec_refs(self, ctx) -> List[GuardFinding]:
        return []

    def _check_review_hook_context(self, ctx) -> List[GuardFinding]:
        return self._to_findings(check_hook_context_usage(ctx.context))

    def _check_review_report_shape(self, ctx) -> List[GuardFinding]:
        return self._to_findings(
            check_report_shape(ctx.context.get("governance_review_report") if isinstance(ctx.context, dict) else None)
        )

    def _check_review_event_shape(self, ctx) -> List[GuardFinding]:
        return self._to_findings(check_event_shape(ctx.context.get("event") if isinstance(ctx.context, dict) else None))

    def _check_review_extension_point_usage(self, ctx) -> List[GuardFinding]:
        return self._to_findings(check_extension_point_usage(ctx.context))

    def _check_review_evolution_mainline(self, ctx) -> List[GuardFinding]:
        return self._to_findings(check_evolution_mainline(ctx.context))

    def _check_review_compatibility_flags(self, ctx) -> List[GuardFinding]:
        return self._to_findings(check_compatibility_flags(ctx.context))

    async def run_planning_gate(
        self,
        project_root: str,
        *,
        release_plan: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardReport:
        findings: List[GuardFinding] = []
        root = Path(project_root)
        self._load_adapters()

        findings.extend(self._to_findings(check_release_plan(release_plan)))
        findings.extend(self._to_findings(check_spec_refs(root, release_plan)))
        findings.extend(self._to_findings(check_hook_context_usage(context)))
        findings.extend(
            self.registry.run_gate("planning", project_root, {"context": context or {}, "release_plan": release_plan})
        )

        if self.config.use_grimp:
            findings.extend(self._grimp.run(project_root))
        if self.config.use_archon:
            findings.extend(self._archon.run(project_root))

        return GuardReport(
            gate="planning",
            findings=findings,
            metadata={
                "project_root": project_root,
                "policy_name": self.config.policy.name,
                "context_keys": sorted(list((context or {}).keys())),
                "registered_rules": [r.rule_id for r in self.registry.enabled_rules_for_gate("planning")],
                "pack_paths": list(self.config.pack_paths),
            },
        )

    async def run_review_gate(
        self,
        project_root: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardReport:
        findings: List[GuardFinding] = []
        self._load_adapters()

        if self.config.use_import_linter:
            findings.extend(self._import_linter.run(project_root))
        if self.config.use_grimp:
            findings.extend(self._grimp.run(project_root))
        if self.config.use_archon:
            findings.extend(self._archon.run(project_root))
        if self.config.use_ruff:
            findings.extend(self._ruff.run(project_root))
        if self.config.use_typecheck:
            findings.extend(self._typecheck.run(project_root))

        findings.extend(self._to_findings(check_hook_context_usage(context)))
        findings.extend(
            self._to_findings(
                check_report_shape(context.get("governance_review_report") if isinstance(context, dict) else None)
            )
        )
        findings.extend(
            self._to_findings(check_event_shape(context.get("event") if isinstance(context, dict) else None))
        )
        findings.extend(self._to_findings(check_extension_point_usage(context)))
        findings.extend(self._to_findings(check_evolution_mainline(context)))
        findings.extend(self._to_findings(check_compatibility_flags(context)))
        findings.extend(self.registry.run_gate("review", project_root, {"context": context or {}}))

        return GuardReport(
            gate="review",
            findings=findings,
            metadata={
                "project_root": project_root,
                "policy_name": self.config.policy.name,
                "context_keys": sorted(list((context or {}).keys())),
                "registered_rules": [r.rule_id for r in self.registry.enabled_rules_for_gate("review")],
                "pack_paths": list(self.config.pack_paths),
            },
        )

    def _to_findings(self, violations: List[Any]) -> List[GuardFinding]:
        out: List[GuardFinding] = []
        for v in violations:
            out.append(
                GuardFinding(
                    rule_id=v.rule_id,
                    severity=v.severity,
                    message=v.message,
                    location=dict(getattr(v, "location", {}) or {}),
                )
            )
        return out
