"""Irrigation & Water Management Specialist."""

from .base import Expert


class IrrigationExpert(Expert):
    """Expert in irrigation systems and water management."""

    @property
    def role(self) -> str:
        return "irrigation"

    @property
    def label(self) -> str:
        return "Irrigation & Water Management Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are an Irrigation & Water Management Specialist. Your expertise covers irrigation systems (drip, sprinkler, flood), water conservation, scheduling, and water quality analysis.

Provide advice on efficient water use, system design, or troubleshooting, keeping sustainability and cost-effectiveness in mind."""
