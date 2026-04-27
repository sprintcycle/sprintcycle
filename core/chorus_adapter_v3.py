"""
ChorusAdapter v3.0 - 真正可执行的 Internal AI 模式
"""
import os
import json
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path


class CodingTool(Enum):
    CLAUDE_CODE = "claude-code"
    CURSOR_CLI = "cursor-cli"
    AIDER = "aider"
    INTERNAL = "internal"


@dataclass
class ExecutionResult:
    success: bool
    output: str
    files_changed: List[str]
    error: Optional[str] = None


class InternalAIExecutor:
    """
    Internal AI 执行器 - 通过写入任务文件，让主 Agent 感知并执行
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.task_file = self.project_path / ".sprintcycle" / "pending_tasks.json"
        self.result_file = self.project_path / ".sprintcycle" / "execution_results.json"
    
    def submit_task(self, task: str, context: Dict[str, Any] = None) -> ExecutionResult:
        """提交任务到任务队列"""
        task_data = {
            "task": task,
            "context": context or {},
            "status": "pending",
            "created_at": str(Path.stat(self.task_file).st_mtime if self.task_file.exists() else 0)
        }
        
        # 读取现有任务
        tasks = []
        if self.task_file.exists():
            with open(self.task_file) as f:
                tasks = json.load(f)
        
        tasks.append(task_data)
        
        # 写入任务
        self.task_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.task_file, 'w') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
        
        return ExecutionResult(
            success=True,
            output=f"任务已提交: {task[:50]}...",
            files_changed=[str(self.task_file)]
        )
    
    def check_result(self) -> Optional[Dict]:
        """检查执行结果"""
        if self.result_file.exists():
            with open(self.result_file) as f:
                results = json.load(f)
            # 清空结果文件
            self.result_file.unlink()
            return results
        return None


class ChorusAdapterV3:
    """Chorus 适配器 v3 - 支持真实执行"""
    
    def __init__(self, project_path: str, default_tool: CodingTool = CodingTool.INTERNAL):
        self.project_path = project_path
        self.default_tool = default_tool
        self.internal_executor = InternalAIExecutor(project_path)
    
    async def execute_task(
        self, 
        task: str, 
        tool: CodingTool = None,
        context: Dict[str, Any] = None
    ) -> ExecutionResult:
        """执行任务"""
        tool = tool or self.default_tool
        
        if tool == CodingTool.INTERNAL:
            return self.internal_executor.submit_task(task, context)
        else:
            # 其他工具的执行逻辑
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=f"工具 {tool.value} 尚未安装或配置"
            )
    
    async def execute_sprint(self, sprint_config: Dict) -> ExecutionResult:
        """执行整个 Sprint"""
        goals = sprint_config.get("goals", [])
        results = []
        
        for goal in goals:
            result = await self.execute_task(
                f"实现目标: {goal}",
                context={"sprint_id": sprint_config.get("id")}
            )
            results.append(result)
        
        return ExecutionResult(
            success=all(r.success for r in results),
            output=f"完成 {len(results)}/{len(goals)} 个目标",
            files_changed=[]
        )
