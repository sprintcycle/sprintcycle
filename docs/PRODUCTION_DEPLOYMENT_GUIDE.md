# SprintCycle Production Deployment Guide

本文档说明 SprintCycle 的生产部署建议，包含配置分层、镜像构建、启动方式、健康检查、升级回滚、以及与外层反向代理和 TLS 的配合方式。

---

## 1. 部署目标

生产环境建议采用如下拓扑：

- **frontend 容器**：Vue Dashboard + Nginx 静态站点
- **backend 容器**：FastAPI + SprintCycle 编排与执行逻辑
- **external Nginx / gateway**：TLS 终止、统一域名入口、证书验证
- **Docker volume**：持久化 `.sprintcycle` 等运行态数据

推荐用户只访问一个域名入口：

```text
https://sprintcycle.example.com
```

---

## 2. 配置分层

### 2.1 `.env.example`

仓库提供 `.env.example` 作为环境变量模板。建议复制为 `.env` 后再部署：

```bash
cp .env.example .env
```

推荐分层：

- **基础层**：`SPRINTCYCLE_ENV`、`PROJECT_PATH`
- **镜像层**：`BACKEND_IMAGE`、`FRONTEND_IMAGE`
- **端口层**：`FRONTEND_PORT`、`BACKEND_PORT`
- **域名层**：`DOMAIN`
- **密钥层**：数据库、第三方 API key、证书路径

---

## 3. Compose 文件分工

### 3.1 `docker-compose.prod.yml`

用于生产环境：

- 默认启用 `restart: unless-stopped`
- 使用明确的端口映射
- 绑定生产 volume
- 适合正式上线

### 3.2 `docker-compose.dev.yml`

用于开发联调：

- 更适合调试和迭代
- 可保留宿主机挂载
- 便于与本地代码同步

### 3.3 `docker-compose.local.yml`

用于单机本地验证：

- 与 dev 类似，但更偏个人开发/演示
- 适合快速起栈

---

## 4. 镜像缓存策略

### 4.1 后端

建议：

- 基础镜像版本固定
- Python 依赖由 `pyproject.toml` 统一管理
- 尽量减少无关层变动

### 4.2 前端

建议：

- 使用 `npm ci` 保证依赖可复现
- `package-lock.json` 变化时才刷新依赖层缓存
- Vue build 与 Nginx 运行层分离

### 4.3 发布策略

建议：

- 生产镜像使用版本号或 git sha
- `latest` 仅用于开发或内部预览
- 每次升级先构建，再启动

---

## 5. 启动命令

### 5.1 最小生产启动

```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

### 5.2 查看状态

```bash
docker compose -f docker-compose.prod.yml --env-file .env ps
docker compose -f docker-compose.prod.yml --env-file .env logs -f backend
docker compose -f docker-compose.prod.yml --env-file .env logs -f frontend
```

---

## 6. 健康检查说明

### 6.1 后端健康检查

后端提供：

```text
GET /health
```

用于验证：

- FastAPI 服务可用
- SprintCycle 核心服务已启动
- 容器内网络正常

### 6.2 前端健康检查

前端 Nginx 提供：

```text
GET /health
```

用于验证：

- 静态站点容器可用
- Nginx 配置加载成功

### 6.3 Compose 健康依赖

建议：

- `frontend` 依赖 `backend` 健康后再启动
- 避免前端刚启动时反代失败

---

## 7. 升级流程

建议升级顺序：

1. 拉取最新代码
2. 检查 `.env` 和镜像标签
3. 构建镜像
4. 重启服务
5. 验证页面、API 和 SSE

示例：

```bash
cd /opt/sprintcycle
git pull
docker compose -f docker-compose.prod.yml --env-file .env build
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

---

## 8. 回滚流程

建议回滚原则：

- 优先回滚镜像，不回滚数据卷
- 保留 `.sprintcycle` 持久化数据
- 回滚前确认上一个稳定标签

示例：

```bash
docker compose -f docker-compose.prod.yml --env-file .env down
# 修改镜像标签后
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

---

## 9. 反向代理与 HTTPS

### 9.1 统一入口

建议最终用户只访问：

```text
https://sprintcycle.example.com
```

并由外层反向代理负责：

- `80 → 443`
- TLS 终止
- `/.well-known/acme-challenge/`
- `/`、`/api/`、`/health` 的路由

### 9.2 Nginx 角色

- 外层 Nginx：域名、TLS、统一入口
- 前端 Nginx：静态资源、SPA 回退、`/api` 反代
- 后端：业务执行与 API

### 9.3 TLS 建议

建议使用：

- Let’s Encrypt
- Certbot 自动签发与续期
- `deploy/nginx/tls.conf` 提供安全参数模板

---

## 10. 运维检查清单

推荐先检查：

- 后端 `/health`
- 前端页面
- `/api/run`
- `/api/plan`
- SSE 连接
- volume 持久化
- TLS 是否生效
- 回滚是否可执行

---

## 11. 最小验收标准

生产环境上线前，至少满足：

- [ ] 前端页面可访问
- [ ] 后端健康检查通过
- [ ] `/api/*` 正常响应
- [ ] SSE 可连接
- [ ] `.sprintcycle` 持久化
- [ ] 自动重启已启用
- [ ] HTTPS 已启用
- [ ] 升级与回滚路径明确
