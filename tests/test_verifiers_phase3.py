"""
Verifiers Phase 3 覆盖率扩展测试
目标: verifiers.py: 53% → 60%
"""
import pytest
from unittest.mock import MagicMock, patch
import subprocess


class TestAccessibilityNodeExtended:
    """AccessibilityNode 扩展测试"""
    
    def test_find_by_role_deep_nesting(self):
        """测试深层嵌套节点查找"""
        from sprintcycle.verifiers import AccessibilityNode
        
        root = AccessibilityNode(
            role="window",
            name="Root",
            children=[
                AccessibilityNode(
                    role="dialog",
                    name="Dialog",
                    children=[
                        AccessibilityNode(
                            role="button",
                            name="Deep Button",
                            children=[
                                AccessibilityNode(role="textbox", name="Input")
                            ]
                        )
                    ]
                )
            ]
        )
        
        buttons = root.find_by_role("button")
        assert len(buttons) == 1
        assert buttons[0].name == "Deep Button"
        
        textboxes = root.find_by_role("textbox")
        assert len(textboxes) == 1
        assert textboxes[0].name == "Input"
    
    def test_find_by_text_partial_match(self):
        """测试部分文本匹配"""
        from sprintcycle.verifiers import AccessibilityNode
        
        root = AccessibilityNode(
            role="region",
            name="Main Content",
            children=[
                AccessibilityNode(role="heading", name="Welcome to the App"),
                AccessibilityNode(role="paragraph", name="This is a description"),
            ]
        )
        
        results = root.find_by_text("Welcome")
        assert len(results) == 1
        assert "Welcome" in results[0].name
        
        results = root.find_by_text("app", exact=False)
        assert len(results) == 1
        assert "App" in results[0].name
    
    def test_find_by_text_with_value(self):
        """测试带 value 的文本查找"""
        from sprintcycle.verifiers import AccessibilityNode
        
        root = AccessibilityNode(
            role="textbox",
            name="Search",
            value="Search term"
        )
        
        results = root.find_by_text("Search term")
        assert len(results) == 1
    
    def test_to_text_deep(self):
        """测试深层文本转换"""
        from sprintcycle.verifiers import AccessibilityNode
        
        root = AccessibilityNode(
            role="form",
            name="Login",
            children=[
                AccessibilityNode(
                    role="group",
                    name="Credentials",
                    children=[
                        AccessibilityNode(
                            role="textbox",
                            name="Username",
                            value="user@example.com"
                        ),
                        AccessibilityNode(
                            role="textbox",
                            name="Password",
                            value="***"
                        )
                    ]
                ),
                AccessibilityNode(role="button", name="Submit")
            ]
        )
        
        text = root.to_text()
        assert "[form] Login" in text
        assert "[group] Credentials" in text
        assert "[textbox] Username" in text
    
    def test_from_dict_with_properties(self):
        """测试带 properties 的字典转换"""
        from sprintcycle.verifiers import AccessibilityNode
        
        data = {
            "role": "button",
            "name": "Click Me",
            "value": None,
            "properties": {
                "disabled": True,
                "aria-label": "Submit button"
            },
            "children": []
        }
        
        node = AccessibilityNode.from_dict(data)
        assert node.role == "button"
        assert node.name == "Click Me"
        assert node.properties["disabled"] is True
        assert node.properties["aria-label"] == "Submit button"


class TestPlaywrightVerifierMCPCmds:
    """PlaywrightVerifier MCP 命令测试"""
    
    def test_run_mcp_command_when_unavailable(self):
        """测试 MCP 不可用时的处理"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        result = verifier._run_mcp_command("navigate", {"url": "http://example.com"})
        
        assert result["success"] is False
        assert result["fallback"] is True
        assert "不可用" in result["error"]
    
    def test_run_mcp_command_timeout(self):
        """测试 MCP 命令超时"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)
            
            result = verifier._run_mcp_command("snapshot", {})
            
            assert result["success"] is False
            assert "超时" in result["error"]
    
    def test_run_mcp_command_exception(self):
        """测试 MCP 命令异常"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Unknown error")
            
            result = verifier._run_mcp_command("click", {"selector": "button"})
            
            assert result["success"] is False
            assert result["fallback"] is True


class TestPlaywrightVerifierFallback:
    """PlaywrightVerifier 降级测试"""
    
    def test_fallback_page_load_success(self):
        """测试降级页面加载成功"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout.strip.return_value = "200"
            mock_run.return_value = mock_result
            
            result = verifier._fallback_page_load("http://example.com")
            
            assert result["success"] is True
            assert result["loaded"] is True
            assert result["fallback"] is True
    
    def test_fallback_page_load_failure(self):
        """测试降级页面加载失败"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout.strip.return_value = "404"
            mock_run.return_value = mock_result
            
            result = verifier._fallback_page_load("http://example.com/notfound")
            
            assert result["success"] is True
            assert result["loaded"] is False
            assert result["http_code"] == "404"
    
    def test_fallback_page_load_exception(self):
        """测试降级页面加载异常"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("curl", 10)
            
            result = verifier._fallback_page_load("http://example.com")
            
            assert result["success"] is False
            assert result["loaded"] is False
            assert "error" in result


