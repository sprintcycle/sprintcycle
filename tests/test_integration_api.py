"""
SprintCycle API Integration Tests

Tests the SprintCycle API class (CLI/MCP/Dashboard shared entry point)
covering all 6 operations: plan, run, diagnose, status, rollback, stop
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from sprintcycle.api import SprintCycle
from sprintcycle.results import (
    PlanResult, RunResult, DiagnoseResult,
    StatusResult, RollbackResult, StopResult,
)
from sprintcycle.execution.sprint_types import ExecutionStatus
from sprintcycle.execution.state_store import StateStore, ExecutionState


class TestAPIPlan:
    """Test plan operation"""

    def setup_method(self):
        """Setup temp directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = Path.cwd()

    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_plan_returns_prd_yaml(self):
        """test_plan_returns_prd_yaml: plan → returns PlanResult containing prd_yaml"""
        sc = SprintCycle(project_path=self.temp_dir)

        # Mock the PRD generation to avoid LLM calls
        with patch('sprintcycle.api.IntentParser') as mock_parser, \
             patch('sprintcycle.api.IntentPRDGenerator') as mock_generator:

            # Setup mock PRD
            from sprintcycle.prd.models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode
            mock_prd = PRD(
                project=PRDProject(name="TestProject", path=self.temp_dir),
                mode=ExecutionMode.NORMAL,
                sprints=[
                    PRDSprint(
                        name="Sprint 1",
                        goals=["Test goal"],
                        tasks=[PRDTask(task="Test task", agent="coder")]
                    )
                ]
            )
            mock_generator.return_value.generate.return_value = mock_prd

            result = sc.plan(intent="Test intent")

            assert isinstance(result, PlanResult)
            assert result.success is True
            assert result.prd_yaml is not None
            assert len(result.prd_yaml) > 0
            assert "project" in result.prd_yaml
            assert "Sprint 1" in result.prd_yaml
            assert result.prd_name == "TestProject"
            assert len(result.sprints) == 1

    def test_plan_with_mode(self):
        """test_plan_with_mode: plan respects mode parameter"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.IntentParser') as mock_parser, \
             patch('sprintcycle.api.IntentPRDGenerator') as mock_generator, \
             patch('sprintcycle.api.PRDValidator') as mock_validator:

            from sprintcycle.prd.models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode
            mock_prd = PRD(
                project=PRDProject(name="TestProject", path=self.temp_dir),
                mode=ExecutionMode.EVOLUTION,
                sprints=[]
            )
            mock_generator.return_value.generate.return_value = mock_prd
            
            # Mock validator
            mock_validator_instance = MagicMock()
            mock_validator_instance.validate.return_value = MagicMock(is_valid=True)
            mock_validator.return_value = mock_validator_instance

            result = sc.plan(intent="Evolve the code", mode="evolution")

            assert result.success is True
            assert result.mode == "evolution"

    def test_plan_failure_handling(self):
        """test_plan_failure_handling: plan handles errors gracefully"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.IntentParser') as mock_parser:
            mock_parser.return_value.parse.side_effect = Exception("Parse error")

            result = sc.plan(intent="Test intent")

            assert isinstance(result, PlanResult)
            assert result.success is False
            assert result.error is not None


