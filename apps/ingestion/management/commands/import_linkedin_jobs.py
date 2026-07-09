"""
Imports real job postings from the LinkedIn Job Postings (2023-2024) Kaggle
dataset, CC BY-SA 4.0 licensed. The underlying postings were originally
scraped from LinkedIn, which prohibits scraping in its own Terms of Service
-- that risk exists independently of the CC BY-SA tag applied by the Kaggle
uploader, and is disclosed on the /about page per the user's informed
decision to include this source anyway.

Source: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings

Actual postings.csv columns were verified by downloading the file directly
(Kaggle's dataset page is a JS-rendered SPA and couldn't be checked any
other way) -- see the column list checked in `handle()` below.

Usage:
    python manage.py import_linkedin_jobs --limit 2000
    python manage.py import_linkedin_jobs --limit 0   # unlimited (123k+ rows)
"""
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("data/kaggle/linkedin")
CSV_PATH = DOWNLOAD_DIR / "postings.csv"

EMPLOYMENT_TYPE_MAP = {
    "full-time": "full_time",
    "part-time": "part_time",
    "contract": "contract",
    "temporary": "contract",
    "internship": "internship",
    "volunteer": "freelance",
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


def _download(stdout) -> Path:
    if CSV_PATH.exists():
        stdout.write(f"Using cached file: {CSV_PATH}")
        return CSV_PATH

    import kaggle

    stdout.write("Downloading arshkon/linkedin-job-postings via Kaggle API (this is a large dataset)...")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files("arshkon/linkedin-job-postings", path=str(DOWNLOAD_DIR), unzip=True)
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Expected {CSV_PATH} after download but it's missing")
    return CSV_PATH


class Command(BaseCommand):
    help = "Import real job postings from the LinkedIn Job Postings Kaggle dataset"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=2000, help="Max rows to import (0 = unlimited, 123k+ rows)")

    def handle(self, *args, **options):
        import pandas as pd
        from django.utils import timezone
        from apps.ingestion.dataset_import import (
            clean_text, content_hash_for, extract_job_skills_batch,
            get_public_dataset_org, is_duplicate_job_content, truncate,
        )
        from apps.jobs.models import JobPost

        limit = options["limit"]
        csv_path = _download(self.stdout)

        expected_cols = {
            "job_id", "company_name", "title", "description", "location",
            "formatted_work_type", "formatted_experience_level", "listed_time",
            "min_salary", "max_salary", "pay_period", "currency",
        }
        # Read just the header first to fail loudly before loading the whole
        # (large) file if the schema has drifted from what was verified.
        header_cols = set(pd.read_csv(csv_path, nrows=0).columns)
        missing = expected_cols - header_cols
        if missing:
            self.stderr.write(self.style.ERROR(f"LinkedIn postings.csv is missing expected columns: {missing}"))
            return

        nrows = None if not limit else limit
        df = pd.read_csv(csv_path, nrows=nrows)

        org = get_public_dataset_org()
        total = len(df)
        self.stdout.write(f"Importing up to {total} LinkedIn job postings...")

        created_jobs = []
        skipped = 0
        for _, row in df.iterrows():
            job_id = str(row["job_id"])
            if JobPost.objects.filter(source="linkedin", external_id=job_id).exists():
                skipped += 1
                continue

            title = clean_text(row.get("title"))
            if not title:
                skipped += 1
                continue

            description = clean_text(row.get("description"))
            company = truncate(clean_text(row.get("company_name")), 255) or "Unknown Employer"
            requirements = clean_text(row.get("skills_desc"))

            # Dedup key is title+company+requirements+description together --
            # avoids falsely collapsing different real companies' postings
            # when one of those fields happens to be blank.
            dedup_basis = f"{title}\n{company}\n{requirements}\n{description}"
            if is_duplicate_job_content(dedup_basis):
                skipped += 1
                continue
            dedup_hash = content_hash_for(dedup_basis)

            location = clean_text(row.get("location"))
            parts = [p.strip() for p in location.split(",")] if location else []
            city = truncate(parts[0], 200) if parts else ""
            region = truncate(parts[-1], 200) if len(parts) > 1 else ""

            employment_type = EMPLOYMENT_TYPE_MAP.get(
                clean_text(row.get("formatted_work_type")).lower(), "full_time"
            )
            experience_level = EXPERIENCE_LEVEL_MAP.get(
                clean_text(row.get("formatted_experience_level")).lower(), "mid"
            )

            salary_min = salary_max = None
            if clean_text(row.get("pay_period")).upper() == "YEARLY":
                salary_min = row.get("min_salary") if pd.notna(row.get("min_salary")) else None
                salary_max = row.get("max_salary") if pd.notna(row.get("max_salary")) else None

            posted_at = None
            listed_time = row.get("listed_time")
            if pd.notna(listed_time):
                try:
                    posted_at = timezone.make_aware(
                        timezone.datetime.fromtimestamp(int(listed_time) / 1000)
                    )
                except (ValueError, OSError, OverflowError):
                    posted_at = None

            job = JobPost.objects.create(
                organization=org,
                title=truncate(title, 300),
                company=company,
                description=description,
                requirements=requirements,
                city=city,
                region=region,
                work_model="remote" if row.get("remote_allowed") == 1 else "onsite",
                employment_type=employment_type,
                experience_level=experience_level,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=clean_text(row.get("currency")) or "USD",
                posted_at=posted_at,
                external_url=clean_text(row.get("job_posting_url")),
                source="linkedin",
                external_id=job_id,
                content_hash=dedup_hash,
                is_synthetic=False,
            )
            created_jobs.append(job)

        self.stdout.write(f"Created {len(created_jobs)} jobs, skipped {skipped}.")

        if created_jobs:
            self.stdout.write("Extracting skills...")
            skill_count = extract_job_skills_batch(created_jobs)
            self.stdout.write(f"Created {skill_count} skill requirements.")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(created_jobs)} LinkedIn jobs imported. Run backfill_job_embeddings next."
        ))
