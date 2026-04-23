<p align="center">
  <img src="../docs/logo.svg" width="120" alt="Gemini Business2API logo" />
</p>
<h1 align="center">Gemini Business2API</h1>
<p align="center">Gemini Business → OpenAI-compatible API gateway</p>
<p align="center">
  <a href="../README.md">简体中文</a> | <strong>English</strong>
</p>
<p align="center"><img src="https://img.shields.io/badge/License-CNC--1.0-red.svg" /> <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white" /> <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white" /> <img src="https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white" /> <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white" /></p>

<p align="center">Focused on the 2API main service, admin panel, and optional refresh-worker.</p>

---

## Project Positioning

Gemini Business2API turns [Gemini Business](https://business.google.com) into an **OpenAI-compatible API gateway** with a built-in admin panel for managing accounts, settings, image / video features, and runtime status.

The current mainline focuses on only three things:

1. **2API main service**
2. **Admin panel**
3. **Optional refresh-worker**

Registration tools, experimental refresh flows, and older script-first deployment paths are no longer the default mainline workflow.

---

## Core Capabilities

- ✅ OpenAI-compatible API for common OpenAI clients and middleware
- ✅ Multi-account scheduling with rotation and availability switching
- ✅ Account management UI with import / export / edit / batch actions / filtering
- ✅ Multimodal support for text, files, images, and video-related features
- ✅ Image generation and image editing with Base64 or URL output
- ✅ Video generation with unified output control
- ✅ Centralized system settings for proxy, mail, refresh, and output behavior
- ✅ Dashboard / monitoring / logs for service visibility
- ✅ SQLite / PostgreSQL support for local persistence or shared deployments
- ✅ Optional refresh-worker enabled independently via Docker Compose profile

---

## Deployment Layout

```text
docker-compose.yml
├─ gemini-api
│  ├─ runs the main 2API service
│  ├─ runs the admin panel
│  ├─ exposes 7860
│  └─ mounts ./data:/app/data
│
└─ refresh-worker (optional)
   ├─ disabled by default
   ├─ enabled with profile refresh
   ├─ does not expose public business APIs
   ├─ reads the same ./data volume
   └─ handles account refresh work
```

Startup:

- 2API only: `docker compose up -d`
- 2API + refresh-worker: `docker compose --profile refresh up -d`

Notes:

- `refresh-worker` is maintained in the separate `refresh-worker` branch
- that branch has its own GitHub Actions workflow to build and publish the refresh-worker Docker image
- the mainline `docker-compose.yml` connects to that image through `REFRESH_WORKER_IMAGE` / `--profile refresh`

---

## Quick Start

### Option 1: Docker Compose (Recommended)

Supports ARM64 / AMD64.

```bash
git clone https://github.com/yukkcat/gemini-business2api.git
cd gemini-business2api
cp .env.example .env
# Edit .env and set at least ADMIN_KEY

docker compose up -d
```

To enable the refresh-worker:

```bash
docker compose --profile refresh up -d
```

---

### Option 2: Interactive Installer (Linux / macOS / WSL / Git Bash)

The mainline now uses `deploy/install.sh`.

```bash
curl -fsSL https://raw.githubusercontent.com/yukkcat/gemini-business2api/main/deploy/install.sh | sudo bash
```

Enable refresh-worker:

```bash
curl -fsSL https://raw.githubusercontent.com/yukkcat/gemini-business2api/main/deploy/install.sh | sudo bash -s -- --with-refresh
```

The installer supports two paths:

- Docker deployment
- Local Python startup for development / debugging

You can also run it inside the repository:

```bash
bash deploy/install.sh
```

---

### Option 3: Local Python Development

Recommended for development and local debugging.

```bash
git clone https://github.com/yukkcat/gemini-business2api.git
cd gemini-business2api
bash deploy/install.sh --mode python
```

The script guides you through:

- Python 3.11 / uv check
- `.venv` creation or reuse
- Python dependency installation
- frontend build
- `.env` initialization
- optional immediate `python main.py` startup

---

### Access URLs

- Admin panel: `http://localhost:7860/`
- OpenAI-compatible endpoint: `http://localhost:7860/v1/chat/completions`
- Health check: `http://localhost:7860/health`

---

## Configuration & Data Boundaries

### Key `.env` entries

```env
ADMIN_KEY=your-admin-login-key
# PORT=7860
# DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
# REFRESH_WORKER_IMAGE=cooooookk/gemini-refresh-worker:latest
# REFRESH_HEALTH_PORT=8080
```

Where:

- the `gemini-business2api` main image is built from the mainline branch
- `REFRESH_WORKER_IMAGE` points by default to the image produced from the separate `refresh-worker` branch

### Data directory

Compose mounts:

```text
./data -> /app/data
```

This stores:

- SQLite database
- persistent runtime data
- locally generated files and cache data

If `DATABASE_URL` is not set, the project uses local SQLite by default.
If `DATABASE_URL` is set, you can switch to PostgreSQL.

---

## API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/v1/chat/completions` | POST | Chat completions with streaming support |
| `/v1/models` | GET | List available models |
| `/v1/images/generations` | POST | Text-to-image generation |
| `/v1/images/edits` | POST | Image editing / image-to-image |
| `/health` | GET | Health check |

Example:

```bash
curl http://localhost:7860/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

> `API_KEY` is configured in the admin panel system settings. Leave it empty for public access.

---

## Common Operations

```bash
# Service status
docker compose ps

# Main service logs
docker compose logs -f gemini-api

# Start main service
docker compose up -d

# Start main service + refresh-worker
docker compose --profile refresh up -d

# Stop refresh-worker
docker compose --profile refresh stop refresh-worker

# Update images
docker compose pull && docker compose up -d

# Stop everything
docker compose down
```

---

## Screenshots

### Admin System

<table>
  <tr>
    <td><img src="img/1.png" alt="Admin System 1" /></td>
    <td><img src="img/2.png" alt="Admin System 2" /></td>
  </tr>
  <tr>
    <td><img src="img/3.png" alt="Admin System 3" /></td>
    <td><img src="img/4.png" alt="Admin System 4" /></td>
  </tr>
  <tr>
    <td><img src="img/5.png" alt="Admin System 5" /></td>
    <td><img src="img/6.png" alt="Admin System 6" /></td>
  </tr>
</table>

### Image Effects

<table>
  <tr>
    <td><img src="img/img_1.png" alt="Image Effects 1" /></td>
    <td><img src="img/img_2.png" alt="Image Effects 2" /></td>
  </tr>
  <tr>
    <td><img src="img/img_3.png" alt="Image Effects 3" /></td>
    <td><img src="img/img_4.png" alt="Image Effects 4" /></td>
  </tr>
</table>

---

## Community

Join the QQ group:

- [https://qm.qq.com/q/yegwCqJisS](https://qm.qq.com/q/yegwCqJisS)

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yukkcat/gemini-business2api&type=date&legend=top-left)](https://www.star-history.com/#yukkcat/gemini-business2api&type=date&legend=top-left)

If this project helps you, please give it a ⭐ Star.

---

## License & Usage Notes

This project uses the **Cooperative Non-Commercial License (CNC-1.0)**.

Usage boundaries:

- Allowed: personal learning, technical research, non-commercial sharing
- Prohibited: commercial usage, paid services, bulk abuse, or usage that violates Google / Microsoft terms of service

Related files:

- License text: [`../LICENSE`](../LICENSE)
- Chinese disclaimer: [`DISCLAIMER.md`](DISCLAIMER.md)
- English disclaimer: [`DISCLAIMER_EN.md`](DISCLAIMER_EN.md)
