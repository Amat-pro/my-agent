from enum import StrEnum

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunRequest(BaseModel):
    user_id: str = Field(default="local-user")
    session_id: str | None = None
    input: str


class AgentRunResult(BaseModel):
    run_id: str
    status: RunStatus
    output: str
    steps_used: int = 0