class TestAPIRun:
    """Test run operation"""

    def setup_method(self):
        """Setup temp directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / ".sprintcycle" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_creates_execution(self):
        """test_run_creates_execution: run → creates execution and returns RunResult"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.IntentParser') as mock_parser, \
             patch('sprintcycle.api.IntentPRDGenerator') as mock_generator, \
             patch('sprintcycle.api.get_state_store') as mock_get_store, \
             patch('sprintcycle.scheduler.dispatcher.TaskDispatcher') as mock_dispatcher_cls:

            # Setup mock state store
            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store
            mock_store.list_executions.return_value = [
                MagicMock(execution_id="test-exec-123")
            ]

            from sprintcycle.prd.models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode
            from sprintcycle.execution.sprint_types import SprintResult, TaskResult

            mock_prd = PRD(
                project=PRDProject(name="TestProject", path=self.temp_dir),
                mode=ExecutionMode.NORMAL,
                sprints=[
                    PRDSprint(
                        name="Sprint 1",
                        goals=["Test"],
                        tasks=[PRDTask(task="Task 1", agent="coder")]
                    )
                ]
            )
            mock_generator.return_value.generate.return_value = mock_prd

            # Mock sprint results
            mock_task = MagicMock()
            mock_task.status = ExecutionStatus.SUCCESS
            mock_task.success_count = 1

            mock_sprint_result = MagicMock()
            mock_sprint_result.status = ExecutionStatus.SUCCESS
            mock_sprint_result.success_count = 1
            mock_sprint_result.task_results = [mock_task]
            mock_sprint_result.duration = 1.0

            # Mock the dispatcher
            mock_dispatcher_instance = MagicMock()
            mock_dispatcher_instance.execute_prd = AsyncMock(return_value=[mock_sprint_result])
            mock_dispatcher_cls.return_value = mock_dispatcher_instance

            # Also need to patch the event_bus
            with patch('sprintcycle.execution.events.get_event_bus') as mock_event_bus:
                mock_event_bus_instance = MagicMock()
                mock_event_bus.return_value = mock_event_bus_instance
                
                # Create a new SprintCycle to get fresh dispatcher
                sc2 = SprintCycle(project_path=self.temp_dir)
                result = sc2.run(intent="Run test")

                assert isinstance(result, RunResult)
                assert result.prd_name == "TestProject"
                assert result.total_sprints >= 0

    def test_run_with_prd_yaml(self):
        """test_run_with_prd_yaml: run accepts prd_yaml parameter"""
        sc = SprintCycle(project_path=self.temp_dir)

        prd_yaml = """
project:
  name: "YAMLProject"
  path: "."
mode: normal
sprints:
  - name: "Sprint 1"
    tasks:
      - task: "Test task"
        agent: coder
"""

        with patch('sprintcycle.api.PRDParser') as mock_parser, \
             patch('sprintcycle.api.get_state_store') as mock_get_store, \
             patch('sprintcycle.scheduler.dispatcher.TaskDispatcher') as mock_dispatcher_cls:

            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store
            mock_store.list_executions.return_value = []

            from sprintcycle.prd.models import PRD, PRDProject, ExecutionMode
            mock_prd = PRD(
                project=PRDProject(name="YAMLProject", path="."),
                mode=ExecutionMode.NORMAL,
                sprints=[]
            )
            mock_parser.return_value.parse_string.return_value = mock_prd

            # Mock the dispatcher
            mock_dispatcher_instance = MagicMock()
            mock_dispatcher_instance.execute_prd = AsyncMock(return_value=[])
            mock_dispatcher_cls.return_value = mock_dispatcher_instance

            with patch('sprintcycle.execution.events.get_event_bus') as mock_event_bus:
                mock_event_bus_instance = MagicMock()
                mock_event_bus.return_value = mock_event_bus_instance
                
                sc2 = SprintCycle(project_path=self.temp_dir)
                result = sc2.run(prd_yaml=prd_yaml)

                assert isinstance(result, RunResult)
                mock_parser.return_value.parse_string.assert_called_once_with(prd_yaml)


class TestAPIStatus:
    """Test status operation"""

    def setup_method(self):
        """Setup temp directory for each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_status_returns_execution_state(self):
        """test_status_returns_execution_state: status → returns StatusResult"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store:
            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store

            # Mock existing execution
            mock_state = ExecutionState(
                execution_id="exec-123",
                prd_name="TestProject",
                mode="normal",
                status=ExecutionStatus.RUNNING,
                current_sprint=1,
                total_sprints=3,
                total_tasks=5,
            )
            mock_state.metadata = {"sprint_history": []}
            mock_store.load.return_value = mock_state

            result = sc.status(execution_id="exec-123")

            assert isinstance(result, StatusResult)
            assert result.success is True
            assert result.execution_id == "exec-123"
            assert result.status == "running"
            assert result.current_sprint == 1
            assert result.total_sprints == 3

    def test_status_lists_all_executions(self):
        """test_status_lists_all_executions: status without id returns all executions"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store:
            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store

            mock_states = [
                ExecutionState(
                    execution_id=f"exec-{i}",
                    prd_name="TestProject",
                    mode="normal",
                    status=ExecutionStatus.COMPLETED,
                    current_sprint=3,
                    total_sprints=3,
                    total_tasks=5,
                )
                for i in range(3)
            ]
            mock_store.list_executions.return_value = mock_states

            result = sc.status()

            assert isinstance(result, StatusResult)
            assert result.success is True
            assert len(result.executions) == 3

    def test_status_not_found(self):
        """test_status_not_found: status returns error for non-existent id"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store:
            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store
            mock_store.load.return_value = None

            result = sc.status(execution_id="non-existent")

            assert isinstance(result, StatusResult)
            assert result.success is False
            assert "未找到" in result.error


