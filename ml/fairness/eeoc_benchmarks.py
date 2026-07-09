"""
Real published EEOC workforce data, used to give a fairness report some
outside context instead of only comparing an organization against itself.

Source: U.S. Equal Employment Opportunity Commission, 2018 EEO-1 Component 1
national aggregate raw dataset (year18_us.txt), downloaded directly from
https://www.eeoc.gov/statistics/2018-job-patterns-minorities-and-women-private-industry-eeo-1-raw-datasets
and computed here from the actual per-job-category counts, not copied from
a secondary source. Total private-industry workforce covered: 56,073,774
employees across 281,932 reporting units.

Two honesty notes that matter for how this gets used:

1. This is workforce composition (who is currently employed, aggregated
   across all private industry), not a selection or hire rate. An
   organization's selection rate for a group can honestly differ from this
   number for reasons that have nothing to do with fairness (a small
   specialised industry, a specific region, a specific role). Treat this as
   a directional sanity check, "does this look broadly in the neighbourhood
   of the national picture," not a compliance certification or a target
   quota.
2. The published EEOC counts by race and gender do not sum to the full
   total workforce figure (rows here sum to about 90% of TOTAL10). The
   EEOC's own documentation notes small cell values are suppressed to
   protect privacy, and that gap is exactly that suppression, not a
   computation error on this platform's part.
"""

EEOC_SOURCE_YEAR = 2018
EEOC_SOURCE_URL = "https://www.eeoc.gov/statistics/2018-job-patterns-minorities-and-women-private-industry-eeo-1-raw-datasets"
EEOC_TOTAL_WORKFORCE = 56_073_774

# Percent of the total national private-industry workforce, computed
# directly from the raw dataset above. Keys are lowercase and match the
# free-text values this platform's own Candidate.gender / Candidate.ethnicity
# fields commonly use, with a few common synonyms mapped in
# GENDER_ALIASES / ETHNICITY_ALIASES below.
EEOC_GENDER_BENCHMARK = {
    "male": 46.08,
    "female": 44.35,
}

EEOC_ETHNICITY_BENCHMARK = {
    "white": 52.30,        # White men + White women
    "black": 14.53,        # Black or African American men + women
    "hispanic": 14.57,     # Hispanic or Latino men + women
    "asian": 6.02,         # Asian men + women
    "american indian or alaska native": 0.51,
    "native hawaiian or pacific islander": 0.45,
    "two or more races": 2.05,
}

GENDER_ALIASES = {"m": "male", "man": "male", "men": "male", "f": "female", "woman": "female", "women": "female"}
ETHNICITY_ALIASES = {
    "black or african american": "black", "african american": "black",
    "hispanic or latino": "hispanic", "latino": "hispanic", "latina": "hispanic",
    "native american": "american indian or alaska native",
    "pacific islander": "native hawaiian or pacific islander",
    "mixed": "two or more races", "multiracial": "two or more races",
}


def get_eeoc_benchmark(protected_attribute: str, group_value: str) -> float | None:
    """Returns the EEOC national workforce percentage for a group value, or
    None if this attribute/group isn't one EEOC publishes a comparable
    figure for (age_range and disability_status aren't covered by EEO-1
    Component 1 at all, so this always returns None for those)."""
    if not group_value:
        return None
    key = group_value.strip().lower()

    if protected_attribute == "gender":
        key = GENDER_ALIASES.get(key, key)
        return EEOC_GENDER_BENCHMARK.get(key)

    if protected_attribute == "ethnicity":
        key = ETHNICITY_ALIASES.get(key, key)
        return EEOC_ETHNICITY_BENCHMARK.get(key)

    return None


def compare_to_eeoc_benchmark(protected_attribute: str, subgroup_data: dict) -> dict:
    """
    Takes the subgroup_data shape apps.fairness.services.compute_fairness_report
    already produces ({group_value: {"selection_rate": ..., ...}}) and
    attaches the matching EEOC benchmark percentage to each group that has
    one, plus the gap between the organization's selection rate and the
    national workforce composition figure.
    """
    if protected_attribute not in ("gender", "ethnicity"):
        return {
            "supported": False,
            "reason": "EEO-1 Component 1 does not publish comparable figures for this attribute.",
        }

    comparison = {}
    for group_value, data in subgroup_data.items():
        benchmark_pct = get_eeoc_benchmark(protected_attribute, group_value)
        if benchmark_pct is None:
            continue
        org_pct = round(data["selection_rate"] * 100, 2)
        comparison[group_value] = {
            "organization_selection_rate_pct": org_pct,
            "eeoc_national_workforce_pct": benchmark_pct,
            "gap_percentage_points": round(org_pct - benchmark_pct, 2),
        }

    return {
        "supported": True,
        "source_year": EEOC_SOURCE_YEAR,
        "source_url": EEOC_SOURCE_URL,
        "note": (
            "This compares your selection rate against national private-industry workforce "
            "composition, not a selection-rate benchmark. Treat this as directional context, "
            "not a compliance target."
        ),
        "groups": comparison,
    }
