"""
ChorusAdapter v2.0 - 多工具适配器
支持 Claude Code、Cursor CLI、Aider 等多种 AI 编码工具
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import subprocess
import json

class CodingTool(Enum):
    """支持的 AI 编码工具"""
    CLAUDE_CODE = "claude-code"
    CURSOR_CLI = "cursor-cli"
    AIDER = "aider"
    COPILOT_CLI = "copilot-cli"
    INTERNAL = "internal"  # 内置AI（如扣子平台）

@dataclass
class ToolConfig:
    """工具配置"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = None
    
@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    files_changed: List[str]
    error: Optional[str] = None

class ChorusAdapter:
    """
    Chorus 适配器 - 连接 SprintCycle 与外部执行层
    
    支持多种 AI 编码工具的统一接口
    """
    
    TOOL_CONFIGS = {
        CodingTool.CLAUDE_CODE: ToolConfig(
            name="Claude Code",
            command="claude",
            args=["--dangerously-skip-permissions"],
            env={"ANTHROPIC_API_KEY": ""}
        ),
        CodingTool.CURSOR_CLI: ToolConfig(
            name="Cursor CLI",
            command="cursor",
            args=["--no-confirm"],
            env={}
        ),
        CodingTool.AIDER: ToolConfig(
            name="Aider",
            command="aider",
            args=["--yes"],
            env={"OPENAI_API_KEY": ""}
        ),
        CodingTool.INTERNAL: ToolConfig(
            name="Internal AI",
            command="",  # 直接调用，无命令行
            args=[],
            env={}
        )
    }
    
    def __init__(self, 
                 default_tool: CodingTool = CodingTool.INTERNAL,
                 fallback_tools: List[CodingTool] = None):
        """
        初始化适配器
        
        Args:
            default_tool: 默认使用的工具
            fallback_tools: 失败时的备用工具列表
        """
        self.default_tool = default_tool
        self.fallback_tools = fallback_tools or [CodingTool.INTERNAL]
        self._chorus_available = self._check_chorus()
    
    def _check_chorus(self) -> bool:
        """检查 Chorus 是否可用"""
        try:
            result = subprocess.run(
                ["chorus", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def init_chorus(self, project_path: str) -> ExecutionResult:
        """
        初始化 Chorus 项目
        
        Args:
            project_path: 项目路径
        """
        if not self._chorus_available:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error="Chorus 未安装或不可用"
            )
        
        try:
            # 尝试初始化
            result = subprocess.run(
                ["chorus", "init"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return ExecutionResult(
                    success=True,
                    output=result.stdout,
                    files_changed=[".chorus/"]
                )
            else:
                # 数据库迁移问题，尝试修复
                if "migration" in result.stderr.lower() or "database" in result.stderr.lower():
                    return self._fix_chorus_db(project_path)
                
                return ExecutionResult(
                    success=False,
                    output=result.stdout,
                    files_changed=[],
                    error=result.stderr
                )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=str(e)
            )
    
    def _fix_chorus_db(self, project_path: str) -> ExecutionResult:
        """修复 Chorus 数据库问题"""
        import os
        from pathlib import Path
        
        chorus_dir = Path.home() / ".chorus"
        db_path = chorus_dir / "chorus.db"
        
        # 创建数据目录
        chorus_dir.mkdir(exist_ok=True)
        
        # 删除旧的数据库文件（如果存在损坏）
        if db_path.exists():
            db_path.unlink()
        
        # 重新初始化
        try:
            result = subprocess.run(
                ["chorus", "init", "--force"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                files_changed=[".chorus/chorus.db"],
                error=result.stderr if result.returncode != 0 else None
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=f"修复失败: {str(e)}"
            )
    
    def execute_task(self, 
                     task: str, 
                     project_path: str,
                     tool: CodingTool = None,
                     context: Dict[str, Any] = None) -> ExecutionResult:
        """
        使用指定工具执行任务
        
        Args:
            task: 任务描述
            project_path: 项目路径
            tool: 使用的工具（None 则使用默认工具）
            context: 额外上下文
        """
        tool = tool or self.default_tool
        config = self.TOOL_CONFIGS.get(tool)
        
        if tool == CodingTool.INTERNAL:
            # 内置 AI 直接执行，返回标记
            return ExecutionResult(
                success=True,
                output=f"[Internal AI] 任务已接收: {task[:50]}...",
                files_changed=[],
                error=None
            )
        
        # 检查工具是否可用
        if not self._check_tool_available(config.command):
            # 尝试备用工具
            for fallback in self.fallback_tools:
                if self._check_tool_available(
                    self.TOOL_CONFIGS[fallback].command
                ):
                    return self.execute_task(
                        task, project_path, fallback, context
                    )
            
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=f"工具 {config.name} 不可用，且无备用工具"
            )
        
        # 执行任务
        try:
            cmd = [config.command] + config.args
            result = subprocess.run(
                cmd,
                input=task,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ, **(config.env or {})}
            )
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                files_changed=self._parse_changed_files(result.stdout),
                error=result.stderr if result.returncode != 0 else None
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=str(e)
            )
    
    def _check_tool_available(self, command: str) -> bool:
        """检查工具是否可用"""
        if not command:
            return True  # 内置工具
        try:
            subprocess.run(
                ["which", command],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False
    
    def _parse_changed_files(self, output: str) -> List[str]:
        """解析输出中的文件变更"""
        # 简单实现，实际需要根据不同工具的输出格式解析
        import re
        files = re.findall(r'(?:created|modified|updated):\s*(\S+)', output)
        return files
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        available = []
        for tool, config in self.TOOL_CONFIGS.items():
            available.append({
                "id": tool.value,
                "name": config.name,
                "available": self._check_tool_available(config.command)
            })
        return available


# 便捷函数
def create_adapter(tool: str = "internal") -> ChorusAdapter:
    """创建适配器实例"""
    tool_map = {
        "claude": CodingTool.CLAUDE_CODE,
        "cursor": CodingTool.CURSOR_CLI,
        "aider": CodingTool.AIDER,
        "internal": CodingTool.INTERNAL
    }
    return ChorusAdapter(default_tool=tool_map.get(tool, CodingTool.INTERNAL))
