# SprintCycle 自动化进化系统

## 📖 概述

SprintCycle 自动化进化系统提供了一个完整的闭环，无需人工干预即可完成：
- 自动检测架构不变性和功能正确性
- **基于 MetaGPT 自动生成用户故事**
- **智能分析用户故事，识别问题点并选出 Top 3**
- **持久化用户故事到本地存储**（支持补充、删除过期、修正）
- 智能评估并选出 Top 3 优化方向
- 自动执行优化工作流
- 运行自动化验证工具
- 根据验证结果自动修正
- 自动更新相关文档

---

## 🚀 快速开始

### 触发方式

#### 方式一：命令触发（推荐）
在 Trae 中输入命令：
```
/sprint evolve
```

#### 方式二：触发词触发
输入以下关键词即可激活进化模式：
- 「进化」
- 「自动优化」
- 「自我改进」
- 「架构进化」
- 「SprintCycle 进化」

#### 方式三：脚本运行
```bash
# 进入项目根目录
cd /path/to/sprintcycle

# 运行进化脚本
./scripts/run_evolution.sh

# 或直接运行 Python
python .cursor/skills/sprint evolve/evolve.py
```

### 参数选项

| 参数 | 说明 | 示例 |
|------|------|------|
| `--dry-run` | 模拟模式，不执行实际变更 | `/sprint evolve --dry-run` |
| `--force` | 强制执行，忽略警告 | `/sprint evolve --force` |
| `--silent` | 静默模式，减少输出 | `/sprint evolve --silent` |
| `--report-only` | 仅生成报告，不执行优化 | `/sprint evolve --report-only` |
| `--skip-user-stories` | 跳过用户故事分析（无需 MetaGPT） | `/sprint evolve --skip-user-stories` |

### 依赖安装

用户故事生成功能需要 MetaGPT：
```bash
# 安装 MetaGPT
pip install metagpt

# 使用 uv 安装（推荐）
uv pip install metagpt
```

### 使用 uv 管理依赖

项目使用 uv 作为包管理器：
```bash
# 激活虚拟环境
cd /path/to/sprintcycle
source scripts/start_develop/activate.sh

# 或直接激活
source .venv/bin/activate

# 同步依赖
uv sync

# 安装额外依赖
uv pip install <package-name>

# 退出虚拟环境
deactivate
```

---

## 🔄 执行流程

```
用户触发 /sprint evolve
        ↓
┌─────────────────────────────────────┐
│  Phase 1: 自动检测与分析            │
│  - 运行架构验证器                    │
│  - 运行单元测试                      │
│  - 识别优化机会                      │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  Phase 2: 用户故事分析              │
│  - 使用 MetaGPT 全量生成用户故事     │
│  - 识别问题点（错误/缺失/优化等）    │
│  - 保存到 userstories 目录          │
│  - 选择 Top 3 问题点                │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  Phase 3: 智能评估与排序            │
│  - 分析优化方向                      │
│  - 评估优先级（分数算法）            │
│  - 选出 Top 3 优化方向              │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  Phase 4: 自动执行优化              │
│  - 执行优化工作流                    │
│  - 前后端同步变更                    │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  Phase 5: 验证与修正                │
│  - 运行自动化验证工具                │
│  - 根据结果自动修正                  │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  Phase 6: 自动文档更新              │
│  - 更新 README.md                   │
│  - 更新 README_EN.md                │
│  - 更新 ARCHITECTURE_INVARIANTS.md  │
│  - 更新架构编排规则                  │
└─────────────────────────────────────┘
        ↓
   进化完成!
```

---

## 📊 优先级评分算法

### 评分模型

系统使用以下算法评估优化优先级：

| 因素 | 权重 | 说明 |
|------|------|------|
| 架构影响 | 30% | 对架构合规性的改善程度 |
| 业务价值 | 25% | 直接业务收益 |
| 复杂度 | 20% | 实现难度（越低越好） |
| 风险 | 15% | 破坏变更的风险 |
| 测试覆盖 | 10% | 现有测试覆盖率 |

