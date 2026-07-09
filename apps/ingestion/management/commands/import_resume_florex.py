"""
Imports real resumes from florex/resume_corpus (CC0-1.0 licensed), an
academic multi-labeled resume corpus from Jiechieu & Tsopze (2020),
"Skills prediction based on multi-label resume classification using CNN
with model predictions explanation."

Source: https://github.com/florex/resume_corpus

The zip contains paired <id>.txt (resume text, with some `<span class="hl">`
HTML highlight artifacts to strip) and <id>.lab (occupation label) files.

Runs the same CV-parsing pipeline as a real upload (skill/experience
extraction + SBERT embedding) so these candidates are fully matchable.

Usage:
    python manage.py import_resume_florex --limit 2000
    python manage.py import_resume_florex --limit 0   # unlimited (~29,000 rows)
"""
import logging
import re
import zipfile
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

ZIP_URL = "https://raw.githubusercontent.com/florex/resume_corpus/master/resumes_corpus.zip"
CACHE_PATH = Path("data/dataset_cache/florex_resumes_corpus.zip")

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _download(stdout) -> Path:
    import requests

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_PATH.exists():
        stdout.write(f"Using cached file: {CACHE_PATH}")
        return CACHE_PATH

    stdout.write(f"Downloading {ZIP_URL} ...")
    resp = requests.get(ZIP_URL, timeout=120)
    resp.raise_for_status()
    CACHE_PATH.write_bytes(resp.content)
    stdout.write(f"Saved to {CACHE_PATH} ({len(resp.content):,} bytes)")
    return CACHE_PATH


class Command(BaseCommand):
    help = "Import real resumes from florex/resume_corpus (CC0)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=2000, help="Max rows to import (0 = unlimited)")
        parser.add_argument("--embed-batch", type=int, default=64, help="SBERT encode batch size")

    def handle(self, *args, **options):
        from apps.candidates.models import Candidate
        from apps.ingestion.dataset_import import (
            content_hash_for, embed_candidates_batch, get_public_dataset_org,
            is_duplicate_candidate_content, make_imported_email, process_candidate_text, truncate,
        )

        limit = options["limit"]
        zip_path = _download(self.stdout)

        with zipfile.ZipFile(zip_path) as z:
            stems = sorted({Path(n).stem for n in z.namelist() if n.endswith(".txt")})
            if limit:
                stems = stems[:limit]

            org = get_public_dataset_org()
            total = len(stems)
            self.stdout.write(f"Importing up to {total} florex resumes...")

            created_candidates = []
            skipped = 0
            for i, stem in enumerate(stems, start=1):
                external_id = stem
                if Candidate.objects.filter(source="florex", external_id=external_id).exists():
                    skipped += 1
                    continue

                try:
                    raw_txt = z.read(f"{stem}.txt").decode("utf-8", errors="ignore")
                    label = z.read(f"{stem}.lab").decode("utf-8", errors="ignore").strip()
                except KeyError:
                    skipped += 1
                    continue

                resume_text = _HTML_TAG_RE.sub(" ", raw_txt).strip()
                if not resume_text:
                    skipped += 1
                    continue
                if is_duplicate_candidate_content(resume_text):
                    skipped += 1
                    continue

                occupation = label.replace("_", " ").title()

                candidate = Candidate.objects.create(
                    sourced_by_organization=org,
                    full_name=f"Resume Corpus Candidate #{external_id}",
                    email=make_imported_email(),
                    current_title=truncate(occupation, 255),
                    source="florex",
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
            f"\nDone. {len(created_candidates)} florex resume candidates imported."
        ))
