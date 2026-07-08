"""
Generates SBERT embeddings for any JobPost missing a JobEmbedding row.

Batch-encodes with the SBERT model directly (rather than dispatching one
Celery task per job) since this is typically a one-off bulk operation over
thousands of rows.

Usage:
    python manage.py backfill_job_embeddings
    python manage.py backfill_job_embeddings --batch 100
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Backfill SBERT embeddings for jobs that don't have one yet"

    def add_arguments(self, parser):
        parser.add_argument("--batch", type=int, default=64, help="SBERT encode batch size")

    def handle(self, *args, **options):
        from apps.jobs.models import JobPost, JobEmbedding
        from ml.embeddings.encoder import encode_batch, get_model_name

        batch_size = options["batch"]

        jobs = list(JobPost.objects.filter(embedding__isnull=True).only(
            "id", "title", "description", "requirements"
        ))
        total = len(jobs)
        self.stdout.write(f"Backfilling embeddings for {total} jobs...")

        if not total:
            self.stdout.write(self.style.SUCCESS("Nothing to do."))
            return

        model_name = get_model_name()
        created = 0

        for start in range(0, total, batch_size):
            chunk = jobs[start:start + batch_size]
            texts = [f"{j.title}\n{j.description}\n{j.requirements}" for j in chunk]
            vectors = encode_batch(texts, batch_size=batch_size)

            JobEmbedding.objects.bulk_create(
                [
                    JobEmbedding(job=j, vector=vec.tolist(), model_name=model_name)
                    for j, vec in zip(chunk, vectors)
                ],
                ignore_conflicts=True,
            )
            created += len(chunk)
            self.stdout.write(f"  Embedded {created}/{total}...")

        self.stdout.write(self.style.SUCCESS(f"\nDone. {created} job embeddings created."))
