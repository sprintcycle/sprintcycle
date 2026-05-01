"""
EvolutionRollbackManager 测试套件
"""

import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sprintcycle.execution.rollback import (
    RollbackConfig,
    VariantBranch,
    RollbackError,
    _run_git,
    _is_git_repo,
)
from sprintcycle.evolution.rollback_manager import EvolutionRollbackManager


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def make_mock_runner(responses=None):
    """Create a git mock runner that returns (rc, stdout, stderr) tuples"""
    if responses is None:
        responses = {}
    def runner(args, cwd=".", timeout=30):
        key = " ".join(args[:2])
        resp = responses.get(key, (0, "", ""))
        return resp  # Return tuple (rc, stdout, stderr)
    return runner


# =============================================================================
# Config Tests
# =============================================================================

class TestRollbackConfig:
    def test_default_values(self):
        config = RollbackConfig()
        assert config.git_branch_mode is True
        assert config.branch_prefix == "evo/variant-"
        assert config.max_branches == 20
        assert config.auto_cleanup is True

    def test_custom_values(self):
        config = RollbackConfig(git_branch_mode=False, backup_dir="/tmp/backups")
        assert config.git_branch_mode is False
        assert config.backup_dir == "/tmp/backups"


# =============================================================================
# VariantBranch Tests
# =============================================================================

class TestVariantBranch:
    def test_default_values(self):
        branch = VariantBranch(variant_id="v1", branch_name="evo/v1", base_commit="abc")
        assert branch.committed is False
        assert branch.merged is False
        assert branch.created_at is not None


# =============================================================================
# Git Helper Tests
# =============================================================================

class TestGitHelpers:
    def test_run_git_success(self, temp_dir):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="HEAD", stderr="")
            rc, stdout, stderr = _run_git(["rev-parse", "HEAD"], cwd=temp_dir)
            assert rc == 0
            assert stdout == "HEAD"

    def test_run_git_failure(self, temp_dir):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            rc, stdout, stderr = _run_git(["rev-parse", "HEAD"], cwd=temp_dir)
            assert rc == 1

    def test_run_git_timeout(self, temp_dir):
        import subprocess
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 30)):
            rc, stdout, stderr = _run_git(["rev-parse", "HEAD"], cwd=temp_dir)
            assert rc == -1
            assert "timed out" in stderr


# =============================================================================
# Git Branch Mode Tests
# =============================================================================

