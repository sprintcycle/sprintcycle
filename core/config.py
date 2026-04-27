"""SprintCycle 配置管理"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class ChorusConfig:
    """Chorus 配置"""
    base_url: str = "http://localhost:3000"
    api_key: Optional[str] = None
    timeout: int = 300
    max_retries: int = 3


@dataclass
class DatabaseConfig:
    """数据库配置"""
    type: str = "sqlite"  # sqlite 或 postgresql
    path: str = "sprintcycle.db"  # SQLite 路径
    host: str = "localhost"
    port: int = 5432
    name: str = "sprintcycle"
    user: str = "postgres"
    password: str = ""


@dataclass
class AIConfig:
    """AI 配置"""
    provider: str = "openai"  # openai, anthropic, mock
    api_key: Optional[str] = None
    model: str = "gpt-4"
    base_url: Optional[str] = None


@dataclass
class SprintCycleConfig:
    """SprintCycle 主配置"""
    project_name: str = "MyProject"
    chorus: ChorusConfig = field(default_factory=ChorusConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    
    # Sprint 配置
    auto_progress: bool = True
    max_retries_per_sprint: int = 3
    knowledge_injection: bool = True
    verification_enabled: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SprintCycleConfig":
        chorus_data = data.get("chorus", {})
        db_data = data.get("database", {})
        ai_data = data.get("ai", {})
        
        return cls(
            project_name=data.get("project_name", "MyProject"),
            chorus=ChorusConfig(**chorus_data),
            database=DatabaseConfig(**db_data),
            ai=AIConfig(**ai_data),
            auto_progress=data.get("auto_progress", True),
            max_retries_per_sprint=data.get("max_retries_per_sprint", 3),
            knowledge_injection=data.get("knowledge_injection", True),
            verification_enabled=data.get("verification_enabled", True),
        )


def load_config(config_path: str = "config.yaml") -> SprintCycleConfig:
    """加载配置文件"""
    path = Path(config_path)
    if not path.exists():
        return SprintCycleConfig()
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    return SprintCycleConfig.from_dict(data)


def save_config(config: SprintCycleConfig, config_path: str = "config.yaml"):
    """保存配置文件"""
    data = {
        "project_name": config.project_name,
        "chorus": {
            "base_url": config.chorus.base_url,
            "api_key": config.chorus.api_key,
            "timeout": config.chorus.timeout,
            "max_retries": config.chorus.max_retries,
        },
        "database": {
            "type": config.database.type,
            "path": config.database.path,
            "host": config.database.host,
            "port": config.database.port,
            "name": config.database.name,
            "user": config.database.user,
            "password": config.database.password,
        },
        "ai": {
            "provider": config.ai.provider,
            "api_key": config.ai.api_key,
            "model": config.ai.model,
            "base_url": config.ai.base_url,
        },
        "auto_progress": config.auto_progress,
        "max_retries_per_sprint": config.max_retries_per_sprint,
        "knowledge_injection": config.knowledge_injection,
        "verification_enabled": config.verification_enabled,
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
