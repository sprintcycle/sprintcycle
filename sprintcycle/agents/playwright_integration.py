"""
Playwright Integration - Playwright Python 客户端封装
"""

import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from loguru import logger

from .types import VerificationType, VerificationSeverity, VerificationResult


@dataclass
class AccessibilityNode:
    """Accessibility Tree 节点"""
    role: str
    name: str
    value: Optional[str] = None
    children: List['AccessibilityNode'] = None
    properties: Dict = None
    level: int = 0
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.properties is None:
            self.properties = {}
    
    @classmethod
    def from_dict(cls, data: Dict, level: int = 0) -> 'AccessibilityNode':
        """从字典创建节点"""
        return cls(
            role=data.get('role', 'unknown'),
            name=data.get('name', ''),
            value=data.get('value'),
            children=[cls.from_dict(c, level + 1) for c in data.get('children', [])],
            properties=data.get('properties', {}),
            level=level
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
    
    def to_text(self, indent: int = 2) -> str:
        """转换为可读文本"""
        prefix = " " * (self.level * indent)
        parts = [f"{prefix}[{self.role}] {self.name}"]
        if self.value:
            parts.append(f"{prefix}  = {self.value}")
        for child in self.children:
            parts.append(child.to_text(indent))
        return "\n".join(parts)


class PlaywrightClient:
    """
    Playwright Python 客户端封装
    
    提供:
    - 页面加载验证
    - 元素存在性验证
    - 文本内容验证
    - 点击交互验证
    - 表单填充验证
    - Accessibility Tree 获取
    - 截图功能
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:3000",
        headless: bool = True,
        screenshot_dir: str = "/root/sprintcycle/logs/ui_screenshots",
        timeout: int = 30000
    ):
        self.base_url = base_url
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.timeout = timeout
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        
        # 确保截图目录存在
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """初始化 Playwright"""
        if self._browser is not None:
            return
        
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            self._page = await self._context.new_page()
            
            # 设置默认超时
            self._page.set_default_timeout(self.timeout)
            
            logger.info("Playwright 客户端初始化成功")
        except ImportError:
            logger.warning("Playwright 未安装，使用降级验证模式")
            self._browser = None
    
    async def close(self):
        """关闭 Playwright"""
        if self._page:
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    async def _ensure_page(self):
        """确保页面可用"""
        if self._page is None:
            await self.initialize()
    
    def _generate_screenshot_path(self, name: str) -> str:
        """生成截图路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(self.screenshot_dir / f"{name}_{timestamp}.png")
    
    # ============ 核心验证方法 ============
    
    async def verify_page_load(self, url: str) -> VerificationResult:
        """验证页面能否正常加载"""
        await self._ensure_page()
        
        start_time = datetime.now()
        screenshot_path = None
        
        try:
            # 构建完整 URL
            full_url = url if url.startswith("http") else f"{self.base_url}{url}"
            
            # 导航并等待网络空闲
            response = await self._page.goto(full_url, wait_until="networkidle")
            
            load_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # 获取页面标题
            title = await self._page.title()
            
            # 截图
            screenshot_path = self._generate_screenshot_path("page_load")
            await self._page.screenshot(path=screenshot_path)
            
            # 检查响应状态
            if response and response.ok:
                return VerificationResult(
                    verification_type=VerificationType.PAGE_LOAD,
                    passed=True,
                    message=f"页面加载成功: {title}",
                    details={
                        "url": full_url,
                        "title": title,
                        "load_time_ms": load_time_ms,
                        "status_code": response.status
                    },
                    screenshot_path=screenshot_path
                )
            else:
                return VerificationResult(
                    verification_type=VerificationType.PAGE_LOAD,
                    passed=False,
                    message=f"页面加载失败: HTTP {response.status if response else 'No Response'}",
                    details={
                        "url": full_url,
                        "load_time_ms": load_time_ms,
                        "status_code": response.status if response else None
                    },
                    severity=VerificationSeverity.HIGH,
                    screenshot_path=screenshot_path,
                    suggestions=["检查服务器是否正常运行", "验证 URL 是否正确"]
                )
                
        except Exception as e:
            load_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            return VerificationResult(
                verification_type=VerificationType.PAGE_LOAD,
                passed=False,
                message=f"页面加载异常: {str(e)}",
                details={"url": url, "load_time_ms": load_time_ms},
                severity=VerificationSeverity.HIGH,
                screenshot_path=screenshot_path,
                suggestions=["检查网络连接", "验证页面是否可访问", "确认服务是否启动"]
            )
    
    async def verify_element_exists(
        self, 
        url: str, 
        selector: str
    ) -> VerificationResult:
        """验证元素是否存在"""
        await self._ensure_page()
        
        # 先加载页面
        await self.verify_page_load(url)
        
        try:
            element = await self._page.query_selector(selector)
            
            if element:
                # 获取元素信息
                box = await element.bounding_box()
                tag = await element.evaluate('el => el.tagName')
                text = await element.inner_text()
                
                return VerificationResult(
                    verification_type=VerificationType.ELEMENT_EXISTS,
                    passed=True,
                    message=f"元素存在: {selector}",
                    details={
                        "selector": selector,
                        "found": True,
                        "tag": tag,
                        "text": text[:100] if text else None,
                        "bounding_box": box
                    }
                )
            else:
                return VerificationResult(
                    verification_type=VerificationType.ELEMENT_EXISTS,
                    passed=False,
                    message=f"元素不存在: {selector}",
                    details={"selector": selector, "found": False},
                    severity=VerificationSeverity.MEDIUM,
                    suggestions=[f"检查选择器是否正确: {selector}", "确认元素是否在 DOM 中"]
                )
                
        except Exception as e:
            return VerificationResult(
                verification_type=VerificationType.ELEMENT_EXISTS,
                passed=False,
                message=f"元素检查异常: {str(e)}",
                details={"selector": selector},
                severity=VerificationSeverity.MEDIUM,
                suggestions=["检查选择器语法", "验证页面是否完全加载"]
            )
    
    async def verify_text_content(
        self, 
        url: str, 
        expected_text: str,
        selector: str = None
    ) -> VerificationResult:
        """验证文本内容是否存在"""
        await self._ensure_page()
        
        # 先加载页面
        await self.verify_page_load(url)
        
        try:
            found = False
            found_in = None
            
            if selector:
                # 在指定元素中查找
                element = await self._page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    found = expected_text.lower() in text.lower()
                    found_in = selector
            else:
                # 在整个页面中查找
                content = await self._page.content()
                found = expected_text.lower() in content.lower()
                found_in = "page"
            
            if found:
                return VerificationResult(
                    verification_type=VerificationType.TEXT_CONTENT,
                    passed=True,
                    message=f"文本存在: {expected_text}",
                    details={"expected_text": expected_text, "found": True, "found_in": found_in}
                )
            else:
                return VerificationResult(
                    verification_type=VerificationType.TEXT_CONTENT,
                    passed=False,
                    message=f"文本不存在: {expected_text}",
                    details={"expected_text": expected_text, "found": False, "searched_in": selector or "page"},
                    severity=VerificationSeverity.MEDIUM,
                    suggestions=[f"验证文本是否正确: {expected_text}", "检查文本是否在正确的位置"]
                )
                
        except Exception as e:
            return VerificationResult(
                verification_type=VerificationType.TEXT_CONTENT,
                passed=False,
                message=f"文本检查异常: {str(e)}",
                details={"expected_text": expected_text},
                severity=VerificationSeverity.LOW
            )
    
    async def verify_click_interaction(
        self, 
        url: str, 
        selector: str,
        expected_change: str = None
    ) -> VerificationResult:
        """验证点击交互"""
        await self._ensure_page()
        
        # 先加载页面
        await self.verify_page_load(url)
        
        screenshot_after = None
        
        try:
            element = await self._page.query_selector(selector)
            
            if not element:
                return VerificationResult(
                    verification_type=VerificationType.CLICK_INTERACTION,
                    passed=False,
                    message=f"点击目标不存在: {selector}",
                    details={"selector": selector},
                    severity=VerificationSeverity.HIGH,
                    suggestions=["检查选择器是否正确"]
                )
            
            # 检查元素是否可点击
            is_disabled = await element.evaluate('el => el.disabled || el.getAttribute("aria-disabled") === "true"')
            if is_disabled:
                return VerificationResult(
                    verification_type=VerificationType.CLICK_INTERACTION,
                    passed=False,
                    message=f"元素被禁用: {selector}",
                    details={"selector": selector, "clickable": False, "disabled": True},
                    severity=VerificationSeverity.HIGH,
                    suggestions=["启用元素或检查业务逻辑"]
                )
            
            # 执行点击
            await element.click()
            await asyncio.sleep(0.5)  # 等待动画/响应
            
            # 截图
            screenshot_after = self._generate_screenshot_path("after_click")
            await self._page.screenshot(path=screenshot_after)
            
            # 检查 URL 变化
            url_after = self._page.url
            
            if expected_change:
                passed = expected_change in url_after
                return VerificationResult(
                    verification_type=VerificationType.CLICK_INTERACTION,
                    passed=passed,
                    message="点击成功" if passed else f"点击后未跳转到: {expected_change}",
                    details={
                        "selector": selector,
                        "clickable": True,
                        "url_after": url_after,
                        "expected_change": expected_change
                    },
                    screenshot_path=screenshot_after,
                    suggestions=[] if passed else [f"检查导航逻辑，预期跳转到: {expected_change}"]
                )
            
            return VerificationResult(
                verification_type=VerificationType.CLICK_INTERACTION,
                passed=True,
                message="点击交互成功",
                details={
                    "selector": selector,
                    "clickable": True,
                    "url_after": url_after
                },
                screenshot_path=screenshot_after
            )
            
        except Exception as e:
            return VerificationResult(
                verification_type=VerificationType.CLICK_INTERACTION,
                passed=False,
                message=f"点击交互异常: {str(e)}",
                details={"selector": selector},
                severity=VerificationSeverity.HIGH,
                screenshot_path=screenshot_after,
                suggestions=["检查元素是否可交互", "尝试使用 force: True 参数"]
            )
    
    async def verify_form_fill(
        self, 
        url: str, 
        form_data: Dict[str, str]
    ) -> VerificationResult:
        """验证表单填充"""
        await self._ensure_page()
        
        # 先加载页面
        await self.verify_page_load(url)
        
        try:
            filled_count = 0
            total_fields = len(form_data)
            errors = []
            
            for field_name, value in form_data.items():
                # 尝试多种选择器
                selectors = [
                    f"[name='{field_name}']",
                    f"#{field_name}",
                    f"input[placeholder*='{field_name}']",
                    f"input[id*='{field_name}']"
                ]
                
                element = None
                for selector in selectors:
                    try:
                        el = await self._page.query_selector(selector)
                        if el:
                            element = el
                            break
                    except Exception:
                        continue
                
                if element:
                    try:
                        input_type = await element.get_attribute("type")
                        
                        # 处理不同类型的输入
                        if input_type == "checkbox":
                            if value.lower() in ["true", "1", "yes"]:
                                await element.check()
                            else:
                                await element.uncheck()
                        elif input_type == "radio":
                            await element.click()
                        elif input_type == "file":
                            await element.set_input_files(value)
                        else:
                            await element.fill(value)
                        
                        filled_count += 1
                    except Exception as e:
                        errors.append(f"{field_name}: {str(e)}")
                else:
                    errors.append(f"{field_name}: 未找到元素")
            
            success = filled_count == total_fields
            score = (filled_count / total_fields * 100) if total_fields > 0 else 0
            
            return VerificationResult(
                verification_type=VerificationType.FORM_FILL,
                passed=success,
                message=f"表单填充: {filled_count}/{total_fields}",
                details={
                    "fields_filled": filled_count,
                    "total_fields": total_fields,
                    "errors": errors,
                    "score": score
                },
                severity=VerificationSeverity.MEDIUM if not success else VerificationSeverity.LOW,
                suggestions=errors if errors else []
            )
            
        except Exception as e:
            return VerificationResult(
                verification_type=VerificationType.FORM_FILL,
                passed=False,
                message=f"表单填充异常: {str(e)}",
                details={"form_data": form_data},
                severity=VerificationSeverity.MEDIUM,
                suggestions=["检查表单结构", "验证选择器"]
            )
    
    async def get_accessibility_tree(self, url: str) -> VerificationResult:
        """获取 Accessibility Tree"""
        await self._ensure_page()
        
        # 先加载页面
        await self.verify_page_load(url)
        
        try:
            # 使用 Playwright 的 accessibility API
            snapshot = await self._page.accessibility.snapshot()
            
            if snapshot:
                root = AccessibilityNode.from_dict(snapshot)
                
                # 统计关键元素
                buttons = root.find_by_role("button")
                links = root.find_by_role("link")
                headings = root.find_by_role("heading")
                inputs = root.find_by_role("textbox")
                
                return VerificationResult(
                    verification_type=VerificationType.ACCESSIBILITY,
                    passed=True,
                    message=f"获取 Accessibility Tree 成功",
                    details={
                        "buttons": len(buttons),
                        "links": len(links),
                        "headings": len(headings),
                        "inputs": len(inputs),
                        "tree_text": root.to_text()[:2000]  # 限制长度
                    }
                )
            else:
                return VerificationResult(
                    verification_type=VerificationType.ACCESSIBILITY,
                    passed=False,
                    message="无法获取 Accessibility Tree",
                    severity=VerificationSeverity.LOW,
                    suggestions=["检查页面是否正确渲染"]
                )
                
        except Exception as e:
            return VerificationResult(
                verification_type=VerificationType.ACCESSIBILITY,
                passed=False,
                message=f"Accessibility Tree 获取异常: {str(e)}",
                severity=VerificationSeverity.LOW
            )
    
    async def verify_navigation_flow(
        self, 
        start_url: str, 
        steps: List[Dict[str, Any]]
    ) -> VerificationResult:
        """验证导航流程"""
        await self._ensure_page()
        
        completed = 0
        step_results = []
        
        try:
            # 起始导航
            await self.verify_page_load(start_url)
            completed = 1
            step_results.append({"step": 1, "action": "navigate", "success": True})
            
            for i, step in enumerate(steps):
                step_num = i + 2
                action = step.get("action")
                
                if action == "click":
                    selector = step.get("selector")
                    expected_url = step.get("expected_url")
                    
                    result = await self.verify_click_interaction(start_url, selector, expected_url)
                    step_results.append({
                        "step": step_num,
                        "action": "click",
                        "selector": selector,
                        "success": result.passed
                    })
                    if result.passed:
                        completed += 1
                
                elif action == "wait":
                    wait_time = step.get("time", 1)
                    await asyncio.sleep(wait_time)
                    completed += 1
                    step_results.append({
                        "step": step_num,
                        "action": "wait",
                        "success": True
                    })
                
                elif action == "verify_text":
                    text = step.get("text")
                    result = await self.verify_text_content(start_url, text)
                    step_results.append({
                        "step": step_num,
                        "action": "verify_text",
                        "text": text,
                        "success": result.passed
                    })
                    if result.passed:
                        completed += 1
            
            total_steps = len(steps) + 1
            success = completed == total_steps
            score = (completed / total_steps * 100) if total_steps > 0 else 0
            
            return VerificationResult(
                verification_type=VerificationType.NAVIGATION,
                passed=success,
                message=f"导航流程: {completed}/{total_steps}",
                details={
                    "completed_steps": completed,
                    "total_steps": total_steps,
                    "step_results": step_results,
                    "score": score
                },
                severity=VerificationSeverity.HIGH if completed < total_steps / 2 else VerificationSeverity.MEDIUM
            )
            
        except Exception as e:
            return VerificationResult(
                verification_type=VerificationType.NAVIGATION,
                passed=False,
                message=f"导航流程异常: {str(e)}",
                details={"step_results": step_results},
                severity=VerificationSeverity.HIGH
            )