### 评分公式

```
分数 = 架构影响(30) + 业务价值(25) + 复杂度(20) + 风险(15) + 测试覆盖(10)
```

### 分数阈值

| 分数范围 | 处理方式 |
|----------|---------|
| ≥ 70 | 自动执行 |
| 60-69 | 条件执行（需 --force） |
| < 60 | 跳过 |

---

## 🎯 优化类型

系统支持以下优化类型：

| 类型 | 说明 | 典型场景 |
|------|------|---------|
| **字段整合** | 将语义相关字段整合为统一上下文 | 多个字段表达同一概念 |
| **DDD 治理** | 修复架构层依赖违规 | 领域层依赖应用层 |
| **兼容清理** | 移除兼容代码和过渡层 | 遗留的兼容辅助方法 |
| **前后端对齐** | 同步 API 契约和类型定义 | API 与类型不一致 |
| **性能优化** | 提升系统性能 | 慢查询、内存泄漏 |
| **安全加固** | 增强安全防护 | 权限漏洞、注入风险 |

---

## 📋 输出报告

执行完成后生成完整报告：

```markdown
## SprintCycle 自动化进化报告

### 分析结果
- 架构违规: 0
- 警告: 12
- 优化机会: 5

### 用户故事分析
- 生成用户故事数: 50
- 识别问题点数: 15
- Top 3 问题点:
  1. [90.0] 错误: 登录接口验证缺失
  2. [85.0] 缺失: 订单状态变更通知
  3. [75.0] 优化: 首页加载性能

### Top 3 优化方向

1. [85.0] ddd_governance: 修复架构层依赖违规
   - 影响: High
   - 复杂度: Medium
   - 风险: Medium
   - 受影响文件: 3 个

2. [75.0] field_consolidation: 识别语义相关字段组
   - 影响: Medium
   - 复杂度: Medium
   - 风险: Low
   - 受影响文件: 5 个

3. [70.0] frontend_backend_alignment: 同步前后端契约
   - 影响: Medium
   - 复杂度: Medium
   - 风险: Medium
   - 受影响文件: 8 个

### 执行结果
- 执行优化数: 3
- 成功: 3
- 失败: 0

### ✅ ddd_governance_001
- 状态: 成功
- 变更:
  - 修复架构层依赖违规
  - 更新领域层代码

### 验证结果
- 架构验证: ✅ 通过
- 单元测试: ✅ 通过
- 集成测试: ✅ 通过
- 前端验证: ✅ 通过

### 文档更新
- 更新文件数: 4
- 更新文件:
  - README.md
  - README_EN.md
  - ARCHITECTURE_INVARIANTS.md
  - sprintcycle-architecture-orchestration.mdc

### 总结
🎉 进化成功！
```

---

## 📖 用户故事管理

### 用户故事存储

用户故事自动保存到项目根目录的 `userstories/` 目录：

```
userstories/
├── stories.json       # 所有用户故事数据
├── metadata.json      # 元数据（数量、更新时间）
└── stories_export_*.json  # 导出文件（可选）
```

### 用户故事状态

| 状态 | 说明 |
|------|------|
| active | 活跃状态，正常使用 |
| completed | 已完成 |
| obsolete | 已过期，等待清理（30天后自动删除） |

### 命令行管理

```bash
# 列出所有用户故事
python .cursor/skills/sprint evolve/story_store.py --list

# 查看 Top 5 用户故事
python .cursor/skills/sprint evolve/story_store.py --top 5

# 导出用户故事
python .cursor/skills/sprint evolve/story_store.py --export

# 清理过期故事（30天前标记为 obsolete 的）
python .cursor/skills/sprint evolve/story_store.py --clean
```

### 问题点识别规则

系统从用户故事中自动识别以下类型的问题点：

