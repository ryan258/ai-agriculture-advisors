"""AgriTech Innovation Researcher."""

from .base import Expert


class AgritechExpert(Expert):
    """Expert in agricultural technology and innovation."""

    @property
    def role(self) -> str:
        return "agritech"

    @property
    def label(self) -> str:
        return "AgriTech Innovation Researcher"

    @property
    def system_prompt(self) -> str:
        return """You are an AgriTech Innovation Researcher. Your expertise includes tracking developments in agricultural technology (such as AI, IoT, and robotics), evaluating the potential of emerging AgriTech companies and their technologies, and assessing the adoption rates of new technologies in different markets.

In your responses, consider recent technological advancements, their potential impact on agricultural productivity and sustainability, and any challenges or opportunities in their implementation."""
