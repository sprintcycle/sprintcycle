"""OpenClaw 技能市场接入接口。"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import SkillArtifact
from ..store import SkillStore


@dataclass
class SkillMarketVersion:
    version: str
    changelog: str = ""
    checksum: str = ""
    created_at: str = ""


@dataclass
class SkillMarketItem:
    skill_id: str
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    versions: List[SkillMarketVersion] = field(default_factory=list)


@dataclass
class InstalledSkillRecord:
    skill_id: str
    version: str
    installed_at: str
    source: str
    checksum: str = ""
    rollback_to: str = ""


class OpenClawMarketplaceClient:
    def __init__(self, cache_dir: str = ".sprintcycle/marketplace", skill_store: Optional[SkillStore] = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._install_log = self.cache_dir / "installs.jsonl"
        self._installed_dir = self.cache_dir / "installed"
        self._installed_dir.mkdir(parents=True, exist_ok=True)
        self._current_dir = self.cache_dir / "current"
        self._current_dir.mkdir(parents=True, exist_ok=True)
        self._skill_store = skill_store or SkillStore()

    def _index_path(self) -> Path:
        return self.cache_dir / "index.json"

    def _installed_skill_dir(self, skill_id: str, version: str) -> Path:
        return self._installed_dir / skill_id / version

    def _version_manifest(self, skill_id: str, version: str) -> Path:
        return self._installed_skill_dir(skill_id, version) / "manifest.json"

    def _safe_link(self, src: Path, dst: Path) -> None:
        if dst.exists() or dst.is_symlink():
            if dst.is_symlink() or dst.is_file():
                dst.unlink()
            else:
                shutil.rmtree(dst)
        dst.symlink_to(src, target_is_directory=True)

    def _persist_artifact(
        self, skill_id: str, version: str, path: str, checksum: str, source: str = "openclaw", status: str = "installed"
    ) -> None:
        self._skill_store.upsert_artifact(
            SkillArtifact(
                skill_id=skill_id,
                version=version,
                path=path,
                content_hash=checksum,
                installed_at=datetime.now().isoformat(),
                source=source,
                status=status,
            )
        )

    async def search(self, query: str, tags: Optional[List[str]] = None) -> List[SkillMarketItem]:
        index = self._index_path()
        if not index.exists():
            return []
        raw = json.loads(index.read_text(encoding="utf-8"))
        items: List[SkillMarketItem] = []
        for item in raw.get("items", []):
            if (
                query.lower()
                not in f"{item.get('skill_id', '')} {item.get('name', '')} {item.get('description', '')}".lower()
            ):
                continue
            if tags and not set(tags).issubset(set(item.get("tags", []))):
                continue
            versions = [SkillMarketVersion(**v) for v in item.get("versions", [])]
            items.append(
                SkillMarketItem(
                    skill_id=item["skill_id"],
                    name=item["name"],
                    description=item.get("description", ""),
                    tags=item.get("tags", []),
                    versions=versions,
                )
            )
        return items

    async def install(self, skill_id: str, version: str = "latest") -> Dict[str, Any]:
        versions = await self.get_versions(skill_id)
        if not versions:
            raise FileNotFoundError(f"skill not found in marketplace: {skill_id}")
        selected = versions[-1] if version == "latest" else next((v for v in versions if v.version == version), None)
        if selected is None:
            raise FileNotFoundError(f"version not found: {skill_id}@{version}")
        target = self._installed_skill_dir(skill_id, selected.version)
        target.mkdir(parents=True, exist_ok=True)
        manifest = InstalledSkillRecord(
            skill_id=skill_id,
            version=selected.version,
            installed_at=datetime.now().isoformat(),
            source="openclaw",
            checksum=selected.checksum,
        )
        manifest_path = self._version_manifest(skill_id, selected.version)
        manifest_path.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
        current_target = self._current_dir / skill_id
        self._safe_link(target, current_target)
        payload = {
            "skill_id": skill_id,
            "version": selected.version,
            "installed": True,
            "manifest": str(manifest_path),
            "checksum": selected.checksum,
            "installed_at": manifest.installed_at,
        }
        with self._install_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._persist_artifact(
            skill_id, selected.version, str(target), selected.checksum, source="openclaw", status="installed"
        )
        return payload

    async def rollback(self, skill_id: str, version: str) -> Dict[str, Any]:
        target = self._installed_skill_dir(skill_id, version)
        if not target.exists():
            raise FileNotFoundError(f"rollback target not found: {skill_id}@{version}")
        current_target = self._current_dir / skill_id
        self._safe_link(target, current_target)
        self._persist_artifact(
            skill_id,
            version,
            str(target),
            self._artifact_checksum(skill_id, version),
            source="openclaw",
            status="rolled_back",
        )
        payload = {"skill_id": skill_id, "version": version, "rolled_back": True}
        with self._install_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return payload

    async def get_versions(self, skill_id: str) -> List[SkillMarketVersion]:
        index = self._index_path()
        if not index.exists():
            return []
        raw = json.loads(index.read_text(encoding="utf-8"))
        for item in raw.get("items", []):
            if item.get("skill_id") == skill_id:
                return [SkillMarketVersion(**v) for v in item.get("versions", [])]
        return []

    async def install_skill_to_path(self, skill_id: str, version: str, path: str) -> Dict[str, Any]:
        payload = await self.install(skill_id, version)
        target = Path(path)
        target.mkdir(parents=True, exist_ok=True)
        marker = target / f"{skill_id}.installed.json"
        marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["path"] = str(marker)
        return payload

    def refresh_skill_state(self, skill_id: str, version: str, *, status: str, path: Optional[str] = None) -> None:
        self._persist_artifact(
            skill_id,
            version,
            path or str(self._installed_skill_dir(skill_id, version)),
            self._artifact_checksum(skill_id, version),
            status=status,
        )

    def _artifact_checksum(self, skill_id: str, version: str) -> str:
        path = self._installed_skill_dir(skill_id, version)
        return hashlib.sha256(str(path).encode("utf-8")).hexdigest()

    @staticmethod
    def checksum_for_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def seed_index(self, items: List[SkillMarketItem]) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        index = self._index_path()
        index.write_text(
            json.dumps({"items": [asdict(i) for i in items]}, ensure_ascii=False, indent=2), encoding="utf-8"
        )


__all__ = ["OpenClawMarketplaceClient", "SkillMarketItem", "SkillMarketVersion", "InstalledSkillRecord"]
