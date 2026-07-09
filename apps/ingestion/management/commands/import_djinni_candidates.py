"""
Imports real candidate profiles from the Djinni Recruitment Dataset (English
candidate profiles), MIT licensed. Profiles are anonymized by the dataset's
own maintainers (lang-uk) -- no real name is included -- so imported
candidates get a neutral placeholder name rather than a fabricated one; a
made-up "realistic" name would misrepresent the data as more identified
than it actually is.

Runs the same CV-parsing pipeline as a real upload (skill/experience
extraction + SBERT embedding) so these candidates are fully matchable, not
just decorative rows.

Source: https://huggingface.co/datasets/lang-uk/recruitment-dataset-candidate-profiles-english

Usage:
    python manage.py import_djinni_candidates --limit 2000
    python manage.py import_djinni_candidates --limit 0   # unlimited (~210,250 rows)
"""
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

PARQUET_URL = "https://huggingface.co/api/datasets/lang-uk/recruitment-dataset-candidate-profiles-english/parquet/default/train/0.parquet"
CACHE_PATH = Path("data/dataset_cache/djinni_candidates.parquet")


def _download(stdout) -> Path:
    import requests

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        stdout.write(f"Using cached file: {CACHE_PATH}")
        return CACHE_PATH

    stdout.write(f"Downloading {PARQUET_URL} ...")
    resp = requests.get(PARQUET_URL, timeout=180)
    resp.raise_for_status()
    CACHE_PATH.write_bytes(resp.content)
    stdout.write(f"Saved to {CACHE_PATH} ({len(resp.content):,} bytes)")
    return CACHE_PATH


class Command(BaseCommand):
    help = "Import real candidate profiles from the Djinni Recruitment Dataset (MIT)"

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
        parquet_path = _download(self.stdout)

        df = pd.read_parquet(parquet_path)
        expected_cols = {"Position", "Moreinfo", "Looking For", "Highlights", "Experience Years", "CV", "id"}
        missing = expected_cols - set(df.columns)
        if missing:
            self.stderr.write(self.style.ERROR(f"Djinni candidates parquet is missing expected columns: {missing}"))
            return

        # Drop rows with no CV text at all -- nothing for the parsing
        # pipeline to work with, and the whole point of importing real
        # data is to have real skill/experience extraction run on it.
        df = df[df["CV"].notna() & (df["CV"].str.strip() != "")]
        if limit:
            df = df.head(limit)

        org = get_public_dataset_org()
        total = len(df)
        self.stdout.write(f"Importing up to {total} Djinni candidate profiles...")

        created_candidates = []
        skipped = 0
        for i, (_, row) in enumerate(df.iterrows(), start=1):
            external_id = clean_text(row.get("id"))
            if not external_id or Candidate.objects.filter(source="djinni", external_id=external_id).exists():
                skipped += 1
                continue

            cv_text = clean_text(row.get("CV"))
            if is_duplicate_candidate_content(cv_text):
                skipped += 1
                continue

            summary = "\n\n".join(filter(None, [
                clean_text(row.get("Moreinfo")), clean_text(row.get("Looking For")), clean_text(row.get("Highlights")),
            ]))
            years = row.get("Experience Years")
            years_of_experience = float(years) if pd.notna(years) else 0.0

            candidate = Candidate.objects.create(
                sourced_by_organization=org,
                full_name=f"Djinni Candidate #{external_id[:8]}",
                email=make_imported_email(),
                current_title=truncate(clean_text(row.get("Position")), 255),
                years_of_experience=years_of_experience,
                summary=truncate(summary, 20_000),
                source="djinni",
                external_id=external_id,
                content_hash=content_hash_for(cv_text),
                is_synthetic=False,
            )
            process_candidate_text(candidate, cv_text)
            created_candidates.append(candidate)

            if i % 200 == 0:
                self.stdout.write(f"  Processed {i}/{total}...")

        self.stdout.write(f"Created {len(created_candidates)} candidates, skipped {skipped}.")

        if created_candidates:
            self.stdout.write("Embedding candidates (batched)...")
            embedded = embed_candidates_batch(created_candidates, batch_size=options["embed_batch"])
            self.stdout.write(f"Embedded {embedded} candidates.")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(created_candidates)} Djinni candidates imported."
        ))
