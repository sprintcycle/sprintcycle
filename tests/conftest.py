"""pytest 配置"""
import sys
from pathlib import Path

# 首先添加 sprintcycle 目录到路径
import os as _os
_sprintcycle_path = Path(__file__).parent.parent / "sprintcycle"
_root_path = Path(__file__).parent.parent

if str(_sprintcycle_path.parent) not in sys.path:
    sys.path.insert(0, str(_sprintcycle_path.parent))

# 确保 sprintcycle 目录在路径中
if str(_sprintcycle_path) not in sys.path:
    sys.path.insert(0, str(_sprintcycle_path))

# 设置环境变量
import os
os.environ.setdefault('SPRINT_LOG_LEVEL', 'ERROR')