class TestAPIStop:
    """Test stop operation"""

    def setup_method(self):
        """Setup temp directory for each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_stop_cancels_execution(self):
        """test_stop_cancels_execution: run → stop → state becomes cancelled"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store:
            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store

            # Mock running execution
            mock_state = ExecutionState(
                execution_id="exec-stop-test",
                prd_name="TestProject",
                mode="normal",
                status=ExecutionStatus.RUNNING,
                current_sprint=1,
                total_sprints=3,
                total_tasks=5,
            )
            mock_state.metadata = {}
            mock_store.load.return_value = mock_state

            result = sc.stop(execution_id="exec-stop-test")

            assert isinstance(result, StopResult)
            assert result.success is True
            assert result.execution_id == "exec-stop-test"
            assert result.cancelled is True
            mock_store.update_status.assert_called_once_with(
                "exec-stop-test",
                ExecutionStatus.CANCELLED
            )

    def test_stop_not_found(self):
        """test_stop_not_found: stop returns error for non-existent execution"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store:
            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store
            mock_store.load.return_value = None

            result = sc.stop(execution_id="non-existent")

            assert isinstance(result, StopResult)
            assert result.success is False


class TestAPIDiagnose:
    """Test diagnose operation"""

    def setup_method(self):
        """Setup temp directory for each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_diagnose_returns_health(self):
        """test_diagnose_returns_health: diagnose → returns DiagnoseResult"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.ProjectDiagnostic') as mock_diagnostic:
            # Setup mock diagnostic report
            mock_report = MagicMock()
            mock_report.health_score = 85.0
            mock_report.coverage = 72.5
            mock_report.complexity = {"average": 10.5}
            mock_report.issues = []

            mock_diagnostic_instance = MagicMock()
            mock_diagnostic_instance.diagnose.return_value = mock_report
            mock_diagnostic.return_value = mock_diagnostic_instance

            result = sc.diagnose()

            assert isinstance(result, DiagnoseResult)
            assert result.success is True
            assert result.health_score == 85.0
            assert result.coverage == 72.5

    def test_diagnose_with_issues(self):
        """test_diagnose_with_issues: diagnose reports issues"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.ProjectDiagnostic') as mock_diagnostic:
            mock_issue = MagicMock()
            mock_issue.severity = "warning"
            mock_issue.message = "Test issue"

            mock_report = MagicMock()
            mock_report.health_score = 60.0
            mock_report.coverage = 50.0
            mock_report.complexity = {}
            mock_report.issues = [mock_issue]

            mock_diagnostic_instance = MagicMock()
            mock_diagnostic_instance.diagnose.return_value = mock_report
            mock_diagnostic.return_value = mock_diagnostic_instance

            result = sc.diagnose()

            assert isinstance(result, DiagnoseResult)
            assert result.success is True
            assert len(result.issues) == 1
            assert result.issues[0]["severity"] == "warning"


