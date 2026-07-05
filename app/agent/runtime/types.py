"""Agent Runtime 数据契约。

本模块只定义 Runtime 层的输入输出、执行步骤和 Planner 动作，不包含具体执行逻辑。
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    """一次 Agent Run 的整体状态。"""

    CREATED = "created"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    """一次执行步骤的状态。"""

    CREATED = "created"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(StrEnum):
    """Runtime 可审计步骤的类型。"""

    PLANNER = "planner"
    TOOL = "tool"
    FINAL_ANSWER = "final_answer"
    APPROVAL = "approval"


class PlannerActionType(StrEnum):
    """Planner 对 Runtime 发出的下一步动作类型。"""

    FINAL_ANSWER = "final_answer"
    TOOL_CALL = "tool_call"


class AgentRunRequest(BaseModel):
    """发起一次 Agent Run 的请求。"""

    user_id: str = Field(default="local-user")
    session_id: str | None = None
    input: str


class ToolCallRequest(BaseModel):
    """Planner 请求 Runtime 调用工具的结构化动作。"""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallResult(BaseModel):
    """Tool Executor 返回给 Runtime 的标准化工具结果。"""

    tool_name: str
    output: Any


class PlannerRequest(BaseModel):
    """Runtime 传给 Planner 的上下文快照。"""

    user_input: str
    session_id: str
    available_tools: list[str] = Field(default_factory=list)
    previous_tool_result: ToolCallResult | None = None


class PlannerAction(BaseModel):
    """Planner 对下一步动作的结构化决策。"""

    action_type: PlannerActionType
    final_answer: str | None = None
    tool_call: ToolCallRequest | None = None


class AgentStep(BaseModel):
    """一次可审计的 Runtime 执行步骤。"""

    step_id: str
    step_type: StepType
    status: StepStatus
    tool_call: ToolCallRequest | None = None
    tool_result: ToolCallResult | None = None
    output: str | None = None
    error_message: str | None = None


class TokenUsage(BaseModel):
    """一次 Agent Run 的 token 使用量。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimation_method: str = "approximate"


class AgentRunResult(BaseModel):
    """一次 Agent Run 的最终结果。"""

    run_id: str
    status: RunStatus
    output: str
    steps_used: int = 0
    steps: list[AgentStep] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    error_message: str | None = None
