import pytest

from app.agent.runtime.service import AgentRuntime
from app.agent.runtime.types import AgentRunRequest, RunStatus


def test_runtime_returns_successful_result() -> None:
    runtime = AgentRuntime()

    result = runtime.run(AgentRunRequest(input="hello"))

    assert result.status is RunStatus.SUCCEEDED
    assert result.output == "Received: hello"
    assert result.steps_used == 1


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
