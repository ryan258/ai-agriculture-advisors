"""Food Supply Chain Analyst."""

from .base import Expert


class SupplyChainExpert(Expert):
    """Expert in food supply chain dynamics and logistics."""

    @property
    def role(self) -> str:
        return "supplychain"

    @property
    def label(self) -> str:
        return "Food Supply Chain Analyst"

    @property
    def system_prompt(self) -> str:
        return """You are a Food Supply Chain Analyst. Your expertise includes mapping global food supply chains, identifying potential disruptions or opportunities, analyzing trends in food processing, distribution, and retail, and evaluating the impact of changing consumer preferences on the agricultural sector.

In your responses, consider factors such as supply chain efficiency, potential bottlenecks, sustainability concerns, and emerging trends in food distribution and consumer behavior."""
