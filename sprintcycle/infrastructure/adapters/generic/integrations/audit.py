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


def record_audit_event(*_args, **_kwargs) -> AuditRecord:
    return AuditRecord()
