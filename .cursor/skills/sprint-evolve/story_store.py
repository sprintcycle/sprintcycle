#!/usr/bin/env python3
"""用户故事存储管理器 - 支持持久化、补充、删除和修正"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import hashlib
from datetime import datetime

from loguru import logger


@dataclass
class StoredUserStory:
    """存储的用户故事"""
    id: str
    title: str
    description: str
    role: str
    feature: str
    purpose: str
    acceptance_criteria: List[str]
    priority: str
    impact: str
    complexity: str
    score: float
    source: str
    type: str
    tags: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    status: str = "active"  # active, completed, obsolete
    version: int = 1


class StoryStoreManager:
    """用户故事存储管理器"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path("userstories")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.base_dir / "stories.json"
        self.metadata_file = self.base_dir / "metadata.json"
        
        # 加载现有数据
        self._stories: Dict[str, StoredUserStory] = {}
        self._load_data()
    
    def _load_data(self):
        """加载现有数据"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for story_id, story_data in data.items():
                        self._stories[story_id] = StoredUserStory(**story_data)
                logger.info(f"✅ 加载了 {len(self._stories)} 个用户故事")
            except Exception as e:
                logger.error(f"加载用户故事失败: {e}")
    
    def _save_data(self):
        """保存数据"""
        try:
            data = {story_id: story.__dict__ for story_id, story in self._stories.items()}
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存元数据
            metadata = {
                "total_stories": len(self._stories),
                "active_stories": sum(1 for s in self._stories.values() if s.status == "active"),
                "updated_at": datetime.now().isoformat()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 保存了 {len(self._stories)} 个用户故事")
        except Exception as e:
            logger.error(f"保存用户故事失败: {e}")
    
    def _generate_id(self, title: str, source: str) -> str:
        """生成唯一ID"""
        hash_str = f"{title}_{source}_{datetime.now().timestamp()}"
        return f"story_{hashlib.md5(hash_str.encode()).hexdigest()[:8]}"
    
    def add_or_update_story(self, story_data: Dict[str, Any]) -> str:
        """添加或更新用户故事"""
        # 尝试找到匹配的现有故事
        existing_id = self._find_matching_story(story_data)
        
        if existing_id:
            return self._update_story(existing_id, story_data)
        else:
            return self._add_new_story(story_data)
    
    def _find_matching_story(self, story_data: Dict[str, Any]) -> Optional[str]:
        """查找匹配的现有故事"""
        title = story_data.get('title', '')
        
        for story_id, story in self._stories.items():
            # 标题相似度匹配
            if self._titles_similar(title, story.title):
                return story_id
        
        return None
    
    def _titles_similar(self, title1: str, title2: str) -> bool:
        """判断两个标题是否相似"""
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        
        # 完全匹配
        if t1 == t2:
            return True
        
        # 包含关系
        if t1 in t2 or t2 in t1:
            return True
        
        return False
    
    def _add_new_story(self, story_data: Dict[str, Any]) -> str:
        """添加新用户故事"""
        now = datetime.now().isoformat()
        
        story = StoredUserStory(
            id=self._generate_id(story_data.get('title', ''), story_data.get('source', 'unknown')),
            title=story_data.get('title', ''),
            description=story_data.get('description', ''),
            role=story_data.get('role', ''),
            feature=story_data.get('feature', ''),
            purpose=story_data.get('purpose', ''),
            acceptance_criteria=story_data.get('acceptance_criteria', []),
            priority=story_data.get('priority', 'Medium'),
            impact=story_data.get('impact', 'Medium'),
            complexity=story_data.get('complexity', 'Medium'),
            score=story_data.get('score', 50.0),
            source=story_data.get('source', 'unknown'),
            type=story_data.get('type', '功能需求'),
            tags=story_data.get('tags', []),
            related_files=story_data.get('related_files', []),
            created_at=now,
            updated_at=now,
            status="active",
            version=1
        )
        
        self._stories[story.id] = story
        self._save_data()
        
        logger.info(f"➕ 添加新用户故事: {story.id} - {story.title}")
        return story.id
    
    def _update_story(self, story_id: str, story_data: Dict[str, Any]) -> str:
        """更新现有用户故事"""
        story = self._stories.get(story_id)
        if not story:
            return ""
        
        # 更新字段
        if 'title' in story_data:
            story.title = story_data['title']
        if 'description' in story_data:
            story.description = story_data['description']
        if 'role' in story_data:
            story.role = story_data['role']
        if 'feature' in story_data:
            story.feature = story_data['feature']
        if 'purpose' in story_data:
            story.purpose = story_data['purpose']
        if 'acceptance_criteria' in story_data:
            story.acceptance_criteria = story_data['acceptance_criteria']
        if 'priority' in story_data:
            story.priority = story_data['priority']
        if 'impact' in story_data:
            story.impact = story_data['impact']
        if 'complexity' in story_data:
            story.complexity = story_data['complexity']
        if 'score' in story_data:
            story.score = story_data['score']
        if 'type' in story_data:
            story.type = story_data['type']
        if 'tags' in story_data:
            # 合并标签，不覆盖
            existing_tags = set(story.tags)
            new_tags = set(story_data['tags'])
            story.tags = list(existing_tags.union(new_tags))
        
        story.updated_at = datetime.now().isoformat()
        story.version += 1
        
        self._save_data()
        
        logger.info(f"🔄 更新用户故事: {story.id} (版本 {story.version})")
        return story_id
    
    def mark_obsolete(self, story_id: str) -> bool:
        """标记故事为过期"""
        story = self._stories.get(story_id)
        if not story:
            return False
        
        story.status = "obsolete"
        story.updated_at = datetime.now().isoformat()
        self._save_data()
        
        logger.info(f"❌ 标记用户故事为过期: {story_id}")
        return True
    
    def delete_story(self, story_id: str) -> bool:
        """删除用户故事"""
        if story_id not in self._stories:
            return False
        
        del self._stories[story_id]
        self._save_data()
        
        logger.info(f"🗑️ 删除用户故事: {story_id}")
        return True
    
    def get_all_stories(self) -> List[StoredUserStory]:
        """获取所有用户故事"""
        return list(self._stories.values())
    
    def get_active_stories(self) -> List[StoredUserStory]:
        """获取活跃的用户故事"""
        return [s for s in self._stories.values() if s.status == "active"]
    
    def get_story_by_id(self, story_id: str) -> Optional[StoredUserStory]:
        """根据ID获取用户故事"""
        return self._stories.get(story_id)
    
    def get_stories_by_type(self, story_type: str) -> List[StoredUserStory]:
        """按类型获取用户故事"""
        return [s for s in self._stories.values() if s.type == story_type and s.status == "active"]
    
    def get_top_stories(self, count: int = 5) -> List[StoredUserStory]:
        """获取 Top N 优先级最高的故事"""
        active = self.get_active_stories()
        return sorted(active, key=lambda x: x.score, reverse=True)[:count]
    
    def clean_obsolete(self, days_threshold: int = 30) -> int:
        """清理过期的用户故事"""
        count = 0
        now = datetime.now()
        
        obsolete_ids = []
        for story_id, story in self._stories.items():
            if story.status == "obsolete":
                try:
                    updated = datetime.fromisoformat(story.updated_at)
                    if (now - updated).days >= days_threshold:
                        obsolete_ids.append(story_id)
                except Exception:
                    obsolete_ids.append(story_id)
        
        for story_id in obsolete_ids:
            self.delete_story(story_id)
            count += 1
        
        if count > 0:
            logger.info(f"🧹 清理了 {count} 个过期用户故事")
        
        return count
    
    def import_stories(self, stories: List[Dict[str, Any]]) -> int:
        """批量导入用户故事"""
        count = 0
        for story_data in stories:
            self.add_or_update_story(story_data)
            count += 1
        
        logger.info(f"📥 批量导入了 {count} 个用户故事")
        return count
    
    def export_stories(self, output_path: Optional[Path] = None) -> bool:
        """导出用户故事"""
        output_path = output_path or self.base_dir / f"stories_export_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            active_stories = self.get_active_stories()
            data = [{
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "role": s.role,
                "feature": s.feature,
                "purpose": s.purpose,
                "acceptance_criteria": s.acceptance_criteria,
                "priority": s.priority,
                "impact": s.impact,
                "complexity": s.complexity,
                "score": s.score,
                "source": s.source,
                "type": s.type,
                "tags": s.tags,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "version": s.version
            } for s in active_stories]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📤 导出了 {len(active_stories)} 个用户故事到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出失败: {e}")
            return False


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="用户故事存储管理器")
    parser.add_argument("--list", action="store_true", help="列出所有用户故事")
    parser.add_argument("--top", type=int, default=5, help="列出 Top N 用户故事")
    parser.add_argument("--export", action="store_true", help="导出用户故事")
    parser.add_argument("--clean", action="store_true", help="清理过期故事")
    
    args = parser.parse_args()
    
    manager = StoryStoreManager()
    
    if args.list:
        stories = manager.get_active_stories()
        print(f"活跃用户故事数: {len(stories)}")
        for story in stories:
            print(f"\n{story.id}")
            print(f"  标题: {story.title}")
            print(f"  优先级: {story.priority}")
            print(f"  分数: {story.score}")
            print(f"  类型: {story.type}")
            print(f"  状态: {story.status}")
    
    elif args.top:
        stories = manager.get_top_stories(args.top)
        print(f"Top {args.top} 用户故事:")
        for i, story in enumerate(stories, 1):
            print(f"\n{i}. [{story.score:.1f}] {story.title}")
            print(f"   - 优先级: {story.priority}")
            print(f"   - 类型: {story.type}")
    
    elif args.export:
        manager.export_stories()
    
    elif args.clean:
        count = manager.clean_obsolete()
        print(f"清理了 {count} 个过期用户故事")
    
    else:
        print("使用 --list, --top, --export, 或 --clean 参数")


if __name__ == "__main__":
    main()