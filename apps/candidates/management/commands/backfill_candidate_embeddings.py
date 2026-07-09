"""
Generates SBERT embeddings for any Candidate missing a CandidateEmbedding row.

Batch-encodes with the SBERT model directly (rather than dispatching one
Celery task per candidate) since this is typically a one-off bulk operation
over thousands of rows. Mirrors
apps/jobs/management/commands/backfill_job_embeddings.py.

Usage:
    python manage.py backfill_candidate_embeddings
    python manage.py backfill_candidate_embeddings --batch 100
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Backfill SBERT embeddings for candidates that don't have one yet"

    def add_arguments(self, parser):
        parser.add_argument("--batch", type=int, default=64, help="SBERT encode batch size")

    def handle(self, *args, **options):
        from apps.ingestion.dataset_import import embed_candidates_batch
        from apps.candidates.models import Candidate

        batch_size = options["batch"]

        candidates = list(
            Candidate.objects.filter(embedding__isnull=True)
            .prefetch_related("skills", "experiences")
        )
        total = len(candidates)
        self.stdout.write(f"Backfilling embeddings for {total} candidates...")

        if not total:
            self.stdout.write(self.style.SUCCESS("Nothing to do."))
            return

        created = embed_candidates_batch(candidates, batch_size=batch_size)
        self.stdout.write(self.style.SUCCESS(f"\nDone. {created} candidate embeddings created."))
