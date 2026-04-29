#!/usr/bin/env python3
"""
SprintCycle Chorus 模块 v4.10
包含 Agent 协调、工具路由、知识库管理

v4.10 改进:
- Sprint 1: files_changed 类型处理 bug 修复 - 统一处理 dict/list/None 类型
- Sprint 2: 失败原因精准归因 - 扩展 ErrorHelper 类
- Sprint 3: 超时处理增强 - 完善 TimeoutHandler
- Sprint 4: UI_VERIFY Agent 完善 - 增强验证方法
- Sprint 5: 任务回滚机制 - 完善 RollbackManager
"""
from .reviewer import ReviewerAgent, ReviewSeverity, ReviewResult
from .scanner import ProjectScanner, IssueSeverity, IssueType, ScanResult
from .autofix import AutoFixEngine, FixSession, FixResult
from .health_check import ProjectHealthChecker, HealthReport, HealthStatus
from .diagnostic import DiagnosticEngine, DiagnosticResult, DiagnosticStatus, quick_diagnose
from .cache import ResponseCache, get_cache, cached

# 延迟导入优化模块以避免循环依赖
_imported_optimizations = False

def _get_optimizations():
    global _imported_optimizations
    if not _imported_optimizations:
        from . import optimizations
        globals().update({
            'FileTracker': getattr(optimizations, 'FileTracker', None),
            'TaskSplitter': getattr(optimizations, 'TaskSplitter', None),
            'SplitConfig': getattr(optimizations, 'SplitConfig', None),
            'ExecutionLog': getattr(optimizations, 'ExecutionLog', None),
            'DependencyManager': getattr(optimizations, 'DependencyManager', None),
            'ResultValidator': getattr(optimizations, 'ResultValidator', None),
            'FiveSourceVerifier': getattr(optimizations, 'FiveSourceVerifier', None),
            'EvolutionEngine': getattr(optimizations, 'EvolutionEngine', None),
            'RollbackManager': getattr(optimizations, 'RollbackManager', None),
            'TimeoutHandler': getattr(optimizations, 'TimeoutHandler', None),
            'ErrorHelper': getattr(optimizations, 'ErrorHelper', None),
        })
        _imported_optimizations = True
    return globals()

from typing import Any, Dict, List, Optional, Generator, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json
import yaml
import os
import subprocess
import time

# Loguru 日志系统
from loguru import logger

# 凭证管理
try:
    from .credentials import get_credential_manager
    _credentials_available = True
except ImportError:
    _credentials_available = False
    def get_credential_manager(project_path="."):
        return None

try:
    from .verifiers import PlaywrightVerifier as _PlaywrightVerifier
except ImportError:
    try:
        from verifiers import PlaywrightVerifier as _PlaywrightVerifier
    except ImportError:
        _PlaywrightVerifier = None


