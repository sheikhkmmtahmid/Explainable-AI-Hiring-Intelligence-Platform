"""
Batch-generate SBERT embeddings for all candidates and jobs that don't have them yet.

This script should be run:
  1. After loading Kaggle data or generating synthetic data
  2. After any bulk import that bypassed the Celery task chain
  3. Periodically to catch any records whose embedding generation failed

Usage
-----
    python scripts/generate_embeddings.py                         # all missing
    python scripts/generate_embeddings.py --target candidates     # candidates only
    python scripts/generate_embeddings.py --target jobs           # jobs only
    python scripts/generate_embeddings.py --batch-size 128        # larger GPU batch
    python scripts/generate_embeddings.py --recompute             # force recompute all
    python scripts/generate_embeddings.py --dry-run               # count only, no writes
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

import numpy as np
from django.db import transaction

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _build_candidate_text(candidate) -> str:
    """Concatenate all textual signals for a candidate into one string."""
    parts = []
    if candidate.current_title:
        parts.append(candidate.current_title)
    if candidate.summary:
        parts.append(candidate.summary)
    skills = " ".join(
        s.skill_name for s in candidate.skills.all()
    )
    if skills:
        parts.append(skills)
    exp_titles = " ".join(
        e.job_title for e in candidate.experiences.all()
    )
    if exp_titles:
        parts.append(exp_titles)
    if candidate.education_field:
        parts.append(candidate.education_field)
    if candidate.raw_cv_text:
        parts.append(candidate.raw_cv_text[:2000])
    return " ".join(parts).strip() or "no profile data"


def _build_job_text(job) -> str:
    """Concatenate all textual signals for a job into one string."""
    parts = [job.title]
    if job.description:
        parts.append(job.description[:3000])
    if job.requirements:
        parts.append(job.requirements[:1000])
    skills = " ".join(
        s.skill_name for s in job.skill_requirements.all()
    )
    if skills:
        parts.append(skills)
    if job.industry:
        parts.append(job.industry)
    return " ".join(parts).strip()


def generate_candidate_embeddings(
    batch_size: int,
    recompute: bool,
    dry_run: bool,
) -> dict:
    from apps.candidates.models import Candidate, CandidateEmbedding
    from ml.embeddings.encoder import encode_batch, get_model_name

    qs = Candidate.objects.prefetch_related("skills", "experiences")
    if not recompute:
        existing_ids = CandidateEmbedding.objects.values_list("candidate_id", flat=True)
        qs = qs.exclude(id__in=existing_ids)

    total = qs.count()
    logger.info("Candidates to embed: %d", total)
    if dry_run or total == 0:
        return {"total": total, "processed": 0, "failed": 0}

    model_name = get_model_name()
    processed = failed = 0
    candidates = list(qs)

    for batch_start in range(0, len(candidates), batch_size):
        batch = candidates[batch_start: batch_start + batch_size]
        texts = [_build_candidate_text(c) for c in batch]

        try:
            t0 = time.perf_counter()
            vectors = encode_batch(texts, batch_size=batch_size)
            elapsed = time.perf_counter() - t0

            with transaction.atomic():
                for candidate, vector in zip(batch, vectors):
                    CandidateEmbedding.objects.update_or_create(
                        candidate=candidate,
                        defaults={
                            "vector": vector.tolist(),
                            "model_name": model_name,
                        },
                    )
            processed += len(batch)
            logger.info(
                "Candidates: %d/%d embedded (%.2fs for batch of %d)",
                processed, total, elapsed, len(batch),
            )
        except Exception as exc:
            failed += len(batch)
            logger.error("Batch failed at index %d: %s", batch_start, exc)

    return {"total": total, "processed": processed, "failed": failed}


def generate_job_embeddings(
    batch_size: int,
    recompute: bool,
    dry_run: bool,
) -> dict:
    from apps.jobs.models import JobPost, JobEmbedding
    from ml.embeddings.encoder import encode_batch, get_model_name

    qs = JobPost.objects.prefetch_related("skill_requirements")
    if not recompute:
        existing_ids = JobEmbedding.objects.values_list("job_id", flat=True)
        qs = qs.exclude(id__in=existing_ids)

    total = qs.count()
    logger.info("Jobs to embed: %d", total)
    if dry_run or total == 0:
        return {"total": total, "processed": 0, "failed": 0}

    model_name = get_model_name()
    processed = failed = 0
    jobs = list(qs)

    for batch_start in range(0, len(jobs), batch_size):
        batch = jobs[batch_start: batch_start + batch_size]
        texts = [_build_job_text(j) for j in batch]

        try:
            t0 = time.perf_counter()
            vectors = encode_batch(texts, batch_size=batch_size)
            elapsed = time.perf_counter() - t0

            with transaction.atomic():
                for job, vector in zip(batch, vectors):
                    JobEmbedding.objects.update_or_create(
                        job=job,
                        defaults={
                            "vector": vector.tolist(),
                            "model_name": model_name,
                        },
                    )
            processed += len(batch)
            logger.info(
                "Jobs: %d/%d embedded (%.2fs for batch of %d)",
                processed, total, elapsed, len(batch),
            )
        except Exception as exc:
            failed += len(batch)
            logger.error("Batch failed at index %d: %s", batch_start, exc)

    return {"total": total, "processed": processed, "failed": failed}


def main():
    parser = argparse.ArgumentParser(description="Batch-generate SBERT embeddings")
    parser.add_argument(
        "--target",
        choices=["candidates", "jobs", "all"],
        default="all",
        help="Which records to embed (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Encoding batch size (increase on GPU, decrease on CPU, default: 64)",
    )
    parser.add_argument(
        "--recompute",
        action="store_true",
        help="Recompute embeddings even if they already exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count records without running the encoder",
    )
    args = parser.parse_args()

    results = {}
    t_start = time.perf_counter()

    if args.target in ("candidates", "all"):
        results["candidates"] = generate_candidate_embeddings(
            args.batch_size, args.recompute, args.dry_run
        )

    if args.target in ("jobs", "all"):
        results["jobs"] = generate_job_embeddings(
            args.batch_size, args.recompute, args.dry_run
        )

    elapsed_total = time.perf_counter() - t_start
    mode = "[DRY RUN] " if args.dry_run else ""
    logger.info("%s=== Summary (%.1fs) ===", mode, elapsed_total)
    for target, stats in results.items():
        logger.info(
            "  %-12s total=%-6d processed=%-6d failed=%d",
            target, stats["total"], stats["processed"], stats["failed"],
        )


if __name__ == "__main__":
    main()
