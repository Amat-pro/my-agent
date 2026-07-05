from fastapi.testclient import TestClient
from pytest import LogCaptureFixture

from app.main import create_app


def test_health_endpoint() -> None:
    """健康检查接口应返回 ok。"""
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint_logs_event(caplog: LogCaptureFixture) -> None:
    """健康检查接口应输出测试日志。"""
    client = TestClient(create_app())

    with caplog.at_level("INFO", logger="app.api.routes.health"):
        client.get("/health")

    assert "health_check_requested" in [record.getMessage() for record in caplog.records]