class TestVerifyPageLoad:
    """verify_page_load 方法测试"""
    
    def test_verify_page_load_with_fallback(self):
        """测试使用降级的页面加载"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout.strip.return_value = "200"
            mock_run.return_value = mock_result
            
            result = verifier.verify_page_load("http://example.com")
            
            assert result["success"] is True
            assert result["loaded"] is True
    
    def test_verify_page_load_with_mcp(self):
        """测试使用 MCP 的页面加载"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = True
        
        with patch.object(verifier, '_run_mcp_command') as mock_cmd:
            mock_cmd.return_value = {
                "success": True,
                "result": {"title": "Example"}
            }
            
            result = verifier.verify_page_load("http://example.com")
            
            assert result["success"] is True
            assert result["loaded"] is True


class TestGetAccessibilityTree:
    """get_accessibility_tree 方法测试"""
    
    def test_get_accessibility_tree_with_fallback(self):
        """测试使用降级的 accessibility tree 获取"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch.object(verifier, '_run_mcp_command') as mock_cmd:
            mock_cmd.return_value = {
                "success": False,
                "fallback": True
            }
            
            result = verifier.get_accessibility_tree()
            
            assert result["success"] is True
            assert result["fallback"] is True
            assert "note" in result


class TestVerifyElementExists:
    """verify_element_exists 方法测试"""
    
    def test_verify_element_exists_with_fallback(self):
        """测试使用降级的元素存在验证"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        verifier._accessibility_tree = None
        
        with patch.object(verifier, 'get_accessibility_tree') as mock_tree:
            mock_tree.return_value = {
                "success": True,
                "tree": None,
                "fallback": True
            }
            
            result = verifier.verify_element_exists("http://example.com", "button")
            
            assert result["success"] is True
            assert result["exists"] is True
            assert result["fallback"] is True
    
    def test_verify_element_exists_not_found(self):
        """测试元素不存在"""
        from sprintcycle.verifiers import AccessibilityNode, PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = True
        verifier._accessibility_tree = AccessibilityNode(role="document", name="Page")
        
        with patch.object(verifier, '_run_mcp_command') as mock_cmd:
            mock_cmd.return_value = {
                "success": True,
                "result": {
                    "tree": {
                        "role": "document",
                        "name": "Page",
                        "children": []
                    }
                }
            }
            
            result = verifier.verify_element_exists("http://example.com", "nonexistent")
            
            assert result["success"] is True
            assert result["exists"] is False


class TestVerifyInteraction:
    """verify_interaction 方法测试"""
    
    def test_verify_interaction_with_fallback(self):
        """测试使用降级的交互验证"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch.object(verifier, 'verify_page_load') as mock_nav:
            mock_nav.return_value = {"success": True}
            
            with patch.object(verifier, '_run_mcp_command') as mock_cmd:
                mock_cmd.return_value = {
                    "success": False,
                    "fallback": True,
                    "error": "MCP not available"
                }
                
                result = verifier.verify_interaction(
                    "http://example.com", "click", "button"
                )
                
                assert result["success"] is False
                assert result["performed"] is False
                assert result["fallback"] is True
    
    def test_verify_interaction_navigation_failure(self):
        """测试导航失败的交互"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        
        with patch.object(verifier, 'verify_page_load') as mock_nav:
            mock_nav.return_value = {
                "success": False,
                "error": "Connection failed"
            }
            
            result = verifier.verify_interaction(
                "http://example.com", "click", "button"
            )
            
            assert result["success"] is False
            assert result["performed"] is False
            assert result["error"] == "Connection failed"


class TestVerifyForm:
    """verify_form 方法测试"""
    
    def test_verify_form_empty_fields(self):
        """测试空字段表单"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        with patch.object(verifier, 'verify_page_load') as mock_nav:
            mock_nav.return_value = {"success": True}
            
            with patch.object(verifier, 'verify_interaction') as mock_interact:
                mock_interact.return_value = {"performed": False}
                
                result = verifier.verify_form(
                    "http://example.com/login",
                    {"fields": [], "submit": None}
                )
                
                assert result["success"] is True
                assert result["fields_filled"] == 0
    
    def test_verify_form_navigation_failure(self):
        """测试表单导航失败"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        
        with patch.object(verifier, 'verify_page_load') as mock_nav:
            mock_nav.return_value = {
                "success": False,
                "error": "Page not found"
            }
            
            result = verifier.verify_form(
                "http://example.com/form",
                {"fields": [{"selector": "input", "value": "test"}]}
            )
            
            assert result["success"] is False
            assert len(result["errors"]) > 0


