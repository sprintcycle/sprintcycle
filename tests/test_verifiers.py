"""测试 SprintCycle Playwright 验证器"""
import pytest
from sprintcycle.verifiers import (
    AccessibilityNode,
    PlaywrightVerifier
)


class TestAccessibilityNode:
    """测试 AccessibilityNode 数据类"""
    
    def test_create_node(self):
        """创建节点"""
        node = AccessibilityNode(role="button", name="Submit")
        assert node.role == "button"
        assert node.name == "Submit"
        assert node.children == []
        assert node.properties == {}
    
    def test_create_node_with_children(self):
        """创建带子节点的节点"""
        child = AccessibilityNode(role="textbox", name="Input")
        parent = AccessibilityNode(role="form", name="Login", children=[child])
        
        assert len(parent.children) == 1
        assert parent.children[0].role == "textbox"
    
    def test_from_dict(self):
        """从字典创建节点"""
        data = {
            'role': 'link',
            'name': 'Click me',
            'value': None,
            'children': [
                {'role': 'img', 'name': 'Icon', 'children': []}
            ],
            'properties': {'disabled': False}
        }
        
        node = AccessibilityNode.from_dict(data)
        assert node.role == 'link'
        assert node.name == 'Click me'
        assert len(node.children) == 1
    
    def test_from_dict_empty(self):
        """从空字典创建节点"""
        node = AccessibilityNode.from_dict({})
        assert node.role == 'unknown'
        assert node.name == ''
    
    def test_find_by_role(self):
        """按角色查找"""
        tree = AccessibilityNode(
            role="document",
            name="Page",
            children=[
                AccessibilityNode(role="button", name="OK"),
                AccessibilityNode(
                    role="region",
                    name="Section",
                    children=[
                        AccessibilityNode(role="button", name="Cancel")
                    ]
                )
            ]
        )
        
        buttons = tree.find_by_role("button")
        assert len(buttons) == 2
    
    def test_find_by_role_case_insensitive(self):
        """按角色查找（大小写不敏感）"""
        node = AccessibilityNode(role="Button", name="Submit")
        results = node.find_by_role("button")
        assert len(results) == 1
    
    def test_find_by_role_not_found(self):
        """查找不存在的角色"""
        tree = AccessibilityNode(role="document", name="Page")
        results = tree.find_by_role("button")
        assert len(results) == 0
    
    def test_find_by_text(self):
        """按文本查找"""
        tree = AccessibilityNode(
            role="list",
            name="Items",
            children=[
                AccessibilityNode(role="listitem", name="Item 1"),
                AccessibilityNode(role="listitem", name="Item 2")
            ]
        )
        
        results = tree.find_by_text("Item 1")
        assert len(results) == 1
    
    def test_find_by_text_exact(self):
        """精确文本查找"""
        tree = AccessibilityNode(
            role="list",
            name="Items",
            children=[
                AccessibilityNode(role="listitem", name="Item 1"),
                AccessibilityNode(role="listitem", name="Item 10")
            ]
        )
        
        results = tree.find_by_text("Item 1", exact=True)
        assert len(results) == 1
        
        results_inexact = tree.find_by_text("Item 1", exact=False)
        assert len(results_inexact) == 2
    
    def test_find_by_text_not_found(self):
        """查找不存在的文本"""
        tree = AccessibilityNode(role="document", name="Page")
        results = tree.find_by_text("NotExist")
        assert len(results) == 0
    
    def test_to_text(self):
        """转换为文本"""
        tree = AccessibilityNode(
            role="form",
            name="Login",
            children=[
                AccessibilityNode(role="textbox", name="Username", value="admin")
            ]
        )
        
        text = tree.to_text()
        assert "[form] Login" in text
        assert "[textbox] Username" in text
        assert "= admin" in text
    
    def test_to_text_no_children(self):
        """无子节点的文本"""
        node = AccessibilityNode(role="button", name="Click")
        text = node.to_text()
        assert "[button] Click" in text


class TestPlaywrightVerifier:
    """测试 PlaywrightVerifier 类"""
    
    def test_create_verifier_default(self):
        """创建默认验证器"""
        verifier = PlaywrightVerifier()
        assert verifier is not None
    
    def test_create_verifier_with_path(self):
        """创建带路径的验证器"""
        verifier = PlaywrightVerifier(project_path="/test")
        assert verifier is not None
    
    def test_playwright_available(self):
        """检查 Playwright 可用性"""
        verifier = PlaywrightVerifier()
        available = verifier._playwright_available
        assert isinstance(available, bool)
