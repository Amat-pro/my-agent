"""Policy Engine 接口与默认实现。

PolicyEngine 负责在 Runtime 执行 Run 或工具调用前做治理检查。
"""

from typing import Protocol

from app.agent.runtime.types import AgentRunRequest, ToolCallRequest
from app.tools.registry.base import ToolDefinition


class PolicyEngine(Protocol):
    """Agent Runtime 治理检查接口。"""

    def assert_run_allowed(self, request: AgentRunRequest) -> None:
        """当 Run 请求违反策略时抛出异常。"""

    def assert_tool_allowed(self, request: ToolCallRequest, tool: ToolDefinition) -> None:
        """当工具调用违反策略时抛出异常。"""


class AllowAllPolicyEngine:
    """只拒绝空输入的本地默认策略。"""

    def assert_run_allowed(self, request: AgentRunRequest) -> None:
        """校验 Run 是否允许执行。"""
        if not request.input.strip():
            raise ValueError("Agent input must not be empty.")

    def assert_tool_allowed(self, request: ToolCallRequest, tool: ToolDefinition) -> None:
        """默认允许所有已注册工具调用。"""
