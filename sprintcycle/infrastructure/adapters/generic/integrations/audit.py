"""Audit support.

This module reserves the integration point for request auditing and event
logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(slots=True)
class AuditRecord:
    request_id: str = ""
    actor: str = ""
    action: str = ""
    resource: str = ""
    outcome: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditAdapter:
    """Infrastructure adapter for audit logging."""

    def record_audit_event(
        self,
        request_id: str,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        **kwargs,
    ) -> AuditRecord:
        """Record an audit event."""
        return AuditRecord(
            request_id=request_id,
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            metadata=kwargs,
        )


def record_audit_event(*_args, **_kwargs) -> AuditRecord:
    """Legacy function for backward compatibility."""
    return AuditRecord()
