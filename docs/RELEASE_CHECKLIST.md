# 发布前检查清单（Maintainer）

面向 **PyPI / 内部 wheel** 与 **带 Dashboard 的发行版**。按需勾选。

## 版本与元数据

- [ ] `pyproject.toml` / `sprintcycle.__version__` / `CHANGELOG` 版本与日期一致（本项目约定以 `pyproject.toml` 为权威来源之一）。
- [ ] `CHANGELOG.md` 已写入本版本条目（[Unreleased] 已落实或已迁移）。

## 质量保证

- [ ] `pip install -e ".[dev,dashboard]"` 后 `pytest` 通过（或 CI 绿）。
- [ ] `ruff check sprintcycle tests`（或 CI architecture + test job）通过。
- [ ] 若改动 import 边界：`lint-imports` 通过。

## Dashboard 前端（若本版本包含 Web UI 或需可安装的静态资源）

**从 sdist/wheel 安装后** `sprintcycle dashboard` 应加载完整 Vue 构建产物，而非仅占位 HTML。

- [ ] `cd frontend && npm ci && npm run build` 成功；产物写入 `sprintcycle/dashboard/static/`（`index.html` + `assets/`）。
- [ ] 本地 Smoke：`sprintcycle dashboard`，浏览器打开根路径，确认界面为 Vue 应用（非「占位页」说明文字）。
- [ ]（可选）记录 `npm run build` 产物的 gzip 体积趋势；大版本可考虑按需引入 / 拆包优化（见 `frontend/vite.config.ts`）。

## 构建产物

- [ ] `python -m build`（或项目采用的打包命令）生成 **wheel + sdist**；抽查 wheel 内是否包含 `sprintcycle/dashboard/static/**/*`（与 `pyproject` 中 `package-data` 一致）。

## 发布命令（示例）

```bash
cd frontend && npm ci && npm run build
cd ..
python -m build
# twine upload dist/…
```

CI（`.github/workflows/ci.yml`）在测试前已执行前端 build，但 **PyPI 发布流水线**若独立，请同步包含上述 `npm ci && npm run build` 步骤。
