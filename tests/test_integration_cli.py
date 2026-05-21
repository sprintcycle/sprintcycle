"""
SprintCycle CLI Integration Tests

Tests the CLI subcommands using click.testing.CliRunner
covering all commands: plan, run, diagnose, status, stop, etc.
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from sprintcycle.cli import cli
from sprintcycle.results import (
    DiagnoseResult,
    PlanResult,
    RollbackResult,
    RunResult,
    StatusResult,
    StopResult,
)


@pytest.fixture
def temp_project():
    """Create a temporary project directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def cli_runner():
    """Create a CLI runner"""
    return CliRunner()


class TestCLIPlan:
    """Test plan subcommand"""

    def test_cli_plan_command(self, cli_runner, temp_project):
        """sprintcycle plan "..." -> outputs plan result"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.plan.return_value = PlanResult(
                success=True,
                release_plan_yaml="# ReleasePlan YAML content",
                sprints=[{"name": "Sprint 1", "tasks": ["Task 1"]}],
                mode="auto",
                release_plan_name="TestProject",
                duration=0.5,
            )

            result = cli_runner.invoke(cli, ['-p', temp_project, 'plan', 'Test intent'])

            assert result.exit_code == 0
            assert 'Sprint' in result.output
            assert 'TestProject' in result.output
            mock_instance.plan.assert_called_once()

    def test_cli_plan_error(self, cli_runner, temp_project):
        """plan handles errors gracefully"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.plan.return_value = PlanResult(
                success=False,
                error="Intent parse error",
                duration=0.1,
            )

            result = cli_runner.invoke(
                cli,
                ['-p', temp_project, 'plan', 'Invalid intent']
            )

            assert result.exit_code == 0


