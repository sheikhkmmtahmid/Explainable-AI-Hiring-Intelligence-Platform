"""
Imports real resumes from noran-mohamed/Resume-Classification-Dataset
(repo code is MIT licensed). Included per the user's explicit informed
decision despite the dataset's own README noting personal-information
exposure concerns (43% of the source resumes were scraped from Google/Bing
Images and OCR'd) -- a license on the surrounding code doesn't address that
consent gap, which is disclosed plainly on the /about page.

Source: https://github.com/noran-mohamed/Resume-Classification-Dataset
        (Dataset.csv, fetched via the Git LFS media endpoint since the repo
        tracks this file with LFS -- the plain raw.githubusercontent.com URL
        only returns the LFS pointer, not the actual content)

Runs the same CV-parsing pipeline as a real upload (skill/experience
extraction + SBERT embedding) so these candidates are fully matchable.

Usage:
    python manage.py import_resume_noranmohamed --limit 2000
    python manage.py import_resume_noranmohamed --limit 0   # unlimited (13,389 rows)
"""
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

CSV_URL = "https://media.githubusercontent.com/media/noran-mohamed/Resume-Classification-Dataset/main/Dataset.csv"
CACHE_PATH = Path("data/dataset_cache/noran_mohamed_dataset.csv")


def _download(stdout) -> Path:
    import requests

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        stdout.write(f"Using cached file: {CACHE_PATH}")
        return CACHE_PATH

    stdout.write(f"Downloading {CSV_URL} ...")
    resp = requests.get(CSV_URL, timeout=120)
    resp.raise_for_status()
    CACHE_PATH.write_bytes(resp.content)
    stdout.write(f"Saved to {CACHE_PATH} ({len(resp.content):,} bytes)")
    return CACHE_PATH


class Command(BaseCommand):
    help = "Import real resumes from noran-mohamed/Resume-Classification-Dataset"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=2000, help="Max rows to import (0 = unlimited)")
        parser.add_argument("--embed-batch", type=int, default=64, help="SBERT encode batch size")

    def handle(self, *args, **options):
        import pandas as pd
        from apps.candidates.models import Candidate
        from apps.ingestion.dataset_import import (
            clean_text, content_hash_for, embed_candidates_batch, get_public_dataset_org,
            is_duplicate_candidate_content, make_imported_email, process_candidate_text, truncate,
        )

        limit = options["limit"]
        csv_path = _download(self.stdout)

        df = pd.read_csv(csv_path)
        expected_cols = {"Category", "Text"}
        missing = expected_cols - set(df.columns)
        if missing:
            self.stderr.write(self.style.ERROR(f"noran-mohamed CSV is missing expected columns: {missing}"))
            return

        df = df.reset_index().rename(columns={"index": "_row_id"})
        if limit:
            df = df.head(limit)

        org = get_public_dataset_org()
        total = len(df)
        self.stdout.write(f"Importing up to {total} noran-mohamed resumes...")

        created_candidates = []
        skipped = 0
        for i, (_, row) in enumerate(df.iterrows(), start=1):
            external_id = str(row["_row_id"])
            if Candidate.objects.filter(source="noran_mohamed", external_id=external_id).exists():
                skipped += 1
                continue

            resume_text = clean_text(row.get("Text"))
            if not resume_text:
                skipped += 1
                continue
            if is_duplicate_candidate_content(resume_text):
                skipped += 1
                continue

            candidate = Candidate.objects.create(
                sourced_by_organization=org,
                full_name=f"Resume Classification Candidate #{external_id}",
                email=make_imported_email(),
                current_title=truncate(clean_text(row.get("Category")), 255),
                source="noran_mohamed",
                external_id=external_id,
                content_hash=content_hash_for(resume_text),
                is_synthetic=False,
            )
            process_candidate_text(candidate, resume_text)
            created_candidates.append(candidate)

            if i % 200 == 0:
                self.stdout.write(f"  Processed {i}/{total}...")

        self.stdout.write(f"Created {len(created_candidates)} candidates, skipped {skipped}.")

        if created_candidates:
            self.stdout.write("Embedding candidates (batched)...")
            embedded = embed_candidates_batch(created_candidates, batch_size=options["embed_batch"])
            self.stdout.write(f"Embedded {embedded} candidates.")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(created_candidates)} noran-mohamed resume candidates imported."
        ))
