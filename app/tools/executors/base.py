"""工具执行器接口与本地执行实现。

执行器只负责调用已经解析出的工具定义，不负责工具发现或高风险审批。
"""

from typing import Any, Protocol

from app.tools.registry.base import ToolDefinition


class ToolExecutor(Protocol):
    """工具执行边界接口。"""

    def execute(self, tool: ToolDefinition, arguments: dict[str, Any]) -> Any:
        """使用标准化参数执行工具并返回原始结果。"""


class LocalToolExecutor:
    """在当前进程内执行 Python handler 的工具执行器。"""

    def execute(self, tool: ToolDefinition, arguments: dict[str, Any]) -> Any:
        """调用工具定义中的本地 handler。"""
        return tool.handler(arguments)
