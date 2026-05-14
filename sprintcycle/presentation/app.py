"""Compatibility shim — use :mod:`sprintcycle.presentation.server` for new code."""

from .server import create_app

__all__ = ["create_app"]
