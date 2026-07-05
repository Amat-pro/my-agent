"""日志配置测试。"""

import json
import logging

from app.observability.logging.config import JsonFormatter


def test_json_formatter_outputs_json_log() -> None:
    """JsonFormatter 应输出可解析的 JSON 日志行。"""
    record = logging.LogRecord(
        name="tests.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "tests.logger"
    assert payload["message"] == "hello world"
    assert "timestamp" in payload


def test_json_formatter_merges_structured_fields() -> None:
    """JsonFormatter 应合并明确传入的结构化字段。"""
    record = logging.LogRecord(
        name="tests.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="agent_run_succeeded",
        args=(),
        exc_info=None,
    )
    record.fields = {"run_id": "run-1", "steps_used": 1}  # type: ignore[attr-defined]

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "agent_run_succeeded"
    assert payload["run_id"] == "run-1"
    assert payload["steps_used"] == 1


def test_json_formatter_splits_uvicorn_access_log() -> None:
    """JsonFormatter 应把 Uvicorn access log 拆成结构化字段。"""
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:46388", "GET", "/health", "1.1", 200),
        exc_info=None,
    )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "http_request"
    assert payload["client_addr"] == "127.0.0.1:46388"
    assert payload["http_method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["http_version"] == "1.1"
    assert payload["status_code"] == 200
