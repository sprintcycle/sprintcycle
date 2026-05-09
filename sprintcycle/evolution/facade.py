"""Public evolution facade.

This is the thin external entrypoint for sandboxed, versioned evolution.
It deliberately delegates to the controller and does not embed business rules.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .controller import EvolutionController
from .models import EvolutionRequest, RollbackOutcome


class EvolutionFacade:
    def __init__(self, controller: EvolutionController) -> None:
        self._controller = controller

    async def evolve(
        self,
        *,
        target: str,
        project_path: str,
        context: Dict[str, Any],
        mode: str = "multi_sprint",
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        request_context = dict(context or {})
        request_context.setdefault("project_path", project_path)

        request = EvolutionRequest(
            request_id=request_id or request_context.get("request_id") or "evo__auto__",
            target=target,  # type: ignore[arg-type]
            mode=mode,  # type: ignore[arg-type]
            project_path=project_path,
            context=request_context,
        )
        plan = await self._controller.intake(request)
        sandbox = await self._controller.create_sandbox(plan)

        try:
            await self._controller.apply(plan, sandbox)
        except Exception as e:
            return {
                "success": False,
                "stage": "apply",
                "error": str(e),
                "plan": plan.to_dict(),
                "sandbox": sandbox.to_dict(),
            }

        validation = await self._controller.validate(plan, sandbox)
        if not validation.success:
            return {
                "success": False,
                "stage": "validated",
                "plan": plan.to_dict(),
                "sandbox": sandbox.to_dict(),
                "validation": validation.to_dict(),
            }
        promotion = await self._controller.promote(plan, sandbox, validation)
        return {
            "success": promotion.success,
            "plan": plan.to_dict(),
            "sandbox": sandbox.to_dict(),
            "validation": validation.to_dict(),
            "promotion": promotion.to_dict(),
        }

    async def rollback(self, version_id: str) -> RollbackOutcome:
        return await self._controller.rollback(version_id)
