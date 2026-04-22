from django.contrib import admin

from .models import JobPost, JobSkillRequirement


class JobSkillInline(admin.TabularInline):
    model = JobSkillRequirement
    extra = 0


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "country", "employment_type", "experience_level", "status", "source"]
    list_filter = ["status", "employment_type", "experience_level", "work_model", "source", "is_synthetic"]
    search_fields = ["title", "company", "country", "city"]
    inlines = [JobSkillInline]
