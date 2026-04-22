from django.db import models


class IngestionRun(models.Model):
    class Source(models.TextChoices):
        ADZUNA = "adzuna", "Adzuna"
        JOOBLE = "jooble", "Jooble"
        THE_MUSE = "the_muse", "The Muse"
        KAGGLE = "kaggle", "Kaggle"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    source = models.CharField(max_length=20, choices=Source.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    query = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=5, default="gb")
    jobs_fetched = models.IntegerField(default=0)
    jobs_created = models.IntegerField(default=0)
    jobs_skipped = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ingestion_run"
        ordering = ["-created_at"]

    def __str__(self):
        return f"IngestionRun [{self.source}] {self.status} ({self.jobs_created} created)"
