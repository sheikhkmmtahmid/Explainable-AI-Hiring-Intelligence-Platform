from django.contrib import admin

from .models import MatchResult, MatchBatchRun


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ["candidate", "job", "overall_score", "rank", "hired", "computed_at"]
    list_display_links = ["candidate", "job"]
    list_editable = ["hired"]
    list_filter = ["model_version", "hired"]
    search_fields = ["candidate__full_name", "job__title"]


@admin.register(MatchBatchRun)
class MatchBatchRunAdmin(admin.ModelAdmin):
    list_display = ["job", "status", "candidates_processed", "started_at", "completed_at"]
    list_filter = ["status"]
