"""
SprintCycle UI 验证器
使用 Playwright 进行全链路交互验证
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

@dataclass
class InteractionIssue:
    """交互问题"""
    page: str
    element: str
    issue_type: str  # animation, feedback, transition, validation, loading
    description: str
    severity: str  # high, medium, low
    screenshot: Optional[str] = None
    fix_suggestion: str = ""

@dataclass
class UIVerificationResult:
    """UI验证结果"""
    total_checks: int
    passed: int
    failed: int
    issues: List[InteractionIssue]
    screenshots: List[str]
    score: float  # 0-100

class UIVerifier:
    """UI交互验证器"""
    
    # 交互细节检查项
    INTERACTION_CHECKS = {
        "animation": [
            "页面加载动画是否流畅",
            "按钮点击是否有反馈动画",
            "页面切换是否有过渡效果",
            "列表滚动是否平滑"
        ],
        "feedback": [
            "按钮点击是否有视觉反馈",
            "表单提交是否有加载状态",
            "错误提示是否友好",
            "成功操作是否有确认反馈"
        ],
        "transition": [
            "路由切换是否有过渡动画",
            "弹窗显示/隐藏是否平滑",
            "下拉菜单展开是否流畅",
            "折叠面板动画是否自然"
        ],
        "validation": [
            "表单验证是否实时",
            "错误提示是否清晰",
            "必填字段标识是否明显",
            "验证反馈是否及时"
        ],
        "loading": [
            "是否有骨架屏加载",
            "加载动画是否优雅",
            "加载超时是否有提示",
            "数据加载失败是否有重试"
        ],
        "touch": [
            "触摸区域是否足够大",
            "滑动操作是否流畅",
            "长按是否有反馈",
            "双击是否正确响应"
        ]
    }
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.screenshot_dir = "/root/sprintcycle/logs/ui_screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def verify_page_interactions(self, page_path: str) -> List[InteractionIssue]:
        """验证页面交互细节"""
        from playwright.async_api import async_playwright
        
        issues = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 375, "height": 812}  # iPhone X 尺寸
            )
            page = await context.new_page()
            
            try:
                # 访问页面
                url = f"{self.base_url}{page_path}"
                await page.goto(url, wait_until="networkidle", timeout=10000)
                
                # 截图
                screenshot_path = f"{self.screenshot_dir}/{page_path.replace('/', '_')}.png"
                await page.screenshot(path=screenshot_path)
                
                # 1. 检查加载状态
                loading_issues = await self._check_loading_state(page, page_path)
                issues.extend(loading_issues)
                
                # 2. 检查按钮交互
                button_issues = await self._check_button_interactions(page, page_path)
                issues.extend(button_issues)
                
                # 3. 检查表单验证
                form_issues = await self._check_form_validation(page, page_path)
                issues.extend(form_issues)
                
                # 4. 检查动画效果
                animation_issues = await self._check_animations(page, page_path)
                issues.extend(animation_issues)
                
            except Exception as e:
                logger.error(f"页面验证失败: {page_path} - {e}")
                issues.append(InteractionIssue(
                    page=page_path,
                    element="page",
                    issue_type="loading",
                    description=f"页面加载失败: {str(e)}",
                    severity="high"
                ))
            
            finally:
                await browser.close()
        
        return issues
    
    async def _check_loading_state(self, page, page_path: str) -> List[InteractionIssue]:
        """检查加载状态"""
        issues = []
        
        # 检查骨架屏
        skeleton = await page.query_selector('[class*="skeleton"], [class*="loading"]')
        if not skeleton:
            issues.append(InteractionIssue(
                page=page_path,
                element="loading",
                issue_type="loading",
                description="缺少骨架屏或加载动画",
                severity="medium",
                fix_suggestion="添加骨架屏组件提升加载体验"
            ))
        
        return issues
    
    async def _check_button_interactions(self, page, page_path: str) -> List[InteractionIssue]:
        """检查按钮交互"""
        issues = []
        
        buttons = await page.query_selector_all('button, [role="button"], .btn')
        
        for i, button in enumerate(buttons[:3]):  # 只检查前3个按钮
            try:
                # 检查按钮尺寸
                box = await button.bounding_box()
                if box and box['height'] < 44:  # iOS 最小触摸尺寸 44px
                    issues.append(InteractionIssue(
                        page=page_path,
                        element=f"button-{i}",
                        issue_type="touch",
                        description=f"按钮高度 {box['height']:.0f}px 小于推荐值 44px",
                        severity="medium",
                        fix_suggestion="增加按钮高度或内边距"
                    ))
                
                # 检查点击反馈
                styles = await button.evaluate('el => getComputedStyle(el)')
                transition = styles.get('transition', '')
                if 'none' in transition or not transition:
                    issues.append(InteractionIssue(
                        page=page_path,
                        element=f"button-{i}",
                        issue_type="animation",
                        description="按钮缺少过渡动画",
                        severity="low",
                        fix_suggestion="添加 transition: all 0.3s ease"
                    ))
                    
            except Exception:
                pass
        
        return issues
    
    async def _check_form_validation(self, page, page_path: str) -> List[InteractionIssue]:
        """检查表单验证"""
        issues = []
        
        inputs = await page.query_selector_all('input, textarea')
        
        if inputs:
            for i, input_el in enumerate(inputs[:2]):  # 检查前2个输入框
                try:
                    # 模拟输入
                    await input_el.fill("test")
                    await asyncio.sleep(0.5)
                    
                    # 检查是否有验证提示
                    error_msg = await page.query_selector('.error, .invalid, [class*="error"]')
                    if not error_msg:
                        # 清空输入，检查必填验证
                        await input_el.fill("")
                        await input_el.evaluate('el => el.blur()')
                        await asyncio.sleep(0.3)
                        
                except Exception:
                    pass
        
        return issues
    
    async def _check_animations(self, page, page_path: str) -> List[InteractionIssue]:
        """检查动画效果"""
        issues = []
        
        # 检查全局过渡设置
        body_styles = await page.evaluate('() => getComputedStyle(document.body)')
        
        # 检查过渡效果
        transitions = await page.query_selector_all('[class*="transition"], [class*="animate"]')
        
        if len(transitions) < 3:  # 页面应该有一些过渡元素
            issues.append(InteractionIssue(
                page=page_path,
                element="global",
                issue_type="transition",
                description="页面缺少过渡动画元素",
                severity="low",
                fix_suggestion="添加 CSS transition 或 Vue transition 组件"
            ))
        
        return issues
    
    async def run_full_verification(self, routes: List[str] = None) -> UIVerificationResult:
        """运行完整UI验证"""
        if routes is None:
            routes = ["/", "/login", "/profile"]
        
        all_issues = []
        screenshots = []
        
        for route in routes:
            logger.info(f"验证页面: {route}")
            issues = await self.verify_page_interactions(route)
            all_issues.extend(issues)
        
        # 计算分数
        total_checks = sum(len(checks) for checks in self.INTERACTION_CHECKS.values()) * len(routes)
        high_issues = len([i for i in all_issues if i.severity == "high"])
        medium_issues = len([i for i in all_issues if i.severity == "medium"])
        low_issues = len([i for i in all_issues if i.severity == "low"])
        
        # 扣分计算
        score = max(0, 100 - high_issues * 20 - medium_issues * 10 - low_issues * 5)
        
        return UIVerificationResult(
            total_checks=total_checks,
            passed=total_checks - len(all_issues),
            failed=len(all_issues),
            issues=all_issues,
            screenshots=screenshots,
            score=score
        )
    
    def generate_fix_prd(self, issues: List[InteractionIssue]) -> Dict:
        """生成修复 PRD"""
        sprints = []
        
        # 按页面分组
        by_page = {}
        for issue in issues:
            if issue.page not in by_page:
                by_page[issue.page] = []
            by_page[issue.page].append(issue)
        
        # 为每个页面生成修复 Sprint
        for page, page_issues in by_page.items():
            tasks = []
            for issue in page_issues:
                tasks.append({
                    "task": f"修复 {issue.element}: {issue.description}",
                    "fix": issue.fix_suggestion
                })
            
            sprints.append({
                "name": f"修复 {page} 交互问题",
                "tasks": tasks,
                "agent": "coder"
            })
        
        return {
            "project": {"name": "UI交互优化"},
            "sprints": sprints
        }

# 便捷函数
async def verify_ui_interactions(base_url: str = "http://localhost:3000", routes: List[str] = None) -> UIVerificationResult:
    """验证UI交互细节"""
    verifier = UIVerifier(base_url)
    return await verifier.run_full_verification(routes)

if __name__ == "__main__":
    result = asyncio.run(verify_ui_interactions())
    print(f"\nUI验证分数: {result.score}/100")
    print(f"发现问题: {len(result.issues)}")
    for issue in result.issues:
        print(f"  - [{issue.severity}] {issue.page}: {issue.description}")
