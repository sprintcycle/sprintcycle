"""
MemoryStore - 进化记忆存储
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvolutionMemory:
    id: str
    memory_type: str
    content: Dict[str, Any]
    context: Dict[str, str] = field(default_factory=dict)
    success: bool = True
    score: float = 0.5
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "memory_type": self.memory_type,
            "content": self.content,
            "context": self.context,
            "success": self.success,
            "score": self.score,
            "tags": self.tags,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionMemory":
        return cls(
            id=data["id"],
            memory_type=data["memory_type"],
            content=data["content"],
            context=data.get("context", {}),
            success=data.get("success", True),
            score=data.get("score", 0.5),
            tags=data.get("tags", []),
            created_at=data.get("created_at", time.time()),
            accessed_at=data.get("accessed_at", time.time()),
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemoryConfig:
    storage_path: str = "./evolution_cache/memory"
    max_memories: int = 1000
    retention_days: int = 30
    enable_compression: bool = False


    @classmethod
    def from_runtime_config(cls, rc) -> "MemoryConfig":
        """Construct from RuntimeConfig."""
        cache_dir = getattr(rc, 'evolution_cache_dir', './evolution_cache')
        return cls(
            storage_path=f"{cache_dir}/memory",
        )


class MemoryStore:
    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        storage_path: Optional[str] = None,
        runtime_config=None,
    ):
        if config:
            self.config = config
        elif storage_path:
            self.config = MemoryConfig(storage_path=storage_path)
        elif runtime_config is not None:
            self.config = MemoryConfig.from_runtime_config(runtime_config)
        else:
            self.config = MemoryConfig()
        
        self._storage_path = Path(self.config.storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        self._memories: Dict[str, EvolutionMemory] = {}
        self._index_by_type: Dict[str, List[str]] = {}
        self._index_by_tag: Dict[str, List[str]] = {}
        
        self._load_from_disk()
    
    def _load_from_disk(self) -> None:
        try:
            index_file = self._storage_path / "index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
                
                for memory_id in index_data.get("memory_ids", []):
                    memory_file = self._storage_path / f"{memory_id}.json"
                    if memory_file.exists():
                        with open(memory_file, "r", encoding="utf-8") as f:
                            memory = EvolutionMemory.from_dict(json.load(f))
                            self._memories[memory_id] = memory
                            self._update_indices(memory)
                
                logger.info(f"Loaded {len(self._memories)} memories from disk")
        except Exception as e:
            logger.warning(f"Failed to load memories from disk: {e}")
    
    def _save_to_disk(self, memory: EvolutionMemory) -> None:
        try:
            memory_file = self._storage_path / f"{memory.id}.json"
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(memory.to_dict(), f, ensure_ascii=False, indent=2)
            
            index_file = self._storage_path / "index.json"
            index_data = {
                "memory_ids": list(self._memories.keys()),
                "updated_at": time.time(),
            }
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save memory to disk: {e}")
    
    def _update_indices(self, memory: EvolutionMemory) -> None:
        if memory.memory_type not in self._index_by_type:
            self._index_by_type[memory.memory_type] = []
        if memory.id not in self._index_by_type[memory.memory_type]:
            self._index_by_type[memory.memory_type].append(memory.id)
        
        for tag in memory.tags:
            if tag not in self._index_by_tag:
                self._index_by_tag[tag] = []
            if memory.id not in self._index_by_tag[tag]:
                self._index_by_tag[tag].append(memory.id)
    
    def store(
        self,
        memory_type: str,
        content: Dict[str, Any],
        context: Optional[Dict[str, str]] = None,
        success: bool = True,
        score: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvolutionMemory:
        memory = EvolutionMemory(
            id=str(uuid.uuid4()),
            memory_type=memory_type,
            content=content,
            context=context or {},
            success=success,
            score=score,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        self._memories[memory.id] = memory
        self._update_indices(memory)
        self._save_to_disk(memory)
        
        logger.debug(f"Stored memory: {memory.id} ({memory_type})")
        self._cleanup_old_memories()
        
        return memory
    
    def get(self, memory_id: str) -> Optional[EvolutionMemory]:
        memory = self._memories.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.accessed_at = time.time()
        return memory
    
    def search(
        self,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        success: Optional[bool] = None,
        min_score: Optional[float] = None,
        limit: int = 10,
    ) -> List[EvolutionMemory]:
        candidates = set(self._memories.keys())
        
        if memory_type:
            candidates &= set(self._index_by_type.get(memory_type, []))
        
        if tags:
            for tag in tags:
                tag_memories = set(self._index_by_tag.get(tag, []))
                candidates &= tag_memories
        
        results = []
        for memory_id in candidates:
            memory = self._memories[memory_id]
            
            if success is not None and memory.success != success:
                continue
            
            if min_score is not None and memory.score < min_score:
                continue
            
            results.append(memory)
        
        results.sort(key=lambda m: (m.score, m.created_at), reverse=True)
        
        return results[:limit]
    
    def get_successful_patterns(
        self, memory_type: str = "gene", min_score: float = 0.7, limit: int = 20
    ) -> List[EvolutionMemory]:
        return self.search(
            memory_type=memory_type,
            success=True,
            min_score=min_score,
            limit=limit,
        )
    
    def get_failed_attempts(self, limit: int = 20) -> List[EvolutionMemory]:
        return self.search(
            memory_type="attempt",
            success=False,
            limit=limit,
        )
    
    def update_score(self, memory_id: str, success: bool, delta: float = 0.0) -> bool:
        memory = self._memories.get(memory_id)
        if not memory:
            return False
        
        memory.success = success
        memory.score = max(0.0, min(1.0, memory.score + delta))
        memory.accessed_at = time.time()
        
        self._save_to_disk(memory)
        return True
    
    def delete(self, memory_id: str) -> bool:
        if memory_id not in self._memories:
            return False
        
        memory = self._memories.pop(memory_id)
        
        if memory.memory_type in self._index_by_type:
            self._index_by_type[memory.memory_type].remove(memory_id)
        
        for tag in memory.tags:
            if tag in self._index_by_tag:
                try:
                    self._index_by_tag[tag].remove(memory_id)
                except ValueError:
                    pass
        
        memory_file = self._storage_path / f"{memory_id}.json"
        if memory_file.exists():
            memory_file.unlink()
        
        logger.debug(f"Deleted memory: {memory_id}")
        return True
    
    def _cleanup_old_memories(self) -> int:
        if len(self._memories) <= self.config.max_memories:
            return 0
        
        memories = sorted(
            self._memories.values(),
            key=lambda m: (m.access_count, m.created_at),
        )
        
        to_delete = memories[: len(memories) - self.config.max_memories]
        for memory in to_delete:
            self.delete(memory.id)
        
        return len(to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        total = len(self._memories)
        by_type = {
            mtype: len(mids)
            for mtype, mids in self._index_by_type.items()
        }
        by_success = {
            "success": sum(1 for m in self._memories.values() if m.success),
            "failed": sum(1 for m in self._memories.values() if not m.success),
        }
        
        return {
            "total_memories": total,
            "by_type": by_type,
            "by_success": by_success,
            "unique_tags": len(self._index_by_tag),
            "storage_path": str(self._storage_path),
        }
    
    def clear(self) -> int:
        count = len(self._memories)
        for memory_id in list(self._memories.keys()):
            self.delete(memory_id)
        
        self._memories.clear()
        self._index_by_type.clear()
        self._index_by_tag.clear()
        
        return count
