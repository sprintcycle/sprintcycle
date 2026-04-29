"""
chorus.config - 配置管理
"""
from pathlib import Path
from typing import Dict, Any
import os
import yaml

# 凭证管理
_credentials_available = None


def _init_credentials():
    global _credentials_available
    if _credentials_available is None:
        try:
            from .credentials import get_credential_manager
            _credentials_available = True
        except ImportError:
            _credentials_available = False


def get_credential_manager_wrapper(project_path="."):
    """凭证管理器获取（延迟初始化）"""
    _init_credentials()
    if _credentials_available:
        try:
            from .credentials import get_credential_manager
            return get_credential_manager(project_path)
        except Exception:
            return None
    return None


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
        import os as _os
        _sprint_root = _os.environ.get("SPRINT_ROOT")
        if _sprint_root:
            config_path = Path(_sprint_root) / "config.yaml"
        else:
            # 向上搜索项目根目录
            config_path = Path(__file__).parent.parent
            while config_path.name != "sprintcycle" and config_path.parent != config_path:
                config_path = config_path.parent
            config_path = config_path / "config.yaml"
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
        cm = get_credential_manager_wrapper()
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