class TestAPIRollback:
    """Test rollback operation"""

    def setup_method(self):
        """Setup temp directory for each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_rollback_restores_state(self):
        """test_rollback_restores_state: run → rollback → state restored"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store, \
             patch.object(sc, '_is_git_repo', return_value=True), \
             patch.object(sc, '_find_pre_execution_commit', return_value="abc1234"), \
             patch.object(sc, '_run_git') as mock_git:

            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store

            mock_state = ExecutionState(
                execution_id="exec-rollback-test",
                prd_name="TestProject",
                mode="normal",
                status=ExecutionStatus.COMPLETED,
                current_sprint=3,
                total_sprints=3,
                total_tasks=5,
            )
            mock_state.metadata = {"pre_execution_commit": "abc1234"}
            mock_store.load.return_value = mock_state

            # Mock successful git checkout
            mock_git.return_value = (0, "", "")

            result = sc.rollback(execution_id="exec-rollback-test")

            assert isinstance(result, RollbackResult)
            assert result.success is True
            assert result.execution_id == "exec-rollback-test"
            assert result.rollback_point == "abc1234"

    def test_rollback_non_git_repo(self):
        """test_rollback_non_git_repo: rollback handles non-git repos"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store, \
             patch.object(sc, '_is_git_repo', return_value=False):

            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store

            mock_state = ExecutionState(
                execution_id="exec-no-git",
                prd_name="TestProject",
                mode="normal",
                status=ExecutionStatus.COMPLETED,
                current_sprint=3,
                total_sprints=3,
                total_tasks=5,
            )
            mock_state.metadata = {}
            mock_store.load.return_value = mock_state

            result = sc.rollback(execution_id="exec-no-git")

            assert isinstance(result, RollbackResult)
            # Non-git repos should fail gracefully
            assert result.success is False


class TestAPIResume:
    """Test resume operation"""

    def setup_method(self):
        """Setup temp directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / ".sprintcycle" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_resume_continues_execution(self):
        """test_resume_continues_execution: run → stop → resume → continues execution"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store, \
             patch('sprintcycle.api.PRDParser') as mock_parser, \
             patch('sprintcycle.scheduler.dispatcher.TaskDispatcher') as mock_dispatcher_cls:

            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store

            # Mock paused execution with checkpoint
            prd_yaml = """
project:
  name: "ResumeProject"
  path: "."
mode: normal
sprints:
  - name: "Sprint 1"
    tasks:
      - task: "Task 1"
        agent: coder
  - name: "Sprint 2"
    tasks:
      - task: "Task 2"
        agent: coder
"""
            mock_state = ExecutionState(
                execution_id="exec-resume-test",
                prd_name="ResumeProject",
                mode="normal",
                status=ExecutionStatus.PAUSED,
                current_sprint=1,
                total_sprints=2,
                total_tasks=2,
            )
            mock_state.metadata = {}
            mock_state.checkpoint = {
                "sprint_idx": 1,
                "sprint_name": "Sprint 2",
                "task_results": [],
                "prd_yaml": prd_yaml,
            }
            mock_store.load.return_value = mock_state
            mock_store.can_resume.return_value = True

            from sprintcycle.prd.models import PRD, PRDProject, ExecutionMode
            mock_prd = PRD(
                project=PRDProject(name="ResumeProject", path="."),
                mode=ExecutionMode.NORMAL,
                sprints=[]
            )
            mock_parser.return_value.parse_string.return_value = mock_prd

            mock_sprint_result = MagicMock()
            mock_sprint_result.status = ExecutionStatus.SUCCESS
            mock_sprint_result.success_count = 1
            mock_sprint_result.task_results = []
            mock_sprint_result.duration = 1.0

            # Mock the dispatcher
            mock_dispatcher_instance = MagicMock()
            mock_dispatcher_instance.resume_from_sprint = AsyncMock(return_value=[mock_sprint_result])
            mock_dispatcher_cls.return_value = mock_dispatcher_instance

            with patch('sprintcycle.execution.events.get_event_bus') as mock_event_bus:
                mock_event_bus_instance = MagicMock()
                mock_event_bus.return_value = mock_event_bus_instance
                
                sc2 = SprintCycle(project_path=self.temp_dir)
                result = sc2.run(execution_id="exec-resume-test", resume=True)

                assert isinstance(result, RunResult)
                assert result.execution_id == "exec-resume-test"
                mock_store.update_status.assert_any_call(
                    "exec-resume-test",
                    ExecutionStatus.RUNNING
                )

    def test_resume_cannot_resume(self):
        """test_resume_cannot_resume: resume returns error when cannot resume"""
        sc = SprintCycle(project_path=self.temp_dir)

        with patch('sprintcycle.api.get_state_store') as mock_get_store:
            mock_store = MagicMock(spec=StateStore)
            mock_get_store.return_value = mock_store
            mock_store.can_resume.return_value = False

            result = sc.run(execution_id="cannot-resume", resume=True)

            assert isinstance(result, RunResult)
            assert result.success is False
            assert "无法续跑" in result.error
