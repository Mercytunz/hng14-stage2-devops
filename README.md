# HNG14 Stage 2 — DevOps: Containerised Microservices

A production-ready containerised job processing system with a full CI/CD pipeline.

## Architecture

```
Browser → Frontend (Node.js :3000)
              ↓  HTTP
           API (FastAPI :8000)
              ↓  Redis queue
           Worker (Python)
              ↑
           Redis (internal only)
```

All services communicate over a named Docker internal network (`app-net`). Redis is **not** exposed on the host machine.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Docker | 24.x |
| Docker Compose (plugin) | 2.x |
| Git | any |

No cloud accounts, no paid services required.

---

## Bringing the Stack Up From Scratch

### 1. Clone your fork
```bash
git clone https://github.com/<your-username>/hng14-stage2-devops.git
cd hng14-stage2-devops
```

### 2. Create your `.env` file
```bash
cp .env.example .env
# Edit .env and set a strong REDIS_PASSWORD
nano .env
```

`.env` must contain:
```
REDIS_PASSWORD=your_strong_password_here
APP_ENV=production
FRONTEND_PORT=3000
```

> ⚠️ Never commit `.env` — it is in `.gitignore`

### 3. Build and start all services
```bash
docker compose up -d --build
```

### 4. Verify all services are healthy
```bash
docker compose ps
```

Expected output — all services should show `healthy`:
```
NAME           IMAGE       STATUS          PORTS
stage2-redis   redis:7     Up (healthy)
stage2-api     ...         Up (healthy)    
stage2-worker  ...         Up (healthy)
stage2-frontend ...        Up (healthy)    0.0.0.0:3000->3000/tcp
```

### 5. Open the dashboard
Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

Click **Submit New Job** — the job should move from `queued` → `completed` within a few seconds.

---

## What a Successful Startup Looks Like

```
✔ Container stage2-redis      Healthy
✔ Container stage2-api        Healthy
✔ Container stage2-worker     Started
✔ Container stage2-frontend   Healthy
```

API logs:
```
INFO:     Connected to Redis at redis:6379
INFO:     Application startup complete.
```

Worker logs:
```
INFO:root:Connected to Redis at redis:6379
INFO:root:Processing job <uuid>
INFO:root:Done: <uuid>
```

---

## Stopping the Stack
```bash
docker compose down          # stop and remove containers
docker compose down -v       # also remove volumes (wipes Redis data)
```

---

## Running Tests Locally
```bash
pip install fastapi uvicorn redis pytest pytest-cov httpx
pytest api/tests/ -v --cov=api
```

---

## CI/CD Pipeline

The GitHub Actions pipeline runs on every push and on PRs to `main`, in strict order:

```
lint → test → build → security-scan → integration-test → deploy
```

| Stage | What it does |
|-------|-------------|
| **lint** | flake8 (Python), eslint (JS), hadolint (Dockerfiles) |
| **test** | pytest unit tests with Redis mocked; uploads coverage XML artifact |
| **build** | Builds all 3 images, tags with git SHA + `latest`, pushes to local registry container |
| **security-scan** | Trivy scans all images; fails pipeline on CRITICAL findings; uploads SARIF artifacts |
| **integration-test** | Brings full stack up, submits a job, polls until `completed`, tears down |
| **deploy** | Runs on `main` only; performs scripted rolling update with 60s health-check timeout |

A failure in any stage prevents all subsequent stages from running.

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `REDIS_PASSWORD` | ✅ | Password for Redis authentication |
| `APP_ENV` | ✅ | `production` or `development` |
| `FRONTEND_PORT` | optional | Host port for frontend (default: `3000`) |

---

## Project Structure

```
.
├── api/
│   ├── main.py            # FastAPI application
│   ├── requirements.txt   # Pinned Python deps
│   ├── Dockerfile         # Multi-stage, non-root, healthcheck
│   └── tests/
│       └── test_api.py    # pytest unit tests (Redis mocked)
├── worker/
│   ├── worker.py          # Job processor
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.js             # Express server
│   ├── package.json
│   ├── package-lock.json
│   ├── Dockerfile
│   └── views/
│       └── index.html
├── .github/
│   └── workflows/
│       └── ci-cd.yml      # Full pipeline
├── docker-compose.yml
├── .env.example
├── .gitignore
├── FIXES.md               # All bugs found and fixed
└── README.md
```
