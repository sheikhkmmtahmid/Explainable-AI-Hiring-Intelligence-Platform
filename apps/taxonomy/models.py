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
