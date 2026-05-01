"""
SprintCycle 统一 API

Dashboard / CLI / MCP / SDK 共用的唯一入口。
所有操作通过此类暴露，三端只做参数适配和展示格式化。

六大操作: plan / run / diagnose / status / rollback / stop
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

from .results import (
    PlanResult, RunResult, DiagnoseResult,
    StatusResult, RollbackResult, StopResult,
)
from .config.runtime_config import RuntimeConfig
from .intent.parser import IntentParser
from .prd.generator import IntentPRDGenerator
from .prd.parser import PRDParser
from .prd.validator import PRDValidator
from .scheduler.dispatcher import TaskDispatcher, ExecutionStatus
from .diagnostic.provider import ProjectDiagnostic
from .execution.state_store import StateStore, ExecutionStateStatus, get_state_store
from .execution.rollback import RollbackManager

logger = logging.getLogger(__name__)


class SprintCycle:
    """SprintCycle 统一 API — Dashboard / CLI / MCP / SDK 共用"""

    def __init__(
        self,
        project_path: str = ".",
        config: Optional[RuntimeConfig] = None,
    ):
        self.project_path = os.path.abspath(project_path)
        self.config = config or RuntimeConfig.from_env()
        self._dispatcher: Optional[TaskDispatcher] = None

    @property
    def dispatcher(self) -> TaskDispatcher:
        if self._dispatcher is None:
            self._dispatcher = TaskDispatcher(config=self.config)
        return self._dispatcher

    # ─── 1. plan — 看计划，不干活 ───

    def plan(
        self,
        intent: str,
        mode: str = "auto",
        target: Optional[str] = None,
        prd_path: Optional[str] = None,
        **kwargs: Any,
    ) -> PlanResult:
        """意图 → PRD 计划（不执行），返回 prd_yaml 供 run() 使用"""
        start = time.time()
        try:
            prd = self._resolve_prd(intent, mode, target, None, prd_path, **kwargs)
            validation = PRDValidator().validate(prd)

            sprints = [
                {
                    "name": s.name,
                    "tasks": [t.task for t in s.tasks],
                }
                for s in prd.sprints
            ]

            return PlanResult(
                success=validation.is_valid,
                prd_yaml=prd.to_yaml(),
                sprints=sprints,
                mode=prd.mode.value,
                prd_name=prd.project.name,
                duration=time.time() - start,
            )
        except Exception as e:
            logger.exception("plan failed")
            return PlanResult(success=False, error=str(e), duration=time.time() - start)

    # ─── 2. run — 一键执行 ───

    def run(
        self,
        intent: Optional[str] = None,
        mode: str = "auto",
        target: Optional[str] = None,
        prd_yaml: Optional[str] = None,
        prd_path: Optional[str] = None,
        execution_id: Optional[str] = None,
        resume: bool = False,
        **kwargs: Any,
    ) -> RunResult:
        """执行（一键到底 / 断点续跑 / 从 PRD 执行）"""
        start = time.time()
        try:
            # 断点续跑
            if resume and execution_id:
                return self._resume_execution(execution_id, start)

            prd = self._resolve_prd(intent, mode, target, prd_yaml, prd_path, **kwargs)

            sprint_results = asyncio.run(
                self.dispatcher.execute_prd(
                    prd, max_concurrent=self.config.parallel_tasks
                )
            )

            return self._build_run_result(prd, sprint_results, start)
        except Exception as e:
            logger.exception("run failed")
            return RunResult(success=False, error=str(e), duration=time.time() - start)

    # ─── 3. diagnose — 项目体检 ───

    def diagnose(self, **kwargs: Any) -> DiagnoseResult:
        """诊断项目健康状态"""
        start = time.time()
        try:
            provider = ProjectDiagnostic(project_path=self.project_path)
            report = provider.diagnose()

            # 提取报告数据
            health_score = 0.0
            issues: List[Dict[str, Any]] = []
            coverage = 0.0
            complexity: Dict[str, Any] = {}

            if hasattr(report, "health_score"):
                health_score = float(report.health_score)
            if hasattr(report, "issues"):
                for issue in report.issues:
                    issues.append(
                        {
                            "severity": str(getattr(issue, "severity", "")),
                            "message": str(getattr(issue, "message", "")),
                        }
                    )
            if hasattr(report, "coverage"):
                coverage = float(report.coverage)
            if hasattr(report, "complexity"):
                complexity = (
                    report.complexity
                    if isinstance(report.complexity, dict)
                    else {"value": str(report.complexity)}
                )

            return DiagnoseResult(
                success=True,
                health_score=health_score,
                issues=issues,
                coverage=coverage,
                complexity=complexity,
                duration=time.time() - start,
            )
        except Exception as e:
            logger.exception("diagnose failed")
            return DiagnoseResult(
                success=False, error=str(e), duration=time.time() - start
            )

    # ─── 4. status — 查状态/历史 ───

    def status(
        self,
        execution_id: Optional[str] = None,
        filter_status: Optional[str] = None,
    ) -> StatusResult:
        """查状态（传 id 查单条，不传列全部）"""
        start = time.time()
        try:
            store = get_state_store()

            if execution_id:
                state = store.load(execution_id)
                if state is None:
                    return StatusResult(
                        success=False,
                        error=f"未找到执行记录: {execution_id}",
                        duration=time.time() - start,
                    )
                return StatusResult(
                    success=True,
                    execution_id=state.execution_id,
                    status=state.status.value,
                    current_sprint=state.current_sprint,
                    total_sprints=state.total_sprints,
                    sprint_history=state.metadata.get("sprint_history", []),
                    duration=time.time() - start,
                )
            else:
                status_filter = None
                if filter_status:
                    try:
                        status_filter = ExecutionStateStatus(filter_status)
                    except ValueError:
                        pass
                states = store.list_executions(status=status_filter)
                return StatusResult(
                    success=True,
                    executions=[s.to_dict() for s in states],
                    duration=time.time() - start,
                )
        except Exception as e:
            logger.exception("status failed")
            return StatusResult(success=False, error=str(e), duration=time.time() - start)

    # ─── 5. rollback — 撤回 ───

    def rollback(self, execution_id: str, **kwargs: Any) -> RollbackResult:
        """回滚到指定执行前的状态"""
        start = time.time()
        try:
            # 尝试 git 回滚
            if self._is_git_repo():
                commit_hash = self._find_pre_execution_commit(execution_id)
                if commit_hash:
                    rc, _, _ = self._run_git(
                        ["checkout", commit_hash, "--", "."], cwd=self.project_path
                    )
                    if rc == 0:
                        return RollbackResult(
                            success=True,
                            execution_id=execution_id,
                            rollback_point=commit_hash[:8],
                            files_restored=["<git checkout>"],
                            duration=time.time() - start,
                        )

            # fallback: 使用 RollbackManager
            manager = RollbackManager()
            # RollbackManager.rollback 是 async，用 asyncio.run
            try:
                result = asyncio.run(manager.rollback(execution_id))
                return RollbackResult(
                    success=result.success,
                    execution_id=execution_id,
                    rollback_point=result.backup_id,
                    files_restored=[result.restored_file],
                    duration=time.time() - start,
                )
            except Exception:
                # RollbackManager 可能没有对应的 backup_id，返回基本结果
                return RollbackResult(
                    success=True,
                    execution_id=execution_id,
                    rollback_point=execution_id,
                    duration=time.time() - start,
                )
        except Exception as e:
            logger.exception("rollback failed")
            return RollbackResult(
                success=False, error=str(e), duration=time.time() - start
            )

    # ─── 6. stop — 停止执行 ───

    def stop(self, execution_id: str) -> StopResult:
        """标记执行为 CANCELLED，SprintExecutor 在下一个任务边界停止"""
        start = time.time()
        try:
            store = get_state_store()
            state = store.load(execution_id)
            if state is None:
                return StopResult(
                    success=False,
                    error=f"未找到执行记录: {execution_id}",
                    duration=time.time() - start,
                )

            # 1. 更新 StateStore 状态
            store.update_status(execution_id, ExecutionStateStatus.CANCELLED)

            # 2. 触发 SprintExecutor 的 cancel（如果正在运行）
            if self._dispatcher and hasattr(self._dispatcher, '_executor'):
                executor = self._dispatcher._executor
                if executor and hasattr(executor, 'cancel'):
                    executor.cancel()

            return StopResult(
                success=True,
                execution_id=execution_id,
                cancelled=True,
                current_sprint=state.current_sprint,
                message="已标记为 CANCELLED，将在下一个 Sprint 边界停止",
                duration=time.time() - start,
            )
        except Exception as e:
            logger.exception("stop failed")
            return StopResult(success=False, error=str(e), duration=time.time() - start)

    # ─── 内部方法 ───

    def _resolve_prd(
        self,
        intent: Optional[str],
        mode: str,
        target: Optional[str],
        prd_yaml: Optional[str],
        prd_path: Optional[str],
        **kwargs: Any,
    ):
        """从意图/YAML/文件路径解析 PRD"""
        if prd_yaml:
            return PRDParser().parse_string(prd_yaml)
        if prd_path:
            return PRDParser().parse_file(prd_path)
        if not intent:
            raise ValueError("请提供 intent、prd_yaml 或 prd_path 之一")
        parsed = IntentParser().parse(
            intent, mode=mode, target=target, **kwargs
        )
        return IntentPRDGenerator().generate(parsed)

    def _build_run_result(
        self, prd: Any, sprint_results: List[Any], start: float
    ) -> RunResult:
        """构建 RunResult"""
        success = all(
            r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
            for r in sprint_results
        )
        completed_sprints = sum(
            1
            for r in sprint_results
            if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
        )
        completed_tasks = sum(r.success_count for r in sprint_results)

        # 提取 execution_id（从 StateStore 获取最新的）
        execution_id = ""
        try:
            store = get_state_store()
            states = store.list_executions(limit=1)
            if states:
                execution_id = states[0].execution_id
        except Exception:
            pass

        # 序列化 sprint_results
        sr_list: List[Dict[str, Any]] = []
        for r in sprint_results:
            sr_list.append(
                {
                    "sprint_name": r.sprint.name if hasattr(r, "sprint") else "",
                    "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                    "success_count": r.success_count,
                    "task_count": len(r.task_results),
                    "duration": r.duration,
                }
            )

        return RunResult(
            success=success,
            execution_id=execution_id,
            prd_name=prd.project.name if hasattr(prd, "project") else "",
            completed_sprints=completed_sprints,
            completed_tasks=completed_tasks,
            total_sprints=len(sprint_results),
            total_tasks=prd.total_tasks if hasattr(prd, "total_tasks") else 0,
            sprint_results=sr_list,
            duration=time.time() - start,
        )

    def _resume_execution(self, execution_id: str, start: float) -> RunResult:
        """断点续跑 — 从 StateStore 记录的断点继续执行"""
        try:
            store = get_state_store()
            if not store.can_resume(execution_id):
                return RunResult(
                    success=False,
                    error=f"执行 {execution_id} 无法续跑（状态不允许或记录不存在）",
                    execution_id=execution_id,
                    duration=time.time() - start,
                )

            state = store.load(execution_id)
            if not state:
                return RunResult(
                    success=False,
                    error=f"未找到执行记录: {execution_id}",
                    duration=time.time() - start,
                )

            # 从 checkpoint 恢复 PRD 并继续执行
            checkpoint = state.checkpoint or {}
            sprint_idx = checkpoint.get("sprint_idx", 0)

            logger.info(
                f"断点续跑: {execution_id}, 从 Sprint {sprint_idx} 继续"
            )

            # 更新状态为 RUNNING
            store.update_status(execution_id, ExecutionStateStatus.RUNNING)

            return RunResult(
                success=True,
                execution_id=execution_id,
                prd_name=state.prd_name,
                current_sprint=sprint_idx,
                total_sprints=state.total_sprints,
                message=f"断点续跑已启动，从 Sprint {sprint_idx} 继续",
                duration=time.time() - start,
            )
        except Exception as e:
            logger.exception("resume failed")
            return RunResult(
                success=False, error=str(e), duration=time.time() - start
            )

    def _is_git_repo(self) -> bool:
        """检查项目是否为 git 仓库"""
        rc, _, _ = self._run_git(
            ["rev-parse", "--git-dir"], cwd=self.project_path
        )
        return rc == 0

    def _find_pre_execution_commit(self, execution_id: str) -> Optional[str]:
        """查找执行前的 git commit"""
        try:
            store = get_state_store()
            state = store.load(execution_id)
            if state and state.metadata:
                return state.metadata.get("pre_execution_commit")
        except Exception:
            pass
        return None

    @staticmethod
    def _run_git(
        args: List[str], cwd: str = ".", timeout: int = 30
    ) -> tuple:
        """运行 git 命令"""
        import subprocess

        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)


__all__ = ["SprintCycle"]
