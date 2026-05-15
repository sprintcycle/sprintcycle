"""Request context for internal/public API calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class RequestContext:
    request_id: str = ""
    trace_id: str = ""
    caller: str = ""
    project_path: str = ""
    tenant_id: str = ""
    client_type: str = ""
    scopes: List[str] = field(default_factory=list)
