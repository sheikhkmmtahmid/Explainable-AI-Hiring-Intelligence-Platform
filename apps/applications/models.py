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

    # Scores
    overall_match_score = models.FloatField(null=True, blank=True)
    semantic_score = models.FloatField(null=True, blank=True)
    skill_overlap_score = models.FloatField(null=True, blank=True)
    experience_score = models.FloatField(null=True, blank=True)
    education_score = models.FloatField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)

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
        ordering = ["-overall_match_score", "-applied_at"]
        unique_together = [["candidate", "job"]]

    def __str__(self):
        return f"{self.candidate.full_name} → {self.job.title} ({self.status})"


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
