import logging
from django.utils import timezone
from config.celery import app as celery_app

logger = logging.getLogger(__name__)

AVAILABLE_SCENARIOS = [
    "no_bias",
    "gender_bias_tech",
    "age_bias_senior",
    "ethnicity_bias",
    "disability_bias",
    "mild_gender_bias",
]


@celery_app.task(bind=True)
def generate_synthetic_candidates_task(self, count: int = 100):
    from apps.candidates.models import Candidate, CandidateSkill
    from apps.synthetic_data.generators import generate_candidate_data
    from apps.synthetic_data.models import SyntheticGenerationRun

    run = SyntheticGenerationRun.objects.create(
        kind=SyntheticGenerationRun.Kind.CANDIDATES,
        count_requested=count,
        status="running",
        started_at=timezone.now(),
    )
    created = 0
    try:
        for _ in range(count):
            data = generate_candidate_data()
            skills = data.pop("skills")
            candidate = Candidate.objects.create(**data)
            CandidateSkill.objects.bulk_create([
                CandidateSkill(candidate=candidate, skill_name=s, source="inferred")
                for s in skills
            ], ignore_conflicts=True)
            created += 1

        run.count_created = created
        run.status = "done"
        run.completed_at = timezone.now()
        run.save()
        logger.info("Synthetic candidates created: %s", created)
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.save()
        logger.error("Synthetic candidate generation failed: %s", exc)
        raise


@celery_app.task(bind=True)
def generate_synthetic_jobs_task(self, count: int = 100):
    from apps.jobs.models import JobPost, JobSkillRequirement
    from apps.synthetic_data.generators import generate_job_data
    from apps.synthetic_data.models import SyntheticGenerationRun

    run = SyntheticGenerationRun.objects.create(
        kind=SyntheticGenerationRun.Kind.JOBS,
        count_requested=count,
        status="running",
        started_at=timezone.now(),
    )
    created = 0
    try:
        for _ in range(count):
            data = generate_job_data()
            skills = data.pop("skills")
            job = JobPost.objects.create(**data)
            JobSkillRequirement.objects.bulk_create([
                JobSkillRequirement(job=job, skill_name=s)
                for s in skills
            ], ignore_conflicts=True)
            created += 1

        run.count_created = created
        run.status = "done"
        run.completed_at = timezone.now()
        run.save()
        logger.info("Synthetic jobs created: %s", created)
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.save()
        logger.error("Synthetic job generation failed: %s", exc)
        raise


@celery_app.task(bind=True)
def generate_synthetic_applications_task(
    self,
    scenario_key: str = "no_bias",
    candidate_limit: int = 0,
    job_limit: int = 0,
    applications_per_candidate: int = 3,
):
    """
    Simulate recruiter decisions for all synthetic candidates × jobs
    using the specified bias scenario.

    scenario_key options:
        no_bias, gender_bias_tech, age_bias_senior,
        ethnicity_bias, disability_bias, mild_gender_bias
    """
    from apps.applications.models import Application
    from apps.candidates.models import Candidate
    from apps.jobs.models import JobPost
    from apps.synthetic_data.generators import generate_application_batch, BIAS_SCENARIOS
    from apps.synthetic_data.models import SyntheticGenerationRun

    if scenario_key not in BIAS_SCENARIOS:
        logger.error("Unknown bias scenario: %s. Valid: %s", scenario_key, list(BIAS_SCENARIOS.keys()))
        return

    run = SyntheticGenerationRun.objects.create(
        kind=SyntheticGenerationRun.Kind.APPLICATIONS,
        count_requested=0,
        status="running",
        started_at=timezone.now(),
        config={"scenario": scenario_key, "applications_per_candidate": applications_per_candidate},
    )

    try:
        candidates_qs = Candidate.objects.prefetch_related("skills").filter(is_synthetic=True)
        if candidate_limit:
            candidates_qs = candidates_qs[:candidate_limit]
        candidates = list(candidates_qs)

        jobs_qs = JobPost.objects.prefetch_related("skill_requirements").filter(is_synthetic=True)
        if job_limit:
            jobs_qs = jobs_qs[:job_limit]
        jobs = list(jobs_qs)

        if not candidates or not jobs:
            logger.warning("No synthetic candidates or jobs found. Generate them first.")
            run.status = "failed"
            run.error_message = "No synthetic candidates or jobs available."
            run.save()
            return

        application_dicts = generate_application_batch(
            candidates=candidates,
            jobs=jobs,
            scenario_key=scenario_key,
            applications_per_candidate=applications_per_candidate,
        )

        run.count_requested = len(application_dicts)

        created = 0
        for app_data in application_dicts:
            _, was_created = Application.objects.get_or_create(
                candidate=app_data["candidate"],
                job=app_data["job"],
                defaults={
                    "status": app_data["status"],
                    "recruiter_notes": app_data["recruiter_notes"],
                    "is_synthetic": True,
                },
            )
            if was_created:
                created += 1

        run.count_created = created
        run.status = "done"
        run.completed_at = timezone.now()
        run.save()
        logger.info(
            "Synthetic applications created: %d (scenario=%s)", created, scenario_key
        )

    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.save()
        logger.error("Synthetic application generation failed: %s", exc)
        raise