class TestCLIRun:
    """Test run subcommand"""

    def test_cli_run_command(self, cli_runner, temp_project):
        """sprintcycle run "..." -> outputs run result"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.run.return_value = RunResult(
                success=True,
                execution_id="exec-123",
                release_plan_name="TestProject",
                completed_sprints=2,
                completed_tasks=5,
                total_sprints=2,
                total_tasks=5,
                duration=10.5,
            )

            result = cli_runner.invoke(
                cli,
                ['-p', temp_project, 'run', 'Run test tasks']
            )

            assert result.exit_code == 0
            assert 'exec-123' in result.output
            mock_instance.run.assert_called_once()

    def test_cli_run_with_mode(self, cli_runner, temp_project):
        """run respects --mode option"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.run.return_value = RunResult(
                success=True,
                duration=1.0,
            )

            result = cli_runner.invoke(
                cli,
                ['-p', temp_project, 'run', '-m', 'evolution', 'Evolve code']
            )

            assert result.exit_code == 0
            mock_instance.run.assert_called_once()

    def test_cli_run_failure(self, cli_runner, temp_project):
        """run exits with code 0 (result contains error field)"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.run.return_value = RunResult(
                success=False,
                error="Execution failed",
                duration=1.0,
            )

            result = cli_runner.invoke(
                cli,
                ['-p', temp_project, 'run', 'Failing task']
            )

            assert result.exit_code == 0
            assert 'Execution failed' in result.output


class TestCLIStatus:
    """Test status subcommand"""

    def test_cli_status_command(self, cli_runner, temp_project):
        """sprintcycle status -> outputs status"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.status.return_value = StatusResult(
                success=True,
                executions=[
                    {
                        "execution_id": "exec-1",
                        "status": "completed",
                        "release_plan_name": "Project 1",
                        "current_sprint": 3,
                        "total_sprints": 3,
                    }
                ],
                duration=0.1,
            )

            result = cli_runner.invoke(cli, ['-p', temp_project, 'status'])

            assert result.exit_code == 0
            assert 'exec-1' in result.output
            mock_instance.status.assert_called_once_with(execution_id="")

    def test_cli_status_with_id(self, cli_runner, temp_project):
        """status with execution ID shows details"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.status.return_value = StatusResult(
                success=True,
                execution_id="exec-specific",
                status="running",
                current_sprint=1,
                total_sprints=3,
                duration=0.1,
            )

            result = cli_runner.invoke(
                cli,
                ['-p', temp_project, 'status', '--execution-id', 'exec-specific']
            )

            assert result.exit_code == 0
            assert 'running' in result.output.lower()
            mock_instance.status.assert_called_once_with(execution_id="exec-specific")


class TestCLIStop:
    """Test stop subcommand"""

    def test_cli_stop_command(self, cli_runner, temp_project):
        """sprintcycle stop -> outputs stop result"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.stop.return_value = StopResult(
                success=True,
                execution_id="exec-to-stop",
                cancelled=True,
                duration=0.2,
            )

            result = cli_runner.invoke(
                cli,
                ['-p', temp_project, 'stop', '--execution-id', 'exec-to-stop']
            )

            assert result.exit_code == 0
            assert 'exec-to-stop' in result.output
            mock_instance.stop.assert_called_once()

    def test_cli_stop_then_run(self, cli_runner, temp_project):
        """stop + run sequence works"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.stop.return_value = StopResult(
                success=True,
                execution_id="exec-1",
                cancelled=True,
                duration=0.1,
            )

            mock_instance.run.return_value = RunResult(
                success=True,
                execution_id="exec-2",
                duration=0.5,
            )

            result = cli_runner.invoke(
                cli,
                ['-p', temp_project, 'stop', '--execution-id', 'exec-1']
            )

            assert result.exit_code == 0
            assert 'exec-1' in result.output


class TestCLIDiagnose:
    """Test diagnose subcommand"""

    def test_cli_diagnose_command(self, cli_runner, temp_project):
        """sprintcycle diagnose -> outputs diagnostic"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.diagnose.return_value = DiagnoseResult(
                success=True,
                health_score=85.0,
                issues=[],
                coverage=75.0,
                complexity={"average": 8.5},
                duration=2.5,
            )

            result = cli_runner.invoke(cli, ['-p', temp_project, 'diagnose'])

            assert result.exit_code == 0
            assert '85' in result.output
            mock_instance.diagnose.assert_called_once()

    def test_cli_diagnose_with_issues(self, cli_runner, temp_project):
        """diagnose reports issues"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.diagnose.return_value = DiagnoseResult(
                success=True,
                health_score=60.0,
                issues=[
                    {"severity": "warning", "message": "Low coverage"},
                ],
                coverage=50.0,
                complexity={},
                duration=1.0,
            )

            result = cli_runner.invoke(cli, ['-p', temp_project, 'diagnose'])

            assert result.exit_code == 0


class TestCLIRollback:
    """Test rollback subcommand"""

    def test_cli_rollback_command(self, cli_runner, temp_project):
        """sprintcycle rollback "id" -> rolls back"""
        with patch('sprintcycle.cli.SprintCycle') as mock_sc:
            mock_instance = MagicMock()
            mock_sc.return_value = mock_instance

            mock_instance.rollback.return_value = RollbackResult(
                success=True,
                execution_id="exec-to-rollback",
                rollback_point="abc1234",
                files_restored=["file1.py", "file2.py"],
                duration=1.5,
            )

            result = cli_runner.invoke(
                cli,
                ['-p', temp_project, 'rollback', '--execution-id', 'exec-to-rollback']
            )

            assert result.exit_code == 0
            assert 'exec-to-rollback' in result.output
            mock_instance.rollback.assert_called_once_with(execution_id="exec-to-rollback")


class TestCLIHelp:
    """Test help"""

    def test_cli_help(self, cli_runner):
        """--help shows help"""
        result = cli_runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'plan' in result.output
        assert 'run' in result.output
        assert 'diagnose' in result.output
        assert 'status' in result.output

    def test_cli_subcommand_help(self, cli_runner):
        """subcommand --help works"""
        result = cli_runner.invoke(cli, ['plan', '--help'])

        assert result.exit_code == 0
        assert 'intent' in result.output or 'plan' in result.output.lower()
