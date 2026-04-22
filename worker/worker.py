import redis
import time
import os
import signal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Bug fix 5 & 6: use env vars for Redis host and password (was hardcoded "localhost" with no auth)
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

# Bug fix 7: handle SIGTERM gracefully (was imported but never used)
running = True


def shutdown(signum, frame):
    global running
    logger.info("Shutdown signal received, finishing current job then exiting...")
    running = False


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)


def process_job(job_id):
    logger.info("Processing job %s", job_id)
    time.sleep(2)
    r.hset(f"job:{job_id}", "status", "completed")
    logger.info("Done: %s", job_id)


# Bug fix 8: queue key was "job" in worker, must match "jobs" used in API
while running:
    job = r.brpop("jobs", timeout=5)
    if job:
        _, job_id = job
        process_job(job_id.decode())

logger.info("Worker exited cleanly.")
