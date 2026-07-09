"""
Imports the Bertrand & Mullainathan (2004) resume-callback audit study,
CC BY-SA 3.0 licensed via OpenIntro. This is the only real-outcome dataset in
this project: researchers sent fictional resumes (identical except for a
randomly assigned first name signalling race/gender) to real job postings in
Boston and Chicago newspapers in 2001-2002, and recorded whether the employer
actually called back. 4,870 resumes sent to 1,323 real job postings.

Citation: Bertrand M, Mullainathan S. 2004. "Are Emily and Greg More
Employable than Lakisha and Jamal? A Field Experiment on Labor Market
Discrimination." American Economic Review 94:4 (991-1013).

Source: https://www.openintro.org/data/index.php?data=resume
CSV: https://www.openintro.org/data/csv/resume.csv

Important honesty notes (also stated on /about):
  - The "candidates" here are fictional constructs the researchers built to
    test discrimination -- not real people. race/gender are the name-coded
    experimental variable the study assigned, not anyone's self-identified
    demographics, and are labelled as such rather than presented as if a
    real candidate reported them.
  - received_callback (did the employer respond) is a REAL, published
    employer decision -- unlike every other dataset in this project, so it
    is mapped onto real Application status, not left as an unlabelled row.
  - There is no free-text resume in this dataset (it's structured
    attributes, not authored prose), so a short descriptive summary is
    assembled from those attributes for embedding purposes -- this is
    disclosed rather than presented as if it were original resume text.

Usage:
    python manage.py import_openintro_audit_study
"""
import logging
import math
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


def clean_text(value) -> str:
    """Local copy of apps.ingestion.dataset_import.clean_text -- duplicated
    rather than imported at module level because that module pulls in
    Django app code, which can't safely be imported before django.setup()
    runs, and this helper is used by module-level functions that build
    description text outside of handle()."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()

CSV_URL = "https://www.openintro.org/data/csv/resume.csv"
CACHE_PATH = Path("data/dataset_cache/openintro_resume.csv")
ORG_SLUG = "audit-study-2004"
ORG_NAME = "Audit Study 2004 (Bertrand & Mullainathan)"

# job_req_min_experience is measured in years directly in this dataset.
EXPERIENCE_LEVEL_BRACKETS = [
    (1, "entry"), (3, "mid"), (6, "senior"), (10, "lead"),
]


def _experience_level_from_years(years) -> str:
    try:
        years = float(years)
    except (TypeError, ValueError):
        return "mid"
    for cutoff, level in EXPERIENCE_LEVEL_BRACKETS:
        if years < cutoff:
            return level
    return "executive"


def _download(stdout) -> Path:
    import requests

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        stdout.write(f"Using cached file: {CACHE_PATH}")
        return CACHE_PATH

    stdout.write(f"Downloading {CSV_URL} ...")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; research data import)"}
    resp = requests.get(CSV_URL, headers=headers, timeout=60)
    resp.raise_for_status()
    CACHE_PATH.write_bytes(resp.content)
    stdout.write(f"Saved to {CACHE_PATH} ({len(resp.content):,} bytes)")
    return CACHE_PATH


def _build_job_description(row) -> str:
    """The study recorded job type, industry, ownership, and city for every
    posting -- that's real and always available, unlike the requirement
    flags below, which are genuinely blank for about a fifth of postings in
    the source data. Building the description from these fields means a job
    with no recorded requirements still gets an accurate, non-empty
    description instead of a placeholder standing in for real content."""
    job_type = clean_text(row.get("job_type")).replace("_", " ")
    job_industry = clean_text(row.get("job_industry")).replace("_", " ")
    ownership = clean_text(row.get("job_ownership")).lower()
    city = clean_text(row.get("job_city"))

    parts = [f"A {job_type} position" if job_type else "A position"]
    if ownership and ownership != "unknown":
        parts.append(f"at a {ownership} employer")
    if job_industry:
        parts.append(f"in the {job_industry} industry")
    if city:
        parts.append(f"in {city}")
    return " ".join(parts).strip() + "."


def _build_job_requirements(row) -> str:
    reqs = []
    if row.get("job_req_any") == 1:
        reqs.append("requires some prior experience")
    if row.get("job_req_communication") == 1:
        reqs.append("requires communication skills")
    if row.get("job_req_education") == 1:
        reqs.append("requires a stated education level")
    if row.get("job_req_computer") == 1:
        reqs.append("requires computer skills")
    if row.get("job_req_organization") == 1:
        reqs.append("requires organizational skills")
    if row.get("job_req_min_experience"):
        try:
            reqs.append(f"minimum {int(row['job_req_min_experience'])} years experience")
        except (TypeError, ValueError):
            pass
    return "; ".join(reqs) or "No specific requirements were recorded for this posting in the original study."


def _build_candidate_summary(row) -> str:
    """No free-text resume exists in this dataset -- this assembles a short,
    honest descriptive summary from the real structured attributes so the
    candidate is still embeddable, without pretending it's original prose."""
    parts = [f"{row.get('years_experience', 0)} years of work experience."]
    if row.get("college_degree") == 1:
        parts.append(f"Completed {row.get('years_college', '?')} years of college, holds a degree.")
    elif row.get("years_college"):
        parts.append(f"{row.get('years_college')} years of college, no degree completed.")
    if row.get("computer_skills") == 1:
        parts.append("Has computer skills.")
    if row.get("special_skills") == 1:
        parts.append("Lists special skills.")
    if row.get("honors") == 1:
        parts.append("Received honors.")
    if row.get("worked_during_school") == 1:
        parts.append("Worked during school.")
    if row.get("volunteer") == 1:
        parts.append("Volunteer experience.")
    if row.get("military") == 1:
        parts.append("Military experience.")
    if row.get("employment_holes") == 1:
        parts.append("Has gaps in employment history.")
    return " ".join(parts)


