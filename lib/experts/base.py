"""Base expert class for all domain experts."""

from abc import ABC, abstractmethod
from lib.engine.llm_client import get_llm_client
from lib.experts.response_format import (
    ACCESSIBILITY_CAPABILITY_INSTRUCTIONS,
    COMPACT_ENDING_INSTRUCTIONS,
)


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
        self,
        query: str,
        transcript: str,
        round_num: int,
        *,
        compact_roundtable: bool = False,
    ) -> str:
        """
        Contribute to a round table discussion.

        Args:
            query: The original user query
            transcript: The discussion transcript so far
            round_num: The current round number
            compact_roundtable: Whether to keep this turn concise and leave the Decision Check to the moderator

        Returns:
            The expert's contribution
        """
        discussion_prompt = f"""You are {self.label} participating in a round table discussion.

Original Query: {query}

{("Discussion so far:\n" + transcript) if transcript else "You are starting the discussion."}

As {self.label}, provide your analysis and insights for round {round_num}.
"""
        system_prompt = self.system_prompt
        if (
            self.role.startswith("accessibility_effort_")
            and ACCESSIBILITY_CAPABILITY_INSTRUCTIONS not in system_prompt
        ):
            # Old captured definitions retain their profile; current discussion rules still apply.
            system_prompt += f"\n\n{ACCESSIBILITY_CAPABILITY_INSTRUCTIONS}"
        if compact_roundtable:
            system_prompt = system_prompt.replace(
                COMPACT_ENDING_INSTRUCTIONS, ""
            ).strip()
            discussion_prompt += """This panel uses a compact roundtable format.
Give at most two short, role-specific bullets (about 60 words total). If the query asks for a
usable artifact, provide your part of it directly instead of recommending that someone create it.
On round 1, give your strongest distinct contribution. On later rounds, add only a material point
not already in the discussion; do not repeat prior recommendations, risks, unknowns, or questions.
If you have no new point, say so briefly. Do not ask the user questions or add a Decision Check;
the moderator will consolidate the discussion and leave at most one decision for the user."""
        else:
            discussion_prompt += "Build on previous points if applicable, but bring your unique perspective."

        client = get_llm_client()
        response = await client.generate(discussion_prompt, system_prompt)
        return response.strip()
