# SprintCycle Demo - 微博类产品

这是一个类似微博的社交产品演示项目，用于展示 SprintCycle 的开发能力。

## 项目功能

- 用户注册/登录
- 发布微博
- 评论互动
- 点赞收藏
- 关注系统

## 技术栈

- Python 3.8+
- FastAPI (Web框架)
- SQLite (数据库)
- JWT (认证)

## 快速开始

```bash
cd sprintcycle/demo

# 安装依赖
pip install -r requirements.txt

# 运行服务
python app.py

# 访问
open http://localhost:8000
```

## 演示 SprintCycle

```bash
# 1. 修复 Bug
sprintcycle "修复 auth.py 的密码验证漏洞" --project .

# 2. 添加功能
sprintcycle "为微博添加转发功能" --project .

# 3. 性能优化
sprintcycle "优化 posts.py 的查询性能" --project .

# 4. 执行 PRD
sprintcycle run prd/demo.yaml
```

## 已知问题（供演示）

| 文件 | 问题 | 类型 |
|------|------|------|
| auth.py | 密码明文存储 | 安全漏洞 |
| auth.py | SQL 注入风险 | 安全漏洞 |
| posts.py | N+1 查询问题 | 性能问题 |
| comments.py | 没有限流 | 功能缺失 |

## 目录结构

```
demo/
├── app.py              # FastAPI 入口
├── models.py           # 数据模型
├── auth.py             # 认证模块
├── posts.py            # 帖子模块
├── comments.py         # 评论模块
├── follows.py          # 关注模块
├── database.py         # 数据库配置
├── requirements.txt    # 依赖
├── prd/
│   └── demo.yaml       # PRD 示例
└── tests/
    └── test_api.py     # API 测试
```
