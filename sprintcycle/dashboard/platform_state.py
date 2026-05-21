"""Platform state management for the dashboard."""

from __future__ import annotations

from typing import Any, Dict

_platform_state: Dict[str, Any] = {}


def reset_platform_state_for_tests() -> None:
    """Reset the platform state (used in tests)."""
    _platform_state.clear()


def get_platform_state() -> Dict[str, Any]:
    """Get the current platform state."""
    return dict(_platform_state)


def update_platform_state(**kwargs: Any) -> None:
    """Update the platform state."""
    _platform_state.update(kwargs)


__all__ = [
    "reset_platform_state_for_tests",
    "get_platform_state",
    "update_platform_state",
]
