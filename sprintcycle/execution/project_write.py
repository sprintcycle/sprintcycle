"""项目写入策略。"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ReferenceProjectSummary:
    path: str
    exists: bool
    files: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class BackupRecord:
    path: str
    backup_path: str
    created_at: str
    method: str = "copy"


@dataclass
class GitRecord:
    is_repo: bool
    branch: str = ""
    dirty: bool = False
    status: str = ""
    diff_before: str = ""
    diff_after: str = ""


@dataclass
class ChangeHint:
    path: str
    action: str
    reason: str = ""
    mode: str = ""


@dataclass
class IncrementalDiffSummary:
    total_files: int = 0
    created_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    backup_count: int = 0
    reference_count: int = 0
    notes: str = ""
    change_hints: List[ChangeHint] = field(default_factory=list)


@dataclass
class ProjectWritePlan:
    target_path: str
    write_policy: str
    intent: str
    references: List[ReferenceProjectSummary] = field(default_factory=list)
    target_exists: bool = False
    created_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    backups: List[BackupRecord] = field(default_factory=list)
    git: Optional[GitRecord] = None
    diff_summary: Optional[IncrementalDiffSummary] = None
    rollback_notes: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProjectWriteStrategy:
    def __init__(self, target_path: str, references: Optional[List[str]] = None, write_policy: str = "incremental") -> None:
        self.target_path = Path(target_path)
        self.references = [Path(p) for p in (references or [])]
        self.write_policy = (write_policy or "incremental").strip().lower()
        self._backup_root = self.target_path / ".sprintcycle" / "backups"

    def summarize_reference(self, path: Path) -> ReferenceProjectSummary:
        if not path.exists():
            return ReferenceProjectSummary(path=str(path), exists=False, notes="reference_missing")
        files = [str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()][:200]
        entry_points: List[str] = []
        for candidate in ["main.py", "app.py", "src/main.py", "index.ts", "index.js", "pyproject.toml", "package.json"]:
            if (path / candidate).exists():
                entry_points.append(candidate)
        languages = sorted({p.suffix.lstrip(".") for p in path.rglob("*") if p.is_file() and p.suffix})
        notes = "reference_ready"
        if entry_points:
            notes = "reference_ready_with_entry_points"
        return ReferenceProjectSummary(path=str(path), exists=True, files=files, entry_points=entry_points, languages=languages[:10], notes=notes)

    def _run_git(self, *args: str) -> str:
        try:
            proc = subprocess.run(["git", *args], cwd=str(self.target_path), capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                return ""
            return proc.stdout.strip()
        except Exception:
            return ""

    def _detect_git(self) -> GitRecord:
        git_dir = self.target_path / ".git"
        is_repo = git_dir.exists()
        if not is_repo:
            return GitRecord(is_repo=False)
        branch = self._run_git("branch", "--show-current")
        status = self._run_git("status", "--short")
        diff_before = self._run_git("diff")
        return GitRecord(is_repo=True, branch=branch, dirty=bool(status), status=status, diff_before=diff_before)

    def _backup_file(self, file_path: Path, plan: ProjectWritePlan) -> None:
        if not file_path.exists():
            return
        rel = file_path.relative_to(self.target_path)
        backup_path = self._backup_root / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        plan.backups.append(BackupRecord(path=str(file_path), backup_path=str(backup_path), created_at=datetime.now().isoformat()))

    def build_plan(self, intent: str) -> ProjectWritePlan:
        refs = [self.summarize_reference(p) for p in self.references]
        return ProjectWritePlan(target_path=str(self.target_path), write_policy=self.write_policy, intent=intent, references=refs, target_exists=self.target_path.exists(), git=self._detect_git())

    def ensure_target(self) -> None:
        self.target_path.mkdir(parents=True, exist_ok=True)

    def _write_file(self, rel_path: str, content: str, plan: ProjectWritePlan, *, allow_overwrite: bool) -> None:
        file_path = self.target_path / rel_path
        existed = file_path.exists()
        if existed and not allow_overwrite:
            plan.skipped_files.append(rel_path)
            return
        if existed and allow_overwrite:
            self._backup_file(file_path, plan)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        if existed:
            plan.modified_files.append(rel_path)
        else:
            plan.created_files.append(rel_path)

    def _reference_note(self, plan: ProjectWritePlan) -> str:
        parts = []
        for ref in plan.references:
            if not ref.exists:
                continue
            label = Path(ref.path).name
            ep = ", ".join(ref.entry_points) if ref.entry_points else "no-entry-point"
            langs = ", ".join(ref.languages[:5]) if ref.languages else "unknown"
            parts.append(f"- {label}: entry={ep}; langs={langs}")
        return "\n".join(parts) if parts else "- none"

    def _build_change_hints(self, plan: ProjectWritePlan) -> List[ChangeHint]:
        hints: List[ChangeHint] = []
        if self.write_policy == "create":
            hints.append(ChangeHint(path="README.md", action="new", reason="bootstrap project skeleton", mode="create"))
            hints.append(ChangeHint(path=".sprintcycle/project.json", action="new", reason="persist project intent and references", mode="create"))
            return hints
        if self.write_policy == "safe":
            hints.append(ChangeHint(path=".sprintcycle/write-plan.json", action="append", reason="record safe plan without overwriting existing files", mode="safe"))
            return hints
        hints.append(ChangeHint(path="README.md", action="modify", reason="refresh project summary with reference context", mode="incremental"))
        hints.append(ChangeHint(path=".sprintcycle/write-plan.json", action="new", reason="record incremental plan and rollback metadata", mode="incremental"))
        for ref in plan.references:
            if ref.exists and ref.entry_points:
                hints.append(ChangeHint(path=ref.entry_points[0], action="inspect-only", reason="reference entry point for style and structure", mode="incremental"))
        return hints

    def _diff_summary(self, plan: ProjectWritePlan) -> IncrementalDiffSummary:
        return IncrementalDiffSummary(
            total_files=len(plan.created_files) + len(plan.modified_files) + len(plan.skipped_files),
            created_files=list(plan.created_files),
            modified_files=list(plan.modified_files),
            skipped_files=list(plan.skipped_files),
            backup_count=len(plan.backups),
            reference_count=len([r for r in plan.references if r.exists]),
            notes="incremental_write" if self.write_policy == "incremental" else self.write_policy,
            change_hints=self._build_change_hints(plan),
        )

    def _template_for_create(self, intent: str, plan: ProjectWritePlan) -> Dict[str, str]:
        refs = self._reference_note(plan)
        return {
            "README.md": f"# {self.target_path.name}\n\n{intent}\n\n## References\n{refs}\n",
            ".sprintcycle/project.json": json.dumps({"intent": intent, "write_policy": self.write_policy, "references": [r.path for r in plan.references]}, ensure_ascii=False, indent=2),
        }

    def _template_for_incremental(self, intent: str, plan: ProjectWritePlan) -> Dict[str, str]:
        refs = self._reference_note(plan)
        return {
            ".sprintcycle/write-plan.json": json.dumps({"intent": intent, "write_policy": self.write_policy, "references": [r.path for r in plan.references]}, ensure_ascii=False, indent=2),
            "README.md": f"# {self.target_path.name}\n\n{intent}\n\n## References\n{refs}\n",
        }

    def _template_for_safe(self, intent: str, plan: ProjectWritePlan) -> Dict[str, str]:
        return {
            ".sprintcycle/write-plan.json": json.dumps({"intent": intent, "write_policy": self.write_policy, "references": [r.path for r in plan.references]}, ensure_ascii=False, indent=2),
        }

    def apply_template(self, plan: ProjectWritePlan, template: Optional[Dict[str, str]] = None) -> ProjectWritePlan:
        self.ensure_target()
        if template is None:
            if self.write_policy == "create":
                template = self._template_for_create(plan.intent, plan)
            elif self.write_policy == "safe":
                template = self._template_for_safe(plan.intent, plan)
            else:
                template = self._template_for_incremental(plan.intent, plan)
        allow_overwrite = self.write_policy in {"incremental", "create"}
        for rel_path, content in template.items():
            self._write_file(rel_path, content, plan, allow_overwrite=allow_overwrite)
        if plan.git and plan.git.is_repo:
            plan.git.diff_after = self._run_git("diff")
            if plan.git.status != plan.git.diff_after:
                plan.rollback_notes.append("git diff captured for rollback")
        plan.diff_summary = self._diff_summary(plan)
        return plan

    def rollback_from_backups(self, plan: ProjectWritePlan) -> None:
        for backup in plan.backups:
            src = Path(backup.backup_path)
            dst = Path(backup.path)
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        plan.rollback_notes.append("restored_from_backup")

    def write_summary(self, plan: ProjectWritePlan) -> Path:
        summary_path = self.target_path / ".sprintcycle" / "write-plan.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return summary_path


__all__ = ["ProjectWriteStrategy", "ProjectWritePlan", "ReferenceProjectSummary", "BackupRecord", "GitRecord", "ChangeHint", "IncrementalDiffSummary"]
