"""数据模型 - 微博类产品"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
    password: str
    email: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "username": self.username, "email": self.email, "nickname": self.nickname, "avatar": self.avatar, "bio": self.bio}

@dataclass
class Post:
    id: int
    user_id: int
    content: str
    images: List[str] = field(default_factory=list)
    likes_count: int = 0
    comments_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "user_id": self.user_id, "content": self.content, "images": self.images, "likes_count": self.likes_count}

@dataclass
class Comment:
    id: int
    post_id: int
    user_id: int
    content: str
    parent_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {"id": self.id, "post_id": self.post_id, "user_id": self.user_id, "content": self.content}
