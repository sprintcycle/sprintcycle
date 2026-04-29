"""
chorus.adapter - 工具路由适配器
"""
import asyncio
import re
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional
from datetime import datetime

from loguru import logger

from .enums import AgentType, ToolType
from .progress import ExecutionResult
from .execution import ExecutionLayer


# 尝试导入 agents 模块
try:
    from ..agents import (
        UIVerifyAgent,
        VerificationType,
        VerificationResult,
        PageVerificationReport,
        ConcurrentExecutor,
        PriorityTask,
        TaskPriority
    )
except ImportError:
    logger.warning("agents 模块导入失败，UI_VERIFY Agent 将使用降级模式")
    UIVerifyAgent = None
    ConcurrentExecutor = None
    TaskPriority = None


class ChorusAdapter:
    """工具路由层"""
    
    AGENT_TOOL_MAP = {
        AgentType.CODER: ToolType.AIDER,
        AgentType.REVIEWER: ToolType.CLAUDE,
        AgentType.ARCHITECT: ToolType.CLAUDE,
        AgentType.TESTER: ToolType.AIDER,
        AgentType.UI_VERIFY: None  # UI_VERIFY 使用专用执行器
    }
    
    AGENT_PROMPTS = {
        AgentType.CODER: "{task}",
        AgentType.REVIEWER: "审查：{task}",
        AgentType.ARCHITECT: "设计方案：{task}",
        AgentType.TESTER: "编写测试：{task}"
    }
    
    def __init__(self):
        self.executor = ExecutionLayer()
        self.available = self.executor.list_available()
        self.default: ToolType = self._get_default()
    
    def _get_default(self) -> ToolType:
        for t in [ToolType.AIDER, ToolType.CLAUDE, ToolType.CURSOR]:
            if self.available.get(t.value):
                return t
        return ToolType.AIDER
    
    def route(self, agent: Optional[AgentType] = None, preferred: Optional[ToolType] = None) -> ToolType:
        if preferred and self.available.get(preferred.value):
            return preferred
        if agent:
            t = self.AGENT_TOOL_MAP.get(agent)
            if t and self.available.get(t.value):
                return t
        return self.default  # type: ignore[attr-defined]
    
    def execute(self, project_path: str, task: str, files: List[str],
                agent: Optional[AgentType] = None, tool: Optional[ToolType] = None,
                on_progress: Optional[Callable[..., None]] = None) -> ExecutionResult:
        if agent == AgentType.TESTER:
            return self._execute_tester_task(project_path, task)
        
        if agent == AgentType.UI_VERIFY:
            return self._execute_ui_verify_task(project_path, task)
        
        selected = self.route(agent, tool) or ToolType.AIDER
        formatted = self.AGENT_PROMPTS.get(agent or AgentType.CODER, "{task}").format(task=task)
        return self.executor.execute(project_path, formatted, files, selected, on_progress)
    
    def _execute_tester_task(self, project_path: str, task: str) -> ExecutionResult:
        """执行 Tester Agent 任务 - 浏览器测试"""
        start_time = datetime.now()
        test_script_path = Path(__file__).parent.parent / "test_xuewanpai_login.py"
        
        if not test_script_path.exists():
            logger.warning("test_xuewanpai_login.py 不存在，使用 AIDER 执行测试任务")
            return self.executor.execute(
                project_path, 
                f"编写测试：{task}", 
                None, 
                ToolType.AIDER
            )
        
        try:
            logger.info("执行 Playwright 浏览器测试...")
            result = subprocess.run(
                ["python3", str(test_script_path)],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            screenshots = []
            for line in output.split("\n"):
                if "截图:" in line or "screenshot" in line.lower():
                    path = line.split("截图:")[-1].strip() if "截图:" in line else line
                    if path.startswith("/"):
                        screenshots.append(path)
            
            return ExecutionResult(
                success=success,
                output=output,
                files_changed={"added": [], "modified": [], "deleted": [], "screenshots": screenshots},
                duration=duration,
                tool="tester",
                error=None if success else "测试失败"
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False, 
                files_changed={"added": [], "modified": [], "deleted": [], "screenshots": []},
                duration=180, tool="tester", 
                error="测试超时",
                error_reason="任务执行超时，超过180秒限制"
            )
        except Exception as e:
            return ExecutionResult(
                success=False, 
                files_changed={"added": [], "modified": [], "deleted": [], "screenshots": []},
                duration=(datetime.now() - start_time).total_seconds(),
                tool="tester", 
                error=str(e),
                error_reason=f"测试执行异常: {str(e)[:50]}"
            )

    async def _execute_ui_verify_task_async(self, project_path: str, task: str, 
                                   context: Dict = None) -> ExecutionResult:
        """执行 UI_VERIFY Agent 任务"""
        start_time = datetime.now()
        context = context or {}
        
        try:
            logger.info("执行 UI_VERIFY 交互验证...")
            
            if UIVerifyAgent is not None:
                base_url = "http://localhost:3000"
                routes = context.get("routes", ["/", "/login", "/profile"])
                
                url_match = re.search(r'https?://[^\s]+', task)
                if url_match:
                    base_url = url_match.group()
                
                agent = UIVerifyAgent(base_url=base_url)
                await agent.initialize()
                
                try:
                    result = await agent.execute(task, {
                        "url": base_url,
                        "routes": routes,
                        **context
                    })
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    output = """
## UI 交互验证报告

**验证分数**: {score}/100
**检查项**: {pages}
**总体状态**: {status}

### 详细结果

""".format(
                        score=result.get("average_score", 0),
                        pages=result.get("pages_verified", 0),
                        status="通过" if result.get("success") else "需要改进"
                    )
                    
                    if "summary" in result:
                        output += result["summary"]
                    
                    screenshots = []
                    for report in result.get("reports", []):
                        for v in report.get("verifications", []):
                            if v.get("screenshot"):
                                screenshots.append(v["screenshot"])
                    
                    return ExecutionResult(
                        success=result.get("success", False),
                        output=output,
                        duration=duration,
                        tool="playwright",
                        files_changed={"added": [], "modified": [], "deleted": [], "screenshots": screenshots},
                        validation={
                            "score": result.get("average_score", 0),
                            "high_severity": result.get("total_high_severity_issues", 0)
                        }
                    )
                finally:
                    await agent.cleanup()
            
            return ExecutionResult(
                success=False,
                output="UI_VERIFY Agent 未安装",
                duration=(datetime.now() - start_time).total_seconds(),
                tool="playwright",
                error="Agent not available"
            )
                
        except Exception as e:
            logger.error(f"UI_VERIFY 执行失败: {e}")
            return ExecutionResult(
                success=False,
                output="UI验证失败: {error}".format(error=str(e)),
                duration=(datetime.now() - start_time).total_seconds(),
                tool="playwright",
                error=str(e),
                error_reason=f"UI验证执行异常: {str(e)[:50]}"
            )
    
    def _execute_ui_verify_task(self, project_path: str, task: str) -> ExecutionResult:
        """执行 UI_VERIFY Agent 任务 - 同步包装"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._execute_ui_verify_task_async(project_path, task)
                    )
                    return future.result()
            else:
                return asyncio.run(self._execute_ui_verify_task_async(project_path, task))
        except RuntimeError:
            return asyncio.run(self._execute_ui_verify_task_async(project_path, task))
