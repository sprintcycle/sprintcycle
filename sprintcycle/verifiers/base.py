"""
verifiers.base - 基础验证器类
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AccessibilityNode:
    """Accessibility Tree 节点"""
    role: str
    name: str
    value: Optional[str] = None
    children: List['AccessibilityNode'] = None
    properties: Dict = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.properties is None:
            self.properties = {}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AccessibilityNode':
        return cls(
            role=data.get('role', 'unknown'),
            name=data.get('name', ''),
            value=data.get('value'),
            children=[cls.from_dict(c) for c in data.get('children', [])],
            properties=data.get('properties', {})
        )
    
    def find_by_role(self, role: str) -> List['AccessibilityNode']:
        """查找指定角色的节点"""
        results = []
        if self.role.lower() == role.lower():
            results.append(self)
        for child in self.children:
            results.extend(child.find_by_role(role))
        return results
    
    def find_by_text(self, text: str, exact: bool = False) -> List['AccessibilityNode']:
        """通过文本内容查找节点"""
        results = []
        check = (lambda n, t: n == t) if exact else (lambda n, t: t.lower() in n.lower())
        if check(self.name, text) or (self.value and check(self.value, text)):
            results.append(self)
        for child in self.children:
            results.extend(child.find_by_text(text, exact))
        return results
    
    def to_text(self) -> str:
        """转换为可读文本"""
        parts = [f"[{self.role}] {self.name}"]
        if self.value:
            parts.append(f"= {self.value}")
        for child in self.children:
            parts.append(f"  {child.to_text()}")
        return "\n".join(parts)
