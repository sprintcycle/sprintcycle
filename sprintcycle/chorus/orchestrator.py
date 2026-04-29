"""
chorus.orchestrator - Agent 协调层
"""
from typing import Callable, Dict, List, Optional
from datetime import datetime

from loguru import logger

from .adapter import ChorusAdapter
from .enums import AgentType, ToolType
from .knowledge import KnowledgeBase
from .progress import ExecutionResult


class Chorus:
    """Agent 协调层"""
    
    VERSION = "v4.10"  # v4.10: 更新版本号
    
    def __init__(self, kb: Optional["KnowledgeBase"] = None):
        self.adapter = ChorusAdapter()
        self.kb = kb
        self.history: List[Dict] = []
    
    def analyze(self, task: str) -> AgentType:
        t = task.lower()
        if any(k in t for k in ["审查", "review"]):
            return AgentType.REVIEWER
        if any(k in t for k in ["架构", "设计", "方案"]):
            return AgentType.ARCHITECT
        if any(k in t for k in ["测试", "test"]):
            return AgentType.TESTER
        if any(k in t for k in ["ui", "界面", "交互", "verify", "验证"]):
            return AgentType.UI_VERIFY
        return AgentType.CODER
    
    def dispatch(self, project_path: str, task: str, files: Optional[List[str]] = None,
                 agent: Optional[AgentType] = None, tool: Optional[ToolType] = None,
                 on_progress: Optional[Callable[..., None]] = None) -> ExecutionResult:
        
        if agent is None:
            agent = self.analyze(task)
        
        if self.kb:
            similar = self.kb.find_similar(task)
            if similar:
                logger.info(f"找到 {len(similar)} 个相似任务")
        
        result = self.adapter.execute(project_path, task, files, agent, tool, on_progress)
        
        if self.kb:
            self.kb.record_task(task, result, files or [])
        
        self.history.append({
            "task": task[:100], "agent": agent.value, "tool": result.tool,
            "success": result.success, "duration": result.duration,
            "retries": result.retries, "timestamp": datetime.now().isoformat(),
            "files_changed": result.files_changed,
            "has_changes": result.has_changes,
            "error_reason": result.error_reason
        })
        
        return result


# 向后兼容: ChorusOrchestrator 是 Chorus 的别名
ChorusOrchestrator = Chorus
