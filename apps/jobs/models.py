from django.db import models
from django.conf import settings


class JobPost(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"
        FILLED = "filled", "Filled"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"
        FREELANCE = "freelance", "Freelance"

    class ExperienceLevel(models.TextChoices):
        ENTRY = "entry", "Entry Level"
        MID = "mid", "Mid Level"
        SENIOR = "senior", "Senior Level"
        LEAD = "lead", "Lead / Principal"
        EXECUTIVE = "executive", "Executive"

    # Core fields
    title = models.CharField(max_length=300)
    company = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)

    # Location (global)
    country = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    region = models.CharField(max_length=200, blank=True)
    work_model = models.CharField(
        max_length=20,
        choices=[("onsite", "On-site"), ("remote", "Remote"), ("hybrid", "Hybrid")],
        default="onsite",
    )

    # Classification
    industry = models.CharField(max_length=255, blank=True)
    job_function = models.CharField(max_length=255, blank=True)
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME
    )
    experience_level = models.CharField(
        max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.MID
    )

    # Compensation
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default="USD")

    # Status & lifecycle
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    posted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)

    # Source tracking
    source = models.CharField(
        max_length=30,
        choices=[
            ("manual", "Manual"), ("adzuna", "Adzuna"), ("jooble", "Jooble"),
            ("the_muse", "The Muse"), ("synthetic", "Synthetic"), ("kaggle", "Kaggle"),
        ],
        default="manual",
    )
    external_id = models.CharField(max_length=255, blank=True)
    external_url = models.URLField(blank=True)

    # Creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_jobs",
    )

    is_synthetic = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobs_jobpost"
        ordering = ["-posted_at", "-created_at"]
        unique_together = [["source", "external_id"]]

    def __str__(self):
        return f"{self.title} @ {self.company}"


class JobSkillRequirement(models.Model):
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="skill_requirements")
    skill_name = models.CharField(max_length=200)
    skill_category = models.CharField(max_length=100, blank=True)
    is_required = models.BooleanField(default=True)
    min_years = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "jobs_skill_requirement"
        unique_together = [["job", "skill_name"]]

    def __str__(self):
        return f"{self.job.title}: {self.skill_name} ({'required' if self.is_required else 'preferred'})"


class JobEmbedding(models.Model):
    job = models.OneToOneField(JobPost, on_delete=models.CASCADE, related_name="embedding")
    vector = models.JSONField()
    model_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobs_embedding"

    def __str__(self):
        return f"Embedding: {self.job.title}"
