"""
chorus.execution - 执行层
"""
import os
import subprocess
import time
from typing import Callable, Dict, List, Optional
from datetime import datetime

from loguru import logger

from .enums import ToolType, TaskStatus
from .progress import ExecutionResult
from .config import Config
from .utils import normalize_files_changed


class ExecutionLayer:
    """统一执行层 - 支持超时重试 v4.10 增强"""
    
    def __init__(self):
        self.config = Config.load()
        try:
            from ..optimizations import ErrorHelper, TimeoutHandler
            self.error_helper = ErrorHelper
            self.timeout_handler = TimeoutHandler(
                max_retries=self.config.get("timeout", {}).get("max_retries", 3),
                default_timeout=self.config.get("timeout", {}).get("default_timeout", 120)
            )
        except ImportError:
            self.error_helper = None
            self.timeout_handler = None
    
    def check_available(self, tool: ToolType) -> bool:
        config = self.config.get(tool.value, {})
        command = config.get("command", "")
        if command.startswith("/"):
            return os.path.exists(command)
        result = subprocess.run(["which", command], capture_output=True)
        return result.returncode == 0
    
    def list_available(self) -> Dict[str, bool]:
        return {tool.value: self.check_available(tool) for tool in ToolType}
    
    def execute(self, project_path: str, task: str, files: List[str], 
                tool: ToolType,
                on_progress: Optional[Callable[..., None]] = None) -> ExecutionResult:
        """执行任务，支持重试 - v4.10 增强错误归因"""
        
        config = self.config.get(tool.value, {})
        command = config.get("command", "")
        timeout = config.get("timeout", 120)
        max_retries = config.get("max_retries", 2)
        
        env = os.environ.copy()
        if tool == ToolType.AIDER:
            env["LLM_API_KEY"] = Config.get_api_key("aider")
        
        retries = 0
        last_error = None
        error_reason = None
        
        for attempt in range(max_retries + 1):
            if on_progress:
                on_progress(TaskStatus.RETRYING if retries > 0 else TaskStatus.RUNNING, 
                           attempt, max_retries + 1)
            
            result = self._run_once(project_path, task, files, tool, command, env, timeout)
            
            if result.success:
                result.retries = retries
                result.error_reason = None
                return result
            
            last_error = result.error
            
            if self.error_helper:
                error_reason = self.error_helper.get_error_reason(last_error or "")
            
            retries += 1
            
            if attempt < max_retries:
                delay = self.config.get("scheduler", {}).get("retry_delay", 5)
                if self.timeout_handler:
                    delay = min(delay * (self.timeout_handler.backoff_multiplier ** (attempt - 1)),
                               self.config.get("timeout", {}).get("max_backoff", 300))
                time.sleep(delay)
        
        return ExecutionResult(
            success=False, 
            output="", 
            files_changed={"added": [], "modified": [], "deleted": [], "screenshots": []},
            duration=0, 
            tool=tool.value, 
            retries=retries, 
            error=last_error,
            error_reason=error_reason
        )
    
    def _run_once(self, project_path: str, task: str, files: List[str], 
                  tool: ToolType, command: str, env: Dict, timeout: int) -> ExecutionResult:
        """单次执行"""
        
        if tool == ToolType.AIDER:
            cmd = [command, "--model", "deepseek/deepseek-chat", 
                   "--yes-always", "--no-auto-commits", "--message", task] + (files or [])
        elif tool == ToolType.CLAUDE:
            cmd = [command, "--allowedTools", "Bash,Read,Edit,Write", "-p", task]
        else:
            cmd = [command, "--yes", "--message", task] + (files or [])
        
        start = datetime.now()
        try:
            result = subprocess.run(cmd, cwd=project_path, capture_output=True, 
                                   text=True, timeout=timeout, env=env)
            duration = (datetime.now() - start).total_seconds()
            
            try:
                from ..optimizations import FileTracker
                files_dict = FileTracker.extract_changed_files(result.stdout, [])
            except Exception:
                files_dict = {"added": [], "modified": [], "deleted": [], "screenshots": []}
            
            files_dict = normalize_files_changed(files_dict)
            
            split_suggestion = []
            try:
                from ..optimizations import TaskSplitter, SplitConfig
                splitter = TaskSplitter(SplitConfig(threshold_seconds=120))
                split_suggestion = splitter.check_and_suggest(task, duration)
            except Exception:
                pass
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                files_changed=files_dict,
                duration=duration,
                tool=tool.value,
                error=result.stderr if result.returncode != 0 else None,
                split_suggestion=split_suggestion
            )
        except subprocess.TimeoutExpired:
            error_reason = "任务执行超时"
            if self.error_helper:
                error_reason = self.error_helper.get_error_reason("TIMEOUT")
            return ExecutionResult(
                False, "", {"added": [], "modified": [], "deleted": [], "screenshots": []}, 
                timeout, tool.value, error="超时", error_reason=error_reason
            )
        except Exception as e:
            error_reason = str(e)
            if self.error_helper:
                error_reason = self.error_helper.get_error_reason(str(e))
            return ExecutionResult(
                False, "", {"added": [], "modified": [], "deleted": [], "screenshots": []}, 
                0, tool.value, error=str(e), error_reason=error_reason
            )
    
    def _parse_files(self, output: str, tool: ToolType) -> List[str]:
        files = []
        for line in output.split("\n"):
            if tool == ToolType.AIDER and "Applied edit to" in line:
                files.append(line.split("Applied edit to")[-1].strip())
            elif tool == ToolType.CLAUDE and ("Modified:" in line or "Created:" in line):
                files.append(line.split(":")[-1].strip())
        return files
