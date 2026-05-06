# Dashboard 部署与 Nginx（含 SSE）

SprintCycle Dashboard 为 **FastAPI 后端 + Vue SPA**（`sprintcycle dashboard`）。生产环境建议在反向代理后运行，并正确转发 **Server-Sent Events (SSE)**。

## 进程与端口

- 默认监听 `0.0.0.0:8080`（可用 `--host` / `--port` 修改）。
- 前端静态资源由 FastAPI 挂载在站点根路径；REST 在 `/api/*`，SSE 在 `/api/events/stream`（及兼容端点）。

## Nginx 示例

以下示例将 HTTPS 入口 `dashboard.example.com` 反代到本机 `127.0.0.1:8080`：

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 443 ssl http2;
    server_name dashboard.example.com;

    # ssl_certificate ...;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE：禁用缓冲，避免事件被 Nginx 攒批导致前端长时间无数据
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

要点：

- **`proxy_buffering off`**：对应应用已在响应头中设置 `X-Accel-Buffering: no`；在 Nginx 侧关闭缓冲可进一步避免 SSE 被延迟。
- **超时**：长连接执行时适当拉长 `proxy_read_timeout`，避免空闲 SSE 被代理提前断开（可按运维策略调整）。

## 仅 API / 分离静态站（高级）

若将 Vue 构建产物托管在 CDN 或独立静态域名，需保证浏览器仍能访问同一后端的 `/api` 与 `/api/events/stream`（CORS、Cookie、SSE 路径一致）。开发模式可使用 `SPRINTCYCLE_ENV=development` 与 Vite 代理；生产环境建议同源部署或显式配置 CORS 与白名单。

## 健康检查

可对 `GET /api/diagnose` 或 `GET /api/clients` 做轻量探测；注意 `diagnose` 可能较重，按环境选择频率。

## 与 CI 一致的前端构建

仓库 CI 在运行 pytest 前会执行 `cd frontend && npm ci && npm run build`，将产物写入 `sprintcycle/dashboard/static/`。发布物（wheel/sdist）应包含该目录或按 `docs/RELEASE_CHECKLIST.md` 在发布流水线中重建前端。
