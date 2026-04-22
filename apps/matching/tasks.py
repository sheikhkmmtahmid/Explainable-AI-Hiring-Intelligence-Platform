import logging
from config.celery import app as celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def generate_candidate_embedding_task(self, candidate_id: int):
    """Generate and store SBERT embedding for a candidate."""
    try:
        from apps.candidates.models import Candidate, CandidateEmbedding
        from ml.embeddings.encoder import encode_text, get_model_name

        candidate = Candidate.objects.prefetch_related("skills", "experiences").get(id=candidate_id)
        text = _build_candidate_text(candidate)
        vector = encode_text(text)

        CandidateEmbedding.objects.update_or_create(
            candidate=candidate,
            defaults={"vector": vector.tolist(), "model_name": get_model_name()},
        )
        logger.info("Candidate embedding generated: candidate=%s", candidate_id)
    except Exception as exc:
        logger.error("Embedding failed: candidate=%s error=%s", candidate_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2)
def generate_job_embedding_task(self, job_id: int):
    """Generate and store SBERT embedding for a job post."""
    try:
        from apps.jobs.models import JobPost, JobEmbedding
        from ml.embeddings.encoder import encode_text, get_model_name

        job = JobPost.objects.get(id=job_id)
        text = f"{job.title}\n{job.description}\n{job.requirements}"
        vector = encode_text(text)

        JobEmbedding.objects.update_or_create(
            job=job,
            defaults={"vector": vector.tolist(), "model_name": get_model_name()},
        )
        logger.info("Job embedding generated: job=%s", job_id)
    except Exception as exc:
        logger.error("Embedding failed: job=%s error=%s", job_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True)
def batch_match_job_task(self, job_id: int):
    """Run full candidate batch matching for a job."""
    from apps.matching.services import run_batch_matching_for_job
    count = run_batch_matching_for_job(job_id)
    logger.info("Batch match complete: job=%s matched=%s", job_id, count)
    return count


def _build_candidate_text(candidate) -> str:
    skills = " ".join(s.skill_name for s in candidate.skills.all())
    exp_titles = " ".join(e.job_title for e in candidate.experiences.all())
    return f"{candidate.current_title} {candidate.summary} {skills} {exp_titles}".strip()
