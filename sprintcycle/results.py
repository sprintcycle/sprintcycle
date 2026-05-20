"""
SprintCycle 统一返回值类型。

所有操作（plan/run/diagnose/status/rollback/stop）返回统一的 Result 对象，
支持 to_dict() 序列化，确保 Dashboard / REST API / SDK 输出一致。
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResultBase:
    """所有 Result 的基类"""

    success: bool
    error: Optional[str] = None
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class EvolutionSummary:
    """对外统一的意图演化摘要。"""

    stage: str = ""
    signals: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "signals": list(self.signals),
            "context": dict(self.context),
        }


@dataclass
class PlanResult(ResultBase):
    """plan() 返回 — 意图 → Release Plan（执行计划 YAML，不执行）"""

    release_plan_yaml: str = ""
    sprints: List[Dict[str, Any]] = field(default_factory=list)
    mode: str = ""
    release_plan_name: str = ""
    evolution: EvolutionSummary = field(default_factory=EvolutionSummary)


@dataclass
class RunResult(ResultBase):
    """run() 返回 — 执行结果"""

    execution_id: str = ""
    release_plan_name: str = ""
    completed_sprints: int = 0
    completed_tasks: int = 0
    total_sprints: int = 0
    total_tasks: int = 0
    current_sprint: int = 0
    lifecycle_state: str = ""
    lifecycle_stage: str = ""
    failure_kind: str = ""
    failure_reason: str = ""
    sprint_results: List[Dict[str, Any]] = field(default_factory=list)
    release_finalization: Dict[str, Any] = field(default_factory=dict)
    pending_knowledge_confirmation: bool = False
    knowledge_injection_preview: Dict[str, Any] = field(default_factory=dict)
    delivery: Dict[str, Any] = field(default_factory=dict)
    runtime_linkage: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    evolution: EvolutionSummary = field(default_factory=EvolutionSummary)


@dataclass
class DiagnoseResult(ResultBase):
    """diagnose() 返回 — 项目体检"""

    health_score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    coverage: float = 0.0
    complexity: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatusResult(ResultBase):
    """status() 返回 — 执行状态/历史"""

    execution_id: str = ""
    status: str = ""
    current_sprint: int = 0
    total_sprints: int = 0
    sprint_history: List[Dict[str, Any]] = field(default_factory=list)
    release_finalization: Dict[str, Any] = field(default_factory=dict)
    executions: List[Dict[str, Any]] = field(default_factory=list)
    execution_timeline: List[Dict[str, Any]] = field(default_factory=list)
    last_stable_state: Dict[str, Any] = field(default_factory=dict)
    event_cursor: Optional[int] = None
    state_machine: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackResult(ResultBase):
    """rollback() 返回 — 回滚结果"""

    execution_id: str = ""
    rollback_point: str = ""
    files_restored: List[str] = field(default_factory=list)


@dataclass
class StopResult(ResultBase):
    """stop() 返回 — 停止结果"""

    execution_id: str = ""
    cancelled: bool = False
    current_sprint: int = 0
    message: str = ""


@dataclass
class EvolutionVersionSummary(ResultBase):
    """演化版本摘要。"""

    version_id: str = ""
    target: str = ""
    commit_hash: str = ""
    tag: str = ""
    branch: str = ""
    manifest_path: str = ""
    sandbox_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()


@dataclass
class EvolutionVersionListResult(ResultBase):
    """演化版本列表。"""

    target: str = ""
    versions: List[EvolutionVersionSummary] = field(default_factory=list)
    total: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["versions"] = [v.to_dict() if hasattr(v, "to_dict") else v for v in self.versions]
        return data


@dataclass
class EvolutionIndexResult(ResultBase):
    """演化版本索引。"""

    index: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()


@dataclass
class FinalSnapshotResult:
    """Final lifecycle snapshot summary."""

    execution_id: str = ""
    stage: str = ""
    status: str = ""
    normalized_request: Dict[str, Any] = field(default_factory=dict)
    lifecycle: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    runtime: Dict[str, Any] = field(default_factory=dict)
    governance: Dict[str, Any] = field(default_factory=dict)
    suggestion: Dict[str, Any] = field(default_factory=dict)
    delivery: Dict[str, Any] = field(default_factory=dict)
    repair: Dict[str, Any] = field(default_factory=dict)
    promotion: Dict[str, Any] = field(default_factory=dict)
    promotion_contract: Dict[str, Any] = field(default_factory=dict)
    health: Dict[str, Any] = field(default_factory=dict)
    validation_refs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FinalSnapshotVersionSummary:
    """Version active pointer 对应的 final snapshot 摘要。"""

    target: str = ""
    version_id: str = ""
    final_snapshot: FinalSnapshotResult = field(default_factory=FinalSnapshotResult)
    promotion_guard: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "version_id": self.version_id,
            "final_snapshot": self.final_snapshot.to_dict()
            if hasattr(self.final_snapshot, "to_dict")
            else dict(self.final_snapshot),
            "promotion_guard": dict(self.promotion_guard),
        }


@dataclass
class EvolutionOverviewResult(ResultBase):
    """演化总览结果。"""

    active_versions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recent_candidates: List[EvolutionVersionSummary] = field(default_factory=list)
    final_snapshot_versions: List[FinalSnapshotVersionSummary] = field(default_factory=list)
    index: Dict[str, List[str]] = field(default_factory=dict)
    totals: Dict[str, int] = field(default_factory=dict)
    sandbox_status: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["recent_candidates"] = [v.to_dict() if hasattr(v, "to_dict") else v for v in self.recent_candidates]
        data["final_snapshot_versions"] = [
            v.to_dict() if hasattr(v, "to_dict") else v for v in self.final_snapshot_versions
        ]
        return data

    def to_dashboard_payload(self) -> Dict[str, Any]:
        """Dashboard 首屏友好的轻量 payload。"""
        active = {
            target: {
                "version_id": info.get("version_id", ""),
                "commit_hash": info.get("commit_hash", ""),
                "tag": info.get("tag", ""),
                "manifest_path": info.get("manifest_path", ""),
                "sandbox_id": info.get("sandbox_id", ""),
            }
            for target, info in self.active_versions.items()
        }
        recent = [
            {
                "version_id": v.version_id,
                "target": v.target,
                "commit_hash": v.commit_hash,
                "tag": v.tag,
                "manifest_path": v.manifest_path,
            }
            for v in self.recent_candidates[:5]
        ]
        final_snapshots = [v.to_dict() if hasattr(v, "to_dict") else v for v in self.final_snapshot_versions[:5]]
        return {
            "active_versions": active,
            "recent_candidates": recent,
            "final_snapshot_versions": final_snapshots,
            "totals": dict(self.totals),
            "sandbox_status": dict(self.sandbox_status),
        }

    def to_cli_text(self) -> str:
        """文本摘要。"""
        lines = ["Evolution Overview"]
        lines.append(f"  versions: {self.totals.get('versions', 0)}")
        lines.append(f"  code_active: {self.totals.get('code_active', 0)}")
        lines.append(f"  requirement_active: {self.totals.get('requirement_active', 0)}")
        lines.append(
            f"  sandbox: {self.sandbox_status.get('backend', 'unknown')} @ {self.sandbox_status.get('root_dir', '')}"
        )
        for target in sorted(self.active_versions.keys()):
            info = self.active_versions[target]
            lines.append(
                f"  active[{target}]: {info.get('version_id', '')}"
                f" ({info.get('tag', '') or info.get('commit_hash', '')})"
            )
        if self.final_snapshot_versions:
            lines.append("  final snapshots:")
            for item in self.final_snapshot_versions[:5]:
                lines.append(f"    - {item.target}: {item.version_id}")
        if self.recent_candidates:
            lines.append("  recent:")
            for v in self.recent_candidates[:5]:
                lines.append(f"    - {v.target}: {v.version_id}")
        return "\n".join(lines)


__all__ = [
    "ResultBase",
    "EvolutionSummary",
    "PlanResult",
    "RunResult",
    "DiagnoseResult",
    "StatusResult",
    "RollbackResult",
    "StopResult",
    "EvolutionVersionSummary",
    "EvolutionVersionListResult",
    "EvolutionIndexResult",
    "FinalSnapshotResult",
    "FinalSnapshotVersionSummary",
    "EvolutionOverviewResult",
]
