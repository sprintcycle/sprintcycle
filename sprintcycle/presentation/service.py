"""Dashboard query helpers for assembling projection bundles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .projections import DashboardProjectionBundle


@dataclass
class DashboardQueryService:
    """Assemble dashboard-ready bundles from facade payloads."""

    def build_bundle(
        self,
        *,
        execution_id: str,
        trace: Dict[str, Any] | None = None,
        replay: Dict[str, Any] | None = None,
        suggestions: Dict[str, Any] | None = None,
        hitl: Dict[str, Any] | None = None,
        deployment: Dict[str, Any] | None = None,
        fitness: Dict[str, Any] | None = None,
    ) -> DashboardProjectionBundle:
        return DashboardProjectionBundle(
            execution_id=execution_id,
            trace=trace or {},
            replay=replay or {},
            suggestions=suggestions or {},
            hitl=hitl or {},
            deployment=deployment or {},
            fitness=fitness or {},
        )


__all__ = ["DashboardQueryService"]
