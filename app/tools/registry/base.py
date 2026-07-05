from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

ToolHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    handler: ToolHandler
    risk_level: str = "low"
    timeout_seconds: int = 30


class ToolRegistryReader(Protocol):
    def get(self, name: str) -> ToolDefinition:
        """Return a registered tool by name."""

    def list_names(self) -> list[str]:
        """List registered tool names."""


class ToolRegistryWriter(Protocol):
    def register(self, tool: ToolDefinition) -> None:
        """Register a tool definition."""


class ToolRegistry(ToolRegistryReader, ToolRegistryWriter, Protocol):
    """Readable and writable tool registry interface."""


class InMemoryToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list_names(self) -> list[str]:
        return sorted(self._tools)
