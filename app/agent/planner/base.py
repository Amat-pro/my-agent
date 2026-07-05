from typing import Protocol


class Planner(Protocol):
    def plan(self, user_input: str) -> str:
        """Return the next response or action plan for a user input."""


class EchoPlanner:
    def plan(self, user_input: str) -> str:
        return f"Received: {user_input}"
