"""
Fairness analysis service.
Computes selection rate parity and disparate impact for protected attributes.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 4/5 rule threshold for disparate impact
DISPARATE_IMPACT_THRESHOLD = 0.8
# Top fraction of ranked candidates considered "shortlisted" (top 20%)
SHORTLIST_TOP_PCT = 0.20


def compute_fairness_report(job_id: int, protected_attribute: str) -> dict:
    from apps.matching.models import MatchResult
    from apps.candidates.models import Candidate
    from .models import FairnessReport, SubgroupMetric

    # Order by rank so the top-N cutoff is straightforward
    job_results = list(
        MatchResult.objects.filter(job_id=job_id)
        .select_related("candidate")
        .order_by("rank")
    )
    if not job_results:
        return {}

    # Shortlist = top 20% of ranked candidates (minimum 1)
    n_shortlisted = max(1, round(len(job_results) * SHORTLIST_TOP_PCT))
    shortlisted_ids = {mr.candidate_id for mr in job_results[:n_shortlisted]}

    groups: dict[str, dict] = {}
    for mr in job_results:
        candidate = mr.candidate
        group_val = getattr(candidate, protected_attribute, None) or "unknown"
        if group_val not in groups:
            groups[group_val] = {"total": 0, "shortlisted": 0, "scores": []}
        groups[group_val]["total"] += 1
        groups[group_val]["scores"].append(mr.overall_score)
        if mr.candidate_id in shortlisted_ids:
            groups[group_val]["shortlisted"] += 1

    subgroup_data = {}
    for group_val, data in groups.items():
        rate = data["shortlisted"] / data["total"] if data["total"] > 0 else 0.0
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0
        subgroup_data[group_val] = {
            "total": data["total"],
            "shortlisted": data["shortlisted"],
            "selection_rate": round(rate, 4),
            "avg_match_score": round(avg_score, 4),
        }

    max_rate = max((v["selection_rate"] for v in subgroup_data.values()), default=0.0)
    overall_rate = (
        sum(v["shortlisted"] for v in subgroup_data.values())
        / max(sum(v["total"] for v in subgroup_data.values()), 1)
    )

    # Disparate impact: min_group_rate / max_group_rate
    min_rate = min((v["selection_rate"] for v in subgroup_data.values()), default=0.0)
    di_ratio = min_rate / max_rate if max_rate > 0 else None
    bias_flag = di_ratio is not None and di_ratio < DISPARATE_IMPACT_THRESHOLD

    report, _ = FairnessReport.objects.update_or_create(
        job_id=job_id,
        protected_attribute=protected_attribute,
        defaults={
            "report_data": subgroup_data,
            "disparate_impact_ratio": di_ratio,
            "selection_rate_overall": round(overall_rate, 4),
            "bias_flag": bias_flag,
        },
    )

    # Save subgroup records
    SubgroupMetric.objects.filter(report=report).delete()
    SubgroupMetric.objects.bulk_create([
        SubgroupMetric(
            report=report,
            group_value=group_val,
            total_candidates=data["total"],
            shortlisted_count=data["shortlisted"],
            selection_rate=data["selection_rate"],
            avg_match_score=data["avg_match_score"],
        )
        for group_val, data in subgroup_data.items()
    ])

    if bias_flag:
        logger.warning(
            "Bias detected: job=%s attribute=%s DI=%.3f",
            job_id, protected_attribute, di_ratio
        )

    return {
        "job_id": job_id,
        "protected_attribute": protected_attribute,
        "subgroups": subgroup_data,
        "disparate_impact_ratio": di_ratio,
        "selection_rate_overall": round(overall_rate, 4),
        "bias_flag": bias_flag,
    }
