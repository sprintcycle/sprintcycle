"""
SprintCycle Verifiers 模块
包含前端验证器，包括 Playwright 验证器

v4.10 改进:
- Playwright MCP 集成 - 使用 accessibility tree 实现 token 高效验证

文件拆分说明 (Phase 2):
- verifiers/base.py: 基础类和 AccessibilityNode
- verifiers/playwright_verifier.py: Playwright 验证器
- verifiers/integration.py: FiveSourceVerifier 集成
"""

from .base import AccessibilityNode
from .playwright_verifier import PlaywrightVerifier
from .integration import integrate_playwright_verifier

# 自动集成
try:
    integrate_playwright_verifier()
except Exception as e:
    print(f"⚠️ PlaywrightVerifier 集成失败: {e}")
    print("   FiveSourceVerifier 仍将使用基础验证")

__all__ = [
    "PlaywrightVerifier",
    "AccessibilityNode",
    "integrate_playwright_verifier"
]
