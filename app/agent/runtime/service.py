"""Agent Runtime 编排服务。

本模块协调 Planner、Policy、Memory、Tool Registry 和 Tool Executor，不直接依赖
具体模型 SDK、数据库客户端或外部工具实现。
"""

import logging
from uuid import uuid4

from app.agent.planner.base import EchoPlanner, Planner
from app.agent.policy.base import AllowAllPolicyEngine, PolicyEngine
from app.agent.runtime.types import (
    AgentRunRequest,
    AgentRunResult,
    AgentStep,
    PlannerActionType,
    PlannerRequest,
    RunStatus,
    StepStatus,
    StepType,
    TokenUsage,
    ToolCallResult,
)
from app.memory.short_term.base import InMemoryShortTermMemory, ShortTermMemory
from app.observability.token_usage.base import ApproximateTokenCounter, TokenCounter
from app.tools.executors.base import LocalToolExecutor, ToolExecutor
from app.tools.registry.base import InMemoryToolRegistry, ToolRegistryReader

logger = logging.getLogger(__name__)


class AgentRuntime:
    """Agent 执行运行时。

    负责协调 Planner、Policy、Memory、Tool Registry 和 Tool Executor。Runtime 只记录
    可审计元数据，不记录用户原始输入，避免敏感内容进入日志。
    """

    def __init__(
        self,
        planner: Planner | None = None,
        policy: PolicyEngine | None = None,
        memory: ShortTermMemory | None = None,
        tools: ToolRegistryReader | None = None,
        tool_executor: ToolExecutor | None = None,
        token_counter: TokenCounter | None = None,
        max_steps: int = 8,
    ) -> None:
        self.planner = planner or EchoPlanner()
        self.policy = policy or AllowAllPolicyEngine()
        self.memory = memory or InMemoryShortTermMemory()
        self.tools = tools or InMemoryToolRegistry()
        self.tool_executor = tool_executor or LocalToolExecutor()
        self.token_counter = token_counter or ApproximateTokenCounter()
        self.max_steps = max_steps

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """执行一次 Agent Run。

        Raises:
            ValueError: 当输入为空或违反 Run Policy 时抛出。
        """
        run_id = str(uuid4())
        session_id = request.session_id or run_id
        steps: list[AgentStep] = []
        previous_tool_result: ToolCallResult | None = None
        prompt_tokens = self.token_counter.count_text(request.input)
        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            total_tokens=prompt_tokens,
            estimation_method="approximate",
        )
        logger.info(
            "agent_run_started",
            extra={"fields": {"run_id": run_id, "session_id": session_id}},
        )
        self.policy.assert_run_allowed(request)
        self.memory.append(session_id, "user", request.input)

        for step_number in range(1, self.max_steps + 1):
            action = self.planner.plan(
                PlannerRequest(
                    user_input=request.input,
                    session_id=session_id,
                    available_tools=self.tools.list_names(),
                    previous_tool_result=previous_tool_result,
                )
            )

            if action.action_type is PlannerActionType.FINAL_ANSWER:
                output = action.final_answer or ""
                completion_tokens = self.token_counter.count_text(output)
                token_usage.completion_tokens += completion_tokens
                token_usage.total_tokens += completion_tokens
                steps.append(
                    AgentStep(
                        step_id=f"{run_id}:{step_number}",
                        step_type=StepType.FINAL_ANSWER,
                        status=StepStatus.SUCCEEDED,
                        output=output,
                    )
                )
                self.memory.append(session_id, "assistant", output)
                logger.info(
                    "agent_run_succeeded",
                    extra={
                        "fields": {
                            "run_id": run_id,
                            "session_id": session_id,
                            "status": RunStatus.SUCCEEDED,
                            "steps_used": len(steps),
                            "prompt_tokens": token_usage.prompt_tokens,
                            "completion_tokens": token_usage.completion_tokens,
                            "total_tokens": token_usage.total_tokens,
                        }
                    },
                )
                return AgentRunResult(
                    run_id=run_id,
                    status=RunStatus.SUCCEEDED,
                    output=output,
                    steps_used=len(steps),
                    steps=steps,
                    token_usage=token_usage,
                )

            if action.action_type is PlannerActionType.TOOL_CALL and action.tool_call is not None:
                try:
                    tool = self.tools.get(action.tool_call.tool_name)
                    self.policy.assert_tool_allowed(action.tool_call, tool)
                    raw_output = self.tool_executor.execute(tool, action.tool_call.arguments)
                except (KeyError, ValueError) as exc:
                    error_message = str(exc).strip("'")
                    steps.append(
                        AgentStep(
                            step_id=f"{run_id}:{step_number}",
                            step_type=StepType.TOOL,
                            status=StepStatus.FAILED,
                            tool_call=action.tool_call,
                            error_message=error_message,
                        )
                    )
                    logger.warning(
                        "agent_run_failed",
                        extra={
                            "fields": {
                                "run_id": run_id,
                                "session_id": session_id,
                                "status": RunStatus.FAILED,
                                "steps_used": len(steps),
                                "error_type": type(exc).__name__,
                                "prompt_tokens": token_usage.prompt_tokens,
                                "completion_tokens": token_usage.completion_tokens,
                                "total_tokens": token_usage.total_tokens,
                            }
                        },
                    )
                    return AgentRunResult(
                        run_id=run_id,
                        status=RunStatus.FAILED,
                        output="",
                        steps_used=len(steps),
                        steps=steps,
                        token_usage=token_usage,
                        error_message=error_message,
                    )

                previous_tool_result = ToolCallResult(
                    tool_name=action.tool_call.tool_name,
                    output=raw_output,
                )
                steps.append(
                    AgentStep(
                        step_id=f"{run_id}:{step_number}",
                        step_type=StepType.TOOL,
                        status=StepStatus.SUCCEEDED,
                        tool_call=action.tool_call,
                        tool_result=previous_tool_result,
                    )
                )
                continue

            error_message = "Planner returned an invalid action."
            steps.append(
                AgentStep(
                    step_id=f"{run_id}:{step_number}",
                    step_type=StepType.PLANNER,
                    status=StepStatus.FAILED,
                    error_message=error_message,
                )
            )
            return AgentRunResult(
                run_id=run_id,
                status=RunStatus.FAILED,
                output="",
                steps_used=len(steps),
                steps=steps,
                token_usage=token_usage,
                error_message=error_message,
            )

        error_message = "Agent exceeded max_steps before producing a final answer."
        logger.warning(
            "agent_run_failed",
            extra={
                "fields": {
                    "run_id": run_id,
                    "session_id": session_id,
                    "status": RunStatus.FAILED,
                    "steps_used": len(steps),
                    "error_type": "MaxStepsExceeded",
                    "prompt_tokens": token_usage.prompt_tokens,
                    "completion_tokens": token_usage.completion_tokens,
                    "total_tokens": token_usage.total_tokens,
                }
            },
        )
        return AgentRunResult(
            run_id=run_id,
            status=RunStatus.FAILED,
            output="",
            steps_used=len(steps),
            steps=steps,
            token_usage=token_usage,
            error_message=error_message,
        )
