#!/usr/bin/env python3
"""配置管理器 - 仅支持配置文件"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import json

from loguru import logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(".cursor/skills/sprint-evolve")
        self.config_file = self.config_dir / "config.json"
        self.example_file = self.config_dir / "config.example.json"
        
        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建示例配置文件（如果不存在）
        self._create_example_config()
    
    def _create_example_config(self):
        """创建示例配置文件"""
        if not self.example_file.exists():
            example_config = {
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "api_key": "your-api-key-here",
                    "base_url": ""
                },
                "story_generator": {
                    "enabled": False,
                    "max_stories": 50,
                    "top_stories_count": 5
                },
                "evolution": {
                    "dry_run": False,
                    "force": False,
                    "silent": False
                }
            }
            
            with open(self.example_file, 'w', encoding='utf-8') as f:
                json.dump(example_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 创建示例配置文件: {self.example_file}")
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config = {}
        
        # 1. 加载示例配置作为默认值
        if self.example_file.exists():
            try:
                with open(self.example_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                logger.warning(f"加载示例配置失败: {e}")
        
        # 2. 如果存在实际配置文件，覆盖配置
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config = self._merge_config(config, user_config)
                logger.info(f"✅ 加载配置文件: {self.config_file}")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        
        return config
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        result = base.copy()
        
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        config = self.load_config()
        return config.get("llm", {})
    
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        llm_config = self.get_llm_config()
        
        required_fields = ["provider", "model", "api_key"]
        missing_fields = [f for f in required_fields if not llm_config.get(f) or llm_config.get(f) == "your-api-key-here"]
        
        if missing_fields:
            logger.error(f"❌ 缺少必需的 LLM 配置: {', '.join(missing_fields)}")
            logger.error(f"请复制 {self.example_file} 到 {self.config_file} 并填写配置")
            return False
        
        return True


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="配置管理器")
    parser.add_argument("--init", action="store_true", help="初始化配置文件")
    parser.add_argument("--show", action="store_true", help="显示当前配置")
    
    args = parser.parse_args()
    
    manager = ConfigManager()
    
    if args.init:
        # 创建配置文件（复制示例）
        if manager.config_file.exists():
            print(f"配置文件已存在: {manager.config_file}")
        else:
            # 复制示例配置
            with open(manager.example_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(manager.config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 创建配置文件: {manager.config_file}")
            print(f"请编辑该文件并填写您的 LLM API 密钥")
    
    elif args.show:
        config = manager.load_config()
        print("当前配置:")
        print(json.dumps(config, ensure_ascii=False, indent=2))
    
    else:
        print("使用 --init 创建配置文件，--show 显示当前配置")


if __name__ == "__main__":
    main()