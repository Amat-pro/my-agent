"""Planner 接口与本地确定性实现。

Planner 只负责决定 Runtime 下一步动作，不直接执行工具、写记忆或访问外部模型。
"""

from typing import Protocol

from app.agent.runtime.types import (
    PlannerAction,
    PlannerActionType,
    PlannerRequest,
    ToolCallRequest,
)


class Planner(Protocol):
    """Agent 规划器接口。"""

    def plan(self, request: PlannerRequest) -> PlannerAction:
        """根据 Runtime 上下文返回下一步动作。"""


class EchoPlanner:
    """返回最终回答的最小 Planner 实现。"""

    def plan(self, request: PlannerRequest) -> PlannerAction:
        """生成回显式最终回答，便于本地开发和测试。"""
        return PlannerAction(
            action_type=PlannerActionType.FINAL_ANSWER,
            final_answer=f"Received: {request.user_input}",
        )


class KeywordToolPlanner:
    """根据本地关键字触发工具调用的测试 Planner。

    支持输入格式 `tool:<tool_name> message=<value>`，用于在不接入真实 LLM 的情况下
    验证 Runtime 的工具调用闭环。
    """

    def plan(self, request: PlannerRequest) -> PlannerAction:
        """把约定格式的用户输入转换为工具调用，否则返回最终回答。"""
        if request.previous_tool_result is not None:
            return PlannerAction(
                action_type=PlannerActionType.FINAL_ANSWER,
                final_answer=str(request.previous_tool_result.output),
            )

        if request.user_input.startswith("tool:"):
            command, _, raw_message = request.user_input.partition(" message=")
            tool_name = command.removeprefix("tool:").strip()
            return PlannerAction(
                action_type=PlannerActionType.TOOL_CALL,
                tool_call=ToolCallRequest(
                    tool_name=tool_name,
                    arguments={"message": raw_message},
                ),
            )

        return PlannerAction(
            action_type=PlannerActionType.FINAL_ANSWER,
            final_answer=f"Received: {request.user_input}",
        )
