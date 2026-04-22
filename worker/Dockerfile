# ---- Build stage ----
FROM python:3.12-alpine AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-alpine

WORKDIR /app

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /install /usr/local
COPY worker.py .

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import redis, os; r=redis.Redis(host=os.getenv('REDIS_HOST','redis'),password=os.getenv('REDIS_PASSWORD','') or None); r.ping()"

CMD ["python", "-u", "worker.py"]
