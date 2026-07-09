"""
Imports real job postings from the EMSCAD dataset (Employment Scam Aegean
Dataset), CC0-1.0 licensed, via its HuggingFace CSV mirror.

Source: https://huggingface.co/datasets/victor/real-or-fake-fake-jobposting-prediction
Original: https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction

Fraudulent-flagged postings (fraudulent == 1) are excluded -- this is a
hiring platform, not a fraud-detection tool, and importing known scam
listings as real JobPost data would pollute matching/fairness data with no
upside.

Usage:
    python manage.py import_emscad
    python manage.py import_emscad --limit 500
"""
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

CSV_URL = "https://huggingface.co/datasets/victor/real-or-fake-fake-jobposting-prediction/resolve/main/fake_job_postings.csv"
CACHE_PATH = Path("data/dataset_cache/emscad_fake_job_postings.csv")

EMPLOYMENT_TYPE_MAP = {
    "full-time": "full_time",
    "part-time": "part_time",
    "contract": "contract",
    "temporary": "contract",
    "internship": "internship",
    "other": "full_time",
}

EXPERIENCE_LEVEL_MAP = {
    "internship": "entry",
    "entry level": "entry",
    "associate": "mid",
    "mid-senior level": "senior",
    "director": "lead",
    "executive": "executive",
    "not applicable": "mid",
}

# Only the clear-cut degree-level values are mapped; ambiguous ones
# (Certification, Professional, Vocational, partial coursework) are left
# unmapped -- compute_education_score treats an unmapped/blank requirement
# as "no stated requirement," which is more honest than forcing a guess.
REQUIRED_EDUCATION_MAP = {
    "high school or equivalent": "high_school",
    "associate degree": "associate",
    "bachelor's degree": "bachelor",
    "master's degree": "master",
    "doctorate": "phd",
}


def _download(stdout) -> Path:
    import requests

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        stdout.write(f"Using cached file: {CACHE_PATH}")
        return CACHE_PATH

    stdout.write(f"Downloading {CSV_URL} ...")
    resp = requests.get(CSV_URL, timeout=60)
    resp.raise_for_status()
    CACHE_PATH.write_bytes(resp.content)
    stdout.write(f"Saved to {CACHE_PATH} ({len(resp.content):,} bytes)")
    return CACHE_PATH


class Command(BaseCommand):
    help = "Import real job postings from the EMSCAD dataset (CC0)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Max rows to import (0 = unlimited)")

    def handle(self, *args, **options):
        import pandas as pd
        from apps.ingestion.dataset_import import (
            clean_text, content_hash_for, extract_job_skills_batch,
            get_public_dataset_org, is_duplicate_job_content, truncate,
        )
        from apps.jobs.models import JobPost

        limit = options["limit"]
        csv_path = _download(self.stdout)

        df = pd.read_csv(csv_path)
        expected_cols = {
            "job_id", "title", "location", "department", "salary_range",
            "company_profile", "description", "requirements", "benefits",
            "employment_type", "required_experience", "required_education",
            "industry", "function", "fraudulent",
        }
        missing = expected_cols - set(df.columns)
        if missing:
            self.stderr.write(self.style.ERROR(f"EMSCAD CSV is missing expected columns: {missing}"))
            return

        excluded = int((df["fraudulent"] == 1).sum())
        df = df[df["fraudulent"] == 0]
        if limit:
            df = df.head(limit)

        org = get_public_dataset_org()
        total = len(df)
        self.stdout.write(f"Importing {total} EMSCAD job postings ({excluded} fraudulent rows excluded)...")

        created_jobs = []
        skipped = 0
        for _, row in df.iterrows():
            job_id = str(row["job_id"])
            if JobPost.objects.filter(source="emscad", external_id=job_id).exists():
                skipped += 1
                continue

            title = truncate(clean_text(row.get("title")), 300) or "Untitled position"
            description = clean_text(row.get("company_profile")) + "\n\n" + clean_text(row.get("description"))
            requirements = clean_text(row.get("requirements"))
            industry = truncate(clean_text(row.get("industry")), 255)
            # EMSCAD has no real company-name column -- industry is the best
            # available stand-in, which means dedup here can't fully tell
            # apart two different real employers in the same industry (a
            # known, disclosed limitation of this specific source).
            company = truncate(industry or f"Employer (EMSCAD #{job_id})", 255)

            # Dedup key is title+company+requirements+description together --
            # using company+requirements alone would falsely collapse two
            # different real employers' postings when one of those fields is
            # blank (verified this happened with jobs.am's Accountant listings,
            # which had 250 distinct real companies sharing a blank description).
            dedup_basis = f"{title}\n{company}\n{requirements}\n{description}"
            if is_duplicate_job_content(dedup_basis):
                skipped += 1
                continue
            dedup_hash = content_hash_for(dedup_basis)

            # EMSCAD location format is "COUNTRY_CODE, STATE/REGION, CITY"
            # e.g. "US, NY, New York" -- verified against the raw CSV.
            location = clean_text(row.get("location"))
            parts = [p.strip() for p in location.split(",")] if location else []
            country = truncate(parts[0], 200) if len(parts) > 0 else ""
            region = truncate(parts[1], 200) if len(parts) > 1 else ""
            city = truncate(parts[2], 200) if len(parts) > 2 else ""

            employment_type = EMPLOYMENT_TYPE_MAP.get(
                clean_text(row.get("employment_type")).lower(), "full_time"
            )
            experience_level = EXPERIENCE_LEVEL_MAP.get(
                clean_text(row.get("required_experience")).lower(), "mid"
            )
            required_education = REQUIRED_EDUCATION_MAP.get(
                clean_text(row.get("required_education")).lower(), ""
            )

            job = JobPost.objects.create(
                organization=org,
                title=title,
                company=company,
                description=description,
                requirements=requirements,
                city=city,
                region=region,
                country=country,
                industry=industry,
                job_function=clean_text(row.get("function")),
                employment_type=employment_type,
                experience_level=experience_level,
                required_education=required_education,
                source="emscad",
                external_id=job_id,
                content_hash=dedup_hash,
                is_synthetic=False,
            )
            created_jobs.append(job)

        self.stdout.write(f"Created {len(created_jobs)} jobs, skipped {skipped} already-imported.")

        if created_jobs:
            self.stdout.write("Extracting skills...")
            skill_count = extract_job_skills_batch(created_jobs)
            self.stdout.write(f"Created {skill_count} skill requirements.")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(created_jobs)} EMSCAD jobs imported. "
            "Run backfill_job_embeddings next."
        ))
