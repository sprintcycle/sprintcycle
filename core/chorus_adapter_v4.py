"""
ChorusAdapter v4.0 - 完全独立的执行层
支持配置文件驱动，优先使用外部 AI 工具
"""
import os
import subprocess
import yaml
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path


class CodingTool(Enum):
    CLAUDE_CODE = "claude_code"
    CURSOR_CLI = "cursor_cli"
    AIDER = "aider"
    INTERNAL = "internal"


@dataclass
class ExecutionResult:
    success: bool
    output: str
    files_changed: List[str]
    error: Optional[str] = None


class ChorusAdapterV4:
    """
    完全独立的执行适配器
    
    从配置文件读取工具配置，优先使用外部 AI 工具
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/root/sprintcycle/config.yaml"
        self.config = self._load_config()
        self.tools = self._init_tools()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        path = Path(self.config_path)
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f)
        return {"execution": {"primary_tool": "internal"}}
    
    def _init_tools(self) -> Dict[str, dict]:
        """初始化工具配置"""
        exec_config = self.config.get("execution", {})
        return exec_config.get("tools", {})
    
    def get_primary_tool(self) -> CodingTool:
        """获取主工具"""
        primary = self.config.get("execution", {}).get("primary_tool", "internal")
        return CodingTool(primary)
    
    def check_tool_available(self, tool: CodingTool) -> tuple:
        """检查工具是否可用"""
        tool_config = self.tools.get(tool.value, {})
        command = tool_config.get("command", "")
        
        if not command:  # internal
            return True, "内置工具可用"
        
        # 展开 ~ 路径
        command = os.path.expanduser(command)
        
        # 检查命令是否存在
        result = subprocess.run(
            ["which", command] if not command.startswith("/") else ["test", "-x", command],
            capture_output=True
        )
        
        if result.returncode == 0:
            return True, f"{tool.value} 可用"
        return False, f"{tool.value} 未安装或路径错误"
    
    def list_tools_status(self) -> List[dict]:
        """列出所有工具状态"""
        status = []
        for tool in CodingTool:
            available, message = self.check_tool_available(tool)
            status.append({
                "tool": tool.value,
                "available": available,
                "message": message,
                "is_primary": tool == self.get_primary_tool()
            })
        return status
    
    async def execute_task(
        self,
        task: str,
        project_path: str,
        tool: CodingTool = None,
        context: Dict[str, Any] = None
    ) -> ExecutionResult:
        """执行任务"""
        # 确定使用的工具
        tool = tool or self.get_primary_tool()
        
        # 检查工具可用性
        available, message = self.check_tool_available(tool)
        
        if not available:
            # 尝试备用工具
            fallback_tools = self.config.get("execution", {}).get("fallback_tools", [])
            for fb in fallback_tools:
                fb_tool = CodingTool(fb)
                fb_available, _ = self.check_tool_available(fb_tool)
                if fb_available:
                    tool = fb_tool
                    available = True
                    break
        
        if not available:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=f"所有工具不可用: {message}"
            )
        
        # 执行任务
        if tool == CodingTool.INTERNAL:
            return self._execute_internal(task, context)
        else:
            return await self._execute_external(tool, task, project_path, context)
    
    def _execute_internal(self, task: str, context: Dict = None) -> ExecutionResult:
        """内部执行（非独立模式）"""
        return ExecutionResult(
            success=True,
            output=f"[非独立模式] 任务已记录: {task[:50]}...\n请使用扣子会话执行此任务",
            files_changed=[],
            error="INTERNAL 模式需要扣子会话支持，请切换到独立工具"
        )
    
    async def _execute_external(
        self,
        tool: CodingTool,
        task: str,
        project_path: str,
        context: Dict = None
    ) -> ExecutionResult:
        """使用外部工具执行"""
        tool_config = self.tools.get(tool.value, {})
        command = os.path.expanduser(tool_config.get("command", ""))
        args = tool_config.get("args", [])
        
        if not command:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=f"工具 {tool.value} 配置错误"
            )
        
        # 构建命令
        cmd = [command] + args
        
        try:
            result = subprocess.run(
                cmd,
                input=task,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                files_changed=self._parse_files(result.stdout),
                error=result.stderr if result.returncode != 0 else None
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error="执行超时（300秒）"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=str(e)
            )
    
    def _parse_files(self, output: str) -> List[str]:
        """解析输出中的文件变更"""
        import re
        files = re.findall(r'(?:created|modified|updated|deleted):\s*(\S+)', output)
        return files


# 便捷函数
def create_standalone_adapter(config_path: str = None) -> ChorusAdapterV4:
    """创建独立适配器"""
    return ChorusAdapterV4(config_path)


def check_environment() -> dict:
    """检查环境配置"""
    adapter = ChorusAdapterV4()
    return {
        "tools": adapter.list_tools_status(),
        "config_loaded": adapter.config is not None,
        "primary_tool": adapter.get_primary_tool().value
    }
