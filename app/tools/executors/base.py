from typing import Any, Protocol

from app.tools.registry.base import ToolDefinition


class ToolExecutor(Protocol):
    def execute(self, tool: ToolDefinition, arguments: dict[str, Any]) -> Any:
        """Execute a tool with normalized arguments."""


class LocalToolExecutor:
    def execute(self, tool: ToolDefinition, arguments: dict[str, Any]) -> Any:
        return tool.handler(arguments)
