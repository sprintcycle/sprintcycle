"""SprintCycle 知识库管理"""

import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib

from ..models.knowledge import KnowledgeEntry, KnowledgeType


class KnowledgeBase:
    """
    知识库管理器
    
    职责:
    1. 存储和检索知识条目
    2. 基于相关性的知识检索
    3. 跨 Sprint 知识共享
    """
    
    def __init__(self, storage_path: str = "knowledge.json"):
        self.storage_path = Path(storage_path)
        self.entries: List[KnowledgeEntry] = []
        self._load()
    
    def _load(self):
        """从文件加载知识库"""
        if self.storage_path.exists():
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.entries = [
                    KnowledgeEntry.from_dict(item) for item in data.get("entries", [])
                ]
    
    def _save(self):
        """保存知识库到文件"""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in self.entries],
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def add_entry(self, entry: KnowledgeEntry) -> str:
        """添加知识条目"""
        # 生成唯一 ID
        if not entry.id:
            content_hash = hashlib.md5(
                f"{entry.title}{entry.content}".encode()
            ).hexdigest()[:8]
            entry.id = f"kb_{datetime.now().strftime('%Y%m%d')}_{content_hash}"
        
        # 检查重复
        existing = [e for e in self.entries if e.title == entry.title]
        if existing:
            # 更新现有条目
            idx = self.entries.index(existing[0])
            self.entries[idx] = entry
        else:
            self.entries.append(entry)
        
        self._save()
        return entry.id
    
    async def retrieve_for_sprint(
        self,
        project_name: str,
        sprint_goals: List[str],
        limit: int = 10,
    ) -> List[KnowledgeEntry]:
        """为 Sprint 检索相关知识"""
        # 构建搜索关键词
        keywords = set()
        for goal in sprint_goals:
            keywords.update(goal.lower().split())
        
        # 计算相关性得分
        scored_entries = []
        for entry in self.entries:
            score = self._calculate_relevance(entry, keywords, project_name)
            if score > 0:
                entry.relevance_score = score
                scored_entries.append(entry)
        
        # 排序并返回
        scored_entries.sort(key=lambda e: e.relevance_score, reverse=True)
        return scored_entries[:limit]
    
    def _calculate_relevance(
        self,
        entry: KnowledgeEntry,
        keywords: set,
        project_name: str,
    ) -> float:
        """计算相关性得分"""
        score = 0.0
        
        # 项目匹配加分
        if entry.project_name == project_name:
            score += 0.5
        
        # 标题关键词匹配
        title_words = set(entry.title.lower().split())
        title_overlap = len(keywords & title_words)
        score += title_overlap * 0.2
        
        # 内容关键词匹配
        content_words = set(entry.content.lower().split())
        content_overlap = len(keywords & content_words)
        score += content_overlap * 0.05
        
        # 标签匹配
        for tag in entry.tags:
            if tag.lower() in keywords:
                score += 0.1
        
        return score
    
    async def search(
        self,
        query: str,
        project_name: Optional[str] = None,
        entry_type: Optional[KnowledgeType] = None,
        limit: int = 10,
    ) -> List[KnowledgeEntry]:
        """搜索知识库"""
        query_words = set(query.lower().split())
        
        results = []
        for entry in self.entries:
            # 类型过滤
            if entry_type and entry.type != entry_type:
                continue
            
            # 项目过滤
            if project_name and entry.project_name != project_name:
                continue
            
            # 计算相关性
            score = self._calculate_relevance(entry, query_words, project_name or "")
            if score > 0:
                entry.relevance_score = score
                results.append(entry)
        
        results.sort(key=lambda e: e.relevance_score, reverse=True)
        return results[:limit]
    
    async def get_by_sprint(self, sprint_index: int) -> List[KnowledgeEntry]:
        """获取特定 Sprint 产生的知识"""
        return [e for e in self.entries if e.source_sprint == sprint_index]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        type_counts = {}
        for entry in self.entries:
            type_name = entry.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            "total_entries": len(self.entries),
            "by_type": type_counts,
            "storage_path": str(self.storage_path),
        }
