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


def export_candidate_data(candidate: Candidate) -> dict:
    """GDPR-style 'right to access' -- every piece of data this platform
    holds about the person, in one portable JSON document."""
    from apps.applications.models import Application
    from apps.matching.models import MatchResult

    applications = Application.objects.filter(candidate=candidate).select_related("job")
    match_results = MatchResult.objects.filter(candidate=candidate).select_related("job")

    return {
        "profile": {
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "country": candidate.country, "city": candidate.city, "region": candidate.region,
            "remote_preference": candidate.remote_preference,
            "current_title": candidate.current_title,
            "years_of_experience": candidate.years_of_experience,
            "seniority_level": candidate.seniority_level,
            "summary": candidate.summary,
            "highest_education": candidate.highest_education,
            "education_field": candidate.education_field,
            "availability_status": candidate.availability_status,
            "expected_salary_min": str(candidate.expected_salary_min) if candidate.expected_salary_min else None,
            "expected_salary_max": str(candidate.expected_salary_max) if candidate.expected_salary_max else None,
            "salary_currency": candidate.salary_currency,
            "gender": candidate.gender, "age_range": candidate.age_range,
            "ethnicity": candidate.ethnicity, "disability_status": candidate.disability_status,
            "created_at": candidate.created_at.isoformat(),
        },
        "cvs": [
            {
                "original_filename": cv.original_filename,
                "file_type": cv.file_type,
                "raw_text": cv.raw_text,
                "uploaded_at": cv.uploaded_at.isoformat(),
            }
            for cv in candidate.cvs.all()
        ],
        "skills": [
            {"skill_name": s.skill_name, "category": s.skill_category, "proficiency": s.proficiency, "source": s.source}
            for s in candidate.skills.all()
        ],
        "experience": [
            {
                "job_title": e.job_title, "company": e.company, "location": e.location,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "is_current": e.is_current, "description": e.description,
            }
            for e in candidate.experiences.all()
        ],
        "applications": [
            {
                "job_title": a.job.title, "company": a.job.company,
                "status": a.status, "applied_at": a.applied_at.isoformat(),
            }
            for a in applications
        ],
        "match_results": [
            {
                "job_title": m.job.title, "overall_score": m.overall_score,
                "rank": m.rank, "computed_at": m.computed_at.isoformat(),
            }
            for m in match_results
        ],
    }


def anonymize_candidate(candidate: Candidate) -> None:
    """GDPR-style 'right to erasure'. Personally-identifying fields are
    scrubbed and CV files/text are deleted outright. Protected-attribute
    categories (gender/age_range/ethnicity/disability_status) and the
    Application/MatchResult outcome rows they're statistically tied to are
    deliberately KEPT -- once the name/email/CV are gone, that data is no
    longer personally identifying, and retaining it is what makes an
    honest fairness/bias audit trail possible after someone leaves the
    system. This mirrors how real HR platforms reconcile GDPR erasure with
    equal-opportunity monitoring obligations.
    """
    for cv in candidate.cvs.all():
        cv.file.delete(save=False)
    candidate.cvs.all().delete()

    candidate.full_name = f"Deleted Candidate #{candidate.id}"
    candidate.email = f"deleted-{candidate.id}@deleted.invalid"
    candidate.phone = ""
    candidate.raw_cv_text = ""
    candidate.summary = ""
    candidate.city = ""
    candidate.region = ""
    candidate.save(update_fields=[
        "full_name", "email", "phone", "raw_cv_text", "summary", "city", "region",
    ])

    if candidate.user_id:
        user = candidate.user
        user.first_name = ""
        user.last_name = ""
        user.email = f"deleted-user-{user.id}@deleted.invalid"
        user.is_active = False
        user.save(update_fields=["first_name", "last_name", "email", "is_active"])
