"""
Score every real OpenIntro audit-study application against its actual job,
and label the result with the study's real outcome, using only data
already imported this session -- no new dataset, no external download.

Why this exists
----------------
The audit study has 4,870 real applications with a real outcome (received
a callback, or didn't). That data has been sitting in Application rows
since import, but almost none of it ever reached MatchResult.hired: the
signal that copies a real outcome onto a match result only fires at
Application-save time, and only updates a MatchResult that already exists
at that exact instant. Most of these applications were imported before
batch matching had ever run for their job, so the signal fired once,
found nothing to update, and never tried again. (See
apps/matching/services.py::run_batch_matching_for_job, which now re-syncs
this on every run -- that fixes it going forward. This command fixes the
already-imported backlog.)

Every candidate and job involved already has an embedding and extracted
skills from import, so scoring these pairs needs no new data -- it is the
platform's own existing scoring formulas run against real people and real
jobs that were simply never scored against each other.

Labeling choice, stated plainly
--------------------------------
The audit study measured callback rate, not final hiring, so these
applications only ever carry status "shortlisted" (got a callback) or
"rejected" (no callback) -- never "hired". This command maps received a
callback -> hired=True and no callback -> hired=False for training
purposes. That is a real, defensible choice (a callback is exactly the
outcome the original study measured and published), but it is a callback
label, not a literal hiring decision, and nothing about this command
pretends otherwise.

Usage:
    python manage.py backfill_openintro_match_results
    python manage.py backfill_openintro_match_results --dry-run
"""
import logging

import numpy as np
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Score and label real OpenIntro audit-study applications against their real jobs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Report counts without writing anything",
        )

    def handle(self, *args, **options):
        from apps.applications.models import Application
        from apps.candidates.models import Candidate
        from apps.jobs.models import JobPost
        from apps.matching.models import MatchResult
        from apps.matching.services import (
            compute_education_score,
            compute_experience_score,
            compute_hybrid_score,
            compute_skill_overlap_score,
        )

        dry_run = options["dry_run"]

        applications = list(
            Application.objects.filter(is_synthetic=False, job__source="openintro")
            .values_list("candidate_id", "job_id", "status")
        )
        self.stdout.write(f"Found {len(applications)} real OpenIntro applications.")
        if not applications:
            return

        candidate_ids = {a[0] for a in applications}
        job_ids = {a[1] for a in applications}

        candidates = {
            c.id: c
            for c in Candidate.objects.filter(id__in=candidate_ids)
            .select_related("embedding")
            .prefetch_related("skills")
        }
        jobs = {
            j.id: j
            for j in JobPost.objects.filter(id__in=job_ids)
            .select_related("embedding")
            .prefetch_related("skill_requirements")
        }

        existing_pairs = set(
            MatchResult.objects.filter(job_id__in=job_ids, candidate_id__in=candidate_ids)
            .values_list("candidate_id", "job_id")
        )

        # Per-job data (skills, min experience, embedding vector) computed
        # once per job, not once per application.
        job_cache = {}
        for job_id, job in jobs.items():
            job_skills = [s.skill_name for s in job.skill_requirements.all()]
            min_exp = None
            for req in job.skill_requirements.all():
                if req.is_required and req.min_years and (min_exp is None or req.min_years > min_exp):
                    min_exp = float(req.min_years)
            try:
                j_vec = np.array(job.embedding.vector, dtype=np.float32)
            except Exception:
                j_vec = None
                logger.warning("No embedding for openintro job=%s", job_id)
            job_cache[job_id] = (job_skills, min_exp, j_vec)

        to_create = []
        to_relabel = []  # (candidate_id, job_id, hired)
        skipped = 0

        for candidate_id, job_id, status in applications:
            candidate = candidates.get(candidate_id)
            job = jobs.get(job_id)
            if candidate is None or job is None or not hasattr(candidate, "embedding"):
                skipped += 1
                continue

            # Received a callback -> treated as the positive label. See the
            # module docstring: this is a callback outcome, not a literal
            # hiring decision.
            hired_value = status == Application.Status.SHORTLISTED

            if (candidate_id, job_id) in existing_pairs:
                to_relabel.append((candidate_id, job_id, hired_value))
                continue

            job_skills, min_exp, j_vec = job_cache[job_id]
            try:
                c_vec = np.array(candidate.embedding.vector, dtype=np.float32)
                semantic = float(np.dot(j_vec, c_vec)) if j_vec is not None else 0.0
            except Exception:
                semantic = 0.0

            candidate_skills = [s.skill_name for s in candidate.skills.all()]
            skill = compute_skill_overlap_score(candidate_skills, job_skills)
            experience = compute_experience_score(float(candidate.years_of_experience or 0), min_exp)
            education = compute_education_score(candidate.highest_education or "", job.required_education or "")
            overall = compute_hybrid_score(semantic, skill, experience, education)

            to_create.append(MatchResult(
                candidate_id=candidate_id,
                job_id=job_id,
                overall_score=round(overall, 4),
                semantic_score=round(semantic, 4),
                skill_overlap_score=round(skill, 4),
                experience_score=round(experience, 4),
                education_score=round(education, 4),
                hired=hired_value,
            ))

        n_true = sum(1 for mr in to_create if mr.hired) + sum(1 for *_, h in to_relabel if h)
        n_false = len(to_create) + len(to_relabel) - n_true

        self.stdout.write(f"Would create: {len(to_create)} | would relabel existing: {len(to_relabel)} | skipped (missing data): {skipped}")
        self.stdout.write(f"Resulting labels: {n_true} callback (hired=True) | {n_false} no callback (hired=False)")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run -- nothing written."))
            return

        MatchResult.objects.bulk_create(to_create, batch_size=500)
        for candidate_id, job_id, hired_value in to_relabel:
            MatchResult.objects.filter(candidate_id=candidate_id, job_id=job_id).update(hired=hired_value)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {len(to_create)} match results, relabeled {len(to_relabel)} existing ones."
        ))