| 问题类型 | 关键词 | 优先级 | 分数 |
|----------|--------|--------|------|
| 错误/Bug | 错误、bug | High | 90 |
| 缺失功能 | 缺失、未实现 | High | 85 |
| 优化/改进 | 优化、改进、增强 | Medium | 75 |
| 重构 | 重构、需要 | Medium | 70 |
| 功能需求 | 作为...我想要... | Medium | 75 |

---

## 🚨 故障排查

### 常见问题

#### 1. 验证失败
```bash
# 现象
验证结果显示架构验证或单元测试失败

# 解决
1. 查看详细错误信息
2. 手动修复问题
3. 重新运行进化
```

#### 2. 文档更新失败
```bash
# 现象
文档更新阶段报错

# 解决
1. 检查文档文件是否存在
2. 检查文件权限
3. 手动更新文档后重新运行
```

#### 3. 优化执行失败
```bash
# 现象
优化执行阶段报错

# 解决
1. 检查错误信息
2. 分析失败原因
3. 根据建议手动处理或跳过该优化
```

#### 4. MetaGPT 不可用
```bash
# 现象
系统提示 MetaGPT 未安装

# 解决
1. 安装 MetaGPT: 
   pip install metagpt
   # 或使用 uv
   uv pip install metagpt

2. 跳过用户故事分析，继续执行其他功能：
   # 命令行方式
   python .cursor/skills/sprint evolve/evolve.py --skip-user-stories
   
   # 或配合其他参数
   python .cursor/skills/sprint evolve/evolve.py --skip-user-stories --dry-run

3. 使用便捷脚本
   source scripts/start_develop/activate.sh
   python .cursor/skills/sprint evolve/evolve.py --skip-user-stories
```

#### 5. 虚拟环境激活失败
```bash
# 现象
运行 activate.sh 提示 ".venv 目录不存在"

# 解决
1. 确保在项目目录中执行
   cd /path/to/sprintcycle

2. 运行开发环境部署脚本
   bash scripts/start_develop/dev-setup.sh

3. 或直接使用绝对路径激活
   source /path/to/sprintcycle/.venv/bin/activate
```

---

## 🔗 集成工作流

本系统自动集成以下工作流：
- [sprintcycle-workflow.mdc](../.cursor/rules/sprintcycle-workflow.mdc) - SDD + optimize + evolve 规则
- [sprint.md](../.cursor/commands/sprint.md) - `/sprint optimize` · `/sprint evolve`
- [SPRINT_OPTIMIZE_GUIDE.md](SPRINT_OPTIMIZE_GUIDE.md) - 使用指南
- [AUTO_VERIFICATION_GUIDE.md](AUTO_VERIFICATION_GUIDE.md) - 自动化验证指南

---

## 📝 最佳实践

### ✅ 推荐做法

1. **定期运行** - 设置定时任务每周自动运行，在重大变更后手动触发
2. **先模拟后执行** - 先用 `--dry-run` 预览变更，确认无误后再执行
3. **备份代码** - 执行前确保代码已提交，使用 Git 进行版本控制
4. **审查报告** - 仔细阅读进化报告，关注警告和错误信息
5. **安装 MetaGPT** - 充分利用用户故事自动生成功能

### ❌ 避免做法

1. **不要在生产环境直接运行** - 先在测试环境验证
2. **不要忽略警告** - 警告可能预示潜在问题
3. **不要中断执行** - 可能导致部分变更
4. **不要删除 userstories 目录** - 会丢失已保存的用户故事

---

## 🛠️ 技术实现原理

