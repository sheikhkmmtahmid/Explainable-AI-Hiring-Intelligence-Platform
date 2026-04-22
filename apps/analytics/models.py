from django.db import models


class PipelineSnapshot(models.Model):
    """Daily snapshot of pipeline metrics for a job."""
    job = models.ForeignKey("jobs.JobPost", on_delete=models.CASCADE, related_name="snapshots")
    date = models.DateField()
    total_applications = models.IntegerField(default=0)
    screened_count = models.IntegerField(default=0)
    shortlisted_count = models.IntegerField(default=0)
    interview_count = models.IntegerField(default=0)
    offer_count = models.IntegerField(default=0)
    hired_count = models.IntegerField(default=0)
    rejected_count = models.IntegerField(default=0)
    avg_match_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_pipeline_snapshot"
        unique_together = [["job", "date"]]
        ordering = ["-date"]

    def __str__(self):
        return f"Snapshot {self.job.title} @ {self.date}"
