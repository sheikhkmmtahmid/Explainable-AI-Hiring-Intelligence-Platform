from django.contrib import admin
from .models import SkillTaxonomy, JobRoleTemplate


@admin.register(SkillTaxonomy)
class SkillTaxonomyAdmin(admin.ModelAdmin):
    list_display = ["canonical_name", "category", "subcategory", "is_technical"]
    list_filter = ["category", "is_technical"]
    search_fields = ["name", "canonical_name"]


@admin.register(JobRoleTemplate)
class JobRoleTemplateAdmin(admin.ModelAdmin):
    list_display = ["title", "industry", "typical_experience_years"]
    search_fields = ["title", "industry"]
    filter_horizontal = ["core_skills"]
