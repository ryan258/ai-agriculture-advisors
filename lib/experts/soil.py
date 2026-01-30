"""Soil Health Specialist."""

from .base import Expert


class SoilExpert(Expert):
    """Expert in soil health, composition, and regenerative practices."""

    @property
    def role(self) -> str:
        return "soil"

    @property
    def label(self) -> str:
        return "Soil Health Specialist"

    @property
    def system_prompt(self) -> str:
        return """You are a Soil Health Specialist. Your expertise covers soil composition, nutrient management, composting, cover cropping, and regenerative agriculture practices.

Provide detailed, scientific, yet practical responses focusing on improving soil biology, structure, and fertility."""
