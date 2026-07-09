"""
Detects when a recruiter's real decision disagrees with the AI's ranking
for that job, and keeps a running rate of how often that happens.

Why this exists: a match score that nobody ever overrides is either a
genuinely excellent predictor or a rubber stamp nobody is actually
checking. A disagreement rate that is tracked and, in particular, sliced by
a candidate's protected attributes, is itself real fairness signal. If
recruiters override the AI far more often for one group than another, that
is worth knowing regardless of whether the AI or the recruiter was "right."

This does not judge who was correct. It only records that a decision and
the AI's ranking pointed in different directions.
"""
import logging

logger = logging.getLogger(__name__)

# Same real-decision statuses the fairness report uses, so "override" means
# the same thing everywhere in this codebase.
ADVANCED_STATUSES = {"shortlisted", "interview", "offer", "hired"}
REJECTED_STATUSES = {"rejected"}

# A candidate ranked in the bottom half by the AI who still gets advanced
# counts as an override in the recruiter's favour. A candidate ranked in
# the top quarter who still gets rejected counts as an override the other
# way. These thresholds are deliberately not symmetrical: rejecting a
# strong match is a bigger departure from the AI's suggestion than
# advancing a middling one, so it takes a higher bar (top quartile, not
# top half) to count.
ADVANCE_OVERRIDE_PERCENTILE = 0.5
REJECT_OVERRIDE_PERCENTILE = 0.25


def compute_override(application, new_status: str) -> tuple[bool | None, float | None]:
    """
    Returns (is_override, candidate_percentile) for a status change on this
    application. percentile is rank / total_candidates_for_this_job, where
    0.0 is the single best-ranked candidate and 1.0 is the worst.

    Returns (None, None) when there's no MatchResult to compare against, or
    when the new status isn't a real decision (applied/screening/withdrawn
    aren't the employer choosing to advance or reject anyone).
    """
    from apps.matching.models import MatchResult

    if new_status not in ADVANCED_STATUSES and new_status not in REJECTED_STATUSES:
        return None, None

    mr = MatchResult.objects.filter(candidate_id=application.candidate_id, job_id=application.job_id).first()
    if mr is None or mr.rank is None:
        return None, None

    total = MatchResult.objects.filter(job_id=application.job_id).count()
    if total == 0:
        return None, None

    percentile = (mr.rank - 1) / total  # rank=1 (best) -> percentile 0.0

    if new_status in ADVANCED_STATUSES:
        is_override = percentile > ADVANCE_OVERRIDE_PERCENTILE
    else:
        is_override = percentile <= REJECT_OVERRIDE_PERCENTILE

    return is_override, round(percentile, 4)


def get_override_summary(organization_id: int, protected_attribute: str | None = None) -> dict:
    """
    Aggregate override rate for an organization, optionally sliced by a
    candidate protected attribute (e.g. "gender", "ethnicity") the same way
    the fairness report slices selection rates. Only counts decisions where
    is_override could actually be computed (is_override is not null).
    """
    from apps.applications.models import ApplicationStatusHistory

    qs = (
        ApplicationStatusHistory.objects
        .filter(application__job__organization_id=organization_id, is_override__isnull=False)
        .select_related("application__candidate")
    )

    if protected_attribute is None:
        total = qs.count()
        overrides = qs.filter(is_override=True).count()
        return {
            "total_decisions": total,
            "override_count": overrides,
            "override_rate": round(overrides / total, 4) if total else None,
        }

    groups: dict[str, dict] = {}
    for row in qs:
        group_val = getattr(row.application.candidate, protected_attribute, None) or "unknown"
        g = groups.setdefault(group_val, {"total": 0, "overrides": 0})
        g["total"] += 1
        if row.is_override:
            g["overrides"] += 1

    return {
        group: {
            "total_decisions": g["total"],
            "override_count": g["overrides"],
            "override_rate": round(g["overrides"] / g["total"], 4) if g["total"] else None,
        }
        for group, g in groups.items()
    }
