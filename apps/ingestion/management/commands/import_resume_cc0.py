"""
Imports real resumes from the CC0-licensed Resume Dataset (2,484 resumes
scraped from livecareer.com's example/template resumes -- these are
professionally-written sample resumes, not private individuals' personal
documents, which is part of why this source was judged safe to use).

Source: https://huggingface.co/datasets/opensporks/resumes
        (mirrors https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset)

Runs the same CV-parsing pipeline as a real upload (skill/experience
extraction + SBERT embedding) so these candidates are fully matchable.

Usage:
    python manage.py import_resume_cc0
"""
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

PARQUET_URL = "https://huggingface.co/api/datasets/opensporks/resumes/parquet/default/train/0.parquet"
CACHE_PATH = Path("data/dataset_cache/resume_cc0.parquet")


def _download(stdout) -> Path:
    import requests

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        stdout.write(f"Using cached file: {CACHE_PATH}")
        return CACHE_PATH

    stdout.write(f"Downloading {PARQUET_URL} ...")
    resp = requests.get(PARQUET_URL, timeout=60)
    resp.raise_for_status()
    CACHE_PATH.write_bytes(resp.content)
    stdout.write(f"Saved to {CACHE_PATH} ({len(resp.content):,} bytes)")
    return CACHE_PATH


class Command(BaseCommand):
    help = "Import real resumes from the CC0 Resume Dataset (snehaanbhawal/opensporks)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Max rows to import (0 = unlimited, 2,484 rows total)")
        parser.add_argument("--embed-batch", type=int, default=64, help="SBERT encode batch size")

    def handle(self, *args, **options):
        import pandas as pd
        from apps.candidates.models import Candidate
        from apps.ingestion.dataset_import import (
            clean_text, content_hash_for, embed_candidates_batch, get_public_dataset_org,
            is_duplicate_candidate_content, make_imported_email, process_candidate_text, truncate,
        )

        limit = options["limit"]
        parquet_path = _download(self.stdout)

        df = pd.read_parquet(parquet_path)
        expected_cols = {"ID", "Resume_str", "Category"}
        missing = expected_cols - set(df.columns)
        if missing:
            self.stderr.write(self.style.ERROR(f"Resume dataset parquet is missing expected columns: {missing}"))
            return

        if limit:
            df = df.head(limit)

        org = get_public_dataset_org()
        total = len(df)
        self.stdout.write(f"Importing up to {total} resumes...")

        created_candidates = []
        skipped = 0
        for i, (_, row) in enumerate(df.iterrows(), start=1):
            external_id = clean_text(row.get("ID"))
            if not external_id or Candidate.objects.filter(source="cc0_resume", external_id=external_id).exists():
                skipped += 1
                continue

            resume_text = clean_text(row.get("Resume_str"))
            if not resume_text:
                skipped += 1
                continue
            if is_duplicate_candidate_content(resume_text):
                skipped += 1
                continue

            candidate = Candidate.objects.create(
                sourced_by_organization=org,
                full_name=f"Resume Dataset Candidate #{external_id}",
                email=make_imported_email(),
                current_title=truncate(clean_text(row.get("Category")).title(), 255),
                source="cc0_resume",
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
            f"\nDone. {len(created_candidates)} CC0 resume candidates imported."
        ))
