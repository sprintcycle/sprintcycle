# SprintCycle 生产就绪推进工作流
## 版本: 1.0.0
## 目标: 分批次修复 34 个 bug，推进 SprintCycle 到生产就绪状态

---

## 🎯 总体目标

```
SprintCycle 代码质量 60% → 85%+ (生产就绪)
```

---

## 📋 工作流设计（扣子 Bot / 工作流）

### 工作流架构

```
┌─────────────────────────────────────────────────────────────┐
│                    SprintCycle 修复工作流                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [触发] ──→ [检查] ──→ [拆解] ──→ [循环修复] ──→ [验证]      │
│                                                             │
│              ▲                                           │  │
│              └──────────── [完成] ←──────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 详细步骤

#### Step 1: 触发条件
- 手动触发："开始 SprintCycle 修复"
- 定时触发：每天 19:00 检查新问题

#### Step 2: 运行检查
```bash
cd sprintcycle && ruff check . --select=F821,F811
```
输出：
- F821 未定义名称（29个）
- F811 重定义未使用名称（5个）

#### Step 3: 拆解任务
根据 bug 类型拆分成小任务：

```
Batch 1: 导入修复（2个）
  └─ 添加 typing.Dict, typing.Any 导入

Batch 2: 核心函数修复（3个）
  ├─ build_lifecycle_contract × 3处
  ├─ build_platform_spec × 1处
  └─ evaluate_hitl_policy × 1处

Batch 3: 类定义修复（3个）
  ├─ _OrchestratorSprintHooks × 2处
  ├─ GovernanceViolation × 12处
  └─ SUGGESTION_ARCHIVE × 3处

Batch 4: 变量修复（2个）
  ├─ _measurement_run_metadata × 2处
  └─ suggestion × 1处

Batch 5: 清理重定义（5个）
  └─ 删除所有 F811 重复定义
```

#### Step 4: 循环修复（每次修一个 batch）
```
For each batch:
  1. 读取 bug 位置
  2. 生成修复代码
  3. 验证修复
  4. 提交 git
  5. 报告结果
```

#### Step 5: 最终验证
```bash
ruff check . --select=F821,F811
git add . && git commit -m "fix: resolve F821/F811 errors - batch N"
```

---

## 🤖 扣子 Bot 配置

### Bot 名称
```
SprintCycle Bug Fixer
```

### 核心指令
```
你是一个专门修复 SprintCycle Python 代码 bug 的助手。

当前任务：修复未定义名称错误（F821）和重定义错误（F811）

## 修复原则
1. 每次只修复一个文件中的一个错误
2. 修复前先理解上下文
3. 不要改变现有逻辑，只补全缺失的定义
4. 修复后验证：运行 ruff check 确认错误消失

## 修复顺序
1. 先检查缺失的导入（typing.Dict, typing.Any）
2. 再补全缺失的函数
3. 再补全缺失的类/异常
4. 最后清理重定义

## 当前待修复的 bug 清单
详见 docs/RELEASE_READINESS/bug_fix_checklist.md
```

### 快捷命令
| 命令 | 功能 |
|------|------|
| `/fix-next` | 修复下一个优先级最高的 bug |
| `/fix-batch N` | 修复第 N 批 bug |
| `/status` | 查看当前修复进度 |
| `/verify` | 运行验证检查 |

---

## 📊 进度追踪

| 批次 | 内容 | 状态 | 修复后验证 |
|------|------|------|-----------|
| Batch 1 | 导入修复 | ⬜ 待做 | ruff check 无 F821 |
| Batch 2 | 核心函数 | ⬜ 待做 | ruff check 无 F821 |
| Batch 3 | 类定义 | ⬜ 待做 | ruff check 无 F821 |
| Batch 4 | 变量修复 | ⬜ 待做 | ruff check 无 F821 |
| Batch 5 | 清理重定义 | ⬜ 待做 | ruff check 无 F811 |

---

## 🚀 使用方式

### 方式 1: 扣子 Bot 对话
```
用户: /fix-batch 1
Bot: 开始修复 Batch 1（导入修复）...
Bot: 修复完成！当前剩余 F821 错误: 27个
```

### 方式 2: 自动执行
```
每天 19:00 自动执行 /fix-next
直到所有 bug 修复完成
```

### 方式 3: 手动触发
```
用户: 开始 SprintCycle 修复
Bot: 运行检查...发现 34 个问题
Bot: 拆解成 5 个批次
Bot: 开始修复 Batch 1...
```

---

## ✅ 验收标准

修复完成后，运行以下验证：

```bash
# 1. 检查 F821/F811 错误
ruff check . --select=F821,F811
# 预期输出：无错误

# 2. 检查代码可运行
python -c "import sprintcycle"
# 预期输出：无 ImportError

# 3. 运行测试
pytest tests/ -v
# 预期输出：大部分测试通过
```

---

## 📝 修复记录模板

```markdown
## Batch N 修复记录
- 日期: YYYY-MM-DD
- 修复人: [Bot/Manual]
- 修复内容:
  - [文件]: [行号] - [修复描述]
  - ...
- 验证结果: ✅ 通过 / ❌ 失败
- 剩余问题: X 个
```
