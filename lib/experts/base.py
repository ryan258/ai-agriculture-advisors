"""Base expert class for all domain experts."""

from abc import ABC, abstractmethod
from lib.engine.llm_client import get_llm_client


class Expert(ABC):
    """Abstract base class for all domain experts."""

    @property
    @abstractmethod
    def role(self) -> str:
        """The unique identifier for this expert (e.g., 'agriculture')."""
        pass

    @property
    @abstractmethod
    def label(self) -> str:
        """Human-readable label for this expert."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt that defines this expert's persona."""
        pass

    def build_prompt(self, query: str) -> str:
        """Build the user prompt for a query."""
        return f"User Query: {query}"

    async def query(self, query: str) -> str:
        """
        Query this expert with a user question.

        Args:
            query: The user's question

        Returns:
            The expert's response
        """
        prompt = self.build_prompt(query)
        client = get_llm_client()
        response = await client.generate(prompt, self.system_prompt)
        return response.strip()

    async def contribute_to_discussion(
        self, query: str, transcript: str, round_num: int
    ) -> str:
        """
        Contribute to a round table discussion.

        Args:
            query: The original user query
            transcript: The discussion transcript so far
            round_num: The current round number

        Returns:
            The expert's contribution
        """
        discussion_prompt = f"""You are {self.label} participating in a round table discussion.

Original Query: {query}

{f"Discussion so far:{chr(10)}{transcript}" if transcript else "You are starting the discussion."}

As {self.label}, provide your analysis and insights for round {round_num}.
Build on previous points if applicable, but bring your unique perspective."""

        client = get_llm_client()
        response = await client.generate(discussion_prompt, self.system_prompt)
        return response.strip()
