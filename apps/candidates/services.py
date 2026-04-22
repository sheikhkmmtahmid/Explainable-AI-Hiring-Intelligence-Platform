import logging
from datetime import date
from typing import Optional

from django.utils import timezone

from .models import Candidate, CandidateCV, CandidateSkill, CandidateExperience

logger = logging.getLogger(__name__)


def get_or_create_candidate_for_user(user) -> Candidate:
    candidate, _ = Candidate.objects.get_or_create(
        user=user,
        defaults={"full_name": user.get_full_name() or user.username, "email": user.email},
    )
    return candidate


def attach_cv(candidate: Candidate, file, filename: str) -> CandidateCV:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
    cv = CandidateCV.objects.create(
        candidate=candidate,
        file=file,
        original_filename=filename,
        file_type=ext,
        is_primary=not candidate.cvs.filter(is_primary=True).exists(),
    )
    logger.info("CV attached: candidate=%s file=%s", candidate.id, filename)
    return cv


def add_skill(
    candidate: Candidate,
    skill_name: str,
    category: str = "",
    proficiency: str = "",
    years_used: Optional[float] = None,
    source: str = "manual",
) -> CandidateSkill:
    skill, _ = CandidateSkill.objects.update_or_create(
        candidate=candidate,
        skill_name=skill_name.strip().lower(),
        defaults={
            "skill_category": category,
            "proficiency": proficiency,
            "years_used": years_used,
            "source": source,
        },
    )
    return skill


def compute_total_experience(candidate: Candidate) -> float:
    """Sum months of all experiences and return total years."""
    total_months = 0
    for exp in candidate.experiences.all():
        start = exp.start_date
        end = exp.end_date if not exp.is_current else date.today()
        if start and end:
            total_months += (end.year - start.year) * 12 + (end.month - start.month)
    return round(total_months / 12, 1)


def update_years_of_experience(candidate: Candidate) -> None:
    years = compute_total_experience(candidate)
    Candidate.objects.filter(pk=candidate.pk).update(years_of_experience=years)
