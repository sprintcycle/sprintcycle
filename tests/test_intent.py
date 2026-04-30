"""
SprintCycle Intent 模块测试
"""

import pytest
from sprintcycle.intent import (
    IntentParser,
    ParsedIntent,
    ActionType,
    IntentResult,
)


class TestActionType:
    """ActionType 枚举测试"""

    def test_action_type_values(self):
        """测试动作类型枚举值"""
        assert ActionType.EVOLVE.value == "evolution"
        assert ActionType.BUILD.value == "normal"
        assert ActionType.FIX.value == "fix"
        assert ActionType.TEST.value == "test"
        assert ActionType.RUN.value == "run"

    def test_action_type_count(self):
        """测试动作类型数量（UNKNOWN与BUILD同值，故为5个唯一枚举）"""
        assert len(ActionType) == 5

    def test_unknown_alias(self):
        """测试 UNKNOWN 是 BUILD 的别名（相同值）"""
        # UNKNOWN 和 BUILD 有相同的值 "normal"
        assert ActionType.UNKNOWN == ActionType.BUILD
        assert ActionType.UNKNOWN.value == "normal"


class TestParsedIntent:
    """ParsedIntent 数据类测试"""

    def test_construction_with_required_fields(self):
        """测试必需字段构造"""
        intent = ParsedIntent(
            action=ActionType.BUILD,
            description="添加用户登录功能",
        )
        assert intent.action == ActionType.BUILD
        assert intent.description == "添加用户登录功能"
        assert intent.target is None
        assert intent.project is None
        assert intent.constraints == []
        assert intent.mode == "auto"
        assert intent.prd_file is None
        assert intent.intent == ""

    def test_construction_with_all_fields(self):
        """测试所有字段构造"""
        intent = ParsedIntent(
            action=ActionType.FIX,
            description="修复登录bug",
            target="src/auth.py",
            project="myapp",
            constraints=["保持接口不变", "不修改数据库"],
            mode="fix",
            prd_file="login.yaml",
            intent="修复 src/auth.py 中的登录问题",
        )
        assert intent.action == ActionType.FIX
        assert intent.description == "修复登录bug"
        assert intent.target == "src/auth.py"
        assert intent.project == "myapp"
        assert len(intent.constraints) == 2
        assert "保持接口不变" in intent.constraints
        assert intent.mode == "fix"
        assert intent.prd_file == "login.yaml"
        assert "修复" in intent.intent

    def test_constraints_default_empty_list(self):
        """测试约束条件默认为空列表"""
        intent = ParsedIntent(action=ActionType.TEST, description="测试")
        assert intent.constraints == []
        assert isinstance(intent.constraints, list)


