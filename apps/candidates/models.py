from django.db import models
from django.conf import settings


class Candidate(models.Model):
    class AvailabilityStatus(models.TextChoices):
        ACTIVELY_LOOKING = "actively_looking", "Actively Looking"
        OPEN = "open", "Open to Opportunities"
        NOT_LOOKING = "not_looking", "Not Looking"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
        null=True,
        blank=True,
    )
    # For synthetic candidates, no user account
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)

    # Location (global)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    remote_preference = models.CharField(
        max_length=20,
        choices=[("onsite", "On-site"), ("remote", "Remote"), ("hybrid", "Hybrid"), ("flexible", "Flexible")],
        default="flexible",
    )

    # Professional details
    current_title = models.CharField(max_length=255, blank=True)
    years_of_experience = models.FloatField(default=0.0)
    seniority_level = models.CharField(
        max_length=20,
        choices=[
            ("intern", "Intern"), ("junior", "Junior"), ("mid", "Mid-level"),
            ("senior", "Senior"), ("lead", "Lead"), ("principal", "Principal"),
            ("director", "Director"), ("executive", "Executive"),
        ],
        blank=True,
    )
    summary = models.TextField(blank=True)

    # Education
    highest_education = models.CharField(
        max_length=30,
        choices=[
            ("high_school", "High School"), ("associate", "Associate"),
            ("bachelor", "Bachelor's"), ("master", "Master's"),
            ("phd", "PhD"), ("other", "Other"),
        ],
        blank=True,
    )
    education_field = models.CharField(max_length=255, blank=True)

    # Status
    availability_status = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.OPEN,
    )
    expected_salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default="USD")

    # Protected attributes (for fairness analysis — stored but anonymised in outputs)
    gender = models.CharField(max_length=30, blank=True)
    age_range = models.CharField(max_length=20, blank=True)
    ethnicity = models.CharField(max_length=100, blank=True)
    disability_status = models.BooleanField(null=True)

    # Metadata
    is_synthetic = models.BooleanField(default=False)
    raw_cv_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidates_candidate"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.current_title})"


class CandidateCV(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="cvs")
    file = models.FileField(upload_to="cvs/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # pdf, docx, txt
    raw_text = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    parsed_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "candidates_cv"

    def __str__(self):
        return f"CV: {self.candidate.full_name} - {self.original_filename}"


class CandidateSkill(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="skills")
    skill_name = models.CharField(max_length=200)
    skill_category = models.CharField(max_length=100, blank=True)
    proficiency = models.CharField(
        max_length=20,
        choices=[
            ("beginner", "Beginner"), ("intermediate", "Intermediate"),
            ("advanced", "Advanced"), ("expert", "Expert"),
        ],
        blank=True,
    )
    years_used = models.FloatField(null=True, blank=True)
    source = models.CharField(
        max_length=20,
        choices=[("cv_parsed", "CV Parsed"), ("manual", "Manual"), ("inferred", "Inferred")],
        default="cv_parsed",
    )

    class Meta:
        db_table = "candidates_skill"
        unique_together = [["candidate", "skill_name"]]

    def __str__(self):
        return f"{self.candidate.full_name}: {self.skill_name}"


class CandidateExperience(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="experiences")
    job_title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "candidates_experience"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.candidate.full_name}: {self.job_title} @ {self.company}"


class CandidateEmbedding(models.Model):
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name="embedding")
    vector = models.JSONField()  # stored as list of floats
    model_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidates_embedding"

    def __str__(self):
        return f"Embedding: {self.candidate.full_name}"
