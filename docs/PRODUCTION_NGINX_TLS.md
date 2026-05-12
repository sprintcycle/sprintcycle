# SprintCycle Production Nginx + TLS Guide

本文档描述 SprintCycle 在生产环境中使用外层反向代理与 TLS 的推荐部署方式，目标是让浏览器只访问一个统一入口，同时保持前端、后端、证书与健康检查职责清晰。

---

## 1. 目标拓扑

推荐最终对外只暴露一个域名，例如：

```text
https://sprintcycle.example.com
```

请求流向建议如下：

```text
Browser
  ↓
External Nginx / Gateway
  ↓
Frontend Container (Nginx + Vue static)
  ↓
Backend Container (FastAPI + SprintCycle)
```

路由职责建议：

- `/`：Vue Dashboard
- `/api/`：后端 API
- `/health`：健康检查
- `/.well-known/acme-challenge/`：Let’s Encrypt 验证目录

---

## 2. 目录建议

建议在部署机器上使用如下结构：

```text
/opt/sprintcycle
/opt/sprintcycle/.env
/opt/sprintcycle/docker-compose.prod.yml
/opt/sprintcycle/deploy/nginx/
/etc/letsencrypt/live/sprintcycle.example.com/
/var/www/certbot/
```

---

## 3. 相关文件

仓库中与生产部署相关的文件：

- `docker-compose.prod.yml`
- `backend.Dockerfile`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `.env.example`
- `deploy/nginx/site.conf`
- `deploy/nginx/tls.conf`
- `deploy/nginx/proxy_headers.conf`
- `deploy/nginx/nginx.conf`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

---

## 4. 内外层 Nginx 职责划分

### 4.1 外层 Nginx

外层 Nginx 建议部署在宿主机或独立网关层，职责如下：

- 监听 `80` 和 `443`
- 将 `80` 跳转到 `443`
- 提供 TLS 终止
- 提供证书验证入口 `/.well-known/acme-challenge/`
- 将 `/` 和 `/api/` 转发到前端容器
- 统一对外域名入口

### 4.2 前端容器内 Nginx

前端容器内的 Nginx 负责：

- 托管 Vue 静态资源
- 处理 SPA 路由回退
- 将 `/api/` 代理到后端容器
- 正确支持 SSE / 长连接

### 4.3 后端容器

后端容器负责：

- SprintCycle API
- 运行时编排
- SSE 事件流
- 治理与建议处理
- 健康检查

---

## 5. 推荐 Nginx 配置

### 5.1 HTTP 站点配置

`deploy/nginx/site.conf` 建议用于：

- 证书验证
- HTTP 强制跳转到 HTTPS

示意：

```nginx
server {
  listen 80;
  server_name _;

  location /.well-known/acme-challenge/ {
    root /var/www/certbot;
  }

  location / {
    return 301 https://$host$request_uri;
  }
}
```

### 5.2 外层 HTTPS 入口

`deploy/nginx/nginx.conf` 建议用于：

- 监听 `443 ssl http2`
- 载入证书
- 设置安全响应头
- 将请求转发给前端容器

建议将 `/` 与 `/api/` 都先转给前端容器，让前端容器内部的 Nginx 再统一处理 `/api/` 到后端的反代。

### 5.3 TLS 参数

`deploy/nginx/tls.conf` 建议至少包含：

- TLSv1.2 / TLSv1.3
- HSTS
- `X-Frame-Options`
- `X-Content-Type-Options`
- `Referrer-Policy`

---

## 6. 推荐反向代理头

`deploy/nginx/proxy_headers.conf` 建议统一设置：

- `Host`
- `X-Real-IP`
- `X-Forwarded-For`
- `X-Forwarded-Proto`
- `X-Forwarded-Host`

这可以确保后端日志、审计和请求追踪更准确。

---

## 7. 证书签发与续期

### 7.1 首次签发

如果使用 Let’s Encrypt + Certbot，可通过 webroot 模式签发：

```bash
certbot certonly --webroot -w /var/www/certbot -d sprintcycle.example.com
```

### 7.2 证书路径

通常证书会位于：

```text
/etc/letsencrypt/live/sprintcycle.example.com/fullchain.pem
/etc/letsencrypt/live/sprintcycle.example.com/privkey.pem
```

### 7.3 自动续期

建议通过系统定时任务或 `certbot renew` 自动续期：

```bash
certbot renew
```

续期后重载 Nginx：

```bash
nginx -s reload
```

---

## 8. Docker 启动建议

### 8.1 生产容器启动

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

### 8.2 健康检查

后端健康检查：

```bash
curl http://127.0.0.1:8000/health
```

前端健康检查：

```bash
curl http://127.0.0.1:3000/health
```

### 8.3 日志查看

```bash
docker compose -f docker-compose.prod.yml --env-file .env logs -f backend
docker compose -f docker-compose.prod.yml --env-file .env logs -f frontend
```

---

## 9. 升级与回滚

### 9.1 升级流程

```bash
cd /opt/sprintcycle
git pull
docker compose -f docker-compose.prod.yml --env-file .env build
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

### 9.2 回滚流程

回滚建议优先回退镜像标签，不要删除持久化卷：

```bash
docker compose -f docker-compose.prod.yml --env-file .env down
# 修改 .env 中镜像标签后

docker compose -f docker-compose.prod.yml --env-file .env up -d
```

---

## 10. 推荐请求路由

建议最终用户只感知一个入口：

- `https://sprintcycle.example.com/`
- `https://sprintcycle.example.com/api/...`

这样可以减少：

- CORS 复杂度
- 多地址配置
- 环境差异导致的部署问题

---

## 11. 生产注意事项

- 前端静态资源应设置长缓存，构建版本变更时通过文件名 hash 自动失效
- `/api/` 反代时关闭缓冲，避免 SSE 被打断
- `backend` 应保留持久化卷，避免 `.sprintcycle` 数据丢失
- 证书建议由外层 Nginx 或网关统一管理
- 生产环境建议使用明确的镜像 tag，而不是始终使用 `latest`

---

## 12. 最小可用配置检查清单

- [ ] 域名已解析到服务器
- [ ] 80/443 端口开放
- [ ] 外层 Nginx 已启用
- [ ] 证书已签发并可读取
- [ ] 前端容器可访问
- [ ] `/api/` 可正常转发
- [ ] `/health` 可正常访问
- [ ] `.sprintcycle` 已挂载并持久化
- [ ] 自动重启策略已配置

---

## 13. 结论

推荐生产部署最终采用：

- 外层 Nginx / 网关：负责 TLS 和域名入口
- 前端容器：负责 Dashboard 静态站点与 `/api` 反代
- 后端容器：负责 SprintCycle 业务逻辑与 API
- 持久化卷：负责执行数据、治理数据与运行时状态

这套结构最适合 SprintCycle 的长期稳定部署与后续演进。
