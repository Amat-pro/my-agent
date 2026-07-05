"""Agent Runtime 编排服务。"""

import logging
from uuid import uuid4

from app.agent.planner.base import EchoPlanner, Planner
from app.agent.policy.base import AllowAllPolicyEngine, PolicyEngine
from app.agent.runtime.types import AgentRunRequest, AgentRunResult, RunStatus
from app.memory.short_term.base import InMemoryShortTermMemory, ShortTermMemory
from app.tools.registry.base import InMemoryToolRegistry, ToolRegistryReader

logger = logging.getLogger(__name__)


class AgentRuntime:
    """Agent 执行运行时。

    负责协调 Planner、Policy、Memory 和 Tool Registry。Runtime 只记录可审计的
    元数据，不记录用户原始输入，避免敏感内容进入日志。
    """

    def __init__(
        self,
        planner: Planner | None = None,
        policy: PolicyEngine | None = None,
        memory: ShortTermMemory | None = None,
        tools: ToolRegistryReader | None = None,
        max_steps: int = 8,
    ) -> None:
        self.planner = planner or EchoPlanner()
        self.policy = policy or AllowAllPolicyEngine()
        self.memory = memory or InMemoryShortTermMemory()
        self.tools = tools or InMemoryToolRegistry()
        self.max_steps = max_steps

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """执行一次 Agent Run。

        Args:
            request: Agent Run 请求。

        Returns:
            Agent Run 执行结果。
        """
        run_id = str(uuid4())
        session_id = request.session_id or run_id
        logger.info(
            "agent_run_started",
            extra={"fields": {"run_id": run_id, "session_id": session_id}},
        )
        self.policy.assert_run_allowed(request)
        self.memory.append(session_id, "user", request.input)
        output = self.planner.plan(request.input)
        self.memory.append(session_id, "assistant", output)
        logger.info(
            "agent_run_succeeded",
            extra={
                "fields": {
                    "run_id": run_id,
                    "session_id": session_id,
                    "status": RunStatus.SUCCEEDED,
                    "steps_used": 1,
                }
            },
        )
        return AgentRunResult(
            run_id=run_id,
            status=RunStatus.SUCCEEDED,
            output=output,
            steps_used=1,
        )
