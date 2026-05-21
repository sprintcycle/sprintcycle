"""Versioned evolution promotion with registry persistence."""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional


def _run_async(coro: Any) -> Any:
    """Run a coroutine safely, handling both sync and async contexts."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        result: list[Any] = [None]

        def _target() -> None:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result[0] = new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
            asyncio.set_event_loop(loop)

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join()
        return result[0]

    return loop.run_until_complete(coro)


from sprintcycle.domain.evolution.models import VersionArtifact
from sprintcycle.application.services.lifecycle_evolution_service import LifecycleEvolutionService


@dataclass
class EvolutionPromotionService:
    lifecycle_evolution: LifecycleEvolutionService
    evolution_registry: Any

    def promote_versioned_evolution(
        self,
        execution_id: str,
        *,
        project_path: str = "",
        suggestion: Optional[Dict[str, Any]] = None,
        governance: Optional[Dict[str, Any]] = None,
        lifecycle_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if lifecycle_contract is not None and not lifecycle_contract.get("validation_refs", {}).get("final_snapshot"):
            return {
                "success": False,
                "error": "promotion requires final snapshot contract",
                "data": {
                    "blocked": True,
                    "reason": "missing_final_snapshot",
                    "contract": lifecycle_contract,
                },
            }
        promotion_result = self.lifecycle_evolution.promote(
            execution_id, project_path=project_path, suggestion=suggestion, governance=governance
        )
        if not isinstance(promotion_result, dict) or not promotion_result.get("success", False):
            return promotion_result
        data = promotion_result.get("data", {}) if isinstance(promotion_result, dict) else {}
        contract = dict(data.get("contract") or lifecycle_contract)
        version = dict(data.get("version") or {})
        version_id = str(version.get("version_id") or f"version_{execution_id}")
        final_snapshot = dict(contract.get("final_snapshot") or contract)
        artifact = VersionArtifact(
            version_id=version_id,
            target="requirement",
            commit_hash=str(contract.get("metadata", {}).get("commit_hash") or "") or None,
            tag=str(contract.get("metadata", {}).get("tag") or "") or None,
            branch=str(contract.get("metadata", {}).get("branch") or "") or None,
            manifest_path=str(contract.get("metadata", {}).get("manifest_path") or "") or None,
            sandbox_id=str(contract.get("correlation", {}).get("runtime_id") or "") or None,
            source_suggestion_id=str(contract.get("correlation", {}).get("suggestion_id") or "") or None,
            source_evolution_request_id=str(contract.get("correlation", {}).get("version_id") or execution_id),
            rollback_to=str(contract.get("validation_refs", {}).get("rollback_to") or "") or None,
            promotion_guard={
                "final_snapshot": True,
                "promotion": data.get("promotion", {}),
                "final_snapshot_contract": final_snapshot,
            },
            metadata={
                "source_execution_id": execution_id,
                "lifecycle_contract": contract,
                "final_snapshot": final_snapshot,
            },
        )
        _run_async(self.evolution_registry.register(artifact))
        try:
            _run_async(self.evolution_registry.set_active(version_id))
        except Exception:
            pass
        return {
            **promotion_result,
            "data": {**data, "version_artifact": artifact.to_dict()},
        }


__all__ = ["EvolutionPromotionService"]
