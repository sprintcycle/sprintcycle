"""
SprintCycle Dashboard — Web 可视化界面

FastAPI + SSE 实时推送，调用 SprintCycle API。
"""

from .app import create_app

__all__ = ["create_app"]
