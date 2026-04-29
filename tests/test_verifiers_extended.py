"""扩展测试 Playwright 验证器功能"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sprintcycle.verifiers import (
    AccessibilityNode, PlaywrightVerifier
)


class TestAccessibilityNodeExtended:
    """扩展测试 AccessibilityNode"""
    
    def test_find_by_role_deep_nesting(self):
        """测试深层嵌套查找"""
        tree = AccessibilityNode(
            role="document",
            name="Root",
            children=[
                AccessibilityNode(
                    role="main",
                    name="Content",
                    children=[
                        AccessibilityNode(
                            role="section",
                            name="Section1",
                            children=[
                                AccessibilityNode(role="button", name="DeepButton")
                            ]
                        )
                    ]
                )
            ]
        )
        
        buttons = tree.find_by_role("button")
        assert len(buttons) == 1
        assert buttons[0].name == "DeepButton"
    
    def test_find_by_text_partial_match(self):
        """测试部分文本匹配"""
        tree = AccessibilityNode(
            role="list",
            name="Items",
            children=[
                AccessibilityNode(role="listitem", name="Item One"),
                AccessibilityNode(role="listitem", name="Item Two"),
                AccessibilityNode(role="listitem", name="OnePlus")
            ]
        )
        
        results = tree.find_by_text("One")
        assert len(results) >= 2
    
    def test_find_by_text_with_value(self):
        """测试带 value 的文本匹配"""
        node = AccessibilityNode(role="heading", name="Title Only")
        results = node.find_by_text("Title")
        assert len(results) == 1
    
    def test_to_text_format(self):
        """测试文本格式"""
        tree = AccessibilityNode(
            role="form",
            name="Login Form",
            children=[
                AccessibilityNode(role="textbox", name="Username", value="admin")
            ]
        )
        
        text = tree.to_text()
        assert "[form] Login Form" in text
        assert "[textbox] Username" in text
        assert "= admin" in text
    
    def test_to_text_deep(self):
        """测试深层文本"""
        tree = AccessibilityNode(
            role="document",
            name="Page",
            children=[
                AccessibilityNode(
                    role="main",
                    name="Main",
                    children=[
                        AccessibilityNode(role="button", name="Click Me")
                    ]
                )
            ]
        )
        
        text = tree.to_text()
        assert "Click Me" in text
    
    def test_from_dict_with_properties(self):
        """测试从带 properties 的字典创建"""
        data = {
            'role': 'button',
            'name': 'Submit',
            'properties': {'disabled': True, 'focused': False}
        }
        node = AccessibilityNode.from_dict(data)
        assert node.role == 'button'
        assert node.properties['disabled'] == True


class TestPlaywrightVerifierExtended:
    """扩展测试 PlaywrightVerifier"""
    
    def test_init_default_timeout(self):
        """测试默认超时设置"""
        verifier = PlaywrightVerifier()
        assert verifier.timeout == 30000
    
    def test_init_custom_mcp_command(self):
        """测试自定义 MCP 命令"""
        verifier = PlaywrightVerifier(mcp_command="custom mcp command")
        assert verifier.mcp_command == "custom mcp command"
    
    def test_init_with_project_path(self):
        """测试带项目路径初始化"""
        verifier = PlaywrightVerifier(project_path="/test/project")
        assert str(verifier.project_path) == "/test/project"
    
    def test_run_mcp_command_when_unavailable(self):
        """测试 MCP 不可用时执行"""
        verifier = PlaywrightVerifier()
        # 强制设置不可用
        verifier._playwright_available = False
        
        result = verifier._run_mcp_command("navigate", {"url": "http://example.com"})
        assert result["success"] == False
        assert result["fallback"] == True
    
    def test_fallback_page_load_success(self):
        """测试降级页面加载-成功"""
        verifier = PlaywrightVerifier()
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = "200"
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = verifier._fallback_page_load("http://example.com")
            assert result["success"] == True
            assert result["loaded"] == True
            assert result["fallback"] == True
    
    def test_fallback_page_load_failure(self):
        """测试降级页面加载-失败"""
        verifier = PlaywrightVerifier()
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = "404"
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = verifier._fallback_page_load("http://example.com/notfound")
            assert result["success"] == True
            assert result["loaded"] == False
    
    def test_fallback_page_load_exception(self):
        """测试降级页面加载-异常"""
        verifier = PlaywrightVerifier()
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("curl failed")
            
            result = verifier._fallback_page_load("http://example.com")
            assert result["success"] == False
            assert result["error"] is not None
    
    def test_verify_page_load_with_fallback(self):
        """测试页面加载使用降级方案"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch.object(verifier, '_fallback_page_load') as mock_fallback:
            mock_fallback.return_value = {
                "success": True,
                "loaded": True,
                "url": "http://example.com",
                "fallback": True
            }
            
            result = verifier.verify_page_load("http://example.com")
            assert result["success"] == True
            assert result["fallback"] == True
    
    def test_get_accessibility_tree_with_fallback(self):
        """测试获取 accessibility tree-降级"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        # 设置导航返回成功以触发降级分支
        with patch.object(verifier, 'verify_page_load') as mock_nav:
            mock_nav.return_value = {"success": True, "loaded": True}
            
            result = verifier.get_accessibility_tree("http://example.com")
            assert result["success"] == True
    
    def test_verify_element_exists_with_fallback(self):
        """测试元素验证-降级模式"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        result = verifier.verify_element_exists("http://example.com", "button")
        assert result["success"] == True
        assert result["fallback"] == True
    
    def test_verify_element_exists_not_found(self):
        """测试元素不存在"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch.object(verifier, 'get_accessibility_tree') as mock_tree:
            mock_tree.return_value = {
                "success": True,
                "tree": AccessibilityNode(role="document", name="Page"),
                "text": ""
            }
            
            result = verifier.verify_element_exists("http://example.com", "nonexistent")
            assert result["success"] == True
            assert result["exists"] == False
    
    def test_verify_interaction_with_fallback(self):
        """测试交互验证-降级"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        result = verifier.verify_interaction(
            "http://example.com", "click", "#button", None
        )
        assert result["fallback"] == True
    
    def test_verify_interaction_navigation_failure(self):
        """测试交互验证-导航失败"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch.object(verifier, 'verify_page_load') as mock_nav:
            mock_nav.return_value = {"success": False, "error": "Network error"}
            
            result = verifier.verify_interaction(
                "http://example.com", "click", "#button"
            )
            assert result["success"] == False
            assert "Network error" in result["error"]
    
    def test_verify_form_empty_fields(self):
        """测试表单验证-空字段"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        result = verifier.verify_form("http://example.com", {"fields": []})
        assert result["fields_filled"] == 0
        assert result["submitted"] == False
    
    def test_verify_form_navigation_failure(self):
        """测试表单验证-导航失败"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch.object(verifier, 'verify_page_load') as mock_nav:
            mock_nav.return_value = {"success": False, "error": "Failed"}
            
            result = verifier.verify_form(
                "http://example.com",
                {"fields": [{"selector": "#x", "value": "test"}]}
            )
            assert len(result["errors"]) > 0


class TestAccessibilityNodeSpecialCases:
    """测试 AccessibilityNode 特殊边界情况"""
    
    def test_find_by_role_empty_children(self):
        """测试空子节点"""
        node = AccessibilityNode(role="div", name="Empty", children=[])
        results = node.find_by_role("span")
        assert len(results) == 0
    
    def test_find_by_text_empty_name(self):
        """测试空名称"""
        node = AccessibilityNode(role="element", name="")
        results = node.find_by_text("test")
        assert len(results) == 0
    
    def test_find_by_text_with_value(self):
        """测试带 value 的节点"""
        node = AccessibilityNode(role="input", name="Input", value="test_value")
        results = node.find_by_text("test_value")
        assert len(results) == 1
    
    def test_from_dict_empty_children(self):
        """测试空子节点列表"""
        data = {'role': 'test', 'name': 'Test', 'children': []}
        node = AccessibilityNode.from_dict(data)
        assert node.children == []
    
    def test_from_dict_missing_fields(self):
        """测试缺少字段"""
        data = {'role': 'button'}
        node = AccessibilityNode.from_dict(data)
        assert node.name == ''
        assert node.value is None


class TestPlaywrightVerifierEdgeCases:
    """测试 PlaywrightVerifier 边界情况"""
    
    def test_verify_page_load_no_url(self):
        """测试无 URL"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        result = verifier.verify_page_load("")
        assert result["url"] == ""
    
    def test_verify_interaction_all_actions(self):
        """测试所有交互类型"""
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        for action in ["click", "fill", "hover", "type"]:
            result = verifier.verify_interaction(
                "http://example.com", action, "#selector", "value" if action == "fill" else None
            )
            assert result["action"] == action
    
    def test_verify_page_load_3xx_redirect(self):
        """测试 3xx 重定向"""
        verifier = PlaywrightVerifier()
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = "301"
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = verifier._fallback_page_load("http://example.com/redirect")
            # 301 不以 2 开头
            assert result["loaded"] == False
    
    def test_verify_page_load_5xx_server_error(self):
        """测试 5xx 服务器错误"""
        verifier = PlaywrightVerifier()
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = "500"
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            result = verifier._fallback_page_load("http://example.com/error")
            assert result["loaded"] == False
