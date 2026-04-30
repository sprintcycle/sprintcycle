"""
RollbackManager - 回滚管理器

实现代码修改的自动备份和回滚功能。
"""

import asyncio
import hashlib
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Shared Dataclasses (also used by evolution/rollback_manager.py)
# =============================================================================

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


# =============================================================================
# Evolution Shared Dataclasses
# =============================================================================

class RollbackError(Exception):
    """回滚管理异常"""
    pass


@dataclass
class RollbackConfig:
    """进化回滚配置"""
    git_branch_mode: bool = True
    repo_path: str = "."
    branch_prefix: str = "evo/variant-"
    backup_dir: str = ".sprintcycle/evo_backups"
    auto_cleanup: bool = True
    max_branches: int = 20


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


# =============================================================================
# Git Operations Helper
# =============================================================================

def _run_git(args: List[str], cwd: str = ".", timeout: int = 30) -> Tuple[int, str, str]:
    """运行 git 命令，返回 (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Git command timed out"
    except Exception as e:
        return -1, "", str(e)


def _is_git_repo(path: str) -> bool:
    """检查路径是否为 git 仓库"""
    rc, _, _ = _run_git(["rev-parse", "--git-dir"], cwd=path)
    return rc == 0


# =============================================================================
# GitRollbackMixin - Git Branch based variant management
# =============================================================================

class GitRollbackMixin:
    """
    Git 分支回滚 Mixin

    提供基于 git branch 的变体分支管理能力：
    - create_variant_branch: 创建变体分支
    - switch_to_variant: 切换到变体分支
    - rollback_to_variant: 回滚到变体分支
    - cleanup_variant_branches: 清理旧分支
    """

    def __init__(
        self,
        config: Optional[RollbackConfig] = None,
        git_runner: Optional[Callable[..., Tuple[int, str, str]]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.config = config or RollbackConfig()
        self._git_runner = git_runner or _run_git
        self._branches: Dict[str, VariantBranch] = {}
        self._lock = asyncio.Lock()

    def _create_branch_name(self, variant_id: str) -> str:
        """生成变体分支名"""
        safe_id = variant_id.replace("/", "-").replace("_", "-")[:20]
        timestamp = datetime.now().strftime("%m%d%H%M")
        return f"{self.config.branch_prefix}{safe_id}-{timestamp}"

    def _get_current_commit(self) -> str:
        """获取当前 HEAD commit"""
        rc, stdout, _ = self._git_runner(["rev-parse", "HEAD"], cwd=self.config.repo_path)
        if rc == 0:
            return stdout.strip()
        return ""

    def create_variant_branch(self, variant_id: str) -> str:
        """
        创建变体分支

        Args:
            variant_id: 变体 ID

        Returns:
            分支名

        Raises:
            RollbackError: 分支创建失败
        """
        # 检查是否已有记录
        existing = next((b for b in self._branches.values() if b.variant_id == variant_id), None)
        if existing:
            # 已存在，切换到该分支
            rc, _, _ = self._git_runner(["checkout", existing.branch_name], cwd=self.config.repo_path)
            if rc == 0:
                return existing.branch_name
            # 切换失败，删除重建
            self._git_runner(["branch", "-D", existing.branch_name], cwd=self.config.repo_path)

        # 检查分支数量限制
        if len(self._branches) >= self.config.max_branches:
            self._cleanup_old_branches()

        branch_name = self._create_branch_name(variant_id)
        base_commit = self._get_current_commit()

        # 创建并切换到新分支
        rc, _, stderr = self._git_runner(
            ["checkout", "-b", branch_name],
            cwd=self.config.repo_path
        )
        if rc != 0:
            raise RollbackError(f"Failed to create branch {branch_name}: {stderr}")

        record = VariantBranch(
            variant_id=variant_id,
            branch_name=branch_name,
            base_commit=base_commit,
        )
        self._branches[variant_id] = record
        logger.info(f"Created branch {branch_name} for variant {variant_id}")
        return branch_name

    def switch_to_variant(self, variant_id: str, repo_path: Optional[str] = None) -> bool:
        """
        切换到指定变体分支

        Args:
            variant_id: 变体 ID
            repo_path: 仓库路径（可选，默认使用 config.repo_path）

        Returns:
            是否成功
        """
        repo = repo_path or self.config.repo_path
        record = self._branches.get(variant_id)
        if not record:
            logger.warning(f"No branch record for variant {variant_id}")
            return False

        rc, _, stderr = self._git_runner(["checkout", record.branch_name], cwd=repo)
        if rc != 0:
            logger.warning(f"Failed to switch to {record.branch_name}: {stderr}")
            return False
        return True

    def rollback_to_variant(self, variant_id: str, repo_path: Optional[str] = None) -> bool:
        """
        回滚到指定变体分支（删除分支，切换回 base 或 main/master）

        Args:
            variant_id: 变体 ID
            repo_path: 仓库路径（可选，默认使用 config.repo_path）

        Returns:
            是否成功
        """
        repo = repo_path or self.config.repo_path
        record = self._branches.get(variant_id)
        if not record:
            logger.warning(f"No branch record for variant {variant_id}")
            return False

        if record.merged:
            logger.warning(f"Variant {variant_id} already merged, cannot rollback")
            return False

        # 删除分支
        rc, _, stderr = self._git_runner(
            ["branch", "-D", record.branch_name],
            cwd=repo
        )
        if rc != 0:
            logger.warning(f"Failed to delete branch {record.branch_name}: {stderr}")

        # 切换回主分支（如果有 base_commit，checkout 到它）
        if record.base_commit:
            rc, _, _ = self._git_runner(
                ["checkout", record.base_commit],
                cwd=repo
            )
        else:
            # 尝试切换到 main 或 master
            for main_branch in ["main", "master", "HEAD"]:
                rc, _, _ = self._git_runner(
                    ["checkout", main_branch],
                    cwd=repo
                )
                if rc == 0:
                    break

        del self._branches[variant_id]
        logger.info(f"Rolled back variant {variant_id}")
        return True

    def cleanup_variant_branches(self, keep_ids: List[str], repo_path: Optional[str] = None) -> int:
        """
        清理除 keep_ids 之外的所有分支

        Args:
            keep_ids: 要保留的变体 ID 列表
            repo_path: 仓库路径（可选，默认使用 config.repo_path）

        Returns:
            清理的分支数量
        """
        repo = repo_path or self.config.repo_path
        cleaned = 0
        for vid, record in list(self._branches.items()):
            if vid not in keep_ids and not record.merged:
                try:
                    rc, _, _ = self._git_runner(
                        ["branch", "-D", record.branch_name],
                        cwd=repo
                    )
                    if rc == 0:
                        del self._branches[vid]
                        cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to cleanup branch {record.branch_name}: {e}")
        return cleaned

    def _cleanup_old_branches(self) -> int:
        """清理过期分支（超过最大数量的旧分支）"""
        if not self._branches:
            return 0

        # 获取所有 evo/variant-* 分支
        rc, stdout, _ = self._git_runner(
            ["branch", "--format=%(refname:short) %(creatordate:iso)"],
            cwd=self.config.repo_path
        )
        if rc != 0:
            return 0

        branch_dates: Dict[str, str] = {}
        for line in stdout.strip().split("\n"):
            parts = line.split()
            if parts and parts[0].startswith(self.config.branch_prefix):
                branch_dates[parts[0]] = parts[1] if len(parts) > 1 else ""

        # 删除不在记录中且超过最大数量的旧分支
        active = set(b.branch_name for b in self._branches.values())
        cleanup_count = 0
        all_branches = sorted(branch_dates.keys())

        for branch in all_branches:
            if branch not in active and cleanup_count < 5:
                rc, _, _ = self._git_runner(
                    ["branch", "-D", branch],
                    cwd=self.config.repo_path
                )
                if rc == 0:
                    cleanup_count += 1

        return cleanup_count

    def get_branch_record(self, variant_id: str) -> Optional[VariantBranch]:
        """获取分支记录"""
        return self._branches.get(variant_id)

    def list_active_branches(self) -> List[VariantBranch]:
        """列出所有活跃分支"""
        return [r for r in self._branches.values() if not r.merged]


# =============================================================================
# RollbackManager
# =============================================================================

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
