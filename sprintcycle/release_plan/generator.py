"""
从意图生成 Release Plan（执行计划）

将 ParsedIntent 转换为 ``ReleasePlan`` 内存模型。
"""

import os
import re
from pathlib import Path
from typing import Any, Optional

from ..config.runtime_config import RuntimeConfig
from ..intent.parser import ActionType, ParsedIntent
from .models import (
    EvolutionParams,
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)


class IntentReleasePlanGenerator:
    """
    将 ParsedIntent 转换为 ``ReleasePlan``。
    """

    # 自进化关键词（必须同时匹配项目名和动作词）
    EVOLUTION_PROJECT_KEYWORDS = [
        "sprintcycle", "sprint cycle", "self", "自身", "自己"
    ]
    EVOLUTION_ACTION_KEYWORDS = [
        "进化", "evolve", "优化", "optimize", "improve",
        "增强", "enhance", "重构", "refactor", "self-evolution"
    ]

    @staticmethod
    def generate(
        parsed: ParsedIntent,
        *,
        config: Optional[RuntimeConfig] = None,
        anchor_project_path: Optional[str] = None,
    ) -> ReleasePlan:
        """
        从解析后的意图生成 ``ReleasePlan``。

        判断优先级：
        1. 意图关键词识别（如 "优化 sprintcycle 自身代码"）
        2. ParsedIntent.action 动作类型
        3. target/project 路径判断

        Args:
            parsed: ParsedIntent 对象
            config: 运行时配置（非自进化进化时用于 product_code_root / products_subdir）
            anchor_project_path: SprintCycle 的 project_path，用于解析相对 product_code_root

        Returns:
            生成的 ``ReleasePlan`` 对象
        """
        cfg = config or RuntimeConfig()
        anchor = anchor_project_path or os.getcwd()

        # 优先级 1: 根据意图描述判断是否为自进化
        if parsed.description:
            inferred_mode = IntentReleasePlanGenerator._infer_mode_from_intent(parsed.description)
            if inferred_mode == ExecutionMode.EVOLUTION:
                # 意图匹配自进化，强制使用 EVOLVE 动作
                return IntentReleasePlanGenerator._from_evolve(parsed, cfg, anchor)

        # 优先级 2: 根据动作类型生成不同的执行计划
        if parsed.action == ActionType.EVOLVE:
            return IntentReleasePlanGenerator._from_evolve(parsed, cfg, anchor)
        elif parsed.action == ActionType.FIX:
            return IntentReleasePlanGenerator._from_fix(parsed)
        elif parsed.action == ActionType.TEST:
            return IntentReleasePlanGenerator._from_test(parsed)
        elif parsed.action == ActionType.RUN:
            return IntentReleasePlanGenerator._from_run(parsed)
        else:
            return IntentReleasePlanGenerator._from_build(parsed)

    @staticmethod
    def _infer_mode_from_intent(description: str) -> Optional[ExecutionMode]:
        """
        根据意图描述推断执行模式
        
        规则：意图同时包含项目关键词和动作关键词 → EVOLUTION
        
        Args:
            description: 意图描述
            
        Returns:
            ExecutionMode 或 None（无法判断）
        """
        if not description:
            return None

        desc_lower = description.lower()

        # 检查是否包含项目关键词
        has_project = any(kw in desc_lower for kw in IntentReleasePlanGenerator.EVOLUTION_PROJECT_KEYWORDS)

        # 检查是否包含动作关键词
        has_action = any(kw in desc_lower for kw in IntentReleasePlanGenerator.EVOLUTION_ACTION_KEYWORDS)

        # 同时满足才判断为自进化
        if has_project and has_action:
            return ExecutionMode.EVOLUTION

        return None

    @staticmethod
    def _is_self_evolution_intent(description: Optional[str]) -> bool:
        if not description:
            return False
        return (
            IntentReleasePlanGenerator._infer_mode_from_intent(description)
            == ExecutionMode.EVOLUTION
        )

    @staticmethod
    def _sanitize_product_slug(raw: str) -> str:
        s = raw.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", s):
            raise ValueError(
                "产品名须为英文标识（字母开头，仅含字母、数字、下划线与连字符）；"
                f"在意图中写明 product: YourName 或传入 product=...，当前无效: {raw!r}"
            )
        return s

    @staticmethod
    def _resolve_product_code_root(cfg: RuntimeConfig, anchor: str) -> Path:
        raw = (cfg.product_code_root or ".").strip() or "."
        p = Path(raw)
        if p.is_absolute():
            return p.resolve()
        return (Path(anchor).expanduser().resolve() / p).resolve()

    @staticmethod
    def _safe_products_subdir(cfg: RuntimeConfig) -> str:
        sub = (cfg.products_subdir or "products").strip().replace("\\", "/").strip("/")
        if not sub or ".." in Path(sub).parts:
            raise ValueError(
                "无效的 products_subdir 配置（须为非空相对路径片段，不能含 ..）"
            )
        return sub

    @staticmethod
    def _infer_mode_from_target(target: Optional[str], project: Optional[str]) -> ExecutionMode:
        """
        根据 target 和 project 路径推断执行模式（备用方法）
        
        Args:
            target: 目标文件/目录路径
            project: 项目根目录路径
            
        Returns:
            ExecutionMode: 推断出的执行模式
        """
        return ExecutionMode.NORMAL

    @staticmethod
    def _get_sprintcycle_root() -> Path:
        """获取 SprintCycle 项目根目录"""
        return Path(__file__).parent.parent.parent

    @staticmethod
    def _from_evolve(
        parsed: ParsedIntent,
        config: RuntimeConfig,
        anchor_project_path: str,
    ) -> ReleasePlan:
        """从进化意图生成 ``ReleasePlan``。

        自进化（意图同时含 sprintcycle/自身 与进化类动词）：产品路径为 SprintCycle 仓库根。
        其余进化：产品代码根为 ``<product_code_root>/<products_subdir>/<product>/``（目录不存在则创建）。
        """
        if IntentReleasePlanGenerator._is_self_evolution_intent(parsed.description):
            project_path_str = str(
                parsed.project or IntentReleasePlanGenerator._get_sprintcycle_root()
            )
            project_name = "sprintcycle"
            version = "v0.6.0"
        else:
            slug_raw = (parsed.product or "").strip()
            if not slug_raw:
                raise ValueError(
                    "非自进化类的进化意图须指定英文产品名：在意图中写明 product: YourName，"
                    "或使用 API/CLI 的 product 参数。代码将写入 "
                    "<product_code_root>/<products_subdir>/YourName/（可在 sprintcycle.toml 的 "
                    "[product_layout] 配置 code_root 与 subdir）。"
                )
            slug = IntentReleasePlanGenerator._sanitize_product_slug(slug_raw)
            base = IntentReleasePlanGenerator._resolve_product_code_root(
                config, anchor_project_path
            )
            sub = IntentReleasePlanGenerator._safe_products_subdir(config)
            products_dir = base / sub
            products_dir.mkdir(parents=True, exist_ok=True)
            dest = products_dir / slug
            dest.mkdir(parents=True, exist_ok=True)
            project_path_str = str(dest.resolve())
            project_name = slug
            version = "v1.0.0"

        project = ProductAnchor(
            name=project_name,
            path=project_path_str,
            version=version,
        )

        evolution = EvolutionParams(
            targets=[parsed.target] if parsed.target else [],
            goals=[parsed.description],
            constraints=parsed.constraints,
            max_variations=5,
            iterations=3,
        )

        return ReleasePlan(
            project=project,
            mode=ExecutionMode.EVOLUTION,
            evolution=evolution,
            sprints=[],
        )

    @staticmethod
    def _from_build(parsed: ParsedIntent) -> ReleasePlan:
        """从构建意图生成 ``ReleasePlan``"""
        project_path = parsed.project or os.getcwd()
        project_name = os.path.basename(os.path.abspath(project_path))
        # 确保 path 是字符串
        project_path_str = str(project_path)

        project = ProductAnchor(
            name=project_name,
            path=project_path_str,
            version="v1.0.0",
        )

        sprint = SprintDefinition(
            name="Feature Development",
            goals=[parsed.description],
            tasks=[
                SprintBacklogItem(
                    description=parsed.description,
                    agent="coder",
                    target=parsed.target,
                    constraints=parsed.constraints,
                )
            ],
        )

        return ReleasePlan(
            project=project,
            mode=ExecutionMode.NORMAL,
            sprints=[sprint],
        )

    @staticmethod
    def _from_fix(parsed: ParsedIntent) -> ReleasePlan:
        """从修复意图生成 ``ReleasePlan``（自进化能力）"""
        # 解析错误信息
        error_info = IntentReleasePlanGenerator._parse_error_info(parsed.description)

        # 定位问题文件
        target_file = parsed.target or error_info.get("file")

        project_path = parsed.project or os.getcwd()
        project_name = os.path.basename(os.path.abspath(project_path))
        project_path_str = str(project_path)

        project = ProductAnchor(
            name=project_name,
            path=project_path_str,
            version="v1.0.0",
        )

        # 构建修复目标描述
        fix_goal = f"修复错误: {parsed.description}"
        if error_info.get("error_type"):
            fix_goal = f"修复 {error_info['error_type']}: {error_info.get('error_msg', parsed.description)}"

        # 使用进化配置
        evolution = EvolutionParams(
            targets=[target_file] if target_file else [],
            goals=[fix_goal],
            constraints=parsed.constraints,
            max_variations=5,
            iterations=3,
        )

        return ReleasePlan(
            project=project,
            mode=ExecutionMode.EVOLUTION,
            evolution=evolution,
            sprints=[],
        )

    @staticmethod
    def _parse_error_info(error_text: str) -> dict[str, Any]:
        """从错误文本中解析关键信息"""
        info: dict[str, Any] = {}

        if not error_text:
            return info

        # Python 错误模式
        patterns = {
            "file": r'File "([^"]+)"',
            "line": r', line (\d+)',
            "error_type": r'^(\w+Error|\w+Exception):',
            "error_msg": r': (.+)$',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, error_text, re.MULTILINE)
            if match:
                info[key] = match.group(1)

        # 如果没有匹配到标准格式，尝试简单提取
        if not info.get("error_type"):
            # 尝试匹配 "NameError: ..." 格式
            simple_match = re.match(r'(\w+Error|\w+Exception):?\s*(.*)', error_text)
            if simple_match:
                info["error_type"] = simple_match.group(1)
                if simple_match.group(2):
                    info["error_msg"] = simple_match.group(2)

        return info

    @staticmethod
    def _from_test(parsed: ParsedIntent) -> ReleasePlan:
        """从测试意图生成 ``ReleasePlan``"""
        return IntentReleasePlanGenerator._from_build(parsed)

    @staticmethod
    def _from_run(parsed: ParsedIntent) -> ReleasePlan:
        """从「运行执行计划文件」类意图生成"""
        # TODO: 实际解析 YAML 执行计划文件
        return IntentReleasePlanGenerator._from_build(parsed)

    @staticmethod
    def sample_release_plan() -> ReleasePlan:
        """生成示例 ``ReleasePlan``"""
        project = ProductAnchor(
            name="demo",
            path="./demo",
            version="v1.0.0",
        )

        sprint = SprintDefinition(
            name="Sprint 1",
            goals=["实现基础功能"],
            tasks=[
                SprintBacklogItem(description="实现用户认证", agent="coder"),
                SprintBacklogItem(description="编写单元测试", agent="tester"),
            ],
        )

        return ReleasePlan(
            project=project,
            mode=ExecutionMode.NORMAL,
            sprints=[sprint],
        )
