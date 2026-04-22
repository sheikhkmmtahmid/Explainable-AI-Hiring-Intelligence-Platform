from django.db import models


class ParseJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    cv = models.ForeignKey(
        "candidates.CandidateCV", on_delete=models.CASCADE, related_name="parse_jobs"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "parsing_parsejob"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ParseJob #{self.id} ({self.status})"