class TestVerifyNavigationFlow:
    """verify_navigation_flow 方法测试"""
    
    def test_verify_navigation_flow_click_step(self):
        """测试点击步骤"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._current_url = "http://example.com"
        
        with patch.object(verifier, 'verify_page_load'):
            with patch.object(verifier, 'verify_interaction') as mock_interact:
                mock_interact.return_value = {"performed": True}
                
                result = verifier.verify_navigation_flow(
                    "http://example.com",
                    [{"action": "click", "selector": ".menu"}]
                )
                
                assert result["total_steps"] == 1
                assert result["step_results"][0]["success"] is True
    
    def test_verify_navigation_flow_verify_url(self):
        """测试 URL 验证步骤"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._current_url = "http://example.com/dashboard"
        
        with patch.object(verifier, 'verify_page_load'):
            result = verifier.verify_navigation_flow(
                "http://example.com",
                [{"action": "verify_url", "pattern": "/dashboard"}]
            )
            
            assert result["completed_steps"] == 1
            assert result["step_results"][0]["success"] is True
    
    def test_verify_navigation_flow_verify_element(self):
        """测试元素验证步骤"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._current_url = "http://example.com"
        
        with patch.object(verifier, 'verify_page_load'):
            with patch.object(verifier, 'verify_element_exists') as mock_exists:
                mock_exists.return_value = {
                    "exists": True,
                    "element": {"role": "heading", "name": "Dashboard"}
                }
                
                result = verifier.verify_navigation_flow(
                    "http://example.com",
                    [{"action": "verify_element", "selector": "h1", "expected": "Dashboard"}]
                )
                
                assert result["completed_steps"] == 1


class TestToolMapping:
    """工具映射测试"""
    
    def test_tool_map_all_actions(self):
        """测试所有动作映射"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        
        # 测试 click 映射
        with patch.object(verifier, 'verify_page_load', return_value={"success": True}):
            with patch.object(verifier, '_run_mcp_command') as mock_cmd:
                mock_cmd.return_value = {"success": True}
                
                verifier.verify_interaction("http://example.com", "click", "button")
                
                call_args = mock_cmd.call_args
                assert call_args[0][0] == "click"
    
    def test_tool_map_fill_action(self):
        """测试 fill 动作映射"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        
        with patch.object(verifier, 'verify_page_load', return_value={"success": True}):
            with patch.object(verifier, '_run_mcp_command') as mock_cmd:
                mock_cmd.return_value = {"success": True}
                
                verifier.verify_interaction("http://example.com", "fill", "input", "test value")
                
                call_args = mock_cmd.call_args
                assert call_args[0][0] == "fill"
                assert call_args[0][1]["value"] == "test value"
    
    def test_tool_map_hover_action(self):
        """测试 hover 动作映射"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        
        with patch.object(verifier, 'verify_page_load', return_value={"success": True}):
            with patch.object(verifier, '_run_mcp_command') as mock_cmd:
                mock_cmd.return_value = {"success": True}
                
                verifier.verify_interaction("http://example.com", "hover", ".tooltip")
                
                call_args = mock_cmd.call_args
                assert call_args[0][0] == "hover"


class TestHTTPStatusCodes:
    """HTTP 状态码测试"""
    
    def test_2xx_success_codes(self):
        """测试 2xx 成功状态码"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        for code in ["200", "201", "204"]:
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.stdout.strip.return_value = code
                mock_run.return_value = mock_result
                
                result = verifier._fallback_page_load("http://example.com")
                assert result["loaded"] is True
    
    def test_4xx_error_codes(self):
        """测试 4xx 错误状态码"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        for code in ["400", "401", "403", "404"]:
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.stdout.strip.return_value = code
                mock_run.return_value = mock_result
                
                result = verifier._fallback_page_load("http://example.com")
                assert result["loaded"] is False
    
    def test_5xx_server_error_codes(self):
        """测试 5xx 服务器错误状态码"""
        from sprintcycle.verifiers import PlaywrightVerifier
        
        verifier = PlaywrightVerifier()
        verifier._playwright_available = False
        
        for code in ["500", "502", "503"]:
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.stdout.strip.return_value = code
                mock_run.return_value = mock_result
                
                result = verifier._fallback_page_load("http://example.com")
                assert result["loaded"] is False
