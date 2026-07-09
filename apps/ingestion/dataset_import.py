"""
Shared helpers for the public-dataset importers in
apps/ingestion/management/commands/import_*.py.

Every importer downloads one external dataset and maps it onto JobPost or
Candidate, but none of them reimplement parsing/embedding -- they call the
exact same pipeline the app already runs for a real CV upload
(apps.parsing.tasks.parse_cv_task) or a synthetic candidate
(apps.synthetic_data.management.commands.generate_candidates), just
synchronously instead of via Celery, matching the pattern generate_candidates.py
already uses for bulk work outside a request/response cycle.
"""
import hashlib
import logging
import uuid

logger = logging.getLogger(__name__)

PUBLIC_DATASET_ORG_SLUG = "public-dataset-import"
PUBLIC_DATASET_ORG_NAME = "Public Dataset Import"


def get_public_dataset_org():
    from apps.organizations.models import Organization

    org, _ = Organization.objects.get_or_create(
        slug=PUBLIC_DATASET_ORG_SLUG,
        defaults={"name": PUBLIC_DATASET_ORG_NAME},
    )
    return org


def make_imported_email() -> str:
    """Real-world resume datasets rarely include a valid, unique email --
    follow the same fake-domain convention generate_candidates.py uses for
    synthetic candidates (synthetic.<uuid8>@candidate.dev), but with a
    distinguishing prefix so imported-real-text candidates stay traceable
    from fully-synthetic ones."""
    return f"imported.{uuid.uuid4().hex[:8]}@candidate.dev"


def process_candidate_text(candidate, raw_text: str) -> None:
    """Run the same CV-parsing sequence apps.parsing.tasks.parse_cv_task runs
    for a real upload (skills, experience, years-of-experience), synchronously.
    Does NOT embed -- call embed_candidates_batch() after processing a whole
    batch, so SBERT runs once in batched mode instead of once per row."""
    from apps.candidates.services import add_skill, update_years_of_experience
    from apps.candidates.models import CandidateExperience
    from apps.parsing.services import parse_cv_text

    candidate.raw_cv_text = raw_text
    candidate.save(update_fields=["raw_cv_text"])

    parsed = parse_cv_text(raw_text)

    for skill_data in parsed.get("skills", []):
        add_skill(candidate, source="cv_parsed", **skill_data)

    for entry in parsed.get("experience_entries") or []:
        job_title = truncate(entry["job_title"], 255)
        if not job_title:
            continue
        CandidateExperience.objects.update_or_create(
            candidate=candidate,
            job_title=job_title,
            company=truncate(entry.get("company", ""), 255),
            start_date=entry.get("start_date"),
            defaults={
                "location": truncate(entry.get("location", ""), 255),
                "end_date": entry.get("end_date"),
                "is_current": entry.get("is_current", False),
                "description": entry.get("description", ""),
            },
        )

    if parsed.get("experience_entries"):
        update_years_of_experience(candidate)
    elif parsed.get("years_of_experience") and not candidate.years_of_experience:
        candidate.years_of_experience = parsed["years_of_experience"]
        candidate.save(update_fields=["years_of_experience"])


def embed_candidates_batch(candidates, batch_size: int = 64) -> int:
    """Batch-encode SBERT embeddings for Candidate objects that already have
    their skills/experience saved. Mirrors the batching approach in
    apps/jobs/management/commands/backfill_job_embeddings.py rather than one
    encode_text() call per row."""
    from apps.candidates.models import CandidateEmbedding
    from apps.matching.tasks import _build_candidate_text
    from ml.embeddings.encoder import encode_batch, get_model_name

    candidates = list(candidates)
    if not candidates:
        return 0

    model_name = get_model_name()
    created = 0
    for start in range(0, len(candidates), batch_size):
        chunk = candidates[start:start + batch_size]
        texts = [_build_candidate_text(c) for c in chunk]
        vectors = encode_batch(texts, batch_size=batch_size)
        CandidateEmbedding.objects.bulk_create(
            [
                CandidateEmbedding(candidate=c, vector=vec.tolist(), model_name=model_name)
                for c, vec in zip(chunk, vectors)
            ],
            ignore_conflicts=True,
        )
        created += len(chunk)
    return created


def extract_job_skills_batch(jobs, batch_size: int = 500) -> int:
    """Populate JobSkillRequirement for JobPost objects by running the same
    skill extraction used for CV parsing (with its keyword-fallback safety
    net) against each job's description+requirements text -- mirrors the
    convention in apps/jobs/management/commands/generate_jobs.py."""
    from apps.jobs.models import JobSkillRequirement
    from apps.parsing.services import extract_skills_from_text

    rows = []
    created = 0
    for job in jobs:
        text = f"{job.title}\n{job.description}\n{job.requirements}"
        for skill in extract_skills_from_text(text):
            rows.append(JobSkillRequirement(
                job=job, skill_name=skill["skill_name"],
                skill_category=skill.get("category", ""), is_required=True,
            ))
        if len(rows) >= batch_size:
            JobSkillRequirement.objects.bulk_create(rows, ignore_conflicts=True)
            created += len(rows)
            rows = []
    if rows:
        JobSkillRequirement.objects.bulk_create(rows, ignore_conflicts=True)
        created += len(rows)
    return created


def content_hash_for(text: str) -> str:
    """SHA-256 of whitespace-normalised, lowercased text -- used to detect
    the same real resume/job posting appearing more than once, whether from
    a re-run of the same importer or genuine overlap between two different
    public datasets (e.g. two sources both scraping livecareer.com)."""
    normalised = " ".join((text or "").split()).lower()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def is_duplicate_candidate_content(text: str) -> bool:
    from apps.candidates.models import Candidate
    return Candidate.objects.filter(content_hash=content_hash_for(text)).exists()


def is_duplicate_job_content(text: str) -> bool:
    from apps.jobs.models import JobPost
    return JobPost.objects.filter(content_hash=content_hash_for(text)).exists()


def truncate(value: str, max_length: int) -> str:
    """Defensively cap a string to a model field's max_length -- source CSVs
    occasionally have malformed/overlong values in fields we expect to be
    short (e.g. a location cell that's actually a full sentence)."""
    return value[:max_length] if value else value


def clean_text(value) -> str:
    """Normalise a raw dataset cell to a plain string: NaN/None -> "", strip
    whitespace. Datasets read via pandas represent missing cells as float
    NaN, which breaks straight string concatenation if not guarded."""
    if value is None:
        return ""
    try:
        import math
        if isinstance(value, float) and math.isnan(value):
            return ""
    except TypeError:
        pass
    return str(value).strip()
