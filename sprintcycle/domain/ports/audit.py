"""Audit logging port definition.

This port defines the interface for audit logging functionality
that should be implemented by infrastructure adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol, runtime_checkable


@dataclass(slots=True)
class AuditRecord:
    request_id: str = ""
    actor: str = ""
    action: str = ""
    resource: str = ""
    outcome: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class AuditPort(Protocol):
    """Interface for audit logging operations."""

    def record_audit_event(
        self,
        request_id: str,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        **kwargs,
    ) -> AuditRecord:
        """
        Record an audit event.

        Args:
            request_id: Unique request identifier
            actor: The entity performing the action
            action: The action being performed
            resource: The resource being accessed
            outcome: The outcome of the action (success/failure)
            **kwargs: Additional metadata

        Returns:
            AuditRecord containing the recorded event
        """
        ...


def register_audit_adapter(adapter: AuditPort) -> None:
    """Register the audit adapter implementation."""
    global _audit_adapter
    _audit_adapter = adapter


def get_audit_adapter() -> AuditPort:
    """Get the registered audit adapter."""
    return _audit_adapter


_audit_adapter: AuditPort | None = None
