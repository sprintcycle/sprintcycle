"""Compatibility shim — use :mod:`sprintcycle.dashboard.server` for new code."""

from .server import create_app

__all__ = ["create_app"]
