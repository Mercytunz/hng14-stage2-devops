# FIXES.md — Bug Report & Resolution Log

## Bug 1 — `api/main.py` line 8: Redis hardcoded to `localhost`
**File:** `api/main.py`  
**Line:** 8  
**Problem:** `redis.Redis(host="localhost", port=6379)` — hardcoded `localhost` will not resolve inside a Docker container. The Redis service will be on a separate container reachable by its service name (e.g. `redis`), not `localhost`.  
**Fix:** Changed to read host from environment variable:
```python
r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", 6379)), password=os.getenv("REDIS_PASSWORD", ""))
```

---

## Bug 2 — `api/main.py` line 8: Redis connection ignores authentication
**File:** `api/main.py`  
**Line:** 8  
**Problem:** Redis client is created without a `password` argument. The `.env` file sets `REDIS_PASSWORD=supersecretpassword123`, but this is never passed to the Redis client, so every connection will be refused with `NOAUTH` when Redis requires authentication.  
**Fix:** Added `password=os.getenv("REDIS_PASSWORD", "")` to the Redis constructor (combined with Bug 1 fix above).

---

## Bug 3 — `api/.env` committed to the repository
**File:** `api/.env`  
**Line:** entire file  
**Problem:** A `.env` file containing real credentials (`REDIS_PASSWORD=supersecretpassword123`) is committed to the repository. Secrets must never be in version control.  
**Fix:** Added `api/.env` and `**/.env` to `.gitignore`. Created `.env.example` with placeholder values. Removed `api/.env` from tracking via `git rm --cached api/.env`.

---

## Bug 4 — `api/.env` line 2: malformed environment variable (no newline between vars)
**File:** `api/.env`  
**Line:** 2  
**Problem:** `APP_ENV=production` is concatenated directly to the previous line with no newline: `REDIS_PASSWORD=supersecretpassword123APP_ENV=production`. This makes `APP_ENV` unparseable and corrupts `REDIS_PASSWORD`.  
**Fix:** Ensured each variable is on its own line in `.env.example` and in runtime environment injection.

---

## Bug 5 — `worker/worker.py` line 5: Redis hardcoded to `localhost`
**File:** `worker/worker.py`  
**Line:** 5  
**Problem:** Same issue as Bug 1 — `redis.Redis(host="localhost", port=6379)` will fail inside Docker as `localhost` does not resolve to the Redis container.  
**Fix:** Changed to use environment variables:
```python
r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", 6379)), password=os.getenv("REDIS_PASSWORD", ""))
```

---

## Bug 6 — `worker/worker.py` line 5: Redis connection ignores authentication
**File:** `worker/worker.py`  
**Line:** 5  
**Problem:** Same as Bug 2 — no `password` passed to Redis client in the worker.  
**Fix:** Added `password=os.getenv("REDIS_PASSWORD", "")` (combined with Bug 5 fix).

---

## Bug 7 — `worker/worker.py`: No graceful shutdown handling
**File:** `worker/worker.py`  
**Line:** entire file  
**Problem:** The worker imports `signal` but never uses it. The `while True` loop has no signal handler, so `SIGTERM` from Docker will kill the process abruptly, potentially mid-job, leaving jobs stuck in a `queued` state forever.  
**Fix:** Added SIGTERM/SIGINT handlers to set a `running = False` flag so the loop exits cleanly after finishing any in-progress job.

---

## Bug 8 — `worker/worker.py`: Queue key mismatch with API
**File:** `worker/worker.py`  
**Line:** 10  
**Problem:** The worker pops from the queue using `r.brpop("job", ...)` — it reads from the **right** end (`brpop`). The API pushes with `r.lpush("job", job_id)` — it pushes to the **left** end. `lpush` + `brpop` = LIFO (stack), not FIFO (queue). While functionally it still processes jobs, the inconsistency means the last submitted job is processed first. More critically, if this was ever changed to `rpush` on one side without updating the other, all jobs would be lost.  
**Fix:** Standardised to `lpush` (API) + `brpop` (worker) which forms a proper FIFO queue — documented clearly in code comments.

---

## Bug 9 — `frontend/app.js` line 5: API URL hardcoded to `localhost`
**File:** `frontend/app.js`  
**Line:** 5  
**Problem:** `const API_URL = "http://localhost:8000"` — inside a Docker container the API service is not on `localhost`, it is reachable by the Docker Compose service name (e.g. `api`).  
**Fix:** Changed to read from environment variable:
```javascript
const API_URL = process.env.API_URL || "http://api:8000";
```

---

## Bug 10 — `api/requirements.txt`: No pinned versions
**File:** `api/requirements.txt`  
**Line:** 1-3  
**Problem:** `fastapi`, `uvicorn`, and `redis` have no version pins. Unpinned dependencies break reproducibility — a future `pip install` may pull incompatible versions.  
**Fix:** Pinned to known-compatible versions: `fastapi==0.111.0`, `uvicorn[standard]==0.29.0`, `redis==5.0.4`.

---

## Bug 11 — `worker/requirements.txt`: No pinned versions
**File:** `worker/requirements.txt`  
**Line:** 1  
**Problem:** `redis` has no version pin.  
**Fix:** Pinned to `redis==5.0.4`.

---

## Bug 12 — `api/main.py`: No startup health / Redis connection check
**File:** `api/main.py`  
**Problem:** The Redis client is created at module load time with no retry logic. If the API container starts before Redis is fully ready, all requests fail immediately with a connection error and the container must be restarted manually.  
**Fix:** Wrapped Redis client initialisation in a retry loop with exponential back-off, and added a `/health` endpoint for Docker HEALTHCHECK.

---

## Bug 13 — `frontend/package.json`: Missing `package-lock.json` / no `engines` field
**File:** `frontend/package.json`  
**Problem:** No `engines` field specifies required Node.js version, leading to non-deterministic builds across Node versions. No lock file present.  
**Fix:** Added `"engines": {"node": ">=18"}` and ensured `npm ci` is used in the Dockerfile (lock file generated and committed).
