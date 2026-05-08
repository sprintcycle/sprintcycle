from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import VerificationConfig
from .model import VerificationFinding, VerificationPolicy, VerificationReport, VerificationRule
from .registry import VerificationRegistry
from .providers.arch_provider import ArchProvider
from .providers.cli_provider import CliProvider
from .providers.playwright_provider import PlaywrightProvider
from .providers.pytest_provider import PytestProvider
from .providers.security_provider import SecurityProvider
from .providers.visual_provider import VisualProvider


class VerificationEngine:
    def __init__(self, config: VerificationConfig):
        self.config = config
        self.registry = VerificationRegistry()
        self._providers = {
            "pytest": PytestProvider(),
            "playwright": PlaywrightProvider(),
            "cli": CliProvider(),
            "visual": VisualProvider(),
            "arch": ArchProvider(),
            "security": SecurityProvider(),
        }
        self._register_builtin_rules()

    def _register_builtin_rules(self) -> None:
        rules = [
            VerificationRule(rule_id="test:pytest", title="pytest 结果", gate="test", severity="warning", action="warn"),
            VerificationRule(rule_id="verify:playwright", title="Playwright 端到端", gate="verify", severity="warning", action="warn"),
            VerificationRule(rule_id="verify:cli", title="CLI 验证", gate="verify", severity="warning", action="warn"),
            VerificationRule(rule_id="verify:visual", title="视觉验证", gate="verify", severity="warning", action="warn"),
            VerificationRule(rule_id="arch:import_linter", title="import-linter", gate="arch", severity="error", action="block"),
            VerificationRule(rule_id="arch:grimp", title="grimp", gate="arch", severity="warning", action="warn"),
            VerificationRule(rule_id="arch:ruff", title="ruff", gate="arch", severity="warning", action="warn"),
            VerificationRule(rule_id="security:secrets", title="敏感信息扫描", gate="security", severity="error", action="block"),
        ]
        for rule in rules:
            self.registry.register_rule(rule)

        for rule_id in [r.rule_id for r in rules]:
            self.registry.register_check(rule_id, self._build_provider_check(rule_id))

    def _build_provider_check(self, rule_id: str):
        provider_key = rule_id.split(":", 1)[0]
        provider = self._providers.get(provider_key)

        def _check(ctx):
            if provider is None:
                return []
            return provider.run(ctx.project_root, ctx.context)

        return _check

    async def run(
        self,
        gate: str,
        project_root: Optional[str] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationReport:
        root = Path(project_root or self.config.project_root).expanduser().resolve()
        findings: List[VerificationFinding] = []
        ctx = dict(context or {})
        ctx.setdefault("project_path", str(root))

        if gate in ("test", "all") and self.config.run_test:
            findings.extend(self.registry.run_gate("test", str(root), ctx))
        if gate in ("verify", "all") and self.config.run_verify:
            findings.extend(self.registry.run_gate("verify", str(root), ctx))
        if gate in ("arch", "all") and self.config.run_arch:
            findings.extend(self.registry.run_gate("arch", str(root), ctx))
        if gate in ("security", "all") and self.config.run_security:
            findings.extend(self.registry.run_gate("security", str(root), ctx))

        return VerificationReport(
            gate=gate,
            findings=findings,
            metadata={
                "project_root": str(root),
                "policy_name": self.config.policy.name,
                "context_keys": sorted(ctx.keys()),
                "registered_rules": [r.rule_id for r in self.registry.enabled_rules_for_gate(gate)],
                "pack_paths": list(self.config.pack_paths),
            },
        )
