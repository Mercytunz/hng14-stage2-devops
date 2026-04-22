from fastapi import FastAPI
import redis
import uuid
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Bug fix 1 & 2: use env vars for Redis host and password (was hardcoded "localhost" with no auth)
def get_redis_client():
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", 6379))
    password = os.getenv("REDIS_PASSWORD", "") or None
    for attempt in range(10):
        try:
            client = redis.Redis(host=host, port=port, password=password, socket_connect_timeout=2)
            client.ping()
            logger.info("Connected to Redis at %s:%s", host, port)
            return client
        except Exception as e:
            logger.warning("Redis not ready (attempt %d/10): %s", attempt + 1, e)
            time.sleep(2)
    raise RuntimeError("Could not connect to Redis after 10 attempts")

r = get_redis_client()


@app.get("/health")
def health():
    try:
        r.ping()
        return {"status": "ok"}
    except Exception:
        return {"status": "error"}, 503


@app.post("/jobs")
def create_job():
    job_id = str(uuid.uuid4())
    r.lpush("jobs", job_id)
    r.hset(f"job:{job_id}", "status", "queued")
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    status = r.hget(f"job:{job_id}", "status")
    if not status:
        return {"error": "not found"}
    return {"job_id": job_id, "status": status.decode()}
