"""Default evolution adapters.

These adapters intentionally implement minimal, safe behavior.
They are designed to be extended later without changing the interfaces.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from .controller import CodeEvolutionAdapter, RequirementEvolutionAdapter
from .models import EvolutionPlan, EvolutionRequest, SandboxSpec, ValidationResult


def _run_command(command: list[str], cwd: str) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=600)
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return -1, "", str(e)


class DefaultCodeEvolutionAdapter(CodeEvolutionAdapter):
    def __init__(self, governance_runner: Any = None) -> None:
        self._governance_runner = governance_runner

    async def plan(self, request: EvolutionRequest) -> EvolutionPlan:
        return EvolutionPlan(
            request_id=request.request_id,
            target="code",
            summary="Code evolution candidate for SprintCycle framework improvement",
            actions=[
                "inspect current governance/execution boundaries",
                "apply framework changes in sandbox",
                "run tests and governance checks",
            ],
            validation_steps=["pytest", "ruff", "mypy", "import-linter", "governance"],
            metadata={"request": request.to_dict(), "context": request.context},
        )

    async def apply(self, sandbox: SandboxSpec, plan: EvolutionPlan) -> None:
        logger.info("Applying code evolution plan {} into sandbox {}", plan.request_id, sandbox.sandbox_id)
        marker = Path(sandbox.worktree_path) / ".sprintcycle" / "evolution_apply.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(
            json.dumps(
                {
                    "target": plan.target,
                    "request_id": plan.request_id,
                    "summary": plan.summary,
                    "actions": plan.actions,
                    "validation_steps": plan.validation_steps,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        plan.metadata.setdefault("apply_artifacts", {})["marker_path"] = str(marker)

    async def validate(self, sandbox: SandboxSpec, plan: EvolutionPlan) -> ValidationResult:
        exists = Path(sandbox.worktree_path).exists()
        errors: list[str] = []
        warnings: list[str] = []
        checks: list[str] = ["sandbox_exists"]
        if not exists:
            errors.append(f"sandbox not found: {sandbox.worktree_path}")
            return ValidationResult(
                success=False,
                checks=checks,
                errors=errors,
                warnings=warnings,
                metadata={"sandbox": sandbox.to_dict(), "plan": plan.to_dict()},
            )

        marker = Path(sandbox.worktree_path) / ".sprintcycle" / "evolution_apply.json"
        if marker.exists():
            checks.append("apply_marker")
        else:
            warnings.append("apply marker missing")

        for name, cmd in [
            ("pytest", ["python", "-m", "pytest", "-q"]),
            ("ruff", ["python", "-m", "ruff", "check", "."]),
            ("mypy", ["python", "-m", "mypy", "."]),
            ("import-linter", ["lint-imports", "--config", "pyproject.toml"]),
        ]:
            rc, stdout, stderr = _run_command(cmd, sandbox.worktree_path)
            checks.append(name)
            if rc != 0:
                warnings.append(f"{name} failed: {(stderr or stdout or '').strip()[:500]}")

        if self._governance_runner is not None:
            try:
                report = await self._governance_runner.run_review_gate(sandbox.worktree_path)
                checks.append("governance_review")
                findings = getattr(report, "findings", [])
                for finding in findings:
                    sev = getattr(finding, "severity", "warning")
                    msg = getattr(finding, "message", "")
                    if sev == "error":
                        errors.append(msg)
                    else:
                        warnings.append(msg)
            except Exception as e:
                warnings.append(f"governance review skipped: {e}")

        return ValidationResult(
            success=len(errors) == 0,
            checks=checks,
            errors=errors,
            warnings=warnings,
            metadata={"sandbox": sandbox.to_dict(), "plan": plan.to_dict()},
        )


class DefaultRequirementEvolutionAdapter(RequirementEvolutionAdapter):
    def __init__(self, plan_validator: Any = None, plan_generator: Any = None) -> None:
        self._plan_validator = plan_validator
        self._plan_generator = plan_generator

    async def plan(self, request: EvolutionRequest) -> EvolutionPlan:
        return EvolutionPlan(
            request_id=request.request_id,
            target="requirement",
            summary="Requirement evolution candidate for intent / release plan refinement",
            actions=[
                "refine intent",
                "rewrite release plan",
                "adjust spec and acceptance criteria",
            ],
            validation_steps=["release_plan_validation", "spec_ref_check", "governance_planning"],
            metadata={"request": request.to_dict(), "context": request.context},
        )

    async def apply(self, sandbox: SandboxSpec, plan: EvolutionPlan) -> None:
        logger.info("Applying requirement evolution plan {} into sandbox {}", plan.request_id, sandbox.sandbox_id)
        request_ctx = dict(plan.metadata.get("request", {}).get("context", {}) or {})
        release_plan = self._extract_release_plan(request_ctx)
        marker = Path(sandbox.worktree_path) / ".sprintcycle" / "evolution_apply.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(
            json.dumps(
                {
                    "target": plan.target,
                    "request_id": plan.request_id,
                    "summary": plan.summary,
                    "has_release_plan": release_plan is not None,
                    "actions": plan.actions,
                    "validation_steps": plan.validation_steps,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        plan.metadata.setdefault("apply_artifacts", {})["marker_path"] = str(marker)
        if release_plan is not None:
            plan.metadata.setdefault("apply_artifacts", {})["release_plan_present"] = True

    def _extract_release_plan(self, request_context: dict[str, Any]) -> Optional[Any]:
        rp = request_context.get("release_plan")
        if rp is not None:
            return rp
        rp_yaml = request_context.get("release_plan_yaml")
        parser = request_context.get("release_plan_parser")
        if rp_yaml is not None and parser is not None:
            try:
                return parser.parse_string(rp_yaml)
            except Exception:
                return None
        return None

    async def validate(self, sandbox: SandboxSpec, plan: EvolutionPlan) -> ValidationResult:
        exists = Path(sandbox.worktree_path).exists()
        errors: list[str] = []
        warnings: list[str] = []
        checks: list[str] = ["sandbox_exists"]
        if not exists:
            errors.append(f"sandbox not found: {sandbox.worktree_path}")
            return ValidationResult(
                success=False,
                checks=checks,
                errors=errors,
                warnings=warnings,
                metadata={"sandbox": sandbox.to_dict(), "plan": plan.to_dict()},
            )

        request_ctx = dict(plan.metadata.get("request", {}).get("context", {}) or {})
        release_plan = self._extract_release_plan(request_ctx)

        if self._plan_validator is not None:
            try:
                checks.append("release_plan_validation")
                if release_plan is not None:
                    res = self._plan_validator.validate(release_plan)
                    errors.extend(list(getattr(res, "errors", []) or []))
                    warnings.extend(list(getattr(res, "warnings", []) or []))
                else:
                    warnings.append("no release_plan found in request context; validation skipped")
            except Exception as e:
                warnings.append(f"release plan validation skipped: {e}")

        if self._plan_generator is not None and release_plan is None:
            try:
                sample = getattr(self._plan_generator, "sample_release_plan", None)
                if callable(sample):
                    checks.append("release_plan_sample_validation")
                    res = self._plan_validator.validate(sample()) if self._plan_validator is not None else None
                    if res is not None:
                        errors.extend(list(getattr(res, "errors", []) or []))
                        warnings.extend(list(getattr(res, "warnings", []) or []))
            except Exception as e:
                warnings.append(f"sample release plan validation skipped: {e}")

        return ValidationResult(
            success=len(errors) == 0,
            checks=checks,
            errors=errors,
            warnings=warnings,
            metadata={
                "sandbox": sandbox.to_dict(),
                "plan": plan.to_dict(),
                "has_release_plan": release_plan is not None,
            },
        )
