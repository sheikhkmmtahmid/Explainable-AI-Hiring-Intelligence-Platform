from django.db import models


class MatchResult(models.Model):
    candidate = models.ForeignKey(
        "candidates.Candidate", on_delete=models.CASCADE, related_name="match_results"
    )
    job = models.ForeignKey(
        "jobs.JobPost", on_delete=models.CASCADE, related_name="match_results"
    )
    overall_score = models.FloatField()
    semantic_score = models.FloatField(default=0.0)
    skill_overlap_score = models.FloatField(default=0.0)
    experience_score = models.FloatField(default=0.0)
    education_score = models.FloatField(default=0.0)
    rank = models.IntegerField(null=True, blank=True)
    # Hiring outcome label -- null = unknown, True = hired, False = rejected.
    # Populated by recruiters after a decision is made. Used to train the ML scorer.
    hired = models.BooleanField(null=True, blank=True, db_index=True)
    model_version = models.CharField(max_length=50, default="v1")
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "matching_result"
        unique_together = [["candidate", "job"]]
        ordering = ["-overall_score"]

    def __str__(self):
        return f"{self.candidate.full_name} ↔ {self.job.title}: {self.overall_score:.3f}"


class MatchBatchRun(models.Model):
    job = models.ForeignKey(
        "jobs.JobPost", on_delete=models.CASCADE, related_name="match_runs"
    )
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("running", "Running"), ("done", "Done"), ("failed", "Failed")],
        default="pending",
    )
    candidates_processed = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "matching_batch_run"
        ordering = ["-created_at"]

    def __str__(self):
        return f"MatchBatch for {self.job.title} ({self.status})"
