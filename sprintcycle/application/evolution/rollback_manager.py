"""EvolutionRollbackManager - 进化回滚管理（精简版）。

支持两种模式：
1. Git Branch 模式（默认）：每个变体一个 branch
2. 文件备份模式（fallback）
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

try:
    from sprintcycle.execution.rollback import (
        GitRollbackMixin,
        RollbackConfig,
        RollbackError,
        VariantBranch,
        _is_git_repo,
        _run_git,
    )
    HAS_GIT_ROLLBACK = True
except ImportError:
    HAS_GIT_ROLLBACK = False
    GitRollbackMixin = object
    RollbackConfig = None
    RollbackError = Exception
    VariantBranch = None


class EvolutionRollbackManager:
    """进化回滚管理（精简版）。"""

    def __init__(
        self,
        git_branch_mode: bool = True,
        repo_path: str = ".",
        branch_prefix: str = "evo/variant-",
        backup_dir: str = ".sprintcycle/evo_backups",
        auto_cleanup: bool = True,
        max_branches: int = 20,
        git_runner: Optional[Any] = None,
    ):
        self._git_runner = git_runner
        if not HAS_GIT_ROLLBACK:
            logger.warning("sprintcycle.execution.rollback not available")
            self._git_available = False
            self._branches: Dict[str, Any] = {}
            self.config = type("Config", (), {
                "git_branch_mode": git_branch_mode,
                "repo_path": repo_path,
                "branch_prefix": branch_prefix,
                "backup_dir": backup_dir,
                "auto_cleanup": auto_cleanup,
                "max_branches": max_branches,
            })()
            return

        self.config = RollbackConfig(
            git_branch_mode=git_branch_mode,
            repo_path=repo_path,
            branch_prefix=branch_prefix,
            backup_dir=backup_dir,
            auto_cleanup=auto_cleanup,
            max_branches=max_branches,
        )
        GitRollbackMixin.__init__(self, **self.config.__dict__)
        if self._git_runner is None or self._git_runner is _run_git:
            self._git_runner = git_runner if git_runner is not None else _run_git
        self._git_available = git_branch_mode and _is_git_repo(repo_path)
        self._branches: Dict[str, Any] = {}

        if git_branch_mode and not self._git_available:
            logger.debug("Git Branch 模式不可用，使用文件备份模式")

    @property
    def mode(self) -> str:
        return "git_branch" if self._git_available else "file_backup"

    def prepare_variant(self, variant_id: str) -> str:
        """创建变体执行环境"""
        if self._git_available and HAS_GIT_ROLLBACK:
            return self._prepare_git_branch(variant_id)
        return self._prepare_file_backup(variant_id)

    def _prepare_git_branch(self, variant_id: str) -> str:
        """创建 git 分支环境"""
        from datetime import datetime

        safe_id = variant_id.replace("/", "-").replace("_", "-")[:20]
        timestamp = datetime.now().strftime("%m%d%H%M")
        branch_name = f"{self.config.branch_prefix}{safe_id}-{timestamp}"

        rc, stdout, stderr = self._git_runner(["checkout", "-b", branch_name], cwd=self.config.repo_path)
        if rc != 0:
            raise RollbackError(f"Failed to create branch {branch_name}: {stderr}")

        record = VariantBranch(
            variant_id=variant_id,
            branch_name=branch_name,
            base_commit="",
        )
        self._branches[variant_id] = record
        return branch_name

    def _prepare_file_backup(self, variant_id: str) -> str:
        """创建文件备份环境"""
        import hashlib
        from datetime import datetime

        backup_ids = []
        repo_path = Path(self.config.repo_path)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        for py_file in repo_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue
            try:
                backup_id = f"evo_{variant_id}_{ts}_{hashlib.md5(str(py_file).encode()).hexdigest()[:6]}"
                backup_path = Path(self.config.backup_dir) / f"{backup_id}.py"
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.write_bytes(py_file.read_bytes())
                backup_ids.append(backup_id)
            except Exception as e:
                logger.debug(f"Backup failed for {py_file}: {e}")

        return ";".join(backup_ids)

    def commit_variant(self, variant_id: str) -> bool:
        """确认变体"""
        if self._git_available:
            record = self._branches.get(variant_id)
            if not record:
                return False
            rc, _, stderr = self._git_runner(
                ["commit", "-am", f"Evolution variant: {variant_id}"], cwd=self.config.repo_path
            )
            record.committed = True
            return rc == 0 or "nothing to commit" in stderr.lower()
        return self._commit_file_backup(variant_id)

    def _commit_git_branch(self, variant_id: str) -> bool:
        """Private alias for commit_variant used by tests."""
        return self.commit_variant(variant_id)

    def _commit_file_backup(self, variant_id: str) -> bool:
        """Confirm file backup variant (always succeeds)."""
        return True

    def _rollback_git_branch(self, variant_id: str) -> bool:
        """Roll back (delete) a git branch variant."""
        record = self._branches.get(variant_id)
        if not record:
            return False
        if getattr(record, "merged", False):
            return False
        rc, _, _ = self._git_runner(
            ["branch", "-D", record.branch_name], cwd=self.config.repo_path
        ) if self._git_available else (0, "", "")
        self._branches.pop(variant_id, None)
        return True

    def _rollback_file_backup(self, variant_id: str) -> bool:
        """Roll back (clean up) a file backup variant."""
        backup_dir = Path(self.config.backup_dir)
        if backup_dir.exists():
            prefix = f"evo_{variant_id}_"
            for backup_file in backup_dir.glob(f"{prefix}*.py"):
                try:
                    backup_file.unlink()
                except Exception:
                    pass
        self._branches.pop(variant_id, None)
        return True

    def _cleanup_old_branches(self, max_branches: int = 20) -> int:
        """Remove excess branches when over the limit."""
        if len(self._branches) <= max_branches:
            return 0
        excess = len(self._branches) - max_branches
        to_remove = sorted(self._branches.items(), key=lambda x: x[1].created_at if hasattr(x[1], "created_at") else "")[:excess]
        for vid, _ in to_remove:
            self._branches.pop(vid, None)
        return excess

    def get_branch_record(self, variant_id: str) -> Optional[VariantBranch]:
        """Get the branch record for a variant."""
        return self._branches.get(variant_id)

    def list_active_branches(self) -> List[VariantBranch]:
        """列出所有活跃（未合并）变体分支记录"""
        return [r for r in self._branches.values() if not getattr(r, "merged", False)]

    def rollback_variant(self, variant_id: str) -> bool:
        """回滚变体"""
        record = self._branches.get(variant_id)
        if not record:
            return True

        if self._git_available:
            self._git_runner(["branch", "-D", record.branch_name], cwd=self.config.repo_path)
            self._git_runner(["checkout", "main"], cwd=self.config.repo_path)
            del self._branches[variant_id]
            return True
        return self._rollback_file_backup(variant_id)

    def merge_winner(self, variant_id: str, target_branch: str = "main") -> bool:
        """将获胜变体合并到目标分支"""
        if not self._git_available:
            return True

        record = self._branches.get(variant_id)
        if not record:
            return False

        self._git_runner(["checkout", target_branch], cwd=self.config.repo_path)
        rc, _, stderr = self._git_runner(
            ["merge", record.branch_name, "--no-ff", "-m", f"Merge variant: {variant_id}"], cwd=self.config.repo_path
        )
        if rc != 0:
            logger.debug(f"Merge warning: {stderr}")

        self._git_runner(["branch", "-d", record.branch_name], cwd=self.config.repo_path)
        record.merged = True

        if self.config.auto_cleanup:
            for vid, rec in list(self._branches.items()):
                if vid != variant_id and not rec.merged:
                    self.rollback_variant(vid)

        return True

    @property
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "mode": self.mode,
            "active_branches": len([r for r in self._branches.values() if not getattr(r, 'merged', False)]),
            "total_variants": len(self._branches),
            "git_available": self._git_available,
        }
