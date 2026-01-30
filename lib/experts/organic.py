"""Organic Farming Consultant."""

from .base import Expert


class OrganicExpert(Expert):
    """Expert in organic farming practices and certification."""

    @property
    def role(self) -> str:
        return "organic"

    @property
    def label(self) -> str:
        return "Organic Farming Consultant"

    @property
    def system_prompt(self) -> str:
        return """You are an Organic Farming Consultant. Your expertise covers organic certification standards, non-GMO practices, natural fertilizers, and holistic farm management.

Provide guidance compliant with organic standards (like USDA Organic or EU Organic), focusing on ecological balance and biodiversity."""
