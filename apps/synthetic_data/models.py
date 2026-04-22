from django.db import models


class SyntheticGenerationRun(models.Model):
    class Kind(models.TextChoices):
        CANDIDATES = "candidates", "Candidates"
        JOBS = "jobs", "Jobs"
        APPLICATIONS = "applications", "Applications"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    count_requested = models.IntegerField()
    count_created = models.IntegerField(default=0)
    config = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("running", "Running"), ("done", "Done"), ("failed", "Failed")],
        default="pending",
    )
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "synthetic_generation_run"
        ordering = ["-created_at"]

    def __str__(self):
        return f"SyntheticRun [{self.kind}] {self.count_created}/{self.count_requested}"