class Command(BaseCommand):
    help = "Import the Bertrand & Mullainathan (2004) resume-callback audit study (CC BY-SA 3.0)"

    def add_arguments(self, parser):
        parser.add_argument("--embed-batch", type=int, default=64, help="SBERT encode batch size")

    def handle(self, *args, **options):
        import pandas as pd
        from apps.applications.models import Application
        from apps.candidates.models import Candidate
        from apps.ingestion.dataset_import import (
            content_hash_for, embed_candidates_batch,
            extract_job_skills_batch, make_imported_email, process_candidate_text, truncate,
        )
        from apps.jobs.models import JobPost
        from apps.organizations.models import Organization

        csv_path = _download(self.stdout)
        df = pd.read_csv(csv_path)
        expected_cols = {
            "job_ad_id", "job_city", "job_industry", "job_type", "received_callback",
            "firstname", "race", "gender", "years_experience", "college_degree",
        }
        missing = expected_cols - set(df.columns)
        if missing:
            self.stderr.write(self.style.ERROR(f"OpenIntro resume.csv is missing expected columns: {missing}"))
            return

        org, _ = Organization.objects.get_or_create(slug=ORG_SLUG, defaults={"name": ORG_NAME})

        # --- Jobs: one JobPost per unique job_ad_id ---
        self.stdout.write(f"Importing {df['job_ad_id'].nunique()} real job postings...")
        job_by_ad_id = {}
        created_jobs = []
        for job_ad_id, group in df.groupby("job_ad_id"):
            external_id = str(job_ad_id)
            existing = JobPost.objects.filter(source="openintro", external_id=external_id).first()
            if existing:
                job_by_ad_id[job_ad_id] = existing
                continue

            row = group.iloc[0]
            job_type = clean_text(row.get("job_type")).replace("_", " ").title()
            job_industry = clean_text(row.get("job_industry")).replace("_", " ").title()
            ownership = clean_text(row.get("job_ownership")).lower()
            company = (
                f"{ownership.title()} employer ({job_industry})" if ownership and ownership != "unknown"
                else f"Employer ({job_industry})"
            )
            description = _build_job_description(row)
            requirements = _build_job_requirements(row)
            dedup_basis = f"{job_type}\n{company}\n{description}\n{requirements}"

            job = JobPost.objects.create(
                organization=org,
                title=job_type or "Untitled position",
                company=truncate(company, 255),
                description=description,
                requirements=requirements,
                city=clean_text(row.get("job_city")),
                country="United States",
                industry=job_industry,
                job_function=job_type,
                experience_level=_experience_level_from_years(row.get("job_req_min_experience")),
                source="openintro",
                external_id=external_id,
                content_hash=content_hash_for(dedup_basis),
                is_synthetic=False,
            )
            job_by_ad_id[job_ad_id] = job
            created_jobs.append(job)

        self.stdout.write(f"Created {len(created_jobs)} jobs ({df['job_ad_id'].nunique() - len(created_jobs)} already existed).")
        if created_jobs:
            self.stdout.write("Extracting job skills...")
            skill_count = extract_job_skills_batch(created_jobs)
            self.stdout.write(f"Created {skill_count} skill requirements.")

        # --- Candidates + Applications: one per row ---
        self.stdout.write(f"Importing {len(df)} resumes with real callback outcomes...")
        created_candidates = []
        created_applications = 0
        skipped = 0

        for i, (idx, row) in enumerate(df.iterrows(), start=1):
            external_id = str(idx)
            if Candidate.objects.filter(source="openintro", external_id=external_id).exists():
                skipped += 1
                continue

            race_raw = clean_text(row.get("race")).lower()
            gender_raw = clean_text(row.get("gender")).lower()
            # Labelled explicitly as name-coded experimental variables, not a
            # real person's self-identified demographics -- these are
            # fictional resumes constructed specifically to test this.
            ethnicity = f"{race_raw.title()} (name-coded, audit study)" if race_raw else ""
            gender = {"f": "female", "m": "male"}.get(gender_raw, "")

            summary = _build_candidate_summary(row)
            highest_education = "bachelor" if row.get("college_degree") == 1 else "high_school"

            candidate = Candidate.objects.create(
                sourced_by_organization=org,
                full_name=truncate(clean_text(row.get("firstname")), 255) or f"Applicant #{external_id}",
                email=make_imported_email(),
                years_of_experience=float(row.get("years_experience") or 0),
                highest_education=highest_education,
                gender=gender,
                ethnicity=ethnicity,
                summary=truncate(summary, 5000),
                source="openintro",
                external_id=external_id,
                content_hash=content_hash_for(summary + external_id),
                is_synthetic=False,
            )
            process_candidate_text(candidate, summary)
            created_candidates.append(candidate)

            job = job_by_ad_id.get(row["job_ad_id"])
            if job:
                status = "shortlisted" if row.get("received_callback") == 1 else "rejected"
                Application.objects.create(
                    candidate=candidate, job=job, status=status, is_synthetic=False,
                )
                created_applications += 1

            if i % 500 == 0:
                self.stdout.write(f"  Processed {i}/{len(df)}...")

        self.stdout.write(f"Created {len(created_candidates)} candidates, {created_applications} applications, skipped {skipped}.")

        if created_candidates:
            self.stdout.write("Embedding candidates (batched)...")
            embedded = embed_candidates_batch(created_candidates, batch_size=options["embed_batch"])
            self.stdout.write(f"Embedded {embedded} candidates.")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(created_jobs)} jobs, {len(created_candidates)} candidates, "
            f"{created_applications} real-outcome applications imported."
        ))