### 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Evolution Engine                          │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │   Analyzer      │  │   Executor      │                      │
│  │  (分析器)       │  │  (执行器)       │                      │
│  └────────┬────────┘  └────────┬────────┘                      │
│           │                    │                              │
│           ▼                    ▼                              │
│  ┌─────────────────────────────────────────┐                  │
│  │           Coordinator                   │                  │
│  │          (协调器)                        │                  │
│  └──────────────────┬──────────────────────┘                  │
│                     │                                        │
│     ┌───────────────┼───────────────┐                        │
│     ▼               ▼               ▼                        │
│  ┌───────────┐ ┌───────────┐ ┌───────────────┐               │
│  │ Validator │ │ Updater   │ │ Reporter      │               │
│  │  (验证器) │ │  (更新器)  │ │  (报告器)     │               │
│  └───────────┘ └───────────┘ └───────────────┘               │
│                     │                                        │
│                     ▼                                        │
│  ┌─────────────────────────────────────────┐                  │
│  │           Story Generator               │                  │
│  │          (用户故事生成器)                │                  │
│  │  ┌─────────────────────────────────┐    │                  │
│  │  │         MetaGPT Integration      │    │                  │
│  │  └──────────────────┬──────────────┘    │                  │
│  │                     │                   │                  │
│  │                     ▼                   │                  │
│  │  ┌─────────────────────────────────┐    │                  │
│  │  │         Story Store              │    │                  │
│  │  │       (用户故事存储)              │    │                  │
│  │  └─────────────────────────────────┘    │                  │
│  └─────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 职责 | 文件路径 |
|------|------|----------|
| **Analyzer** | 分析代码库，识别优化机会 | `evolve.py` |
| **Executor** | 执行优化操作 | `evolve.py` |
| **Validator** | 运行验证套件 | `evolve.py` |
| **Updater** | 自动更新文档 | `document_updater.py` |
| **Reporter** | 生成进化报告 | `evolve.py` |
| **Coordinator** | 协调各组件工作流 | `evolve.py` |
| **StoryGenerator** | 使用 MetaGPT 生成用户故事 | `story_generator_integrator.py` |
| **StoryStore** | 持久化管理用户故事 | `story_store.py` |

### 核心类设计

```python
class EvolutionEngine:
    """自动化进化引擎 - 核心控制器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root
        self.dry_run = False
        self.force = False
        self.silent = False
    
    def analyze(self) -> AnalysisResult:
        """分析代码库，识别优化机会"""
    
    def analyze_user_stories(self) -> UserStoryResult:
        """分析用户故事（使用 MetaGPT）"""
    
    def get_top_optimizations(self, count: int = 3) -> List[Optimization]:
        """获取 Top N 优化方向"""
    
    def execute_optimization(self, optimization: Optimization) -> ExecutionResult:
        """执行单个优化"""
    
    def validate(self) -> ValidationResult:
        """运行完整验证套件"""
    
    def run(self, dry_run=False, force=False, silent=False) -> EvolutionResult:
        """运行完整进化周期"""
```

### 评分算法实现

```python
def _calculate_score(self, impact: str, complexity: str, risk: str) -> float:
    """计算优化优先级分数"""
    impact_weights = {"High": 30, "Medium": 20, "Low": 10}
    complexity_weights = {"Low": 20, "Medium": 15, "High": 10}
    risk_weights = {"Low": 15, "Medium": 10, "High": 5}
    
    return (
        impact_weights[impact] +      # 架构影响 (30%)
        25 +                          # 业务价值 (固定25%)
        complexity_weights[complexity] + # 复杂度 (20%)
        risk_weights[risk] +          # 风险 (15%)
        10                            # 测试覆盖 (固定10%)
    )
```

### 用户故事生成器

```python
class StoryGeneratorIntegrator:
    """用户故事生成器集成器 - 使用 MetaGPT"""
    
    def __init__(self):
        self._generator = MetaGPTGenerator()
    
    def generate(self, code_path: Path, doc_path: Optional[Path] = None) -> List[GeneratedUserStory]:
        """使用 MetaGPT 生成用户故事"""
    
    def get_top_stories(self, code_path: Path, count: int = 5) -> List[GeneratedUserStory]:
        """获取 Top N 用户故事"""
```

### 用户故事存储管理器

