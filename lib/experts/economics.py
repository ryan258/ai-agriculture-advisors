"""Agricultural Economics Advisor."""

from .base import Expert


class EconomicsExpert(Expert):
    """Expert in agricultural economics and financial planning."""

    @property
    def role(self) -> str:
        return "economics"

    @property
    def label(self) -> str:
        return "Agricultural Economics Advisor"

    @property
    def system_prompt(self) -> str:
        return """You are an Agricultural Economics Advisor. Your expertise covers farm budgeting, market analysis, crop insurance, subsidies, and financial planning for agribusinesses.

Provide financial analysis, risk assessment, or economic advice to help the user make profitable and sustainable business decisions."""
