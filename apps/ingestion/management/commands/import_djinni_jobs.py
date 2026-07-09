"""
Imports real job postings from the Djinni Recruitment Dataset (English job
descriptions), MIT licensed.

Source: https://huggingface.co/datasets/lang-uk/recruitment-dataset-job-descriptions-english

Usage:
    python manage.py import_djinni_jobs --limit 2000
    python manage.py import_djinni_jobs --limit 0   # unlimited (~141,897 rows)
"""
import logging
import re
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

PARQUET_URL = "https://huggingface.co/api/datasets/lang-uk/recruitment-dataset-job-descriptions-english/parquet/default/train/0.parquet"
CACHE_PATH = Path("data/dataset_cache/djinni_jobs.parquet")


def _download(stdout) -> Path:
    import requests

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        stdout.write(f"Using cached file: {CACHE_PATH}")
        return CACHE_PATH

    stdout.write(f"Downloading {PARQUET_URL} ...")
    resp = requests.get(PARQUET_URL, timeout=120)
    resp.raise_for_status()
    CACHE_PATH.write_bytes(resp.content)
    stdout.write(f"Saved to {CACHE_PATH} ({len(resp.content):,} bytes)")
    return CACHE_PATH


def _experience_level_from_years(exp_years_raw: str) -> str:
    match = re.search(r"(\d+(?:\.\d+)?)", exp_years_raw or "")
    years = float(match.group(1)) if match else 0.0
    if years < 1:
        return "entry"
    if years < 3:
        return "mid"
    if years < 6:
        return "senior"
    if years < 10:
        return "lead"
    return "executive"


class Command(BaseCommand):
    help = "Import real job postings from the Djinni Recruitment Dataset (MIT)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=2000, help="Max rows to import (0 = unlimited)")

    def handle(self, *args, **options):
        import pandas as pd
        from apps.ingestion.dataset_import import (
            clean_text, content_hash_for, extract_job_skills_batch,
            get_public_dataset_org, is_duplicate_job_content, truncate,
        )
        from apps.jobs.models import JobPost

        limit = options["limit"]
        parquet_path = _download(self.stdout)

        df = pd.read_parquet(parquet_path)
        expected_cols = {"Position", "Long Description", "Company Name", "Exp Years", "Primary Keyword", "Published", "id"}
        missing = expected_cols - set(df.columns)
        if missing:
            self.stderr.write(self.style.ERROR(f"Djinni jobs parquet is missing expected columns: {missing}"))
            return

        if limit:
            df = df.head(limit)

        org = get_public_dataset_org()
        total = len(df)
        self.stdout.write(f"Importing up to {total} Djinni job postings...")

        created_jobs = []
        skipped = 0
        for _, row in df.iterrows():
            external_id = clean_text(row.get("id"))
            if not external_id or JobPost.objects.filter(source="djinni", external_id=external_id).exists():
                skipped += 1
                continue

            title = clean_text(row.get("Position"))
            if not title:
                skipped += 1
                continue

            description = clean_text(row.get("Long Description"))
            company = truncate(clean_text(row.get("Company Name")), 255) or "Unknown Employer"

            # Djinni's job schema has no separate requirements field -- the
            # whole posting is one "Long Description" blob, so title+company
            # +description is the full dedup key here.
            dedup_basis = f"{title}\n{company}\n{description}"
            if is_duplicate_job_content(dedup_basis):
                skipped += 1
                continue
            dedup_hash = content_hash_for(dedup_basis)

            posted_at = None
            published = row.get("Published")
            if pd.notna(published):
                try:
                    posted_at = pd.Timestamp(published).to_pydatetime()
                except (ValueError, TypeError):
                    posted_at = None

            job = JobPost.objects.create(
                organization=org,
                title=truncate(title, 300),
                company=company,
                description=description,
                job_function=truncate(clean_text(row.get("Primary Keyword")), 255),
                experience_level=_experience_level_from_years(clean_text(row.get("Exp Years"))),
                posted_at=posted_at,
                source="djinni",
                external_id=external_id,
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
            f"\nDone. {len(created_jobs)} Djinni jobs imported. Run backfill_job_embeddings next."
        ))
