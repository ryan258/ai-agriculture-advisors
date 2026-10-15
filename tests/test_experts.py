"""Tests for the expert system."""

import pytest

from lib.experts import get_expert, get_all_experts, expert_registry
from lib.experts.base import Expert


def test_all_experts_registered() -> None:
    """Test that all 27 experts are registered."""
    assert len(expert_registry) == 27

    expected_roles = [
        "agriculture",
        "climate",
        "commodities",
        "agritech",
        "supplychain",
        "soil",
        "pest",
        "irrigation",
        "organic",
        "economics",
    ]

    for role in expected_roles:
        assert role in expert_registry, f"Missing expert: {role}"


def test_get_expert_valid() -> None:
    """Test getting a valid expert."""
    expert = get_expert("agriculture")
    assert expert is not None
    assert expert.role == "agriculture"
    assert expert.label == "Agricultural Science Expert"


def test_get_expert_invalid() -> None:
    """Test getting an invalid expert returns None."""
    expert = get_expert("invalid_role")
    assert expert is None


def test_get_all_experts() -> None:
    """Test getting list of all experts."""
    experts = get_all_experts()
    assert len(experts) == 27
    assert all("role" in e and "label" in e for e in experts)


def test_expert_has_system_prompt() -> None:
    """Test that all experts have system prompts."""
    for role, expert in expert_registry.items():
        assert expert.system_prompt, f"Expert {role} has no system prompt"
        assert len(expert.system_prompt) > 50, f"Expert {role} system prompt too short"


def test_expert_build_prompt() -> None:
    """Test that experts build prompts correctly."""
    expert = get_expert("agriculture")
    assert expert is not None

    prompt = expert.build_prompt("How do I grow tomatoes?")
    assert "How do I grow tomatoes?" in prompt


@pytest.mark.parametrize(
    "role,expected_label",
    [
        ("agriculture", "Agricultural Science Expert"),
        ("climate", "Climate Change Impact Analyst"),
        ("commodities", "Commodities Trading Specialist"),
        ("agritech", "AgriTech Innovation Researcher"),
        ("supplychain", "Food Supply Chain Analyst"),
        ("soil", "Soil Health Specialist"),
        ("pest", "Pest & Disease Management Expert"),
        ("irrigation", "Irrigation & Water Management Specialist"),
        ("organic", "Organic Farming Consultant"),
        ("economics", "Agricultural Economics Advisor"),
    ],
)
def test_expert_labels(role: str, expected_label: str) -> None:
    """Test that all experts have correct labels."""
    expert = get_expert(role)
    assert expert is not None
    assert expert.label == expected_label
