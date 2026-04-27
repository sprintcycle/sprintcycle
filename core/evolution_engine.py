"""EvolutionEngine - 自进化引擎 v2.0"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import hashlib


class EvolutionType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    IMPROVEMENT = "improvement"


class ImpactLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EvolutionRecord:
    id: str
    type: EvolutionType
    sprint_index: int
    title: str
    description: str
    impact: ImpactLevel
    context: Dict[str, Any] = field(default_factory=dict)
    applied: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "type": self.type.value, "sprint_index": self.sprint_index,
            "title": self.title, "description": self.description, "impact": self.impact.value,
            "context": self.context, "applied": self.applied, "created_at": self.created_at.isoformat()
        }


class EvolutionEngine:
    """自进化引擎 - 从失败中学习"""
    
    def __init__(self, path: str = "evolution.json"):
        self.path = Path(path)
        self.records: List[EvolutionRecord] = []
        self._load()
    
    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                for r in data.get("records", []):
                    self.records.append(EvolutionRecord(
                        id=r["id"], type=EvolutionType(r["type"]), sprint_index=r["sprint_index"],
                        title=r["title"], description=r["description"], impact=ImpactLevel(r.get("impact", "medium")),
                        context=r.get("context", {}), applied=r.get("applied", False),
                        created_at=datetime.fromisoformat(r["created_at"]) if r.get("created_at") else datetime.now()
                    ))
            except: pass
    
    def _save(self):
        self.path.write_text(json.dumps({
            "version": "2.0", "records": [r.to_dict() for r in self.records]
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    
    async def record_success(self, sprint: int, result: Dict[str, Any]) -> str:
        pattern = f"任务数: {len(result.get('tasks', []))}" if result.get('tasks') else "执行成功"
        r = EvolutionRecord(
            id=f"evo_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=EvolutionType.SUCCESS, sprint_index=sprint,
            title=f"Sprint {sprint+1} 成功模式", description=pattern,
            impact=ImpactLevel.MEDIUM, context={"result": str(result)[:500]}
        )
        self.records.append(r)
        self._save()
        print(f"📈 {r.title}")
        return r.id
    
    async def record_failure(self, sprint: int, error: str, error_type: str = None) -> str:
        analysis = self._analyze_error(error)
        r = EvolutionRecord(
            id=f"evo_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=EvolutionType.FAILURE, sprint_index=sprint,
            title=f"Sprint {sprint+1} 失败: {error_type or 'Unknown'}",
            description=error, impact=ImpactLevel.HIGH,
            context={"error_type": error_type, "analysis": analysis}
        )
        self.records.append(r)
        self._save()
        print(f"📉 {r.title}")
        return r.id
    
    def _analyze_error(self, error: str) -> Dict[str, Any]:
        patterns = {
            "timeout": {"cause": "执行超时", "fix": ["增加超时时间", "优化性能"]},
            "connection": {"cause": "连接失败", "fix": ["检查网络", "重试"]},
            "permission": {"cause": "权限不足", "fix": ["检查权限"]},
        }
        for key, info in patterns.items():
            if key in error.lower():
                return info
        return {"cause": error[:100], "fix": ["检查日志"]}
    
    async def get_recommendations(self) -> List[dict]:
        return [
            {"id": r.id, "title": r.title, "description": r.description, "fixes": r.context.get("analysis", {}).get("fix", [])}
            for r in self.records if r.impact == ImpactLevel.HIGH and not r.applied
        ]
    
    async def generate_knowledge(self, record_id: str) -> Optional[dict]:
        r = next((x for x in self.records if x.id == record_id), None)
        if not r: return None
        return {
            "type": "error_solution" if r.type == EvolutionType.FAILURE else "best_practice",
            "title": r.title, "content": r.description, "source_sprint": r.sprint_index
        }
    
    async def mark_applied(self, record_id: str) -> bool:
        for r in self.records:
            if r.id == record_id:
                r.applied = True
                self._save()
                return True
        return False
    
    async def get_statistics(self) -> dict:
        return {
            "total": len(self.records),
            "success": len([r for r in self.records if r.type == EvolutionType.SUCCESS]),
            "failure": len([r for r in self.records if r.type == EvolutionType.FAILURE]),
            "pending": len([r for r in self.records if r.impact == ImpactLevel.HIGH and not r.applied]),
        }
