# GEPA Bug Fix 模式

本文档说明 `--mode fix` 如何使用 Hermes GEPA 自进化引擎。

## 核心改动

### 1. PRDGenerator._from_fix()

修改了 `sprintcycle/sprintcycle/prd/generator.py` 中的 `_from_fix()` 方法：

```python
@staticmethod
def _from_fix(parsed: ParsedIntent) -> PRD:
    """从修复意图生成 PRD - 使用 GEPA 自进化能力"""
    # 解析错误信息
    error_info = PRDGenerator._parse_error_info(parsed.description)
    
    # 定位问题文件
    target_file = parsed.target or error_info.get("file")
    
    project_path = parsed.project or os.getcwd()
    project_name = os.path.basename(os.path.abspath(project_path))
    
    project = PRDProject(
        name=project_name,
        path=str(project_path),
        version="v1.0.0",
    )
    
    # 构建修复目标描述
    fix_goal = f"修复错误: {parsed.description}"
    if error_info.get("error_type"):
        fix_goal = f"修复 {error_info['error_type']}: {error_info.get('error_msg', parsed.description)}"
    
    # 使用进化配置
    evolution = EvolutionConfig(
        targets=[target_file] if target_file else [],
        goals=[fix_goal],
        constraints=parsed.constraints,
        max_variations=5,
        iterations=3,
    )
    
    sprint = PRDSprint(
        name="Bug Fix Sprint",
        goals=[fix_goal],
        tasks=[
            PRDTask(
                task=fix_goal,
                agent="evolver",  # 关键：使用 evolver 而不是 coder
                target=target_file,
                constraints=parsed.constraints,
            )
        ],
    )
    
    return PRD(
        project=project,
        mode=ExecutionMode.EVOLUTION,  # 关键：使用 evolution 模式
        evolution=evolution,
        sprints=[sprint],
    )
```

### 2. 错误信息解析

添加了 `_parse_error_info()` 方法来解析 Python 错误：

```python
@staticmethod
def _parse_error_info(error_text: str) -> dict:
    """从错误文本中解析关键信息"""
    info = {}
    
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
        simple_match = re.match(r'(\w+Error|\w+Exception):?\s*(.*)', error_text)
        if simple_match:
            info["error_type"] = simple_match.group(1)
            if simple_match.group(2):
                info["error_msg"] = simple_match.group(2)
    
    return info
```

## 执行流程

1. 用户执行 `sprintcycle --mode fix "NameError: ..." -t broken.py`
2. `IntentParser` 解析为 `ActionType.FIX`
3. `PRDGenerator.generate()` 调用 `_from_fix()`
4. `_from_fix()` 返回 `mode=EVOLUTION` 的 PRD
5. `TaskDispatcher.execute_prd()` 检测到 `prd.is_evolution_mode=True`
6. 调用 `_execute_evolution_mode()` 执行进化任务
7. `EvolutionEngine` 处理 bug 修复

## 使用示例

```bash
# Bug 修复 - 使用 GEPA 自进化能力
sprintcycle --mode fix "NameError: name 'x' is not defined" -t broken.py

# 从错误日志修复
sprintcycle --mode fix "$(cat error.log)" -p ./myproject

# 修复特定错误类型
sprintcycle --mode fix "IndexError: list index out of range" -t data.py

# 完整错误堆栈（自动提取文件路径）
sprintcycle --mode fix 'File "/path/to/app.py", line 42, in main
    result = x + y
NameError: name "x" is not defined'
```

## 验证

修改后运行：

```bash
python3 -c "
from sprintcycle.prd.generator import PRDGenerator
from sprintcycle.prd.models import ExecutionMode
from sprintcycle.intent.parser import ParsedIntent, ActionType

parsed = ParsedIntent(
    action=ActionType.FIX,
    description='NameError: name \"x\" is not defined',
    target='broken.py',
    constraints=[]
)

prd = PRDGenerator.generate(parsed)
print(f'Mode: {prd.mode}')
print(f'Is Evolution: {prd.is_evolution_mode}')
print(f'Agent: {prd.sprints[0].tasks[0].agent}')
print(f'Task: {prd.sprints[0].tasks[0].task}')
"
```

应该看到：
- `Mode: ExecutionMode.EVOLUTION`
- `Is Evolution: True`
- `Agent: evolver`
- `Task: 修复 NameError: name "x" is not defined`