class TestGitBranchMode:
    def test_prepare_variant_creates_branch(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        responses = {
            "rev-parse --git-dir": (0, "/git/dir", ""),
            "rev-parse HEAD": (0, "abc123def", ""),
            "branch -D evo/v": (0, "", ""),
        }
        mock_runner = make_mock_runner(responses)
        manager = EvolutionRollbackManager(git_runner=mock_runner)

        with patch.object(manager, '_git_available', True):
            with patch.object(manager, '_cleanup_old_branches', return_value=0):
                branch_name = manager._prepare_git_branch("variant_test_001")
        assert branch_name.startswith(config.branch_prefix)
        # underscore replaced with dash in branch name
        assert "variant-test-001" in branch_name

    def test_prepare_variant_creates_record(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        responses = {
            "rev-parse --git-dir": (0, "/git/dir", ""),
            "rev-parse HEAD": (0, "abc123", ""),
        }
        mock_runner = make_mock_runner(responses)
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        with patch.object(manager, '_cleanup_old_branches', return_value=0):
            branch_name = manager._prepare_git_branch("var_rec_test")
        record = manager.get_branch_record("var_rec_test")
        assert record is not None
        assert record.variant_id == "var_rec_test"

    def test_commit_git_branch(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        record = VariantBranch(variant_id="commit_test", branch_name="evo/commit-test", base_commit="abc")
        manager._branches["commit_test"] = record

        success = manager._commit_git_branch("commit_test")
        assert success is True
        assert record.committed is True

    def test_rollback_git_branch(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        record = VariantBranch(variant_id="rb_test", branch_name="evo/rb-test", base_commit="abc123")
        manager._branches["rb_test"] = record

        success = manager._rollback_git_branch("rb_test")
        assert success is True
        assert "rb_test" not in manager._branches

    def test_rollback_already_merged_fails(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        record = VariantBranch(variant_id="merged_test", branch_name="evo/merged", base_commit="abc", merged=True)
        manager._branches["merged_test"] = record

        success = manager._rollback_git_branch("merged_test")
        assert success is False


# =============================================================================
# File Backup Mode Tests
# =============================================================================

class TestFileBackupMode:
    def test_init_file_backup_mode(self, temp_dir):
        # When git is not available, manager falls back to file_backup mode
        config = RollbackConfig(git_branch_mode=False, backup_dir=temp_dir + "/backups")
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=False):
            manager = EvolutionRollbackManager(git_branch_mode=False, backup_dir=temp_dir + "/backups")
            assert manager.mode == "file_backup"

    def test_prepare_file_backup_returns_string(self, temp_dir):
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir, backup_dir=temp_dir + "/backups")
        manager = EvolutionRollbackManager()
        backup_id = manager._prepare_file_backup("fb_test_var")
        assert isinstance(backup_id, str)

    def test_commit_file_backup(self, temp_dir):
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir)
        manager = EvolutionRollbackManager()
        success = manager._commit_file_backup("any_var")
        assert success is True

    def test_rollback_file_backup(self, temp_dir):
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir, backup_dir=temp_dir + "/backups")
        manager = EvolutionRollbackManager()
        manager._prepare_file_backup("rollback_fb_test")
        success = manager._rollback_file_backup("rollback_fb_test")
        assert success is True


# =============================================================================
# Mode Switching Tests
# =============================================================================

class TestModeSwitching:
    def test_git_mode_when_git_available(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=True):
            responses = {"rev-parse --git-dir": (0, "/git/dir")}
            mock_runner = make_mock_runner(responses)
            manager = EvolutionRollbackManager(git_runner=mock_runner)
            assert manager.mode == "git_branch"

    def test_fallback_to_file_when_no_git(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir, backup_dir=temp_dir + "/bk")
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=False):
            manager = EvolutionRollbackManager()
            assert manager.mode == "file_backup"

    def test_explicit_file_backup_mode(self, temp_dir):
        # When git_branch_mode=False, should use file_backup mode regardless of git availability
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir, backup_dir=temp_dir + "/bk")
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=True):
            manager = EvolutionRollbackManager(git_branch_mode=False, backup_dir=temp_dir + "/bk")
            assert manager.mode == "file_backup"


# =============================================================================
# Public API Tests
# =============================================================================

