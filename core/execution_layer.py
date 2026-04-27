"""
SprintCycle 执行层 v2.0 - 完全独立
支持 Aider + DeepSeek / Cursor CLI / Claude Code 等多种工具
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ExecutionTool(Enum):
    CURSOR_CLI = "cursor_cli"
    CLAUDE_CODE = "claude_code"
    AIDER = "aider"
    COZE_API = "coze_api"
    INTERNAL = "internal"


@dataclass
class ExecutionResult:
    success: bool
    output: str
    files_changed: List[str]
    error: Optional[str] = None
    session_id: Optional[str] = None


class ExecutionLayer:
    """
    统一执行层 - 支持多种 AI 编码工具
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.venv_path = self.config.get("venv_path", "/root/aider-venv")
        self.env = self._build_env()
        
    def _build_env(self) -> Dict[str, str]:
        """构建环境变量"""
        env = os.environ.copy()
        tool_env = self.config.get("env", {})
        env.update(tool_env)
        return env
        
    def _check_available(self) -> bool:
        """检查工具是否可用"""
        command = self.config.get("command", "aider")
        
        # 检查虚拟环境中的 aider
        if self.venv_path:
            aider_path = os.path.join(self.venv_path, "bin", "aider")
            if os.path.exists(aider_path):
                return True
        
        # 检查系统中的 aider
        result = subprocess.run(
            ["which", command],
            capture_output=True,
            env=self.env
        )
        return result.returncode == 0
        
    @property
    def available(self) -> bool:
        return self._check_available()
    
    def get_aider_command(self) -> List[str]:
        """获取 Aider 命令"""
        if self.venv_path:
            aider_path = os.path.join(self.venv_path, "bin", "aider")
            if os.path.exists(aider_path):
                return [aider_path]
        return ["aider"]
        
    async def execute(
        self,
        task: str,
        project_path: str = ".",
        files: List[str] = None,
        auto_approve: bool = True,
        **kwargs
    ) -> ExecutionResult:
        """
        执行任务
        
        Args:
            task: 任务描述
            project_path: 项目路径
            files: 要编辑的文件列表
            auto_approve: 自动批准
        """
        return await self._execute_aider(task, project_path, files)
            
    async def _execute_aider(
        self,
        task: str,
        project_path: str,
        files: List[str] = None
    ) -> ExecutionResult:
        """使用 Aider + DeepSeek 执行"""
        try:
            cmd = self.get_aider_command()
            
            # 基础参数
            cmd.extend([
                "--model", "deepseek/deepseek-chat",
                "--yes-always",
                "--no-auto-commits",
                "--message", task
            ])
            
            # 添加文件
            if files:
                cmd.extend(files)
            
            print(f"\n🔧 执行命令: {' '.join(cmd[:5])}...")
            
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
                env=self.env
            )
            
            output = result.stdout
            
            # 提取修改的文件
            files_changed = []
            if "Applied edit to" in output:
                for line in output.split("\n"):
                    if "Applied edit to" in line:
                        file_name = line.split("Applied edit to")[-1].strip()
                        files_changed.append(file_name)
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=output,
                files_changed=files_changed,
                error=result.stderr if result.returncode != 0 else None
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error="执行超时 (300s)"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                files_changed=[],
                error=str(e)
            )


def create_execution_layer(config_path: str = None) -> ExecutionLayer:
    """创建执行层实例"""
    import yaml
    
    if config_path is None:
        config_path = "/root/sprintcycle/config.yaml"
    
    config = {}
    if os.path.exists(config_path):
        with open(config_path) as f:
            full_config = yaml.safe_load(f)
            config = full_config.get("execution", {}).get("tools", {}).get("aider", {})
    
    return ExecutionLayer(config=config)
