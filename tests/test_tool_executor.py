"""Tool Executor 边界测试。"""

from app.tools.executors.base import LocalToolExecutor
from app.tools.registry.base import ToolDefinition


def test_local_tool_executor_calls_registered_handler() -> None:
    """LocalToolExecutor 会委托已注册工具 handler 执行。"""
    tool = ToolDefinition(
        name="echo",
        description="Echo a message.",
        handler=lambda arguments: arguments["message"],
    )
    executor = LocalToolExecutor()

    result = executor.execute(tool, {"message": "hello"})

    assert result == "hello"
