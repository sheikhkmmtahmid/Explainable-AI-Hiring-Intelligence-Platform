"""
Imports real job postings from the jobs.am dataset -- ~19,000 postings from
Armenia's CareerCenter HR portal, 2004-2015. License was never confirmed on
Kaggle's own page (a JS-rendered SPA that can't be fetched directly to check);
imported anyway per the user's explicit informed decision, disclosed on the
/about page along with the source link so a rights holder can request removal.

Source: https://www.kaggle.com/datasets/madhab/jobposts

Usage:
    python manage.py import_jobsam
    python manage.py import_jobsam --limit 500

Requires the Kaggle CLI to be authenticated (~/.kaggle/kaggle.json) and the
dataset already downloaded to data/kaggle/jobsam/ (this command will
download it on first run if missing).
"""
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("data/kaggle/jobsam")


def _download(stdout) -> Path:
    existing = list(DOWNLOAD_DIR.glob("*.csv"))
    if existing:
        stdout.write(f"Using cached file: {existing[0]}")
        return existing[0]

    import kaggle

    stdout.write("Downloading madhab/jobposts via Kaggle API...")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files("madhab/jobposts", path=str(DOWNLOAD_DIR), unzip=True)
    found = list(DOWNLOAD_DIR.glob("*.csv"))
    if not found:
        raise FileNotFoundError(f"No CSV found in {DOWNLOAD_DIR} after download")
    return found[0]


class Command(BaseCommand):
    help = "Import real job postings from the jobs.am / Armenian CareerCenter dataset"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Max rows to import (0 = unlimited)")

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

        df = pd.read_csv(csv_path)
        expected_cols = {"Title", "Company", "Location", "JobDescription", "JobRequirment", "RequiredQual", "Year", "Month", "IT"}
        missing = expected_cols - set(df.columns)
        if missing:
            self.stderr.write(self.style.ERROR(f"jobs.am CSV is missing expected columns: {missing}"))
            return

        df = df.reset_index().rename(columns={"index": "_row_id"})
        if limit:
            df = df.head(limit)

        org = get_public_dataset_org()
        total = len(df)
        self.stdout.write(f"Importing up to {total} jobs.am postings...")

        created_jobs = []
        skipped = 0
        for _, row in df.iterrows():
            external_id = str(row["_row_id"])
            if JobPost.objects.filter(source="jobsam", external_id=external_id).exists():
                skipped += 1
                continue

            title = clean_text(row.get("Title"))
            if not title:
                skipped += 1
                continue

            description = clean_text(row.get("JobDescription"))
            company = truncate(clean_text(row.get("Company")), 255) or "Unknown Employer"
            requirements = "\n\n".join(
                filter(None, [clean_text(row.get("JobRequirment")), clean_text(row.get("RequiredQual"))])
            )

            # Dedup key is title+company+requirements+description together --
            # company+requirements alone would falsely collapse different real
            # companies' postings when one field is blank; verified jobs.am's
            # "Accountant" postings alone span 250 distinct real companies
            # that mostly have a blank JobDescription.
            dedup_basis = f"{title}\n{company}\n{requirements}\n{description}"
            if is_duplicate_job_content(dedup_basis):
                skipped += 1
                continue
            dedup_hash = content_hash_for(dedup_basis)

            location = clean_text(row.get("Location"))
            parts = [p.strip() for p in location.split(",")] if location else []
            city = truncate(parts[0], 200) if parts else ""
            country = truncate(parts[-1], 200) if len(parts) > 1 else ("Armenia" if city else "")

            year = row.get("Year")
            month = row.get("Month")
            posted_at = None
            try:
                if pd.notna(year) and pd.notna(month):
                    posted_at = timezone.make_aware(timezone.datetime(int(year), int(month), 1))
            except (TypeError, ValueError):
                pass

            job = JobPost.objects.create(
                organization=org,
                title=truncate(title, 300),
                company=company,
                description=description,
                requirements=requirements,
                city=city,
                country=country,
                industry="Information Technology" if bool(row.get("IT")) else "",
                posted_at=posted_at,
                source="jobsam",
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
            f"\nDone. {len(created_jobs)} jobs.am jobs imported. Run backfill_job_embeddings next."
        ))
