"""Planner 行为测试。"""

from app.agent.planner.base import EchoPlanner, KeywordToolPlanner
from app.agent.runtime.types import PlannerActionType, PlannerRequest


def test_echo_planner_returns_final_answer_action() -> None:
    """EchoPlanner 返回结构化最终回答动作。"""
    planner = EchoPlanner()

    action = planner.plan(
        PlannerRequest(user_input="hello", session_id="session-1", available_tools=[])
    )

    assert action.action_type is PlannerActionType.FINAL_ANSWER
    assert action.final_answer == "Received: hello"
    assert action.tool_call is None


def test_keyword_tool_planner_returns_tool_call_action() -> None:
    """KeywordToolPlanner 将约定前缀输入转换为工具调用动作。"""
    planner = KeywordToolPlanner()

    action = planner.plan(
        PlannerRequest(
            user_input="tool:echo message=hello",
            session_id="session-1",
            available_tools=["echo"],
        )
    )

    assert action.action_type is PlannerActionType.TOOL_CALL
    assert action.final_answer is None
    assert action.tool_call is not None
    assert action.tool_call.tool_name == "echo"
    assert action.tool_call.arguments == {"message": "hello"}