# Agent 模块
try:
    from .agents import (
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


# ============================================================
# v4.10 新增: files_changed 类型处理工具函数
# ============================================================

def normalize_files_changed(files_changed: Any) -> Dict[str, List[str]]:
    """
    统一处理 files_changed 类型，确保返回标准格式
    
    支持的类型:
    - Dict: {"added": [], "modified": [], "deleted": [], "screenshots": []}
    - List: ["file1", "file2", ...]
    - None: 返回空字典
    - 其他: 尝试转换为字符串列表
    
    Returns:
        Dict[str, List[str]]: 标准格式的 files_changed
    """
    default = {"added": [], "modified": [], "deleted": [], "screenshots": []}
    
    if files_changed is None:
        return default
    
    if isinstance(files_changed, dict):
        return {
            "added": files_changed.get("added", []),
            "modified": files_changed.get("modified", []),
            "deleted": files_changed.get("deleted", []),
            "screenshots": files_changed.get("screenshots", [])
        }
    
    if isinstance(files_changed, list):
        return {
            "added": [],
            "modified": files_changed,
            "deleted": [],
            "screenshots": []
        }
    
    logger.warning(f"files_changed 类型不支持: {type(files_changed)}, 使用默认值")
    return default


def extract_files_list(files_changed: Any) -> List[str]:
    """从 files_changed 中提取所有文件列表"""
    normalized = normalize_files_changed(files_changed)
    result = []
    for file_list in normalized.values():
        if isinstance(file_list, list):
            result.extend(file_list)
    return result


def has_changes(files_changed: Any) -> bool:
    """检查是否有任何文件变更"""
    files_list = extract_files_list(files_changed)
    return len(files_list) > 0


def get_change_summary(files_changed: Any) -> str:
    """获取变更摘要"""
    normalized = normalize_files_changed(files_changed)
    parts = []
    if normalized["added"]:
        parts.append(f"+{len(normalized['added'])} 新增")
    if normalized["modified"]:
        parts.append(f"~{len(normalized['modified'])} 修改")
    if normalized["deleted"]:
        parts.append(f"-{len(normalized['deleted'])} 删除")
    if normalized["screenshots"]:
        parts.append(f"[{len(normalized['screenshots'])} 截图]")
    
    if not parts:
        return "无变更"
    return " ".join(parts)


# ============================================================
# 枚举与数据类
# ============================================================

class ToolType(Enum):
    CURSOR = "cursor"
    CLAUDE = "claude"
    AIDER = "aider"


class AgentType(Enum):
    """Agent 类型枚举"""
    CODER = "coder"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    TESTER = "tester"
    DIAGNOSTIC = "diagnostic"
    UI_VERIFY = "ui_verify"
    
    @classmethod
    def from_string(cls, value: str) -> "AgentType":
        """安全转换，未知类型自动映射到 CODER
        
        支持动态扩展新的 Agent 类型，自动映射未知类型到 CODER
        """
        if not value:
            return None
        try:
            return cls(value.lower())
        except ValueError:
            from loguru import logger
            logger.info(f"未知 agent 类型 '{value}'，自动映射到 CODER")
            return cls.CODER




class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ExecutionResult:
    """执行结果 v4.10 - 增强 files_changed 处理"""
    success: bool
    output: str
    duration: float
    tool: str
    files_changed: Dict = field(default_factory=lambda: {"added": [], "modified": [], "deleted": [], "screenshots": []})
    retries: int = 0
    error: Optional[str] = None
    error_reason: Optional[str] = None  # v4.10 新增: 精确错误原因
    split_suggestion: List[str] = field(default_factory=list)
    validation: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """v4.10: 自动规范化 files_changed 类型"""
        self.files_changed = normalize_files_changed(self.files_changed)
    
    @property
    def files_list(self) -> List[str]:
        """v4.10: 获取所有变更文件的列表"""
        return extract_files_list(self.files_changed)
    
    @property
    def has_changes(self) -> bool:
        """v4.10: 是否有变更"""
        return has_changes(self.files_changed)
    
    @property
    def change_summary(self) -> str:
        """v4.10: 获取变更摘要"""
        return get_change_summary(self.files_changed)
    
    def to_dict(self) -> Dict:
        """v4.10: 转换为字典格式"""
        return {
            "success": self.success,
            "output": self.output,
            "duration": self.duration,
            "tool": self.tool,
            "files_changed": self.files_changed,
            "files_list": self.files_list,
            "has_changes": self.has_changes,
            "retries": self.retries,
            "error": self.error,
            "error_reason": self.error_reason,
            "split_suggestion": self.split_suggestion,
            "validation": self.validation
        }


@dataclass
class TaskProgress:
    """任务进度"""
    task_id: str
    status: TaskStatus
    progress: int
    message: str
    start_time: datetime = None
    end_time: datetime = None


# ============================================================
# 配置管理
# ============================================================

class Config:
    """配置管理 - 支持环境变量和配置文件"""
    
    DEFAULT_CONFIG = {
        "aider": {
            "command": "/root/aider-venv/bin/aider",
            "model": "deepseek/deepseek-chat",
            "api_key_env": "LLM_API_KEY",
            "timeout": 120,
            "max_retries": 2
        },
        "claude": {
            "command": "claude",
            "timeout": 180
        },
        "cursor": {
            "command": "cursor-agent",
            "timeout": 180
        },
        "scheduler": {
            "max_concurrent": 5,
            "retry_delay": 5
        },
        "task": {
            "split_threshold_seconds": 120,
            "suggest_split": True,
            "exclude_dirs": ["node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build"]
        },
        # v4.10 新增: 回滚配置
        "rollback": {
            "enabled": True,
            "auto_backup": True,
            "max_backups": 10
        },
        # v4.10 新增: 超时处理配置
        "timeout": {
            "default_timeout": 120,
            "max_retries": 3,
            "backoff_multiplier": 1.5,
            "max_backoff": 300
        }
    }
    
    @classmethod
    def load(cls) -> Dict:
        config_path = Path("/root/sprintcycle/config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                config = cls.DEFAULT_CONFIG.copy()
                cls._deep_update(config, user_config.get("tools", {}))
                return config
        return cls.DEFAULT_CONFIG
    
    @classmethod
    def _deep_update(cls, base: Dict, update: Dict):
        """深度合并配置"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                cls._deep_update(base[key], value)
            else:
                base[key] = value
    
    @classmethod
    def get_api_key(cls, tool: str) -> str:
        """获取 API Key - 优先使用 CredentialManager（支持多层加载）"""
        if _credentials_available:
            cm = get_credential_manager()
            if cm:
                key = cm.get_api_key(tool)
                if key:
                    return key
        # 回退到环境变量
        return cls._get_env_api_key(tool)
    
    @classmethod
    def _get_env_api_key(cls, tool: str) -> str:
        """从环境变量获取 API Key（兼容旧方式）"""
        config = cls.load().get(tool, {})
        env_var = config.get("api_key_env", "")
        return os.environ.get(env_var, "")


# ============================================================
# 知识库
# ============================================================

class KnowledgeBase:
    """
    知识库 - 记录和检索历史经验
    v4.10: 增强 files_changed 处理
    """
    
    def __init__(self, project_path: str):
        self.path = Path(project_path) / ".sprintcycle" / "knowledge.json"
        self.data = self._load()
    
    def _load(self) -> Dict:
        if self.path.exists():
            with open(self.path) as f:
                return json.load(f)
        return {"tasks": [], "patterns": [], "solutions": []}
    
    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def record_task(self, task: str, result: ExecutionResult, files: List[str]):
        """记录任务执行结果 - v4.10 增强 files_changed 处理"""
        files_list = files
        normalized = normalize_files_changed(result.files_changed)
        
        if isinstance(normalized, dict):
            files_list = []
            for file_list in normalized.values():
                if isinstance(file_list, list):
                    files_list.extend(file_list)
        
        task_entry = {
            "task": task,
            "success": result.success,
            "tool": result.tool,
            "files": files_list,
            "files_changed": result.files_changed,
            "has_changes": len(files_list) > 0,
            "duration": result.duration,
            "timestamp": datetime.now().isoformat()
        }
        
        if result.error:
            task_entry["error"] = result.error
        if result.error_reason:
            task_entry["error_reason"] = result.error_reason
        
        if hasattr(result, 'review') and result.review:
            task_entry['review'] = result.review
        
        self.data["tasks"].append(task_entry)
        
        if result.success and files_list:
            pattern = {"type": "file_pattern", "files": files_list, "for_task": task[:50]}
            self.data["patterns"].append(pattern)
        
        self._save()
    
    def find_similar(self, task: str) -> List[Dict]:
        """查找相似任务的历史"""
        results = []
        task_keywords = set(task.lower().split())
        
        for t in self.data["tasks"][-20:]:
            hist_keywords = set(t["task"].lower().split())
            overlap = len(task_keywords & hist_keywords)
            if overlap > 2:
                results.append(t)
        
        return results[:3]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        tasks = self.data["tasks"]
        if not tasks:
            return {"total": 0, "total_tasks": 0, "success_rate": 0}
        
        success = sum(1 for t in tasks if t["success"])
        return {
            "total": len(tasks),
            "total_tasks": len(tasks),
            "success": success,
            "success_rate": round(success / len(tasks) * 100, 1),
            "avg_duration": round(sum(t["duration"] for t in tasks) / len(tasks), 1)
        }
    
    def add_entry(self, entry: Dict):
        """添加一条知识条目"""
        self.data.setdefault("solutions", []).append(entry)
        self._save()

    def record_task_entry(self, task_entry: Dict):
        """记录完整的 task_entry（包含 review 和 verification） - v4.10 增强"""
        from enum import Enum
        
        def sanitize(obj):
            if obj is None:
                return None
            if isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, list):
                result = [sanitize(item) for item in obj]
                return result if any(r is not None for r in result) else None
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    sv = sanitize(v)
                    if sv is not None:
                        result[k] = sv
                return result if result else None
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, '__dict__'):
                return sanitize(obj.__dict__)
            if hasattr(obj, '__dataclass_fields__'):
                return sanitize({f: getattr(obj, f) for f in obj.__dataclass_fields__})
            return str(obj)
        
        files_changed_raw = task_entry.get("files_changed", {})
        files_changed = normalize_files_changed(files_changed_raw)
        files_list = extract_files_list(files_changed)
        
        record = {
            "task": task_entry.get("task", ""),
            "success": task_entry.get("status") == "completed",
            "tool": task_entry.get("tool", "aider"),
            "files": task_entry.get("files", files_list),
            "files_changed": files_changed,
            "has_changes": has_changes(files_changed),
            "duration": task_entry.get("duration_seconds", 0),
            "timestamp": task_entry.get("completed_at", datetime.now().isoformat()),
            "review": sanitize(task_entry.get("review")),
            "verification": sanitize(task_entry.get("verification")),
            "validation": sanitize(task_entry.get("validation")),
        }
        
        if task_entry.get("error"):
            record["error"] = task_entry["error"]
        if task_entry.get("error_reason"):
            record["error_reason"] = task_entry["error_reason"]
        
        record = {k: v for k, v in record.items() if v is not None and v != {} and v != []}
        
        self.data["tasks"].append(record)
        
        files_to_use = record.get("files", files_list)
        if record.get("success") and files_to_use:
            pattern = {"type": "file_pattern", "files": files_to_use, "for_task": record["task"][:50]}
            self.data["patterns"].append(pattern)
        
        self._save()
        logger.success(f"已保存任务到 knowledge.json: {record['task'][:40]}...")


# ============================================================
# ExecutionLayer - 统一执行层
# ============================================================

class ExecutionLayer:
    """统一执行层 - 支持超时重试 v4.10 增强"""
    
    def __init__(self):
        self.config = Config.load()
        try:
            from .optimizations import ErrorHelper, TimeoutHandler
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
                on_progress: callable = None) -> ExecutionResult:
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
                from .optimizations import FileTracker
                files_dict = FileTracker.extract_changed_files(result.stdout, [])
            except:
                files_dict = {"added": [], "modified": [], "deleted": [], "screenshots": []}
            
            files_dict = normalize_files_changed(files_dict)
            
            split_suggestion = []
            try:
                from .optimizations import TaskSplitter, SplitConfig
                splitter = TaskSplitter(SplitConfig(threshold_seconds=120))
                split_suggestion = splitter.check_and_suggest(task, duration)
            except:
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


# ============================================================
# ChorusAdapter - 工具路由层
# ============================================================

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
        self.default = self._get_default()
    
    def _get_default(self) -> ToolType:
        for t in [ToolType.AIDER, ToolType.CLAUDE, ToolType.CURSOR]:
            if self.available.get(t.value):
                return t
        return ToolType.AIDER
    
    def route(self, agent: AgentType = None, preferred: ToolType = None) -> ToolType:
        if preferred and self.available.get(preferred.value):
            return preferred
        if agent:
            t = self.AGENT_TOOL_MAP.get(agent)
            if t and self.available.get(t.value):
                return t
        return self.default
    
    def execute(self, project_path: str, task: str, files: List[str],
                agent: AgentType = None, tool: ToolType = None,
                on_progress: callable = None) -> ExecutionResult:
        if agent == AgentType.TESTER:
            return self._execute_tester_task(project_path, task)
        
        if agent == AgentType.UI_VERIFY:
            return self._execute_ui_verify_task(project_path, task)
        
        selected = self.route(agent, tool)
        formatted = self.AGENT_PROMPTS.get(agent, "{task}").format(task=task)
        return self.executor.execute(project_path, formatted, files, selected, on_progress)
    
    def _execute_tester_task(self, project_path: str, task: str) -> ExecutionResult:
        """执行 Tester Agent 任务 - 浏览器测试"""
        import subprocess
        from pathlib import Path
        
        start_time = datetime.now()
        test_script_path = Path(__file__).parent / "test_xuewanpai_login.py"
        
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
        import re
        from pathlib import Path
        
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
        import asyncio
        
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


# ============================================================
# Chorus - Agent 协调层
# ============================================================

class Chorus:
    """Agent 协调层"""
    
    VERSION = "v4.10"  # v4.10: 更新版本号
    
    def __init__(self, kb: KnowledgeBase = None):
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
    
    def dispatch(self, project_path: str, task: str, files: List[str] = None,
                 agent: AgentType = None, tool: ToolType = None,
                 on_progress: callable = None) -> ExecutionResult:
        
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


# 导出公共接口
__all__ = [
    "Config",
    "ToolType", 
    "AgentType",
    "TaskStatus",
    "ExecutionResult",
    "TaskProgress",
    "KnowledgeBase",
    "ExecutionLayer",
    "ChorusAdapter",
    "Chorus",
    # v4.10 新增导出
    "normalize_files_changed",
    "extract_files_list",
    "has_changes",
    "get_change_summary"
]
