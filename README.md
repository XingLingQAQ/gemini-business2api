<p align="center">
  <img src="docs/logo.svg" width="120" alt="Gemini Business2API logo" />
</p>
<h1 align="center">Gemini Business2API</h1>
<p align="center">Gemini Business → OpenAI 兼容 API 网关</p>
<p align="center">
  <strong>简体中文</strong> | <a href="docs/README_EN.md">English</a>
</p>
<p align="center"><img src="https://img.shields.io/badge/License-CNC--1.0-red.svg" /> <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white" /> <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white" /> <img src="https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white" /> <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white" /></p>

<p align="center">聚焦 2API 主服务、管理后台与可选 refresh-worker。</p>

---

## 项目定位

Gemini Business2API 是一个把 [Gemini Business](https://business.google.com) 能力转换为 **OpenAI 兼容接口** 的网关服务，内置后台管理面板，适合统一管理账号池、系统设置、图片 / 视频能力与运行状态。

---

## 社区交流

点击链接加入群聊【business2api 交流群】：

- [https://qm.qq.com/q/yegwCqJisS](https://qm.qq.com/q/yegwCqJisS)

---

## 核心能力

- ✅ OpenAI API 兼容：可直接对接常见 OpenAI 客户端与中间层
- ✅ 多账号调度：支持轮询、可用性切换与批量管理
- ✅ 账号管理后台：导入 / 导出 / 编辑 / 批量操作 / 状态筛选
- ✅ 多模态能力：支持文本、文件、图片、视频相关能力
- ✅ 图片生成 / 图生图：支持 Base64 或 URL 返回
- ✅ 视频生成：支持统一配置与输出格式控制
- ✅ 系统设置集中管理：代理、邮箱、刷新、输出格式等统一收口
- ✅ 仪表盘 / 监控 / 日志：便于观察服务状态与账号池情况
- ✅ SQLite / PostgreSQL：支持本地持久化与多实例共享数据
- ✅ 可选 refresh-worker：通过 Docker Compose profile 独立启用

---

## 部署架构

```text
docker-compose.yml
├─ gemini-api
│  ├─ 运行 2API 主服务
│  ├─ 运行管理后台
│  ├─ 暴露 7860
│  └─ 挂载 ./data:/app/data
│
└─ refresh-worker（可选）
   ├─ 默认不启动
   ├─ 使用 profile refresh 启动
   ├─ 不暴露业务 API
   ├─ 读取同一个 ./data
   └─ 负责账号刷新
```

启动方式：

- 只跑 2API：`docker compose up -d`
- 2API + refresh-worker：`docker compose --profile refresh up -d`

说明：

- `refresh-worker` 由独立的 `refresh-worker` 分支维护
- 该分支通过 GitHub Actions 自动构建并发布 refresh-worker Docker 镜像
- 主线 `docker-compose.yml` 通过 `REFRESH_WORKER_IMAGE` / `--profile refresh` 直接接入该镜像

---

## 快速开始

### 方式一：Docker Compose（推荐）

支持 ARM64 / AMD64。

```bash
git clone https://github.com/yukkcat/gemini-business2api.git
cd gemini-business2api
cp .env.example .env
# 编辑 .env，至少设置 ADMIN_KEY

docker compose up -d
```

如果需要启用 refresh-worker：

```bash
docker compose --profile refresh up -d
```

---

### 方式二：交互式安装脚本（Linux / macOS / WSL / Git Bash）

主线现在统一使用 `deploy/install.sh`。

```bash
curl -fsSL https://raw.githubusercontent.com/yukkcat/gemini-business2api/main/deploy/install.sh | sudo bash
```

启用 refresh-worker：

```bash
curl -fsSL https://raw.githubusercontent.com/yukkcat/gemini-business2api/main/deploy/install.sh | sudo bash -s -- --with-refresh
```

脚本支持两条路径：

- Docker 部署
- Python 本地启动（开发 / 调试）

也可以在仓库内运行：

```bash
bash deploy/install.sh
```

---

### 方式三：Python 本地开发

适合开发、调试或本地改代码。

```bash
git clone https://github.com/yukkcat/gemini-business2api.git
cd gemini-business2api
bash deploy/install.sh --mode python
```

脚本会引导你完成：

- Python 3.11 / uv 检查
- `.venv` 创建或复用
- Python 依赖安装
- 前端构建
- `.env` 初始化
- 可选直接启动 `python main.py`

---

### 访问地址

- 管理面板：`http://localhost:7860/`
- OpenAI 兼容接口：`http://localhost:7860/v1/chat/completions`
- 健康检查：`http://localhost:7860/health`

---

## 配置与数据边界

### `.env` 关键项

```env
ADMIN_KEY=your-admin-login-key
# PORT=7860
# DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
# REFRESH_WORKER_IMAGE=cooooookk/gemini-refresh-worker:latest
# REFRESH_HEALTH_PORT=8080
```

其中：

- `gemini-business2api` 主服务镜像由主线构建
- `REFRESH_WORKER_IMAGE` 默认指向独立 `refresh-worker` 分支产出的镜像

### 数据目录

Compose 默认挂载：

```text
./data -> /app/data
```

这里会保存：

- SQLite 数据库
- 运行时持久化数据
- 本地生成文件与缓存数据

如果不配置 `DATABASE_URL`，默认使用本地 SQLite。
如果配置了 `DATABASE_URL`，则可以切到 PostgreSQL。

---

## API 兼容接口

| 接口                     | 方法 | 说明                 |
| ------------------------ | ---- | -------------------- |
| `/v1/chat/completions`   | POST | 对话补全（支持流式） |
| `/v1/models`             | GET  | 获取可用模型列表     |
| `/v1/images/generations` | POST | 图片生成（文生图）   |
| `/v1/images/edits`       | POST | 图片编辑（图生图）   |
| `/health`                | GET  | 健康检查             |

调用示例：

```bash
curl http://localhost:7860/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }'
```

> `API_KEY` 在后台系统设置中配置；留空则表示公开访问。

---

## 常用运维命令

```bash
# 查看服务状态
docker compose ps

# 查看主服务日志
docker compose logs -f gemini-api

# 启动主服务
docker compose up -d

# 启动主服务 + refresh-worker
docker compose --profile refresh up -d

# 停止 refresh-worker
docker compose --profile refresh stop refresh-worker

# 更新镜像
docker compose pull && docker compose up -d

# 停止全部服务
docker compose down
```

---

## 功能展示

### 管理系统

<table>
  <tr>
    <td><img src="docs/img/1.png" alt="管理系统 1" /></td>
    <td><img src="docs/img/2.png" alt="管理系统 2" /></td>
  </tr>
  <tr>
    <td><img src="docs/img/3.png" alt="管理系统 3" /></td>
    <td><img src="docs/img/4.png" alt="管理系统 4" /></td>
  </tr>
  <tr>
    <td><img src="docs/img/5.png" alt="管理系统 5" /></td>
    <td><img src="docs/img/6.png" alt="管理系统 6" /></td>
  </tr>
</table>

### 图片效果

<table>
  <tr>
    <td><img src="docs/img/img_1.png" alt="图片效果 1" /></td>
    <td><img src="docs/img/img_2.png" alt="图片效果 2" /></td>
  </tr>
  <tr>
    <td><img src="docs/img/img_3.png" alt="图片效果 3" /></td>
    <td><img src="docs/img/img_4.png" alt="图片效果 4" /></td>
  </tr>
</table>

---


## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yukkcat/gemini-business2api&type=date&legend=top-left)](https://www.star-history.com/#yukkcat/gemini-business2api&type=date&legend=top-left)

如果这个项目对你有帮助，欢迎点一个 ⭐ Star。

---

## 开源协议与使用说明

本项目采用 **Cooperative Non-Commercial License (CNC-1.0)**。

使用边界：

- 允许：个人学习、技术研究、非商业交流
- 禁止：商业用途、盈利性服务、批量滥用、违反 Google / Microsoft 服务条款的使用方式

相关文件：

- 协议文本：[`LICENSE`](LICENSE)
- 中文免责声明：[`docs/DISCLAIMER.md`](docs/DISCLAIMER.md)
- 英文免责声明：[`docs/DISCLAIMER_EN.md`](docs/DISCLAIMER_EN.md)
