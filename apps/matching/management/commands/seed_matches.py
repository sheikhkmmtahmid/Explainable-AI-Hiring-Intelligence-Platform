"""
Generate SBERT embeddings for all jobs that lack them, then pre-seed
MatchResult rows for a random sample of jobs.

Usage:
    python manage.py seed_matches                    # embed all jobs, match 150
    python manage.py seed_matches --match-jobs 0    # embed only, no matching
    python manage.py seed_matches --match-jobs 300
"""
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

EMBED_BATCH = 64   # SBERT encode_batch size
DB_BATCH    = 200  # bulk_create chunk size


class Command(BaseCommand):
    help = "Embed all jobs + pre-seed match results for a job sample"

    def add_arguments(self, parser):
        parser.add_argument(
            "--match-jobs", type=int, default=150,
            help="Number of jobs to run batch-matching for (0 = skip)",
        )

    def handle(self, *args, **options):
        self._generate_job_embeddings()
        n = options["match_jobs"]
        if n > 0:
            self._seed_match_results(n)

    # ------------------------------------------------------------------
    def _generate_job_embeddings(self):
        from apps.jobs.models import JobPost, JobEmbedding
        from ml.embeddings.encoder import encode_batch, get_model_name

        qs = JobPost.objects.filter(embedding__isnull=True).values_list(
            "id", "title", "description", "requirements"
        )
        total = qs.count()
        if total == 0:
            self.stdout.write("All jobs already have embeddings.")
            return

        self.stdout.write(f"Generating embeddings for {total} jobs...")
        model_name = get_model_name()

        ids, texts = [], []
        processed = 0

        def _flush():
            nonlocal processed
            vectors = encode_batch(texts, batch_size=EMBED_BATCH)
            objs = [
                JobEmbedding(job_id=jid, vector=vec.tolist(), model_name=model_name)
                for jid, vec in zip(ids, vectors)
            ]
            # Insert in smaller DB chunks to avoid huge single INSERT
            for start in range(0, len(objs), DB_BATCH):
                JobEmbedding.objects.bulk_create(
                    objs[start:start + DB_BATCH], ignore_conflicts=True
                )
            processed += len(ids)
            ids.clear()
            texts.clear()
            if processed % 1000 == 0 or processed == total:
                self.stdout.write(f"  {processed}/{total} embeddings done")

        for job_id, title, description, requirements in qs.iterator(chunk_size=EMBED_BATCH):
            text = f"{title}\n{description or ''}\n{requirements or ''}".strip()
            ids.append(job_id)
            texts.append(text)
            if len(ids) >= EMBED_BATCH:
                _flush()

        if ids:
            _flush()

        self.stdout.write(self.style.SUCCESS(f"Embeddings complete: {processed} generated"))

    # ------------------------------------------------------------------
    def _seed_match_results(self, n: int):
        from apps.jobs.models import JobPost
        from apps.matching.services import run_batch_matching_for_job

        jobs = list(
            JobPost.objects.filter(embedding__isnull=False, status="active")
            .order_by("?")[:n]
        )
        total = len(jobs)
        self.stdout.write(f"Running batch matching for {total} jobs...")

        for i, job in enumerate(jobs, 1):
            count = run_batch_matching_for_job(job.id)
            if i % 10 == 0 or i == total:
                self.stdout.write(f"  {i}/{total} — {job.title} ({count} matches)")

        self.stdout.write(self.style.SUCCESS(f"Matching complete: {total} jobs seeded"))
