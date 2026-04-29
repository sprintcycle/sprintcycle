"""
verifiers.integration - Playwright 验证器集成
"""
from typing import Dict, Optional

from .playwright_verifier import PlaywrightVerifier


def integrate_playwright_verifier():
    """
    将 PlaywrightVerifier 集成到 FiveSourceVerifier
    """
    try:
        from ..optimizations import FiveSourceVerifier
    except ImportError:
        from optimizations import FiveSourceVerifier
    
    # 创建类方法包装
    _pw_verifier = None
    
    def _get_verifier(project_path: str) -> PlaywrightVerifier:
        nonlocal _pw_verifier
        if _pw_verifier is None:
            _pw_verifier = PlaywrightVerifier(project_path)
        return _pw_verifier
    
    @classmethod
    def verify_frontend_enhanced(cls, project_path: str, url: Optional[str], timeout: int = 10) -> Dict:
        """
        增强的 Frontend 验证 - 使用 Playwright MCP
        
        优先使用 Playwright MCP 获取 accessibility tree，
        降级时使用基础检查。
        """
        verifier = _get_verifier(project_path)
        result = verifier.verify_all(url, checks=["load", "accessibility"])
        
        # 兼容原有格式
        return {
            "passed": result["passed"],
            "issues": [],
            "warnings": [],
            "logs": [],
            "accessibility": result["checks"]["accessibility"],
            "summary": result["summary"]
        }
    
    @classmethod
    def verify_visual_enhanced(cls, project_path: str, url: Optional[str], baseline: Optional[str] = None) -> Dict:
        """
        增强的 Visual 验证 - 使用 accessibility tree
        
        使用 accessibility tree 替代截图对比，
        更 token 高效且更稳定。
        """
        verifier = _get_verifier(project_path)
        
        # 获取 accessibility tree
        tree_result = verifier.get_accessibility_tree(url)
        
        result = {
            "passed": True,
            "screenshot_path": None,
            "accessibility_tree": tree_result.get("text"),
            "issues": [],
            "warnings": []
        }
        
        if not tree_result.get("success"):
            result["passed"] = False
            result["issues"].append("无法获取页面结构")
        
        # 如果有 baseline，进行对比
        if baseline:
            # baseline 是之前的 accessibility tree 文本
            # 简单对比：检查关键元素是否存在
            baseline_elements = set(baseline.lower().split())
            current_elements = set(tree_result.get("text", "").lower().split())
            missing = baseline_elements - current_elements
            if len(missing) > 10:  # 超过10个词不同
                result["passed"] = False
                result["warnings"].append(f"页面结构变化较大")
        
        return result
    
    # 注入方法
    FiveSourceVerifier.verify_frontend_enhanced = verify_frontend_enhanced
    FiveSourceVerifier.verify_visual_enhanced = verify_visual_enhanced
    
    return True
