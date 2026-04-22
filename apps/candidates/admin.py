from django.contrib import admin

from .models import Candidate, CandidateCV, CandidateSkill, CandidateExperience, CandidateEmbedding


class CandidateSkillInline(admin.TabularInline):
    model = CandidateSkill
    extra = 0


class CandidateExperienceInline(admin.TabularInline):
    model = CandidateExperience
    extra = 0


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "current_title", "country", "years_of_experience", "is_synthetic"]
    list_filter = ["is_synthetic", "seniority_level", "availability_status", "country"]
    search_fields = ["full_name", "email", "current_title"]
    inlines = [CandidateSkillInline, CandidateExperienceInline]


@admin.register(CandidateCV)
class CandidateCVAdmin(admin.ModelAdmin):
    list_display = ["candidate", "original_filename", "file_type", "is_primary", "uploaded_at"]
    list_filter = ["file_type", "is_primary"]
