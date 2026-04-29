"""
UI_VERIFY Agent - 基于 Playwright 的 UI 交互验证 Agent
"""

from .base import BaseAgent, AgentCapability
from .types import VerificationType, VerificationSeverity, VerificationResult, PageVerificationReport
from .playwright_integration import PlaywrightClient, AccessibilityNode
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import re


class UIVerifyAgent(BaseAgent):
    """
    UI 验证 Agent - 使用 Playwright 进行全链路交互验证
    
    支持的验证能力:
    - 页面加载验证
    - 元素存在性验证
    - 文本内容验证
    - 点击交互验证
    - 表单填充验证
    - 导航流程验证
    - Accessibility 树分析
    - 视觉对比（可选）
    """
    
    name = "UIVerify"
    description = "UI 交互验证 Agent，使用 Playwright 进行页面验证"
    capabilities = [
        AgentCapability.VERIFICATION,
        AgentCapability.TESTING,
        AgentCapability.BROWSER_AUTOMATION
    ]
    
    def __init__(self, base_url: str = "http://localhost:3000", headless: bool = True):
        super().__init__()
        self.base_url = base_url
        self.headless = headless
        self.client: Optional[PlaywrightClient] = None
        import os as _os
        _sprint_root = _os.environ.get("SPRINT_ROOT", str(Path(__file__).parent.parent.parent))
        self.screenshot_dir = str(Path(_sprint_root) / "logs" / "ui_screenshots")
    
    async def initialize(self):
        """初始化 Playwright 客户端"""
        if self.client is None:
            self.client = PlaywrightClient(
                base_url=self.base_url,
                headless=self.headless,
                screenshot_dir=self.screenshot_dir
            )
            await self.client.initialize()
    
    async def cleanup(self):
        """清理资源"""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行 UI 验证任务
        
        Args:
            task: 验证任务描述
            context: 额外上下文
            
        Returns:
            验证结果字典
        """
        await self.initialize()
        context = context or {}
        
        # 解析任务类型
        task_lower = task.lower()
        
        if "验证页面加载" in task or "page_load" in task_lower:
            return await self._verify_page_load(task)
        elif "检查元素" in task or "element" in task_lower:
            return await self._verify_element_exists(task)
        elif "验证文本" in task or "text_content" in task_lower:
            return await self._verify_text_content(task)
        elif "点击" in task or "click" in task_lower:
            return await self._verify_click_interaction(task)
        elif "表单" in task or "form" in task_lower:
            return await self._verify_form_fill(task)
        elif "导航" in task or "navigation" in task_lower:
            return await self._verify_navigation(task, context)
        elif "完整验证" in task or "full_verify" in task_lower:
            return await self._full_verification(context)
        else:
            # 默认执行完整验证
            return await self._full_verification(context)
    
    async def _verify_page_load(self, task: str) -> Dict[str, Any]:
        """验证页面加载"""
        url = self._extract_url(task) or self.base_url
        
        result = await self.client.verify_page_load(url)
        
        return {
            "success": result.passed,
            "type": "page_load",
            "url": url,
            "load_time_ms": result.details.get("load_time_ms", 0),
            "message": result.message,
            "screenshot": result.screenshot_path,
            "score": 100 if result.passed else 0
        }
    
    async def _verify_element_exists(self, task: str) -> Dict[str, Any]:
        """验证元素存在"""
        selector = self._extract_selector(task)
        url = self._extract_url(task) or self.base_url
        
        result = await self.client.verify_element_exists(url, selector)
        
        return {
            "success": result.passed,
            "type": "element_exists",
            "selector": selector,
            "found": result.details.get("found", False),
            "message": result.message,
            "element_info": result.details.get("element_info"),
            "score": 100 if result.passed else 0
        }
    
    async def _verify_text_content(self, task: str) -> Dict[str, Any]:
        """验证文本内容"""
        text = self._extract_text(task)
        url = self._extract_url(task) or self.base_url
        
        result = await self.client.verify_text_content(url, text)
        
        return {
            "success": result.passed,
            "type": "text_content",
            "expected_text": text,
            "found": result.details.get("found", False),
            "message": result.message,
            "score": 100 if result.passed else 0
        }
    
    async def _verify_click_interaction(self, task: str) -> Dict[str, Any]:
        """验证点击交互"""
        selector = self._extract_selector(task)
        url = self._extract_url(task) or self.base_url
        
        result = await self.client.verify_click_interaction(url, selector)
        
        return {
            "success": result.passed,
            "type": "click_interaction",
            "selector": selector,
            "clickable": result.details.get("clickable", False),
            "message": result.message,
            "screenshot_after": result.screenshot_path,
            "score": 100 if result.passed else 50
        }
    
    async def _verify_form_fill(self, task: str) -> Dict[str, Any]:
        """验证表单填充"""
        url = self._extract_url(task) or self.base_url
        form_data = self._extract_form_data(task)
        
        result = await self.client.verify_form_fill(url, form_data)
        
        return {
            "success": result.passed,
            "type": "form_fill",
            "fields_filled": result.details.get("fields_filled", 0),
            "total_fields": result.details.get("total_fields", 0),
            "message": result.message,
            "score": result.details.get("score", 0)
        }
    
    async def _verify_navigation(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """验证导航流程"""
        steps = context.get("navigation_steps", [])
        start_url = self._extract_url(task) or self.base_url
        
        result = await self.client.verify_navigation_flow(start_url, steps)
        
        return {
            "success": result.passed,
            "type": "navigation",
            "completed_steps": result.details.get("completed_steps", 0),
            "total_steps": result.details.get("total_steps", 0),
            "step_results": result.details.get("step_results", []),
            "message": result.message,
            "score": result.details.get("score", 0)
        }
    
    async def _full_verification(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整页面验证"""
        url = context.get("url", self.base_url)
        routes = context.get("routes", ["/"])
        
        all_reports = []
        
        for route in routes:
            full_url = f"{url}{route}" if route.startswith("/") else route
            report = await self._verify_single_page(full_url)
            all_reports.append(report)
        
        # 计算总分
        avg_score = sum(r.overall_score for r in all_reports) / len(all_reports) if all_reports else 0
        total_high_severity = sum(r.high_severity_count for r in all_reports)
        
        return {
            "success": avg_score >= 70 and total_high_severity == 0,
            "type": "full_verification",
            "pages_verified": len(all_reports),
            "average_score": avg_score,
            "total_high_severity_issues": total_high_severity,
            "reports": [r.to_dict() for r in all_reports],
            "summary": "\n\n".join(r.summary() for r in all_reports)
        }
    
    async def _verify_single_page(self, url: str) -> PageVerificationReport:
        """验证单个页面的多个方面"""
        verifications = []
        
        # 1. 页面加载验证
        load_result = await self.client.verify_page_load(url)
        verifications.append(load_result)
        
        # 2. 获取 accessibility tree
        a11y_result = await self.client.get_accessibility_tree(url)
        if a11y_result.passed:
            verifications.append(a11y_result)
        
        # 3. 检查关键元素
        critical_elements = ["main", "header", "nav", "[role='main']"]
        for selector in critical_elements:
            elem_result = await self.client.verify_element_exists(url, selector)
            if elem_result.passed:
                verifications.append(elem_result)
                break
        
        # 计算分数
        high_fail = sum(1 for v in verifications if not v.passed and v.severity == VerificationSeverity.HIGH)
        medium_fail = sum(1 for v in verifications if not v.passed and v.severity == VerificationSeverity.MEDIUM)
        low_fail = sum(1 for v in verifications if not v.passed and v.severity == VerificationSeverity.LOW)
        
        score = max(0, 100 - high_fail * 30 - medium_fail * 15 - low_fail * 5)
        
        return PageVerificationReport(
            url=url,
            page_title=load_result.details.get("title", ""),
            load_time_ms=load_result.details.get("load_time_ms", 0),
            verifications=verifications,
            overall_score=score
        )
    
    # ============ 辅助方法 ============
    
    def _extract_url(self, task: str) -> Optional[str]:
        """从任务中提取 URL"""
        patterns = [
            r'https?://[^\s\)]+',
            r'http://localhost:\d+[^\s\)]+',
            r'/[a-zA-Z0-9/_\-]+'
        ]
        for pattern in patterns:
            match = re.search(pattern, task)
            if match:
                return match.group()
        return None
    
    def _extract_selector(self, task: str) -> str:
        """从任务中提取 CSS 选择器"""
        match = re.search(r'["\']([^"\']+)["\']', task)
        if match:
            return match.group(1)
        
        for pattern in [
            r'["\']([^"\']+)["\']',  # 引号内
            r'([.#][\w-]+)',  # .class 或 #id
            r'\[([\w-]+)="([^"]+)"\]'  # [attr="value"]
        ]:
            match = re.search(pattern, task)
            if match:
                return match.group()
        
        return "body"
    
    def _extract_text(self, task: str) -> str:
        """从任务中提取要验证的文本"""
        match = re.search(r'["\']([^"\']+)["\']', task)
        if match:
            return match.group(1)
        return ""
    
    def _extract_form_data(self, task: str) -> Dict[str, str]:
        """从任务中提取表单数据"""
        form_data = {}
        matches = re.findall(r'(\w+):\s*["\']?([^"\'\s,]+)["\']?', task)
        for key, value in matches:
            if key.lower() not in ["url", "page"]:
                form_data[key] = value
        return form_data


# ============ 便捷函数 ============

async def create_ui_verify_agent(base_url: str = "http://localhost:3000") -> UIVerifyAgent:
    """创建 UI 验证 Agent"""
    agent = UIVerifyAgent(base_url=base_url)
    await agent.initialize()
    return agent


async def quick_verify(url: str, checks: List[str] = None) -> Dict[str, Any]:
    """快速验证页面"""
    agent = UIVerifyAgent()
    try:
        result = await agent.execute(f"完整验证 {url}")
        return result
    finally:
        await agent.cleanup()


# Re-export types for convenience
__all__ = [
    "UIVerifyAgent",
    "VerificationType",
    "VerificationResult",
    "PageVerificationReport",
    "VerificationSeverity",
    "create_ui_verify_agent",
    "quick_verify"
]