class TestPublicAPI:
    def test_prepare_variant_routes_correctly(self, temp_dir):
        # With git_branch_mode=False, prepare_variant should call _prepare_file_backup
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir, backup_dir=temp_dir + "/bk")
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=False):
            manager = EvolutionRollbackManager(git_branch_mode=False, backup_dir=temp_dir + "/bk")

            with patch.object(manager, '_prepare_file_backup', return_value="backup_id_123") as mock_prep:
                result = manager.prepare_variant("test_var")
                mock_prep.assert_called_once_with("test_var")

    def test_commit_variant_routes_correctly(self, temp_dir):
        # With git_branch_mode=False, commit_variant should call _commit_file_backup
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir, backup_dir=temp_dir + "/bk")
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=False):
            manager = EvolutionRollbackManager(git_branch_mode=False, backup_dir=temp_dir + "/bk")

            with patch.object(manager, '_commit_file_backup', return_value=True) as mock_commit:
                result = manager.commit_variant("test_var")
                mock_commit.assert_called_once_with("test_var")
                assert result is True

    def test_rollback_variant_routes_correctly(self, temp_dir):
        # With git_branch_mode=False, rollback_variant should call _rollback_file_backup
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir, backup_dir=temp_dir + "/bk")
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=False):
            manager = EvolutionRollbackManager(git_branch_mode=False, backup_dir=temp_dir + "/bk")

            with patch.object(manager, '_rollback_file_backup', return_value=True) as mock_rb:
                result = manager.rollback_variant("test_var")
                mock_rb.assert_called_once_with("test_var")
                assert result is True

    def test_merge_winner_git_mode(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir, auto_cleanup=True)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        record = VariantBranch(variant_id="winner_var", branch_name="evo/winner", base_commit="abc")
        manager._branches["winner_var"] = record

        success = manager.merge_winner("winner_var", "main")
        assert success is True
        assert record.merged is True

    def test_merge_winner_file_mode(self, temp_dir):
        # In file_backup mode, merge_winner requires a record to return True
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir, backup_dir=temp_dir + "/bk")
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=False):
            manager = EvolutionRollbackManager(git_branch_mode=False, backup_dir=temp_dir + "/bk")
            
            # First prepare the variant to create a record
            manager._prepare_file_backup("any_var")
            
            # In file_backup mode without git, merge_winner returns True (winner auto-confirmed)
            success = manager.merge_winner("any_var", "main")
            assert success is True

    def test_list_active_branches(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        record1 = VariantBranch(variant_id="v1", branch_name="evo/v1", base_commit="a", merged=False)
        record2 = VariantBranch(variant_id="v2", branch_name="evo/v2", base_commit="b", merged=True)
        manager._branches["v1"] = record1
        manager._branches["v2"] = record2

        active = manager.list_active_branches()
        assert len(active) == 1
        assert active[0].variant_id == "v1"

    def test_get_stats(self, temp_dir):
        # The implementation uses a `stats` property, not a `get_stats()` method
        config = RollbackConfig(git_branch_mode=False, repo_path=temp_dir, backup_dir=temp_dir + "/bk")
        with patch('sprintcycle.evolution.rollback_manager._is_git_repo', return_value=False):
            manager = EvolutionRollbackManager(git_branch_mode=False, backup_dir=temp_dir + "/bk")
            stats = manager.stats  # Use property, not method
            assert "mode" in stats
            assert stats["mode"] == "file_backup"
            assert "total_variants" in stats

    def test_get_branch_record(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True
        record = VariantBranch(variant_id="rec_test", branch_name="evo/rec", base_commit="x")
        manager._branches["rec_test"] = record
        retrieved = manager.get_branch_record("rec_test")
        assert retrieved is not None
        assert retrieved.variant_id == "rec_test"


# =============================================================================
# Exception Tests
# =============================================================================

class TestExceptions:
    def test_rollback_error_message(self):
        error = RollbackError("Branch creation failed")
        assert str(error) == "Branch creation failed"

    def test_rollback_error_inheritance(self):
        error = RollbackError("test")
        assert isinstance(error, Exception)

    def test_prepare_git_raises_on_failure(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        responses = {
            "rev-parse --git-dir": (0, "/git/dir", ""),
            "rev-parse HEAD": (0, "abc", ""),
            "branch -D evo/": (0, "", ""),
            "checkout -b": (1, "", "fatal: could not create branch"),
            "checkout": (0, "", ""),  # Default checkout (for existing branches)
        }
        mock_runner = make_mock_runner(responses)
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        with patch.object(manager, '_cleanup_old_branches', return_value=0):
            # Use a unique variant_id to avoid collision with manager init
            with pytest.raises(RollbackError) as exc_info:
                manager._prepare_git_branch("unique_fail_variant_xyz")
        assert "Failed to create branch" in str(exc_info.value)


# =============================================================================
# Boundary Condition Tests
# =============================================================================

class TestBoundaryConditions:
    def test_prepare_variant_max_branches(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir, max_branches=3)
        responses = {
            "rev-parse --git-dir": (0, "/git/dir", ""),
            "rev-parse HEAD": (0, "abc123", ""),
        }
        mock_runner = make_mock_runner(responses)
        manager = EvolutionRollbackManager(git_runner=mock_runner, max_branches=3)
        manager._git_available = True

        with patch.object(manager, '_cleanup_old_branches', return_value=2) as mock_cleanup:
            with patch.object(manager, '_create_branch_name', return_value="evo/v0"):
                # Create 5 branches, cleanup should be called when exceeding max_branches
                for i in range(5):
                    try:
                        manager._prepare_git_branch(f"max_test_{i}")
                    except RollbackError:
                        pass
            # cleanup should be called when we exceed max_branches (at index 3, when len >= 3)
            assert mock_cleanup.call_count >= 1

    def test_rollback_nonexistent_variant(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        success = manager._rollback_git_branch("nonexistent_variant")
        assert success is False

    def test_commit_nonexistent_variant(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        success = manager._commit_git_branch("nonexistent_variant")
        assert success is False

    def test_cleanup_old_branches(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        responses = {
            "branch --format": (0, "evo/v1-0101 2024-01-01\nevo/v2-0102 2024-01-02\nmain 2024-01-03", ""),
        }
        mock_runner = make_mock_runner(responses)
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        cleaned = manager._cleanup_old_branches()
        assert isinstance(cleaned, int)

    def test_merge_winner_no_record(self, temp_dir):
        config = RollbackConfig(git_branch_mode=True, repo_path=temp_dir)
        mock_runner = make_mock_runner()
        manager = EvolutionRollbackManager(git_runner=mock_runner)
        manager._git_available = True

        success = manager.merge_winner("no_such_variant", "main")
        assert success is False
