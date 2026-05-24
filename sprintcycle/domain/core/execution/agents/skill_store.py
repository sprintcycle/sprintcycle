"""Skill 持久化仓库。"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .skill_models import SkillArtifact, SkillExecutionRecord, SkillInjectionState, TaskSkillTrace


class SkillStore:
    def __init__(self, store_dir: str = ".sprintcycle/skills") -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts_dir = self.store_dir / "artifacts"
        self._states_dir = self.store_dir / "states"
        self._records_dir = self.store_dir / "records"
        self._traces_dir = self.store_dir / "traces"
        for d in (self._artifacts_dir, self._states_dir, self._records_dir, self._traces_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _artifact_path(self, skill_id: str, version: str) -> Path:
        return self._artifacts_dir / f"{skill_id}__{version}.json"

    def _state_path(self, execution_id: str, sprint_name: str, task_name: str, skill_id: str) -> Path:
        key = "__".join([execution_id, sprint_name, task_name, skill_id]).replace("/", "_")
        return self._states_dir / f"{key}.json"

    def _record_path(self, execution_id: str) -> Path:
        return self._records_dir / f"{execution_id}.jsonl"

    def _trace_path(self, execution_id: str) -> Path:
        return self._traces_dir / f"{execution_id}.jsonl"

    def save_artifact(self, artifact: SkillArtifact) -> None:
        data = asdict(artifact)
        if not data.get("installed_at"):
            data["installed_at"] = datetime.now().isoformat()
        self._artifact_path(artifact.skill_id, artifact.version).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def list_artifacts(self, skill_id: Optional[str] = None) -> List[SkillArtifact]:
        items: List[SkillArtifact] = []
        for p in self._artifacts_dir.glob("*.json"):
            raw = json.loads(p.read_text(encoding="utf-8"))
            if skill_id and raw.get("skill_id") != skill_id:
                continue
            items.append(SkillArtifact(**raw))
        return items

    def get_latest_artifact(self, skill_id: str) -> Optional[SkillArtifact]:
        artifacts = self.list_artifacts(skill_id)
        if not artifacts:
            return None
        artifacts.sort(key=lambda a: a.installed_at or "", reverse=True)
        return artifacts[0]

    def upsert_artifact(self, artifact: SkillArtifact) -> None:
        self.save_artifact(artifact)

    def refresh_artifact_state(
        self, skill_id: str, version: str, *, status: str, path: Optional[str] = None, source: str = "openclaw"
    ) -> None:
        artifact = self.get_latest_artifact(skill_id)
        if artifact is None or artifact.version != version:
            artifact = SkillArtifact(
                skill_id=skill_id,
                version=version,
                path=path or "",
                source=source,
                status=status,
                installed_at=datetime.now().isoformat(),
            )
        else:
            artifact.status = status
            if path is not None:
                artifact.path = path
            artifact.source = source
        self.upsert_artifact(artifact)

    def save_state(self, execution_id: str, sprint_name: str, task_name: str, state: SkillInjectionState) -> None:
        self._state_path(execution_id, sprint_name, task_name, state.skill_id).write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load_state(
        self, execution_id: str, sprint_name: str, task_name: str, skill_id: str
    ) -> Optional[SkillInjectionState]:
        path = self._state_path(execution_id, sprint_name, task_name, skill_id)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return SkillInjectionState(**raw)

    def delete_state(self, execution_id: str, sprint_name: str, task_name: str, skill_id: str) -> bool:
        path = self._state_path(execution_id, sprint_name, task_name, skill_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def append_record(self, record: SkillExecutionRecord) -> None:
        payload: Dict[str, Any] = asdict(record)
        with self._record_path(record.execution_id).open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def append_trace(self, trace: TaskSkillTrace) -> None:
        payload = asdict(trace)
        with self._trace_path(trace.execution_id).open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def load_record_lines(self, execution_id: str) -> List[Dict[str, Any]]:
        path = self._record_path(execution_id)
        if not path.exists():
            return []
        lines: List[Dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                lines.append(json.loads(line))
        return lines

    def load_trace_lines(self, execution_id: str) -> List[Dict[str, Any]]:
        path = self._trace_path(execution_id)
        if not path.exists():
            return []
        lines: List[Dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                lines.append(json.loads(line))
        return lines


__all__ = ["SkillStore"]