class TestIntentParser:
    """IntentParser 解析器测试"""

    def test_init(self):
        """测试解析器初始化"""
        parser = IntentParser()
        assert parser is not None
        assert hasattr(parser, "EVOLVE_KEYWORDS")
        assert hasattr(parser, "BUILD_KEYWORDS")
        assert hasattr(parser, "FIX_KEYWORDS")

    def test_parse_basic_intent(self):
        """测试基本意图解析"""
        parser = IntentParser()
        result = parser.parse("添加用户模块")
        
        assert isinstance(result, ParsedIntent)
        assert result.description == "添加用户模块"
        assert result.action == ActionType.BUILD

    def test_parse_evolve_intent(self):
        """测试优化意图识别"""
        parser = IntentParser()
        
        # 测试中文关键词
        result1 = parser.parse("优化系统性能")
        assert result1.action == ActionType.EVOLVE
        
        # 测试英文关键词
        result2 = parser.parse("optimize database queries")
        assert result2.action == ActionType.EVOLVE
        
        # 测试重构
        result3 = parser.parse("重构代码结构")
        assert result3.action == ActionType.EVOLVE

    def test_parse_build_intent(self):
        """测试构建意图识别"""
        parser = IntentParser()
        
        # 测试添加
        result1 = parser.parse("添加新功能")
        assert result1.action == ActionType.BUILD
        
        # 测试创建
        result2 = parser.parse("create new component")
        assert result2.action == ActionType.BUILD
        
        # 测试实现
        result3 = parser.parse("实现用户接口")
        assert result3.action == ActionType.BUILD

    def test_parse_fix_intent(self):
        """测试修复意图识别"""
        parser = IntentParser()
        
        # 测试修复
        result1 = parser.parse("修复bug")
        assert result1.action == ActionType.FIX
        
        # 测试解决
        result2 = parser.parse("解决登录错误")
        assert result2.action == ActionType.FIX
        
        # 测试排查
        result3 = parser.parse("排查内存泄漏问题")
        assert result3.action == ActionType.FIX

    def test_parse_test_intent(self):
        """测试测试意图识别"""
        parser = IntentParser()
        
        result1 = parser.parse("运行测试")
        assert result1.action == ActionType.TEST
        
        result2 = parser.parse("验证功能")
        assert result2.action == ActionType.TEST
        
        result3 = parser.parse("test the code")
        assert result3.action == ActionType.TEST

    def test_parse_prd_file_path(self):
        """测试PRD文件路径识别"""
        parser = IntentParser()
        
        result = parser.parse("执行 demo.yaml")
        assert result.action == ActionType.RUN
        assert result.prd_file == "demo.yaml"

    def test_parse_with_project(self):
        """测试带项目参数的解析"""
        parser = IntentParser()
        result = parser.parse("添加登录功能", project="myapp")
        
        assert result.project == "myapp"
        assert result.description == "添加登录功能"

    def test_parse_with_target(self):
        """测试带目标参数的解析"""
        parser = IntentParser()
        result = parser.parse("修复bug", target="src/main.py")
        
        assert result.target == "src/main.py"

    def test_parse_with_mode(self):
        """测试强制模式"""
        parser = IntentParser()
        
        # 强制指定模式
        result = parser.parse("写代码", mode="fix")
        assert result.action == ActionType.FIX
        assert result.mode == "fix"

    def test_parse_extract_target_file(self):
        """测试目标文件提取"""
        parser = IntentParser()
        
        # 提取 Python 文件
        result1 = parser.parse("修改 app.py")
        assert result1.target == "app.py"
        
        # 提取带路径的文件
        result2 = parser.parse("更新 src/utils/helpers.ts")
        assert "helpers.ts" in result2.target

    def test_parse_extract_constraints(self):
        """测试约束条件提取"""
        parser = IntentParser()
        
        result = parser.parse("添加功能（保持接口不变）（不修改样式）")
        assert len(result.constraints) >= 2

    def test_infer_action_priority(self):
        """测试动作推断优先级 - FIX优先于其他"""
        parser = IntentParser()
        
        # 包含 FIX 关键词时应该返回 FIX
        result = parser.parse("修复测试失败的问题")
        assert result.action == ActionType.FIX

    def test_unknown_intent(self):
        """测试未知意图（无匹配关键词时返回BUILD，即UNKNOWN的别名）"""
        parser = IntentParser()
        
        result = parser.parse("随便写点什么")
        assert result.action == ActionType.BUILD  # UNKNOWN == BUILD

    def test_parsed_intent_mode_value(self):
        """测试 mode 字段为 action 的值"""
        parser = IntentParser()
        
        result = parser.parse("优化性能")
        assert result.mode == result.action.value

    def test_case_insensitive_keywords(self):
        """测试关键词大小写不敏感"""
        parser = IntentParser()
        
        result1 = parser.parse("FIX this bug")
        assert result1.action == ActionType.FIX
        
        result2 = parser.parse("FIX the error")
        assert result2.action == ActionType.FIX

    def test_parse_preserves_original_intent(self):
        """测试保留原始意图文本"""
        parser = IntentParser()
        original = "修复 src/main.py 的编译错误"
        
        result = parser.parse(original)
        assert result.intent == original
