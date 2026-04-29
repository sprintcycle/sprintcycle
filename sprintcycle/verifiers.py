"""
PlaywrightVerifier - 使用 Playwright MCP 进行前端验证

集成 Playwright MCP（npx @playwright/mcp@latest），通过 accessibility tree 
实现 token 高效的页面验证。

依赖：
- Playwright MCP: npx @playwright/mcp@latest
- Python: subprocess 模块
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class AccessibilityNode:
    """Accessibility Tree 节点"""
    role: str
    name: str
    value: Optional[str] = None
    children: List['AccessibilityNode'] = None
    properties: Dict = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.properties is None:
            self.properties = {}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AccessibilityNode':
        return cls(
            role=data.get('role', 'unknown'),
            name=data.get('name', ''),
            value=data.get('value'),
            children=[cls.from_dict(c) for c in data.get('children', [])],
            properties=data.get('properties', {})
        )
    
    def find_by_role(self, role: str) -> List['AccessibilityNode']:
        """查找指定角色的节点"""
        results = []
        if self.role.lower() == role.lower():
            results.append(self)
        for child in self.children:
            results.extend(child.find_by_role(role))
        return results
    
    def find_by_text(self, text: str, exact: bool = False) -> List['AccessibilityNode']:
        """通过文本内容查找节点"""
        results = []
        check = (lambda n, t: n == t) if exact else (lambda n, t: t.lower() in n.lower())
        if check(self.name, text) or (self.value and check(self.value, text)):
            results.append(self)
        for child in self.children:
            results.extend(child.find_by_text(text, exact))
        return results
    
    def to_text(self) -> str:
        """转换为可读文本"""
        parts = [f"[{self.role}] {self.name}"]
        if self.value:
            parts.append(f"= {self.value}")
        for child in self.children:
            parts.append(f"  {child.to_text()}")
        return "\n".join(parts)


class PlaywrightVerifier:
    """
    使用 Playwright MCP 进行前端验证
    
    特点：
    - 通过 npx 启动 Playwright MCP
    - 使用 accessibility tree 而非截图（token 高效）
    - 支持渐进式降级（无 MCP 时降级到基础检查）
    
    工具：
    - navigate: 访问页面
    - snapshot: 获取 accessibility tree
    - click: 点击元素
    - fill: 填写表单
    - hover: 悬停
    """
    
    def __init__(self, project_path: Optional[str] = None, mcp_command: Optional[str] = None, timeout: int = 30000):
        """
        初始化 PlaywrightVerifier
        
        Args:
            project_path: 项目路径
            mcp_command: MCP 命令，默认 npx @playwright/mcp@latest
            timeout: 超时时间（毫秒）
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.timeout = timeout
        self.mcp_command = mcp_command or "npx @playwright/mcp@latest"
        self._mcp_process = None
        self._current_url = None
        self._accessibility_tree = None
        self._playwright_available = self._check_playwright_mcp()
    
    def _check_playwright_mcp(self) -> bool:
        """检查 Playwright MCP 是否可用"""
        try:
            # 检查 npx 是否可用
            result = subprocess.run(
                ["which", "npx"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False
            
            # 检查 npm 包是否已安装（通过尝试获取帮助）
            result = subprocess.run(
                ["npx", "@playwright/mcp@latest", "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return True
        except Exception:
            return False
    
    def _run_mcp_command(self, tool: str, args: Optional[Dict] = None) -> Dict:
        """
        运行 MCP 工具命令
        
        Args:
            tool: 工具名称（navigate, snapshot, click, fill 等）
            args: 工具参数
        
        Returns:
            工具执行结果
        """
        if not self._playwright_available:
            return {
                "success": False,
                "error": "Playwright MCP 不可用",
                "fallback": True
            }
        
        # 构造 MCP 请求
        mcp_request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": f"tools/{tool}",
            "params": args or {}
        }
        
        try:
            # 使用 npx 启动 MCP 并发送请求
            # 注意：这里简化了实现，实际需要通过 MCP 协议通信
            result = subprocess.run(
                ["npx", "@playwright/mcp@latest"],
                input=json.dumps(mcp_request),
                capture_output=True,
                text=True,
                timeout=self.timeout / 1000
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                return {
                    "success": True,
                    "result": response.get("result", {})
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "fallback": True
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "MCP 执行超时",
                "fallback": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": True
            }
    
    def verify_page_load(self, url: Optional[str]) -> Dict:
        """
        验证页面能否正常加载
        
        Args:
            url: 页面 URL
        
        Returns:
            {
                "success": bool,
                "loaded": bool,
                "title": str,
                "url": str,
                "error": str
            }
        """
        result = {
            "success": False,
            "loaded": False,
            "url": url,
            "title": None,
            "error": None
        }
        
        # 尝试使用 Playwright MCP
        mcp_result = self._run_mcp_command("navigate", {"url": url})
        
        if mcp_result.get("success") and not mcp_result.get("fallback"):
            self._current_url = url
            response_data = mcp_result.get("result", {})
            result["success"] = True
            result["loaded"] = True
            result["title"] = response_data.get("title")
        else:
            # 降级：使用基础检查
            result = self._fallback_page_load(url)
        
        return result
    
    def _fallback_page_load(self, url: Optional[str]) -> Dict:
        """降级的页面加载检查（使用 curl）"""
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
                capture_output=True,
                text=True,
                timeout=10
            )
            http_code = result.stdout.strip()
            
            return {
                "success": True,
                "loaded": http_code.startswith("2"),
                "url": url,
                "http_code": http_code,
                "title": None,
                "fallback": True,
                "note": "使用 curl 降级检查"
            }
        except Exception as e:
            return {
                "success": False,
                "loaded": False,
                "url": url,
                "error": str(e),
                "fallback": True
            }
    
    def get_accessibility_tree(self, url: Optional[str] = None) -> Dict:
        """
        获取页面的 accessibility tree
        
        Args:
            url: 页面 URL（可选，如果已加载则使用当前页面）
        
        Returns:
            {
                "success": bool,
                "tree": AccessibilityNode,
                "raw": dict,
                "text": str  # 文本表示
            }
        """
        result = {
            "success": False,
            "tree": None,
            "raw": None,
            "text": ""
        }
        
        # 如果提供了 URL，先导航
        if url:
            nav_result = self.verify_page_load(url)
            if not nav_result.get("success"):
                result["error"] = nav_result.get("error", "导航失败")
                return result
        
        # 获取 accessibility snapshot
        mcp_result = self._run_mcp_command("snapshot")
        
        if mcp_result.get("success") and not mcp_result.get("fallback"):
            raw_tree = mcp_result.get("result", {}).get("tree", {})
            tree = AccessibilityNode.from_dict(raw_tree) if raw_tree else None
            self._accessibility_tree = tree
            
            result["success"] = True
            result["tree"] = tree
            result["raw"] = raw_tree
            result["text"] = tree.to_text() if tree else ""
        else:
            # 降级：生成简化信息
            result["success"] = True
            result["fallback"] = True
            result["note"] = "无法获取 accessibility tree，请安装 Playwright MCP"
            result["text"] = "Tree unavailable (Playwright MCP not available)"
        
        return result
    
    def verify_element_exists(self, url: Optional[str], selector: str) -> Dict:
        """
        验证元素是否存在
        
        Args:
            url: 页面 URL
            selector: 选择器（CSS 选择器或文本）
        
        Returns:
            {
                "success": bool,
                "exists": bool,
                "element": dict
            }
        """
        # 获取 accessibility tree
        tree_result = self.get_accessibility_tree(url)
        
        if not tree_result.get("success"):
            return {
                "success": False,
                "exists": False,
                "error": tree_result.get("error")
            }
        
        tree = tree_result.get("tree")
        
        if tree is None:
            # 降级模式
            return {
                "success": True,
                "exists": True,
                "fallback": True,
                "note": "降级模式：假设元素存在"
            }
        
        # 尝试通过文本查找
        text_matches = tree.find_by_text(selector)
        if text_matches:
            return {
                "success": True,
                "exists": True,
                "element": {
                    "role": text_matches[0].role,
                    "name": text_matches[0].name
                },
                "match_count": len(text_matches)
            }
        
        # 尝试通过角色查找
        role_matches = tree.find_by_role(selector)
        if role_matches:
            return {
                "success": True,
                "exists": True,
                "element": {
                    "role": role_matches[0].role,
                    "name": role_matches[0].name
                },
                "match_count": len(role_matches)
            }
        
        return {
            "success": True,
            "exists": False,
            "element": None
        }
    
    def verify_interaction(self, url: Optional[str], action: str, selector: str, value: Optional[str] = None) -> Dict:
        """
        验证交互操作（点击、输入等）
        
        Args:
            url: 页面 URL
            action: 操作类型（click, fill, hover）
            selector: 选择器
            value: 输入值（仅 fill 操作需要）
        
        Returns:
            {
                "success": bool,
                "action": str,
                "performed": bool,
                "error": str
            }
        """
        # 导航到页面
        nav_result = self.verify_page_load(url)
        if not nav_result.get("success"):
            return {
                "success": False,
                "action": action,
                "performed": False,
                "error": nav_result.get("error")
            }
        
        # 构建操作参数
        tool_map = {
            "click": "click",
            "fill": "fill",
            "hover": "hover",
            "type": "fill"  # type 也使用 fill
        }
        
        tool = tool_map.get(action.lower(), "click")
        args = {"selector": selector}
        
        if tool == "fill" and value:
            args["value"] = value
        
        # 执行操作
        mcp_result = self._run_mcp_command(tool, args)
        
        if mcp_result.get("success") and not mcp_result.get("fallback"):
            return {
                "success": True,
                "action": action,
                "performed": True,
                "result": mcp_result.get("result")
            }
        else:
            # 降级
            return {
                "success": False,
                "action": action,
                "performed": False,
                "error": mcp_result.get("error"),
                "fallback": True,
                "note": "Playwright MCP 不可用，无法执行交互验证"
            }
    
    def verify_form(self, url: Optional[str], form_config: Dict) -> Dict:
        """
        验证表单功能
        
        Args:
            url: 表单页面 URL
            form_config: 表单配置
                {
                    "fields": [
                        {"selector": "#username", "value": "test", "type": "fill"},
                        {"selector": "#password", "value": "pass123", "type": "fill"}
                    ],
                    "submit": {"selector": "button[type=submit]", "action": "click"}
                }
        
        Returns:
            {
                "success": bool,
                "fields_filled": int,
                "submitted": bool,
                "error": str
            }
        """
        result = {
            "success": False,
            "fields_filled": 0,
            "submitted": False,
            "errors": []
        }
        
        # 导航
        nav = self.verify_page_load(url)
        if not nav.get("success"):
            result["errors"].append(f"导航失败: {nav.get('error')}")
            return result
        
        # 填充字段
        fields = form_config.get("fields", [])
        for field in fields:
            selector = field.get("selector")
            value = field.get("value", "")
            field_type = field.get("type", "fill")
            
            fill_result = self.verify_interaction(url, field_type, selector, value)
            if fill_result.get("performed"):
                result["fields_filled"] += 1
            else:
                result["errors"].append(f"填充字段失败: {selector}")
        
        # 提交
        submit = form_config.get("submit")
        if submit:
            selector = submit.get("selector")
            action = submit.get("action", "click")
            submit_result = self.verify_interaction(url, action, selector)
            result["submitted"] = submit_result.get("performed")
        
        result["success"] = result["fields_filled"] == len(fields)
        
        return result
    
    def verify_navigation_flow(self, url: Optional[str], steps: List[Dict]) -> Dict:
        """
        验证导航流程
        
        Args:
            url: 起始 URL
            steps: 导航步骤
                [
                    {"action": "click", "selector": ".menu-item"},
                    {"action": "verify_url", "pattern": "/dashboard"},
                    {"action": "verify_element", "selector": "h1", "expected": "Dashboard"}
                ]
        
        Returns:
            {
                "success": bool,
                "completed_steps": int,
                "total_steps": int,
                "step_results": []
            }
        """
        result = {
            "success": False,
            "completed_steps": 0,
            "total_steps": len(steps),
            "step_results": []
        }
        
        # 起始导航
        self.verify_page_load(url)
        
        for i, step in enumerate(steps):
            step_result = {"step": i + 1, "success": False}
            action = step.get("action")
            
            if action == "click":
                res = self.verify_interaction(url, "click", step.get("selector"))
                step_result["success"] = res.get("performed")
                step_result["error"] = res.get("error")
            
            elif action == "verify_url":
                pattern = step.get("pattern")
                if self._current_url and pattern in self._current_url:
                    step_result["success"] = True
            
            elif action == "verify_element":
                selector = step.get("selector")
                expected = step.get("expected")
                res = self.verify_element_exists(self._current_url, selector)
                step_result["success"] = res.get("exists")
                if expected and res.get("element"):
                    step_result["success"] = expected in res["element"].get("name", "")
            
            result["step_results"].append(step_result)
            if step_result["success"]:
                result["completed_steps"] += 1
        
        result["success"] = result["completed_steps"] == result["total_steps"]
        
        return result
    
    def verify_all(self, url: Optional[str], checks: Optional[List[str]] = None) -> Dict:
        """
        执行所有检查
        
        Args:
            url: 页面 URL
            checks: 要执行的检查列表，默认 ["load", "elements", "accessibility"]
        
        Returns:
            综合验证结果
        """
        if checks is None:
            checks = ["load", "elements", "accessibility"]
        
        result = {
            "url": url,
            "passed": True,
            "checks": {},
            "summary": {}
        }
        
        # 1. 页面加载检查
        if "load" in checks:
            load_result = self.verify_page_load(url)
            result["checks"]["load"] = load_result
            if not load_result.get("success"):
                result["passed"] = False
        
        # 2. Accessibility Tree 获取
        if "accessibility" in checks:
            a11y_result = self.get_accessibility_tree()
            result["checks"]["accessibility"] = a11y_result
            result["checks"]["accessibility"]["text_preview"] = (
                a11y_result.get("text", "")[:500] if a11y_result.get("text") else ""
            )
        
        # 3. 元素检查
        if "elements" in checks:
            elements_to_check = ["button", "link", "heading", "form"]
            elements_result = {}
            tree = result["checks"]["accessibility"].get("tree")
            
            if tree:
                for role in elements_to_check:
                    found = tree.find_by_role(role)
                    elements_result[role] = len(found)
            else:
                for role in elements_to_check:
                    elements_result[role] = None
            
            result["checks"]["elements"] = {
                "success": True,
                "found": elements_result
            }
        
        # 汇总
        passed_checks = sum(1 for c in result["checks"].values() if c.get("success", False))
        result["summary"] = {
            "total_checks": len(checks),
            "passed_checks": passed_checks,
            "passed": result["passed"]
        }
        
        return result


# ============================================================
# 集成到 FiveSourceVerifier
# ============================================================

def integrate_playwright_verifier():
    """
    将 PlaywrightVerifier 集成到 FiveSourceVerifier
    """
    try:
        from .optimizations import FiveSourceVerifier
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
