"""
Matching service: orchestrates semantic + skill + experience scoring.
Heavy ML work is delegated to ml.matching module.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _load_weights() -> dict:
    """
    Load hybrid score weights from trained model if available,
    falling back to calibrated heuristic defaults.
    """
    try:
        from ml.matching.train_weights import load_weights
        return load_weights()
    except Exception:
        pass
    return {
        "semantic_score": 0.50,
        "skill_overlap_score": 0.30,
        "experience_score": 0.15,
        "education_score": 0.05,
    }


# Loaded once at import time; restart worker to pick up newly trained weights
_WEIGHTS = _load_weights()
WEIGHTS = {
    "semantic": _WEIGHTS.get("semantic_score", 0.50),
    "skill_overlap": _WEIGHTS.get("skill_overlap_score", 0.30),
    "experience": _WEIGHTS.get("experience_score", 0.15),
    "education": _WEIGHTS.get("education_score", 0.05),
}


def compute_skill_overlap_score(candidate_skills: list[str], job_skills: list[str]) -> float:
    if not job_skills:
        return 0.0
    candidate_set = {s.lower() for s in candidate_skills}
    job_set = {s.lower() for s in job_skills}
    overlap = candidate_set & job_set
    return len(overlap) / len(job_set)


def compute_experience_score(candidate_years: float, job_required_years: Optional[float]) -> float:
    if job_required_years is None or job_required_years == 0:
        return 1.0
    ratio = min(candidate_years / job_required_years, 1.5)
    return min(ratio, 1.0)


def compute_education_score(candidate_edu: str, job_edu: str) -> float:
    edu_order = ["high_school", "associate", "bachelor", "master", "phd"]
    try:
        c_idx = edu_order.index(candidate_edu) if candidate_edu in edu_order else 0
        j_idx = edu_order.index(job_edu) if job_edu in edu_order else 0
        return 1.0 if c_idx >= j_idx else c_idx / max(j_idx, 1)
    except ValueError:
        return 0.5


def compute_hybrid_score(
    semantic_score: float,
    skill_overlap_score: float,
    experience_score: float,
    education_score: float,
) -> float:
    return (
        WEIGHTS["semantic"] * semantic_score
        + WEIGHTS["skill_overlap"] * skill_overlap_score
        + WEIGHTS["experience"] * experience_score
        + WEIGHTS["education"] * education_score
    )


def _compute_overall(
    semantic: float,
    skill: float,
    experience: float,
    education: float,
    candidate,
    job,
) -> float:
    """
    Return the overall match score. Uses the trained ML model when one exists,
    otherwise falls back to the fixed-weight hybrid scorer.
    """
    try:
        from ml.matching.trained_scorer import predict_score
        from ml.matching.scorer import build_feature_vector

        candidate_skills = list(candidate.skills.values_list("skill_name", flat=True))
        job_required = list(job.skill_requirements.filter(is_required=True).values_list("skill_name", flat=True))
        job_preferred = list(job.skill_requirements.filter(is_required=False).values_list("skill_name", flat=True))
        min_exp = 0.0
        for req in job.skill_requirements.filter(min_years__isnull=False):
            if req.min_years and req.min_years > min_exp:
                min_exp = float(req.min_years)

        candidate_data = {
            "semantic_score": semantic,
            "skills": candidate_skills,
            "years_of_experience": float(candidate.years_of_experience or 0),
            "highest_education": candidate.highest_education or "",
            "seniority_level": getattr(candidate, "seniority_level", "mid") or "mid",
            "remote_preference": getattr(candidate, "remote_preference", "flexible") or "flexible",
        }
        job_data = {
            "required_skills": job_required,
            "preferred_skills": job_preferred,
            "min_experience_years": min_exp,
            "required_education": "bachelor",
            "experience_level": job.experience_level or "mid",
            "work_model": job.work_model or "onsite",
        }
        fv = build_feature_vector(candidate_data, job_data)
        score = predict_score(fv)
        if score is not None:
            return round(score, 4)
    except Exception:
        pass

    return compute_hybrid_score(semantic, skill, experience, education)


def match_candidate_to_job(candidate, job) -> dict:
    """Compute full match scores between one candidate and one job."""
    from ml.embeddings.encoder import cosine_similarity_score

    # Semantic score via SBERT embeddings
    try:
        c_emb = candidate.embedding.vector
        j_emb = job.embedding.vector
        semantic = cosine_similarity_score(c_emb, j_emb)
    except Exception:
        semantic = 0.0
        logger.warning("Embedding missing for candidate=%s or job=%s", candidate.id, job.id)

    # Skill overlap
    candidate_skills = list(candidate.skills.values_list("skill_name", flat=True))
    job_skills = list(job.skill_requirements.values_list("skill_name", flat=True))
    skill = compute_skill_overlap_score(candidate_skills, job_skills)

    # Experience
    exp_required = None
    exp_req_field = job.skill_requirements.filter(is_required=True).values_list("min_years", flat=True).first()
    experience = compute_experience_score(candidate.years_of_experience, exp_required)

    # Education
    education = compute_education_score(candidate.highest_education, "bachelor")

    # Use trained ML model if available, otherwise fall back to fixed weights
    overall = _compute_overall(semantic, skill, experience, education, candidate, job)

    return {
        "overall_score": round(overall, 4),
        "semantic_score": round(semantic, 4),
        "skill_overlap_score": round(skill, 4),
        "experience_score": round(experience, 4),
        "education_score": round(education, 4),
    }


def run_batch_matching_for_job(job_id: int) -> int:
    """Match all candidates with embeddings against a job."""
    from apps.jobs.models import JobPost
    from apps.candidates.models import Candidate
    from .models import MatchResult, MatchBatchRun

    job = JobPost.objects.get(id=job_id)
    batch = MatchBatchRun.objects.create(job=job, status="running")

    from django.utils import timezone
    batch.started_at = timezone.now()
    batch.save(update_fields=["started_at"])

    candidates = Candidate.objects.filter(embedding__isnull=False)
    results = []
    for candidate in candidates:
        scores = match_candidate_to_job(candidate, job)
        results.append(MatchResult(candidate=candidate, job=job, **scores))

    MatchResult.objects.bulk_create(results, update_conflicts=True,
        update_fields=["overall_score", "semantic_score", "skill_overlap_score",
                       "experience_score", "education_score", "computed_at"],
        unique_fields=["candidate", "job"])

    # Assign ranks
    for rank, mr in enumerate(
        MatchResult.objects.filter(job=job).order_by("-overall_score"), start=1
    ):
        MatchResult.objects.filter(pk=mr.pk).update(rank=rank)

    batch.status = "done"
    batch.candidates_processed = len(results)
    batch.completed_at = timezone.now()
    batch.save(update_fields=["status", "candidates_processed", "completed_at"])
    logger.info("Batch matching done: job=%s candidates=%s", job_id, len(results))
    return len(results)
