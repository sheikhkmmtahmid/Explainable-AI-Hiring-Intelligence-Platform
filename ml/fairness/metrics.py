"""
Fairness metrics library.
Implements: Disparate Impact, Demographic Parity, Equal Opportunity.
"""
from typing import Optional


def disparate_impact(selection_rates: dict[str, float]) -> Optional[float]:
    """
    4/5 (80%) rule: min_group_rate / max_group_rate.
    Values < 0.8 indicate potential bias.
    """
    if not selection_rates:
        return None
    rates = [v for v in selection_rates.values() if v > 0]
    if not rates:
        return None
    return min(rates) / max(rates)


def demographic_parity_difference(selection_rates: dict[str, float]) -> float:
    """
    Max difference in selection rates between groups.
    Closer to 0 = more fair.
    """
    if not selection_rates:
        return 0.0
    rates = list(selection_rates.values())
    return max(rates) - min(rates)


def equal_opportunity_difference(tpr_rates: dict[str, float]) -> float:
    """
    Max difference in true positive rates (interview invitation rates) between groups.
    """
    if not tpr_rates:
        return 0.0
    rates = list(tpr_rates.values())
    return max(rates) - min(rates)


def flag_bias(di_ratio: Optional[float], threshold: float = 0.8) -> bool:
    if di_ratio is None:
        return False
    return di_ratio < threshold


def summarise_fairness(subgroup_data: dict) -> dict:
    """
    Return a comprehensive fairness summary from subgroup selection rates.
    """
    selection_rates = {g: d["selection_rate"] for g, d in subgroup_data.items()}
    di = disparate_impact(selection_rates)
    dpd = demographic_parity_difference(selection_rates)
    return {
        "disparate_impact_ratio": round(di, 4) if di is not None else None,
        "demographic_parity_difference": round(dpd, 4),
        "bias_detected": flag_bias(di),
        "highest_selection_group": max(selection_rates, key=selection_rates.get) if selection_rates else None,
        "lowest_selection_group": min(selection_rates, key=selection_rates.get) if selection_rates else None,
    }
