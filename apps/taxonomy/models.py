from django.conf import settings
from django.db import models


class SkillTaxonomy(models.Model):
    """Skill ontology inspired by ESCO/O*NET."""
    name = models.CharField(max_length=200, unique=True)
    canonical_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100, blank=True)
    aliases = models.JSONField(default=list)
    related_skills = models.ManyToManyField("self", blank=True, symmetrical=True)
    description = models.TextField(blank=True)
    is_technical = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "taxonomy_skill"
        ordering = ["category", "name"]
        verbose_name_plural = "Skill Taxonomies"

    def __str__(self):
        return f"{self.canonical_name} [{self.category}]"


class JobRoleTemplate(models.Model):
    """Standard job role definitions with typical skill sets."""
    title = models.CharField(max_length=200, unique=True)
    industry = models.CharField(max_length=100, blank=True)
    core_skills = models.ManyToManyField(SkillTaxonomy, related_name="core_roles", blank=True)
    typical_education = models.CharField(max_length=30, blank=True)
    typical_experience_years = models.FloatField(default=0.0)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "taxonomy_job_role"
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} ({self.industry})"


class PendingSkill(models.Model):
    """
    A candidate skill name awaiting review before it becomes a real
    SkillTaxonomy entry -- keeps automated discovery (ESCO sync, corpus
    mining) and free-typed "add new skill" submissions from a job posting
    from silently polluting the taxonomy with typos or duplicates.
    """

    class Source(models.TextChoices):
        ESCO_SYNC = "esco_sync", "ESCO Sync"
        CORPUS_MINING = "corpus_mining", "Corpus Mining"
        USER_SUBMITTED = "user_submitted", "User Submitted"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    proposed_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices)
    source_detail = models.CharField(
        max_length=255, blank=True,
        help_text="e.g. ESCO concept URI, or 'seen in 6 job postings'",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Populated by the dedup check at proposal time -- lets a reviewer see
    # "this looks like it might already be X" without re-running the check.
    similar_existing_skill = models.ForeignKey(
        SkillTaxonomy, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="pending_duplicates",
    )
    similarity_score = models.FloatField(null=True, blank=True)
    similarity_match_type = models.CharField(max_length=20, blank=True)  # exact | fuzzy | embedding

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="submitted_pending_skills",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="reviewed_pending_skills",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "taxonomy_pending_skill"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.proposed_name} ({self.status})"
