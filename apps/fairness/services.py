"""
Fairness analysis service.
Computes selection rate parity and disparate impact for protected attributes.

The audit is grounded in REAL recruiter decisions (Application.status)
whenever any exist for the job -- "were our actual hiring choices fair"
is the thing worth auditing, not just "does the AI's ranking look even."
Only when nobody has made a single real decision yet (no applications
resolved to shortlisted/interview/offer/hired/rejected) does this fall
back to a clearly-labeled provisional estimate based on the AI's ranking,
so a report is never silently presented as more authoritative than it is.
"""
import logging

logger = logging.getLogger(__name__)

# 4/5 rule threshold for disparate impact
DISPARATE_IMPACT_THRESHOLD = 0.8
# Top fraction of ranked candidates considered "selected", used only in the
# ai_rank_provisional fallback when no real decisions exist yet.
SHORTLIST_TOP_PCT = 0.20

# A recruiter choosing to advance someone -- a real, positive decision.
ADVANCED_STATUSES = {"shortlisted", "interview", "offer", "hired"}
# A recruiter choosing not to -- a real, negative decision.
REJECTED_STATUSES = {"rejected"}
# Not yet decided (applied/screening), or not the employer's decision at
# all (withdrawn) -- excluded from the audit rather than guessed at.


def _groups_from_pairs(pairs, protected_attribute):
    """pairs: iterable of (candidate, selected: bool, score: float|None)"""
    groups: dict[str, dict] = {}
    for candidate, selected, score in pairs:
        group_val = getattr(candidate, protected_attribute, None) or "unknown"
        g = groups.setdefault(group_val, {"total": 0, "shortlisted": 0, "scores": []})
        g["total"] += 1
        if selected:
            g["shortlisted"] += 1
        if score is not None:
            g["scores"].append(score)
    return groups


def _compute_from_real_decisions(job_id, protected_attribute):
    from apps.applications.models import Application
    from apps.matching.models import MatchResult

    resolved = list(
        Application.objects.filter(job_id=job_id, status__in=ADVANCED_STATUSES | REJECTED_STATUSES)
        .select_related("candidate")
    )
    if not resolved:
        return None

    scores_by_candidate = dict(
        MatchResult.objects.filter(job_id=job_id).values_list("candidate_id", "overall_score")
    )
    pairs = [
        (a.candidate, a.status in ADVANCED_STATUSES, scores_by_candidate.get(a.candidate_id))
        for a in resolved
    ]
    return _groups_from_pairs(pairs, protected_attribute)


def _compute_from_ai_rank(job_id, protected_attribute):
    from apps.matching.models import MatchResult

    job_results = list(
        MatchResult.objects.filter(job_id=job_id).select_related("candidate").order_by("rank")
    )
    if not job_results:
        return None
    n_top = max(1, round(len(job_results) * SHORTLIST_TOP_PCT))
    top_ids = {mr.candidate_id for mr in job_results[:n_top]}
    pairs = [(mr.candidate, mr.candidate_id in top_ids, mr.overall_score) for mr in job_results]
    return _groups_from_pairs(pairs, protected_attribute)


def compute_fairness_report(job_id: int, protected_attribute: str) -> dict:
    from .models import FairnessReport, SubgroupMetric

    groups = _compute_from_real_decisions(job_id, protected_attribute)
    basis = FairnessReport.Basis.ACTUAL_DECISIONS
    if groups is None:
        groups = _compute_from_ai_rank(job_id, protected_attribute)
        basis = FairnessReport.Basis.AI_RANK_PROVISIONAL
    if not groups:
        return {}

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
            "basis": basis,
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
            "Bias detected: job=%s attribute=%s DI=%.3f basis=%s",
            job_id, protected_attribute, di_ratio, basis,
        )

    return {
        "job_id": job_id,
        "protected_attribute": protected_attribute,
        "subgroups": subgroup_data,
        "disparate_impact_ratio": di_ratio,
        "selection_rate_overall": round(overall_rate, 4),
        "bias_flag": bias_flag,
        "basis": basis,
    }
