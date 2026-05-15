"""Authentication support.

This module reserves the integration point for future auth policies and request
identity resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class AuthContext:
    subject: str = ""
    scheme: str = ""
    scopes: List[str] = field(default_factory=list)
    tenant_id: str = ""
    project_id: str = ""


def resolve_auth_context(*_args, **_kwargs) -> AuthContext:
    return AuthContext()
