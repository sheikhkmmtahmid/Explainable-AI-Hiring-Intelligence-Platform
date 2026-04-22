import logging
from typing import Optional

from .models import JobPost, JobSkillRequirement

logger = logging.getLogger(__name__)


def extract_and_attach_skills(job: JobPost, skills_data: list[dict]) -> None:
    """Bulk-create skill requirements from parsed data."""
    objs = [
        JobSkillRequirement(
            job=job,
            skill_name=s["skill_name"].strip().lower(),
            skill_category=s.get("skill_category", ""),
            is_required=s.get("is_required", True),
            min_years=s.get("min_years"),
        )
        for s in skills_data
    ]
    JobSkillRequirement.objects.bulk_create(objs, ignore_conflicts=True)
    logger.info("Attached %d skills to job %s", len(objs), job.id)


def get_active_jobs(filters: Optional[dict] = None):
    qs = JobPost.objects.filter(status=JobPost.Status.ACTIVE)
    if filters:
        qs = qs.filter(**filters)
    return qs


def close_expired_jobs() -> int:
    from django.utils import timezone
    today = timezone.now().date()
    count = JobPost.objects.filter(
        status=JobPost.Status.ACTIVE,
        expires_at__lt=today,
    ).update(status=JobPost.Status.CLOSED)
    logger.info("Closed %d expired jobs", count)
    return count
