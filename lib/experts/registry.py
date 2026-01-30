"""Expert registry for accessing domain experts."""

from typing import Dict, List, Optional

from .base import Expert
from .agriculture import AgricultureExpert
from .climate import ClimateExpert
from .commodities import CommoditiesExpert
from .agritech import AgritechExpert
from .supply_chain import SupplyChainExpert
from .soil import SoilExpert
from .pest import PestExpert
from .irrigation import IrrigationExpert
from .organic import OrganicExpert
from .economics import EconomicsExpert

# Instantiate all experts
_agriculture = AgricultureExpert()
_climate = ClimateExpert()
_commodities = CommoditiesExpert()
_agritech = AgritechExpert()
_supply_chain = SupplyChainExpert()
_soil = SoilExpert()
_pest = PestExpert()
_irrigation = IrrigationExpert()
_organic = OrganicExpert()
_economics = EconomicsExpert()

# Registry mapping role keys to expert instances
expert_registry: Dict[str, Expert] = {
    "agriculture": _agriculture,
    "climate": _climate,
    "commodities": _commodities,
    "agritech": _agritech,
    "supplychain": _supply_chain,
    "soil": _soil,
    "pest": _pest,
    "irrigation": _irrigation,
    "organic": _organic,
    "economics": _economics,
}


def get_expert(role: str) -> Optional[Expert]:
    """Get an expert instance by role key."""
    return expert_registry.get(role)


def get_all_experts() -> List[Dict[str, str]]:
    """Get list of all available experts with their roles and labels."""
    return [
        {"role": expert.role, "label": expert.label}
        for expert in expert_registry.values()
    ]
