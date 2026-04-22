"""
Unit tests for the API service.
Redis is mocked so no live Redis instance is needed.
Run from the api/ directory: pytest tests/
"""
import pytest
from unittest.mock import MagicMock, patch

mock_redis = MagicMock()
mock_redis.ping.return_value = True

with patch("redis.Redis", return_value=mock_redis):
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import main as main_module
    main_module.r = mock_redis
    from main import app

from fastapi.testclient import TestClient
client = TestClient(app)


def setup_function():
    mock_redis.reset_mock()


def test_health_returns_ok():
    mock_redis.ping.return_value = True
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_job_returns_job_id():
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = 1
    response = client.post("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36


def test_create_job_pushes_to_queue():
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = 1
    response = client.post("/jobs")
    job_id = response.json()["job_id"]
    mock_redis.lpush.assert_called_once_with("jobs", job_id)


def test_create_job_sets_queued_status():
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = 1
    response = client.post("/jobs")
    job_id = response.json()["job_id"]
    mock_redis.hset.assert_called_once_with(f"job:{job_id}", "status", "queued")


def test_get_job_returns_status():
    mock_redis.hget.return_value = b"queued"
    response = client.get("/jobs/test-job-123")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-123"
    assert data["status"] == "queued"


def test_get_job_not_found():
    mock_redis.hget.return_value = None
    response = client.get("/jobs/nonexistent")
    assert response.status_code == 200
    assert response.json() == {"error": "not found"}


def test_get_job_completed_status():
    mock_redis.hget.return_value = b"completed"
    response = client.get("/jobs/done-job-456")
    assert response.json()["status"] == "completed"
