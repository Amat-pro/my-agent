"""JSON 日志配置。

本模块提供应用内部日志和 Uvicorn 日志可共用的 formatter，保证控制台输出为
一行一个 JSON 对象，便于后续接入日志采集、Trace 和检索系统。
"""

import json
import logging
from datetime import UTC, datetime
from logging import LogRecord
from typing import Any


class JsonFormatter(logging.Formatter):
    """将标准 logging 记录格式化为 JSON 行。"""

    def format(self, record: LogRecord) -> str:
        """序列化一条日志记录。

        Args:
            record: Python logging 传入的原始日志记录。

        Returns:
            JSON 字符串，包含时间、级别、logger 名称和消息。
        """
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }

        if record.name == "uvicorn.access":
            payload.update(self._format_uvicorn_access(record))
        else:
            payload["message"] = record.getMessage()

        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(fields)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        return json.dumps(payload, ensure_ascii=False)

    def _format_uvicorn_access(self, record: LogRecord) -> dict[str, Any]:
        """拆分 Uvicorn access log 的结构化字段。

        Uvicorn access logger 的参数顺序通常是：
        `(client_addr, method, full_path, http_version, status_code)`。
        当参数形态不符合预期时，回退到原始消息，避免丢日志。
        """
        if isinstance(record.args, tuple) and len(record.args) >= 5:
            client_addr, method, path, http_version, status_code = record.args[:5]
            try:
                normalized_status_code = int(str(status_code))
            except ValueError:
                return {"message": record.getMessage()}

            return {
                "message": "http_request",
                "client_addr": client_addr,
                "http_method": method,
                "path": path,
                "http_version": http_version,
                "status_code": normalized_status_code,
            }

        return {"message": record.getMessage()}


def configure_logging(level: int = logging.INFO) -> None:
    """配置应用内部日志为 JSON 控制台输出。

    Args:
        level: 根 logger 的日志级别。
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    has_project_handler = any(
        getattr(handler, "_my_agent_json_handler", False) for handler in root_logger.handlers
    )
    if has_project_handler:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler._my_agent_json_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(handler)
