#!/usr/bin/env python3
"""用户故事生成器集成器 - 仅使用 MetaGPT"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
import subprocess
import sys

from loguru import logger


class GeneratorType(Enum):
    """生成器类型"""
    METAGPT = "metagpt"


@dataclass
class GeneratedUserStory:
    """生成的用户故事"""
    id: str
    title: str
    description: str = ""
    role: str = ""
    feature: str = ""
    purpose: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    priority: str = "Medium"
    impact: str = "Medium"
    complexity: str = "Medium"
    score: float = 50.0
    source: str = "metagpt"
    related_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class MetaGPTGenerator:
    """MetaGPT 用户故事生成器"""
    
    def __init__(self):
        self._check_dependencies()
        self._config = None
    
    def _check_dependencies(self):
        """检查依赖"""
        try:
            import metagpt
            logger.info("✅ MetaGPT 已安装")
            self._available = True
        except ImportError:
            logger.warning("⚠️ MetaGPT 未安装，请运行: pip install metagpt")
            self._available = False
    
    def _load_config(self):
        """加载配置"""
        if self._config is None:
            try:
                from .config import ConfigManager
                manager = ConfigManager()
                self._config = manager.get_llm_config()
            except ImportError as e:
                logger.error(f"加载配置管理器失败: {e}")
                self._config = {}
    
    def _get_llm_config(self):
        """获取 LLM 配置"""
        self._load_config()
        
        llm_config = {
            "provider": self._config.get("provider", "openai"),
            "model": self._config.get("model", "gpt-4o"),
            "api_key": self._config.get("api_key", ""),
        }
        
        base_url = self._config.get("base_url")
        if base_url:
            llm_config["base_url"] = base_url
        
        logger.info(f"📦 使用 LLM 配置: provider={llm_config['provider']}, model={llm_config['model']}")
        return llm_config
    
    def _validate_config(self) -> bool:
        """验证配置"""
        self._load_config()
        
        if not self._config:
            logger.error("❌ 无法加载配置")
            return False
        
        required = ["provider", "model", "api_key"]
        missing = []
        
        for field in required:
            value = self._config.get(field)
            if not value or value == "your-api-key-here":
                missing.append(field)
        
        if missing:
            logger.error(f"❌ 缺少必需的 LLM 配置: {', '.join(missing)}")
            logger.error("请创建配置文件: python config.py --init")
            return False
        
        return True
    
    def generate(self, code_path: Path, doc_path: Optional[Path] = None) -> List[GeneratedUserStory]:
        """使用 MetaGPT 生成用户故事"""
        if not self._available:
            return []
        
        # 验证配置
        if not self._validate_config():
            return []
        
        try:
            from metagpt.software_company import generate_repo
            from metagpt.actions import UserStory
            
            logger.info("🚀 使用 MetaGPT 生成用户故事...")
            
            config = {
                "requirement": "基于现有Python代码库生成详细的Agile用户故事，包含："
                               "1. 用户角色 2. 功能描述 3. 业务目的 4. 验收标准 "
                               "5. 优先级评估 6. 影响范围 7. 复杂度评估",
                "code_path": str(code_path),
                "llm": self._get_llm_config(),
            }
            
            if doc_path and doc_path.exists():
                config["doc_path"] = str(doc_path)
            
            repo = generate_repo(**config)
            user_stories = repo.get_actions(UserStory)
            
            result = []
            for i, us in enumerate(user_stories, 1):
                story = self._parse_metagpt_story(us, i)
                if story:
                    result.append(story)
            
            logger.info(f"✅ MetaGPT 生成完成，共 {len(result)} 个用户故事")
            return result
            
        except Exception as e:
            logger.error(f"MetaGPT 生成失败: {e}")
            return []
    
    def _parse_metagpt_story(self, us, index: int) -> Optional[GeneratedUserStory]:
        """解析 MetaGPT 返回的用户故事"""
        try:
            content = str(us.content)
            
            role = self._extract_field(content, "作为", "，")
            feature = self._extract_field(content, "我想要", "，")
            purpose = self._extract_field(content, "以便", "。")
            
            criteria = []
            if "验收标准" in content:
                criteria_section = content.split("验收标准")[1].strip()
                for line in criteria_section.split("\n")[:5]:
                    line = line.strip("-* 1234567890. ")
                    if line:
                        criteria.append(line)
            
            return GeneratedUserStory(
                id=f"story_mgpt_{index:04d}",
                title=f"作为{role}，我想要{feature}",
                description=content,
                role=role,
                feature=feature,
                purpose=purpose,
                acceptance_criteria=criteria,
                priority="High",
                impact="Medium",
                complexity="Medium",
                score=75.0,
                source="metagpt",
                related_files=[],
                tags=["metagpt", "generated"]
            )
        except Exception as e:
            logger.debug(f"解析 MetaGPT 故事失败: {e}")
            return None
    
    def _extract_field(self, content: str, start: str, end: str) -> str:
        """从内容中提取字段"""
        if start in content:
            part = content.split(start)[1]
            if end in part:
                return part.split(end)[0].strip()
            return part.strip()
        return ""


class StoryGeneratorIntegrator:
    """用户故事生成器集成器 - 仅使用 MetaGPT"""
    
    def __init__(self):
        self._generator = MetaGPTGenerator()
    
    def generate(self, code_path: Path, doc_path: Optional[Path] = None) -> List[GeneratedUserStory]:
        """生成用户故事"""
        return self._generator.generate(code_path, doc_path)
    
    def get_top_stories(self, code_path: Path, count: int = 5) -> List[GeneratedUserStory]:
        """获取 Top N 用户故事"""
        stories = self.generate(code_path)
        return sorted(stories, key=lambda x: x.score, reverse=True)[:count]
    
    def is_available(self) -> bool:
        """检查 MetaGPT 是否可用"""
        return self._generator._available
    
    def is_configured(self) -> bool:
        """检查配置是否完整"""
        return self._generator._validate_config()


def install_dependencies():
    """安装 MetaGPT 依赖"""
    logger.info("📦 安装 MetaGPT...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "metagpt"])
        logger.info("✅ MetaGPT 安装成功")
    except subprocess.CalledProcessError:
        logger.error("❌ MetaGPT 安装失败")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="用户故事生成器（MetaGPT）")
    parser.add_argument("--code-path", default="./sprintcycle", help="代码目录")
    parser.add_argument("--doc-path", default="./docs", help="文档目录")
    parser.add_argument("--count", type=int, default=5, help="返回故事数量")
    parser.add_argument("--install", action="store_true", help="安装 MetaGPT")
    
    args = parser.parse_args()
    
    if args.install:
        install_dependencies()
        return
    
    integrator = StoryGeneratorIntegrator()
    
    if not integrator.is_available():
        print("⚠️ MetaGPT 未安装，请先运行: python story_generator_integrator.py --install")
        return
    
    if not integrator.is_configured():
        print("⚠️ LLM 配置不完整，请先运行: python config.py --init")
        return
    
    stories = integrator.get_top_stories(
        code_path=Path(args.code_path),
        count=args.count
    )
    
    print("===== MetaGPT 生成的用户故事 =====")
    for i, story in enumerate(stories, 1):
        print(f"\n{i}. [{story.score:.1f}] {story.title}")
        print(f"   - 来源: {story.source}")
        print(f"   - 角色: {story.role}")
        print(f"   - 功能: {story.feature}")
        print(f"   - 目的: {story.purpose}")
        print(f"   - 优先级: {story.priority}")
        print(f"   - 影响: {story.impact}")
        print(f"   - 复杂度: {story.complexity}")
        if story.acceptance_criteria:
            print(f"   - 验收标准:")
            for j, criteria in enumerate(story.acceptance_criteria, 1):
                print(f"     {j}. {criteria}")


if __name__ == "__main__":
    main()