```python
class StoryStoreManager:
    """用户故事存储管理器"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path("userstories")
    
    def add_or_update_story(self, story_data: Dict[str, Any]) -> str:
        """添加或更新用户故事（自动去重）"""
    
    def mark_obsolete(self, story_id: str) -> bool:
        """标记故事为过期"""
    
    def delete_story(self, story_id: str) -> bool:
        """删除用户故事"""
    
    def get_top_stories(self, count: int = 5) -> List[StoredUserStory]:
        """获取 Top N 优先级最高的故事"""
    
    def clean_obsolete(self, days_threshold: int = 30) -> int:
        """清理过期的用户故事"""
```

### 文档更新机制

```python
class DocumentUpdater:
    """文档自动更新器"""
    
    def update_all_documents(self) -> List[DocumentUpdate]:
        """更新所有文档"""
        updates = []
        
        # 更新 README.md
        updates.extend(self._update_readme())
        
        # 更新 README_EN.md
        updates.extend(self._update_readme_en())
        
        # 更新 ARCHITECTURE_INVARIANTS.md
        updates.extend(self._update_architecture_invariants())
        
        # 更新架构编排规则
        updates.extend(self._update_architecture_orchestration())
        
        return updates
```

### 错误处理机制

```python
def execute_optimization(self, optimization: Optimization) -> ExecutionResult:
    """执行单个优化，支持重试"""
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            changes = self._execute_optimization_internal(optimization)
            return ExecutionResult(success=True, optimization_id=optimization.id, changes_made=changes)
        
        except TransientError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            raise
        
        except CriticalError as e:
            return ExecutionResult(success=False, optimization_id=optimization.id, errors=[str(e)])
```

---

## 📁 文件结构

```
.cursor/skills/sprint evolve/
├── SKILL.md                  # Skill 定义
├── evolve.py                 # 核心进化引擎
├── document_updater.py       # 文档更新器
├── story_generator_integrator.py  # 用户故事生成器（MetaGPT集成）
└── story_store.py            # 用户故事存储管理器

scripts/
└── run_evolution.sh          # 一键运行脚本

.cursor/commands/
└── sprint.md                 # `/sprint evolve` 统一入口

.cursor/rules/
└── sprintcycle-workflow.mdc  # evolve + optimize + SDD

userstories/                  # 用户故事存储目录（自动创建）
├── stories.json              # 用户故事数据
└── metadata.json             # 元数据

docs/
└── SPRINT_EVOLVE_SYSTEM.md   # 本文档
```

---

## 📈 监控与指标

### 关键指标

| 指标 | 说明 |
|------|------|
| 分析时间 | 分析阶段耗时 |
| 用户故事生成时间 | MetaGPT 生成用户故事耗时 |
| 优化执行时间 | 各优化执行耗时 |
| 验证时间 | 验证阶段耗时 |
| 文档更新时间 | 文档更新耗时 |
| 优化成功率 | 优化执行成功率 |
| 验证通过率 | 验证通过比例 |
| 用户故事生成数量 | 每次运行生成的用户故事数 |

---

## 🔧 扩展机制

### 添加新的优化类型

```python
# 1. 添加新的枚举值
class OptimizationType(Enum):
    NEW_OPTIMIZATION_TYPE = "new_optimization_type"

# 2. 添加检测逻辑
def _detect_new_optimization(self) -> Optional[Optimization]:
    return Optimization(
        id="new_opt_001",
        type=OptimizationType.NEW_OPTIMIZATION_TYPE,
        description="新优化类型描述",
        # ...
    )

# 3. 添加执行逻辑
def _execute_new_optimization(self, optimization: Optimization) -> List[str]:
    return ["变更内容"]
```

### 扩展用户故事来源

系统当前使用 MetaGPT 作为用户故事生成器。如需扩展其他来源：

```python
# 添加新的生成器类型
class GeneratorType(Enum):
    METAGPT = "metagpt"
    CODE2PROMPT = "code2prompt"  # 可扩展

# 实现新的生成器类
class Code2PromptGenerator:
    def generate(self, code_path: Path, doc_path: Optional[Path] = None) -> List[GeneratedUserStory]:
        # 实现 code2prompt + LLM 逻辑
        pass
```

---

*Last updated: 2026-06-01*