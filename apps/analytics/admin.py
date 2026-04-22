from django.contrib import admin
from .models import PipelineSnapshot


@admin.register(PipelineSnapshot)
class PipelineSnapshotAdmin(admin.ModelAdmin):
    list_display = ["job", "date", "total_applications", "shortlisted_count", "hired_count"]
    list_filter = ["date"]
