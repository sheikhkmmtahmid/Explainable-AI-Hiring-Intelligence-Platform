import logging
from django.utils import timezone
from config.celery import app as celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def parse_cv_task(self, cv_id: int):
    """Parse an uploaded CV and populate candidate profile data."""
    from apps.candidates.models import CandidateCV
    from apps.candidates.services import add_skill, update_years_of_experience
    from apps.parsing.models import ParseJob
    from apps.parsing.services import extract_text_from_file, parse_cv_text
    from apps.matching.tasks import generate_candidate_embedding_task

    parse_job = ParseJob.objects.create(cv_id=cv_id)

    try:
        cv = CandidateCV.objects.select_related("candidate").get(id=cv_id)
        parse_job.status = ParseJob.Status.PROCESSING
        parse_job.started_at = timezone.now()
        parse_job.save(update_fields=["status", "started_at"])

        raw_text = extract_text_from_file(cv.file.path)
        cv.raw_text = raw_text
        cv.parsed_at = timezone.now()
        cv.save(update_fields=["raw_text", "parsed_at"])

        parsed = parse_cv_text(raw_text)
        candidate = cv.candidate

        if not candidate.raw_cv_text:
            candidate.raw_cv_text = raw_text
            candidate.save(update_fields=["raw_cv_text"])

        for skill_data in parsed.get("skills", []):
            add_skill(candidate, source="cv_parsed", **skill_data)

        if parsed.get("years_of_experience"):
            candidate.years_of_experience = parsed["years_of_experience"]
            candidate.save(update_fields=["years_of_experience"])

        parse_job.status = ParseJob.Status.DONE
        parse_job.completed_at = timezone.now()
        parse_job.save(update_fields=["status", "completed_at"])

        generate_candidate_embedding_task.delay(candidate.id)
        logger.info("CV parsed successfully: cv=%s candidate=%s", cv_id, candidate.id)

    except Exception as exc:
        parse_job.status = ParseJob.Status.FAILED
        parse_job.error_message = str(exc)
        parse_job.save(update_fields=["status", "error_message"])
        logger.error("CV parsing failed: cv=%s error=%s", cv_id, exc)
        raise self.retry(exc=exc)
