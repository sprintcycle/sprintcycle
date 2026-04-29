"""
SprintCycle 凭证管理

分层加载策略（优先级从高到低）：
1. 环境变量
2. .env.local (本地开发，不提交)
3. .env (团队共享)
4. ~/.sprintcycle/credentials.yaml (用户级)
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class CredentialConfig:
    """凭证配置"""
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    aider_api_key: Optional[str] = None
    
    def is_configured(self, provider: str) -> bool:
        """检查是否配置了指定提供商的 API Key"""
        key_map = {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "aider": self.aider_api_key,
        }
        return bool(key_map.get(provider.lower()))


class CredentialManager:
    """凭证管理器"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self._credentials: Optional[CredentialConfig] = None
    
    def load(self) -> CredentialConfig:
        """加载凭证（按优先级）"""
        if self._credentials:
            return self._credentials
        
        cred = CredentialConfig()
        
        # 1. 环境变量（最高优先级）
        cred.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        cred.openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        # 2. .env.local（本地开发）
        env_local = self.project_path / ".env.local"
        if env_local.exists():
            cred = self._load_env_file(env_local, cred)
        
        # 3. .env（团队共享）
        env_file = self.project_path / ".env"
        if env_file.exists():
            cred = self._load_env_file(env_file, cred)
        
        # 4. ~/.sprintcycle/credentials.yaml（用户级）
        user_cred = Path.home() / ".sprintcycle" / "credentials.yaml"
        if user_cred.exists():
            cred = self._load_yaml_file(user_cred, cred)
        
        self._credentials = cred
        return cred
    
    def _load_env_file(self, path: Path, cred: CredentialConfig) -> CredentialConfig:
        """加载 .env 文件"""
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().upper()
                    value = value.strip().strip('"\'')
                    if key == "ANTHROPIC_API_KEY" and not cred.anthropic_api_key:
                        cred.anthropic_api_key = value
                    elif key == "OPENAI_API_KEY" and not cred.openai_api_key:
                        cred.openai_api_key = value
        return cred
    
    def _load_yaml_file(self, path: Path, cred: CredentialConfig) -> CredentialConfig:
        """加载 YAML 凭证文件"""
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        
        api_keys = data.get("api_keys", {})
        if not cred.anthropic_api_key:
            cred.anthropic_api_key = api_keys.get("anthropic")
        if not cred.openai_api_key:
            cred.openai_api_key = api_keys.get("openai")
        
        return cred
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """获取指定提供商的 API Key"""
        cred = self.load()
        key_map = {
            "anthropic": cred.anthropic_api_key,
            "openai": cred.openai_api_key,
            "aider": cred.aider_api_key or cred.anthropic_api_key,
        }
        return key_map.get(provider.lower())
    
    def setup_env(self, provider: str = "aider"):
        """设置环境变量（供 aider 等工具使用）"""
        cred = self.load()
        if provider == "aider":
            # aider 优先使用 ANTHROPIC_API_KEY
            if cred.anthropic_api_key:
                os.environ["ANTHROPIC_API_KEY"] = cred.anthropic_api_key
            if cred.openai_api_key:
                os.environ["OPENAI_API_KEY"] = cred.openai_api_key


# 全局实例
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager(project_path: str = ".") -> CredentialManager:
    """获取凭证管理器单例"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager(project_path)
    return _credential_manager
