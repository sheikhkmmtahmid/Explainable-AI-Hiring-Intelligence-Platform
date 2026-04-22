from django.db.models import Count, Avg
from django.utils import timezone

from apps.applications.models import Application
from apps.matching.models import MatchResult
from .models import PipelineSnapshot


def build_pipeline_snapshot(job_id: int) -> dict:
    apps = Application.objects.filter(job_id=job_id)
    status_counts = dict(apps.values_list("status").annotate(c=Count("status")).values_list("status", "c"))
    avg_score = MatchResult.objects.filter(job_id=job_id).aggregate(avg=Avg("overall_score"))["avg"]

    snapshot, _ = PipelineSnapshot.objects.update_or_create(
        job_id=job_id,
        date=timezone.now().date(),
        defaults={
            "total_applications": apps.count(),
            "screened_count": status_counts.get("screening", 0),
            "shortlisted_count": status_counts.get("shortlisted", 0),
            "interview_count": status_counts.get("interview", 0),
            "offer_count": status_counts.get("offer", 0),
            "hired_count": status_counts.get("hired", 0),
            "rejected_count": status_counts.get("rejected", 0),
            "avg_match_score": round(avg_score, 4) if avg_score else None,
        },
    )
    return {
        "job_id": job_id,
        "total_applications": snapshot.total_applications,
        "pipeline": {
            "screened": snapshot.screened_count,
            "shortlisted": snapshot.shortlisted_count,
            "interview": snapshot.interview_count,
            "offer": snapshot.offer_count,
            "hired": snapshot.hired_count,
            "rejected": snapshot.rejected_count,
        },
        "avg_match_score": snapshot.avg_match_score,
    }


def get_platform_summary() -> dict:
    from apps.candidates.models import Candidate
    from apps.jobs.models import JobPost

    return {
        "total_candidates": Candidate.objects.count(),
        "synthetic_candidates": Candidate.objects.filter(is_synthetic=True).count(),
        "total_jobs": JobPost.objects.count(),
        "active_jobs": JobPost.objects.filter(status="active").count(),
        "total_applications": Application.objects.count(),
        "total_matches": MatchResult.objects.count(),
    }
