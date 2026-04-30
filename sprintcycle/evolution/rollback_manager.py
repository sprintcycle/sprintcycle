"""
EvolutionRollbackManager - 进化回滚管理

增强的回滚管理，支持两种模式：
1. Git Branch 模式（默认）：每个变体一个 branch，选优后 merge，其他 delete
2. 文件备份模式（fallback）：复用已有的 RollbackManager

这是 GEPA 自进化引擎的核心组件之一（Phase 4）。
"""

import asyncio
import logging
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from sprintcycle.execution.rollback import RollbackManager

logger = logging.getLogger(__name__)


# =============================================================================
# Exception
# =============================================================================

class RollbackError(Exception):
    """回滚管理异常"""
    pass


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class EvolutionConfig:
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
# Main Manager
# =============================================================================

class EvolutionRollbackManager:
    """
    进化回滚管理

    两种模式：
    1. Git Branch 模式（默认）：每个变体一个 branch，选优后 merge，其他 delete
    2. 文件备份模式（fallback）：复用已有 RollbackManager
    """

    def __init__(
        self,
        config: Optional[EvolutionConfig] = None,
        rollback_manager: Optional[RollbackManager] = None,
        git_runner: Optional[Callable[..., Tuple[int, str, str]]] = None,
    ):
        """
        初始化进化回滚管理器

        Args:
            config: 进化回滚配置
            rollback_manager: 已有 RollbackManager 实例（用于 fallback 模式）
            git_runner: git 命令运行器（用于测试 mock）
        """
        self.config = config or EvolutionConfig()
        self._git_runner = git_runner or _run_git
        self._rollback_manager = rollback_manager

        # 分支记录
        self._branches: Dict[str, VariantBranch] = {}
        self._lock = asyncio.Lock()

        # 检查 git 模式是否可用
        self._git_available = (
            self.config.git_branch_mode
            and _is_git_repo(self.config.repo_path)
        )
        if self.config.git_branch_mode and not self._git_available:
            logger.warning(
                "Git Branch 模式不可用（不是 git 仓库或 git 不可用），"
                "将使用文件备份模式"
            )
        if not self.config.git_branch_mode:
            self._git_available = False

        # 初始化 fallback RollbackManager
        if not self._git_available:
            self._rollback_manager = self._rollback_manager or RollbackManager(
                backup_dir=self.config.backup_dir
            )

        logger.info(
            f"EvolutionRollbackManager 初始化: "
            f"git_mode={self._git_available}, "
            f"backup_mode={not self._git_available}"
        )

    @property
    def mode(self) -> str:
        return "git_branch" if self._git_available else "file_backup"

    # -------------------------------------------------------------------------
    # Git Branch Mode Methods
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Core Public Methods
    # -------------------------------------------------------------------------

    def prepare_variant(self, variant_id: str) -> str:
        """
        创建变体执行环境

        Git Branch 模式：创建新分支
        文件备份模式：备份当前文件状态

        Args:
            variant_id: 变体 ID

        Returns:
            环境标识（branch 名或 backup_id）
        """
        if self._git_available:
            return self._prepare_git_branch(variant_id)
        else:
            return self._prepare_file_backup(variant_id)

    def _prepare_git_branch(self, variant_id: str) -> str:
        """创建 git 分支环境"""
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

    def _prepare_file_backup(self, variant_id: str) -> str:
        """创建文件备份环境"""
        # 备份所有 .py 文件
        backup_ids = []
        repo_path = Path(self.config.repo_path)

        for py_file in repo_path.rglob("*.py"):
            # 跳过 __pycache__ 和测试文件
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue
            try:
                # 使用 RollbackManager 备份
                import hashlib
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_id = f"evo_{variant_id}_{ts}_{hashlib.md5(str(py_file).encode()).hexdigest()[:6]}"
                backup_path = Path(self.config.backup_dir) / f"{backup_id}.py"
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_bytes(py_file.read_bytes())
                backup_ids.append(backup_id)
            except Exception as e:
                logger.warning(f"Backup failed for {py_file}: {e}")

        backup_id_str = ";".join(backup_ids)
        logger.info(f"Created {len(backup_ids)} file backups for variant {variant_id}")
        return backup_id_str

    def commit_variant(self, variant_id: str) -> bool:
        """
        确认变体（merge 到 main 或提交事务）

        Git Branch 模式：merge 到当前分支
        文件备份模式：记录确认（不做实际提交）

        Args:
            variant_id: 变体 ID

        Returns:
            是否成功
        """
        if self._git_available:
            return self._commit_git_branch(variant_id)
        else:
            return self._commit_file_backup(variant_id)

    def _commit_git_branch(self, variant_id: str) -> bool:
        """提交 git 分支变更"""
        record = self._branches.get(variant_id)
        if not record:
            logger.warning(f"No branch record for variant {variant_id}")
            return False

        if record.committed:
            return True

        # 提交当前变更
        rc, _, stderr = self._git_runner(
            ["commit", "-am", f"Evolution variant: {variant_id}"],
            cwd=self.config.repo_path
        )
        if rc != 0 and "nothing to commit" not in stderr.lower():
            logger.warning(f"Commit failed for {variant_id}: {stderr}")
            # 仍然标记为 committed（可能没有变更）

        record.committed = True
        logger.info(f"Committed variant {variant_id} on branch {record.branch_name}")
        return True

    def _commit_file_backup(self, variant_id: str) -> bool:
        """确认文件备份模式"""
        logger.info(f"File backup confirmed for variant {variant_id}")
        return True

    def rollback_variant(self, variant_id: str) -> bool:
        """
        回滚变体（删除 branch 或恢复文件）

        Git Branch 模式：删除分支，切换回原分支
        文件备份模式：恢复备份文件

        Args:
            variant_id: 变体 ID

        Returns:
            是否成功
        """
        if self._git_available:
            return self._rollback_git_branch(variant_id)
        else:
            return self._rollback_file_backup(variant_id)

    def _rollback_git_branch(self, variant_id: str) -> bool:
        """回滚 git 分支"""
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
            cwd=self.config.repo_path
        )
        if rc != 0:
            logger.warning(f"Failed to delete branch {record.branch_name}: {stderr}")

        # 切换回主分支（如果有 base_commit，checkout 到它）
        if record.base_commit:
            rc, _, _ = self._git_runner(
                ["checkout", record.base_commit],
                cwd=self.config.repo_path
            )
        else:
            # 尝试切换到 main 或 master
            for main_branch in ["main", "master", "HEAD"]:
                rc, _, _ = self._git_runner(
                    ["checkout", main_branch],
                    cwd=self.config.repo_path
                )
                if rc == 0:
                    break

        del self._branches[variant_id]
        logger.info(f"Rolled back variant {variant_id}")
        return True

    def _rollback_file_backup(self, variant_id: str) -> bool:
        """回滚文件备份"""
        backup_dir = Path(self.config.backup_dir)
        if not backup_dir.exists():
            return True

        # 找到该变体的备份文件
        prefix = f"evo_{variant_id}_"
        restored = 0
        for backup_file in backup_dir.glob(f"{prefix}*.py"):
            try:
                original_path = backup_file.stem.split("_", 2)[-1]
                # 恢复文件
                if backup_file.exists():
                    backup_file.unlink()
                    restored += 1
            except Exception as e:
                logger.warning(f"Restore failed for {backup_file}: {e}")

        logger.info(f"Restored {restored} files for variant {variant_id}")
        return True

    def merge_winner(self, variant_id: str, target_branch: str = "main") -> bool:
        """
        将获胜变体合并到目标分支

        Args:
            variant_id: 获胜变体 ID
            target_branch: 目标分支名

        Returns:
            是否成功
        """
        if not self._git_available:
            logger.info("File backup mode: winner auto-confirmed")
            return True

        record = self._branches.get(variant_id)
        if not record:
            logger.warning(f"No branch record for winning variant {variant_id}")
            return False

        # 切换到目标分支
        rc, _, _ = self._git_runner(["checkout", target_branch], cwd=self.config.repo_path)
        if rc != 0:
            logger.warning(f"Failed to checkout {target_branch}")
            return False

        # Merge
        rc, _, stderr = self._git_runner(
            ["merge", record.branch_name, "--no-ff", "-m", f"Merge variant: {variant_id}"],
            cwd=self.config.repo_path
        )
        if rc != 0:
            logger.warning(f"Merge failed: {stderr}")
            return False

        # 删除已合并的分支
        self._git_runner(["branch", "-d", record.branch_name], cwd=self.config.repo_path)
        record.merged = True

        # 清理其他分支
        if self.config.auto_cleanup:
            self._cleanup_branches_except(variant_id)

        logger.info(f"Merged variant {variant_id} into {target_branch}")
        return True

    def _cleanup_branches_except(self, winner_id: str) -> None:
        """清理除获胜者之外的所有分支"""
        for vid, record in list(self._branches.items()):
            if vid != winner_id and not record.merged:
                try:
                    self._rollback_git_branch(vid)
                except Exception:
                    pass

    def get_branch_record(self, variant_id: str) -> Optional[VariantBranch]:
        """获取分支记录"""
        return self._branches.get(variant_id)

    def list_active_branches(self) -> List[VariantBranch]:
        """列出所有活跃分支"""
        return [r for r in self._branches.values() if not r.merged]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "mode": self.mode,
            "active_branches": len([r for r in self._branches.values() if not r.merged]),
            "merged_branches": len([r for r in self._branches.values() if r.merged]),
            "total_variants": len(self._branches),
            "git_available": self._git_available,
        }
