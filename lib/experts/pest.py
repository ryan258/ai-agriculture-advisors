"""Pest & Disease Management Expert."""

from .base import Expert


class PestExpert(Expert):
    """Expert in pest and disease management for crops."""

    @property
    def role(self) -> str:
        return "pest"

    @property
    def label(self) -> str:
        return "Pest & Disease Management Expert"

    @property
    def system_prompt(self) -> str:
        return """You are a Pest & Disease Management Expert. Your expertise includes identifying crop diseases, pest life cycles, integrated pest management (IPM), and biological control methods.

Provide a diagnosis if possible and recommend sustainable management strategies, prioritizing non-chemical interventions where appropriate."""
