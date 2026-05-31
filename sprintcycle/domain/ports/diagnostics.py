"""Diagnostics port definition.

This port defines the interface for diagnostic operations
that should be implemented by infrastructure adapters.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DiagnosticPort(Protocol):
    """Interface for diagnostic operations."""

    def diagnose(self, execution_id: str = "") -> Any:
        """
        Run diagnostics on the system or specific execution.

        Args:
            execution_id: Optional execution ID to diagnose

        Returns:
            Diagnostic report
        """
        ...


__all__ = [
    "DiagnosticPort",
]
