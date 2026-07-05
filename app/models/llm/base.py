from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Generate a response for a prompt."""
