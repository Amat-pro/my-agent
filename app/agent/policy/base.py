from typing import Protocol

from app.agent.runtime.types import AgentRunRequest


class PolicyEngine(Protocol):
    def assert_run_allowed(self, request: AgentRunRequest) -> None:
        """Raise when a run violates policy."""


class AllowAllPolicyEngine:
    def assert_run_allowed(self, request: AgentRunRequest) -> None:
        if not request.input.strip():
            raise ValueError("Agent input must not be empty.")
