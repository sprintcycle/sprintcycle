"""知识库模型定义"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class KnowledgeType(Enum):
    """知识类型"""
    ERROR_SOLUTION = "error_solution"      # 错误解决方案
    BEST_PRACTICE = "best_practice"        # 最佳实践
    ARCHITECTURE = "architecture"          # 架构决策
    API_USAGE = "api_usage"               # API 使用方法
    PATTERN = "pattern"                   # 设计模式
    LESSON_LEARNED = "lesson_learned"     # 经验教训


@dataclass
class KnowledgeEntry:
    """知识条目"""
    id: Optional[str] = None
    type: KnowledgeType = KnowledgeType.LESSON_LEARNED
    title: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    source_sprint: Optional[int] = None
    project_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    relevance_score: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "source_sprint": self.source_sprint,
            "project_name": self.project_name,
            "created_at": self.created_at.isoformat(),
            "relevance_score": self.relevance_score,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeEntry":
        return cls(
            id=data.get("id"),
            type=KnowledgeType(data.get("type", "lesson_learned")),
            title=data.get("title", ""),
            content=data.get("content", ""),
            tags=data.get("tags", []),
            source_sprint=data.get("source_sprint"),
            project_name=data.get("project_name"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            relevance_score=data.get("relevance_score", 0.0),
        )
