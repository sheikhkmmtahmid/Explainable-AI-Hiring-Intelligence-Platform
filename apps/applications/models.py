from django.db import models
from django.conf import settings


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        SHORTLISTED = "shortlisted", "Shortlisted"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer Extended"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    candidate = models.ForeignKey(
        "candidates.Candidate", on_delete=models.CASCADE, related_name="applications"
    )
    job = models.ForeignKey(
        "jobs.JobPost", on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NOTE: match scores (overall/semantic/skill/experience/education/rank) are
    # intentionally NOT stored here. They live on MatchResult and are looked
    # up live by the serializer -- storing a second copy risks it going stale
    # whenever a job gets re-matched. See ApplicationSerializer.

    # Recruiter actions
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reviewed_applications",
    )
    recruiter_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Fairness flag
    is_synthetic = models.BooleanField(default=False)

    class Meta:
        db_table = "applications_application"
        ordering = ["-applied_at"]
        unique_together = [["candidate", "job"]]

    def __str__(self):
        return f"{self.candidate.full_name} → {self.job.title} ({self.status})"


class ApplicationStatusHistory(models.Model):
    """
    Every status transition an application goes through, kept forever
    (Application.status/reviewed_by/reviewed_at only holds the CURRENT
    state -- each change here overwrote the last, leaving no trail of who
    actually decided what). This is what makes a real fairness audit
    possible: "were our actual hiring decisions fair" needs to know who
    got shortlisted/rejected and by whom, not just today's snapshot.
    """
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="application_status_changes",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "applications_status_history"
        ordering = ["-changed_at"]
        verbose_name_plural = "Application status histories"

    def __str__(self):
        return f"{self.application_id}: {self.from_status} -> {self.to_status}"


class ApplicationNote(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "applications_note"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.application}"


class InterviewSlot(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="interview_slots")
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    interview_type = models.CharField(
        max_length=20,
        choices=[
            ("phone", "Phone Screen"), ("video", "Video Call"),
            ("technical", "Technical"), ("final", "Final Round"),
        ],
        default="video",
    )
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    outcome = models.CharField(
        max_length=20,
        choices=[("passed", "Passed"), ("failed", "Failed"), ("pending", "Pending")],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "applications_interview"
