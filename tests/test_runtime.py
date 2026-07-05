import pytest

from app.agent.planner.base import KeywordToolPlanner
from app.agent.runtime.service import AgentRuntime
from app.agent.runtime.types import (
    AgentRunRequest,
    PlannerAction,
    PlannerActionType,
    PlannerRequest,
    RunStatus,
    StepStatus,
    StepType,
    ToolCallRequest,
)
from app.tools.registry.base import InMemoryToolRegistry, ToolDefinition


class EndlessToolPlanner:
    """永远请求下一次工具调用的测试 Planner。"""

    def plan(self, request: PlannerRequest) -> PlannerAction:
        """返回同一个工具调用，用于验证 max_steps 保护。"""
        return PlannerAction(
            action_type=PlannerActionType.TOOL_CALL,
            tool_call=ToolCallRequest(tool_name="echo", arguments={"message": "again"}),
        )


def test_runtime_returns_successful_result() -> None:
    runtime = AgentRuntime()

    result = runtime.run(AgentRunRequest(input="hello"))

    assert result.status is RunStatus.SUCCEEDED
    assert result.output == "Received: hello"
    assert result.steps_used == 1


def test_runtime_result_contains_structured_steps() -> None:
    """Runtime 返回普通最终回答时，应包含可审计的结构化步骤。"""
    runtime = AgentRuntime()

    result = runtime.run(AgentRunRequest(input="hello"))

    assert result.status is RunStatus.SUCCEEDED
    assert result.output == "Received: hello"
    assert result.steps_used == 1
    assert result.error_message is None
    assert len(result.steps) == 1
    assert result.steps[0].step_type == StepType.FINAL_ANSWER
    assert result.steps[0].status == StepStatus.SUCCEEDED


def test_runtime_executes_tool_call_and_returns_final_answer() -> None:
    """Runtime 通过 Registry、Policy、Executor 执行 Planner 发起的工具调用。"""
    registry = InMemoryToolRegistry()
    registry.register(
        ToolDefinition(
            name="echo",
            description="Echo a message.",
            handler=lambda arguments: arguments["message"],
        )
    )
    runtime = AgentRuntime(planner=KeywordToolPlanner(), tools=registry)

    result = runtime.run(AgentRunRequest(input="tool:echo message=hello"))

    assert result.status is RunStatus.SUCCEEDED
    assert result.output == "hello"
    assert result.steps_used == 2
    assert [step.step_type for step in result.steps] == [StepType.TOOL, StepType.FINAL_ANSWER]
    assert result.steps[0].tool_call is not None
    assert result.steps[0].tool_call.tool_name == "echo"
    assert result.steps[0].tool_result is not None
    assert result.steps[0].tool_result.output == "hello"


def test_runtime_returns_failed_result_for_unknown_tool() -> None:
    """未知工具应被转换为结构化失败结果，而不是泄漏 KeyError。"""
    runtime = AgentRuntime(planner=KeywordToolPlanner())

    result = runtime.run(AgentRunRequest(input="tool:missing message=hello"))

    assert result.status is RunStatus.FAILED
    assert result.output == ""
    assert result.error_message == "Unknown tool: missing"
    assert result.steps_used == 1
    assert result.steps[0].status is StepStatus.FAILED
    assert result.steps[0].step_type is StepType.TOOL


def test_runtime_fails_when_max_steps_is_exceeded() -> None:
    """Runtime 会终止无法产出最终回答的工具调用循环。"""
    registry = InMemoryToolRegistry()
    registry.register(
        ToolDefinition(
            name="echo",
            description="Echo a message.",
            handler=lambda arguments: arguments["message"],
        )
    )
    runtime = AgentRuntime(planner=EndlessToolPlanner(), tools=registry, max_steps=2)

    result = runtime.run(AgentRunRequest(input="loop"))

    assert result.status is RunStatus.FAILED
    assert result.output == ""
    assert result.steps_used == 2
    assert result.error_message == "Agent exceeded max_steps before producing a final answer."


def test_runtime_result_includes_token_usage_estimate() -> None:
    """Runtime 在接入真实模型 usage 前暴露近似 token 使用量。"""
    runtime = AgentRuntime()

    result = runtime.run(AgentRunRequest(input="hello world"))

    assert result.token_usage.prompt_tokens == 2
    assert result.token_usage.completion_tokens == 3
    assert result.token_usage.total_tokens == 5
    assert result.token_usage.estimation_method == "approximate"


def test_runtime_logs_run_metadata(caplog: pytest.LogCaptureFixture) -> None:
    """Runtime 日志只记录 Run 元数据，不记录用户原始输入。"""
    runtime = AgentRuntime()

    with caplog.at_level("INFO", logger="app.agent.runtime.service"):
        runtime.run(AgentRunRequest(input="secret user text"))

    messages = [record.getMessage() for record in caplog.records]
    assert "agent_run_started" in messages
    assert "agent_run_succeeded" in messages
    assert all("secret user text" not in record.getMessage() for record in caplog.records)


def test_runtime_rejects_empty_input() -> None:
    runtime = AgentRuntime()

    with pytest.raises(ValueError, match="must not be empty"):
        runtime.run(AgentRunRequest(input=" "))
