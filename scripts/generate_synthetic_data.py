"""
Generate synthetic candidates, jobs, and applications with bias scenarios.

Usage
-----
    python scripts/generate_synthetic_data.py
    python scripts/generate_synthetic_data.py --candidates 100 --jobs 10
"""
import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def create_candidates(n: int) -> list:
    from apps.candidates.models import Candidate, CandidateSkill
    from apps.synthetic_data.generators import generate_candidate_data

    created = []
    for i in range(n):
        data = generate_candidate_data()
        skills = data.pop("skills", [])
        candidate = Candidate.objects.create(**data)
        CandidateSkill.objects.bulk_create(
            [CandidateSkill(candidate=candidate, skill_name=s) for s in skills],
            ignore_conflicts=True,
        )
        created.append(candidate)
        if (i + 1) % 50 == 0:
            logger.info("Candidates created: %d", i + 1)
    logger.info("Total candidates created: %d", len(created))
    return created


def create_jobs(n: int) -> list:
    import uuid
    from apps.jobs.models import JobPost, JobSkillRequirement
    from apps.synthetic_data.generators import generate_job_data

    created = []
    for i in range(n):
        data = generate_job_data()
        skills = data.pop("skills", [])
        data["external_id"] = f"syn_{uuid.uuid4().hex[:12]}"
        job = JobPost.objects.create(**data)
        JobSkillRequirement.objects.bulk_create(
            [JobSkillRequirement(job=job, skill_name=s, is_required=True) for s in skills],
            ignore_conflicts=True,
        )
        created.append(job)
    logger.info("Total jobs created: %d", len(created))
    return created


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for HiringAI")
    parser.add_argument("--candidates", type=int, default=200)
    parser.add_argument("--jobs", type=int, default=20)
    parser.add_argument("--applications", type=int, default=500)
    args = parser.parse_args()

    from apps.synthetic_data.generators import generate_application_batch

    logger.info("Generating %d synthetic candidates...", args.candidates)
    create_candidates(args.candidates)

    logger.info("Generating %d synthetic jobs...", args.jobs)
    create_jobs(args.jobs)

    from apps.candidates.models import Candidate
    from apps.jobs.models import JobPost

    candidates = list(Candidate.objects.filter(is_synthetic=True))
    jobs = list(JobPost.objects.filter(is_synthetic=True))

    from apps.applications.models import Application

    logger.info("Generating applications (no_bias scenario)...")
    app_dicts = generate_application_batch(candidates=candidates, jobs=jobs, scenario_key="no_bias")
    Application.objects.bulk_create(
        [Application(**d) for d in app_dicts], ignore_conflicts=True
    )
    logger.info("Created %d applications (no_bias)", len(app_dicts))

    logger.info("Generating applications (gender_bias_tech scenario)...")
    app_dicts = generate_application_batch(candidates=candidates, jobs=jobs, scenario_key="gender_bias_tech")
    Application.objects.bulk_create(
        [Application(**d) for d in app_dicts], ignore_conflicts=True
    )
    logger.info("Created %d applications (gender_bias_tech)", len(app_dicts))

    logger.info("Done.")


if __name__ == "__main__":
    main()
