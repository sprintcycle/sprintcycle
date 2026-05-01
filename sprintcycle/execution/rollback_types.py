"""
Rollback Types - 回滚相关的数据类型和配置
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class BackupRecord:
    """备份记录"""
    backup_id: str
    file_path: str
    backup_path: str
    timestamp: datetime
    file_hash: str
    file_size: int
    description: str = ""
    operation: str = "modify"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "backup_id": self.backup_id, "file_path": self.file_path, "backup_path": self.backup_path,
            "timestamp": self.timestamp.isoformat(), "file_hash": self.file_hash, "file_size": self.file_size,
            "description": self.description, "operation": self.operation, "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupRecord":
        data = data.copy()
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class RollbackResult:
    """回滚结果"""
    success: bool
    backup_id: str
    restored_file: str
    message: str = ""
    duration: float = 0.0


class RollbackError(Exception):
    """回滚管理异常"""
    pass


@dataclass
class VariantBranch:
    """变体分支记录"""
    variant_id: str
    branch_name: str
    base_commit: str
    created_at: datetime = field(default_factory=datetime.now)
    committed: bool = False
    merged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
