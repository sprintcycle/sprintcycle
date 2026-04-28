"""
RollbackManager - 回滚管理器

实现代码修改的自动备份和回滚功能。
"""

import asyncio
import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BackupRecord:
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
    success: bool
    backup_id: str
    restored_file: str
    message: str = ""
    duration: float = 0.0


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, backup_dir: str = ".sprintcycle/backups", max_backups_per_file: int = 10, enable_compression: bool = False):
        self.backup_dir = Path(backup_dir)
        self.max_backups_per_file = max_backups_per_file
        self.enable_compression = enable_compression
        self._backups: Dict[str, BackupRecord] = {}
        self._file_backups: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        try:
            asyncio.create_task(self._load_index())
        except RuntimeError:
            # No running event loop, will load synchronously later
            pass
    
    def _generate_backup_id(self, file_path: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"bk_{timestamp}_{hashlib.md5(f'{file_path}:{timestamp}'.encode()).hexdigest()[:8]}"
    
    def _compute_file_hash(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    async def backup(self, file_path: str, description: str = "", operation: str = "modify", **metadata) -> Optional[BackupRecord]:
        async with self._lock:
            try:
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    logger.warning(f"File not found: {file_path}")
                    return None
                
                backup_id = self._generate_backup_id(file_path)
                backup_subdir = self.backup_dir / Path(file_path).parent.name
                backup_subdir.mkdir(parents=True, exist_ok=True)
                backup_path = backup_subdir / f"{backup_id}{file_path_obj.suffix}"
                
                shutil.copy2(file_path_obj, backup_path)
                
                record = BackupRecord(
                    backup_id=backup_id, file_path=str(file_path), backup_path=str(backup_path),
                    timestamp=datetime.now(), file_hash=self._compute_file_hash(file_path_obj),
                    file_size=file_path_obj.stat().st_size, description=description, operation=operation, metadata=metadata,
                )
                
                self._backups[backup_id] = record
                if file_path not in self._file_backups:
                    self._file_backups[file_path] = []
                self._file_backups[file_path].append(backup_id)
                
                await self._cleanup_old_backups(file_path)
                await self._save_index()
                
                logger.info(f"Backup created: {file_path} -> {backup_id}")
                return record
            except Exception as e:
                logger.error(f"Backup failed: {file_path}, {e}")
                return None
    
    async def rollback(self, backup_id: str) -> RollbackResult:
        import time
        start_time = time.time()
        async with self._lock:
            try:
                record = self._backups.get(backup_id)
                if not record:
                    return RollbackResult(success=False, backup_id=backup_id, restored_file="", message=f"Backup not found: {backup_id}")
                
                backup_path = Path(record.backup_path)
                if not backup_path.exists():
                    return RollbackResult(success=False, backup_id=backup_id, restored_file=record.file_path, message=f"Backup file missing")
                
                current_path = Path(record.file_path)
                if current_path.exists():
                    current_backup_id = self._generate_backup_id(record.file_path)
                    shutil.copy2(current_path, self.backup_dir / f"{current_backup_id}_pre_rollback{current_path.suffix}")
                
                shutil.copy2(backup_path, current_path)
                
                if record.file_path in self._file_backups:
                    bk_list = self._file_backups[record.file_path]
                    if backup_id in bk_list:
                        bk_list.remove(backup_id)
                        bk_list.append(backup_id)
                
                await self._save_index()
                logger.info(f"Rollback successful: {backup_id} -> {record.file_path}")
                return RollbackResult(success=True, backup_id=backup_id, restored_file=record.file_path,
                                      message=f"Rolled back to {record.timestamp.isoformat()}", duration=time.time() - start_time)
            except Exception as e:
                logger.error(f"Rollback failed: {backup_id}, {e}")
                return RollbackResult(success=False, backup_id=backup_id, restored_file="", message=f"Rollback failed: {e}")
    
    async def restore_batch(self, backup_ids: List[str]) -> List[RollbackResult]:
        return [await self.rollback(bid) for bid in backup_ids]
    
    def list_backups(self, file_path: str) -> List[BackupRecord]:
        backup_ids = self._file_backups.get(file_path, [])
        return [self._backups[bid] for bid in reversed(backup_ids) if bid in self._backups]
    
    def get_backup(self, backup_id: str) -> Optional[BackupRecord]:
        return self._backups.get(backup_id)
    
    async def cleanup(self, max_age_days: int = 7, max_backups: int = 100) -> int:
        async with self._lock:
            cleaned = 0
            cutoff = datetime.now().timestamp() - (max_age_days * 86400)
            to_remove = [bid for bid, r in self._backups.items() if r.timestamp.timestamp() < cutoff]
            for backup_id in list(self._backups.keys())[:-max_backups]:
                if backup_id not in to_remove:
                    to_remove.append(backup_id)
            for backup_id in to_remove:
                record = self._backups.get(backup_id)
                if record:
                    backup_path = Path(record.backup_path)
                    if backup_path.exists():
                        backup_path.unlink()
                    if record.file_path in self._file_backups and backup_id in self._file_backups[record.file_path]:
                        self._file_backups[record.file_path].remove(backup_id)
                    del self._backups[backup_id]
                    cleaned += 1
            if cleaned > 0:
                await self._save_index()
            return cleaned
    
    async def _cleanup_old_backups(self, file_path: str) -> None:
        if file_path not in self._file_backups:
            return
        while len(self._file_backups[file_path]) > self.max_backups_per_file:
            oldest_id = self._file_backups[file_path][0]
            record = self._backups.get(oldest_id)
            if record:
                backup_path = Path(record.backup_path)
                if backup_path.exists():
                    backup_path.unlink()
                del self._backups[oldest_id]
                self._file_backups[file_path].pop(0)
    
    async def _save_index(self) -> None:
        try:
            with open(self.backup_dir / "index.json", "w", encoding="utf-8") as f:
                json.dump({"backups": {bid: r.to_dict() for bid, r in self._backups.items()}, "file_backups": self._file_backups}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save index failed: {e}")
    
    async def _load_index(self) -> None:
        try:
            index_file = self.backup_dir / "index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._backups = {bid: BackupRecord.from_dict(d) for bid, d in data.get("backups", {}).items()}
                self._file_backups = data.get("file_backups", {})
                logger.info(f"Loaded {len(self._backups)} backup records")
        except Exception as e:
            logger.error(f"Load index failed: {e}")


_default_manager: Optional[RollbackManager] = None


def get_rollback_manager() -> RollbackManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = RollbackManager()
    return _default_manager
