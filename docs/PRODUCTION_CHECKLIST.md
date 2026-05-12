# SprintCycle Production Launch Checklist

这份清单用于 SprintCycle 上线前检查，目标是确保前端、后端、反向代理、TLS、持久化和升级回滚策略都已准备就绪。

---

## 1. 基础环境

- [ ] 服务器已安装 Docker
- [ ] 服务器已安装 Docker Compose
- [ ] 服务器已安装外层 Nginx 或网关
- [ ] 服务器已安装 Certbot 或接入证书管理平台
- [ ] 服务器时间同步正常
- [ ] 服务器磁盘空间充足
- [ ] 宿主机 `3000`、`8000`、`80`、`443` 端口无冲突

---

## 2. 仓库与配置

- [ ] 仓库已部署到生产目录，例如 `/opt/sprintcycle`
- [ ] `.env` 已从 `.env.example` 复制并完成配置
- [ ] `SPRINTCYCLE_ENV=production`
- [ ] `PROJECT_PATH` 已设置为持久化工作目录
- [ ] `BACKEND_IMAGE` / `FRONTEND_IMAGE` 已确认
- [ ] 如使用自定义域名，`DOMAIN` 已配置

---

## 3. 持久化

- [ ] `.sprintcycle` 已挂载到 Docker volume
- [ ] 执行历史可跨容器重启保留
- [ ] 治理报告可持久化
- [ ] 需要保留的产物已纳入备份策略

---

## 4. 容器与构建

- [ ] `backend.Dockerfile` 构建成功
- [ ] `frontend/Dockerfile` 构建成功
- [ ] `docker-compose.prod.yml` 可正常解析
- [ ] `backend` 容器健康检查通过
- [ ] `frontend` 容器健康检查通过
- [ ] 重启策略已启用（`unless-stopped`）

---

## 5. 入口与路由

- [ ] 外层 Nginx 已配置
- [ ] `80` 已跳转到 `443`
- [ ] `/` 已正确转发到前端
- [ ] `/api/` 已正确转发到后端
- [ ] `/.well-known/acme-challenge/` 已可用
- [ ] 前端 Nginx 的 `/api/` 反代已可用
- [ ] SSE 长连接可正常通过代理

---

## 6. TLS

- [ ] 证书已签发
- [ ] 证书路径正确挂载
- [ ] TLSv1.2 / TLSv1.3 已启用
- [ ] HSTS 已开启或已评估开启时机
- [ ] 证书自动续期已配置
- [ ] 续期后 Nginx 可自动或半自动 reload

---

## 7. 功能验证

- [ ] `GET /health` 返回正常
- [ ] Dashboard 页面可访问
- [ ] 前端静态资源加载正常
- [ ] `POST /api/run` 可正常执行
- [ ] `POST /api/plan` 可正常返回
- [ ] `GET /api/dashboard/platform` 可正常返回
- [ ] SSE 事件流可正常连接
- [ ] 需求进化流程可完成一轮闭环

---

## 8. 运维验证

- [ ] `docker compose ps` 显示服务健康
- [ ] `docker compose logs` 可正常查看日志
- [ ] 容器异常退出可自动重启
- [ ] 日志中无明显 5xx / 错误堆栈
- [ ] 资源占用在预期范围内

---

## 9. 升级与回滚

- [ ] 已准备上一个稳定镜像标签
- [ ] 已确认升级命令
- [ ] 已确认回滚命令
- [ ] 不会在升级时误删 volume
- [ ] 回滚后能恢复到可用状态

---

## 10. 监控与告警

- [ ] 已接入基础监控或日志收集
- [ ] 已设置服务不可用告警
- [ ] 已设置证书过期提醒
- [ ] 已设置磁盘空间提醒
- [ ] 已设置容器重启异常提醒

---

## 11. 上线前最终确认

- [ ] 域名解析已生效
- [ ] HTTPS 访问正常
- [ ] 生产页面可访问
- [ ] 后端 API 可用
- [ ] 数据持久化已确认
- [ ] 回滚方案已演练

---

## 12. 最小上线命令

```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

验证：

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3000/health
```

---

## 13. 上线建议

- 先在测试域名完成一次完整验证
- 先验证后端，再验证前端，再验证外层网关
- 先灰度后全量
- 先保留旧镜像，再切换新镜像
