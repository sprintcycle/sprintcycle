#!/usr/bin/env python3
"""
SprintCycle Verifiers 模块 (向后兼容入口)

此文件已重构为 verifiers 包，原有内容拆分到 verifiers/ 子模块中。
请使用 `from sprintcycle.verifiers import PlaywrightVerifier`。

保持向后兼容: 旧的 import 方式仍然有效。
"""
from .verifiers import (
    PlaywrightVerifier,
    AccessibilityNode,
    integrate_playwright_verifier,
)

__all__ = [
    "PlaywrightVerifier",
    "AccessibilityNode",
    "integrate_playwright_verifier",
]
